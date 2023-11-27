from logging import Logger
from pathlib import Path
from time import sleep
from typing import Optional, Union

from fastapi import BackgroundTasks, HTTPException
from requests import get
from sqlalchemy.exc import InvalidRequestError, OperationalError
from sqlalchemy.orm import Session
from app.database.query import (
    get_all_templates, get_font, get_interface, get_sync
)

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.cards import create_episode_cards, get_watched_statuses, refresh_remote_card_types
from app.internal.episodes import refresh_episode_data
from app.internal.sources import download_episode_source_images, download_series_logo
from app.internal.translate import translate_episode
from app.models.card import Card
from app.models.episode import Episode
from app.models.loaded import Loaded
from app.models.series import Series
from app.schemas.base import UNSPECIFIED
from app.schemas.connection import EpisodeDataSourceInterface
from app.schemas.series import NewSeries, SearchResult, UpdateSeries

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface


def set_all_series_ids(*, log: Logger = log) -> None:
    """
    Schedule-able function to set any missing Series ID's for all Series
    in the Database.

    Args:
        log: Logger for all log messages.
    """

    try:
        with next(get_database()) as db:
            # Get all Series
            changed = False
            for series in db.query(Series).all():
                try:
                    changed |= set_series_database_ids(series, db, commit=False)
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping ID assignment')
                    continue

            # Commit changes if any were made
            if changed:
                db.commit()
    except Exception as e:
        log.exception(f'Failed to set Series IDs', e)


def load_all_media_servers(*, log: Logger = log) -> None:
    """
    Schedule-able function to load all Title Cards in the Database to
    the media servers.

    Args:
        log: Logger for all log messages.
    """

    try:
        # Get the Database
        retries = 0
        with next(get_database()) as db:
            # Get all Series
            for series in db.query(Series).all():
                # Skip this Series if it has no library
                if not series.libraries:
                    log.debug(f'{series.log_str} has no Library, not loading Title Cards')
                    continue

                # Load Title Cards for this Series
                try:
                    load_all_series_title_cards(series, db, log=log)
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping Title Card loading')
                    continue
                except OperationalError:
                    if (retries := retries + 1) > 10:
                        log.warning(f'Database is very busy - stopping Task')
                        break
                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to load Title Cards', e)


def download_all_series_posters(*, log: Logger = log) -> None:
    """
    Schedule-able function to download all posters for all monitored
    Series in the Database.

    Args:
        log: Logger for all log messages.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            for series in db.query(Series).all():
                try:
                    download_series_poster(db, series, log=log)
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping poster selection')
                    continue
    except Exception as e:
        log.exception(f'Failed to download Series posters', e)


def set_series_database_ids(
        series: Series,
        db: Session,
        *,
        commit: bool = True,
        log: Logger = log,
    ) -> bool:
    """
    Set the database IDs of the given Series.

    Args:
        series: Series to set the IDs of.
        db: Database to commit changes to.
        commit: Whether to commit changes after setting any IDs.
        log: Logger for all log messages.

    Returns:
        Whether the Series was modified.
    """

    # Create SeriesInfo object for this entry, query all interfaces
    series_info = series.as_series_info
    for library in series.libraries:
        if (interface := get_interface(library['interface_id'])):
            interface.set_series_ids(library['name'], series_info, log=log)
    for _, interface in get_sonarr_interfaces():
        interface.set_series_ids(None, series_info, log=log)
    for _, interface in get_tmdb_interfaces():
        interface.set_series_ids(None, series_info, log=log)

    # Update Series with new IDs
    if (changed := series.update_from_series_info(series_info)) and commit:
        db.commit()

    return changed


def download_series_poster(
        db: Session,
        series: Series,
        *,
        log: Logger = log,
    ) -> None:
    """
    Download the poster for the given Series.

    Args:
        db: Database to commit any changes to.
        series: Series to download the poster of.
        log: Logger for all log messages.
    """

    # If Series poster exists and is not a placeholder, return
    path = Path(series.poster_file)
    if path.name != 'placeholder.jpg' and path.exists():
        poster_url = f'/assets/{series.id}/poster.jpg'
        if series.poster_url != poster_url:
            series.poster_url = poster_url
            db.commit()
        return None

    # Download poster from Media Server if possible
    series_info, poster = series.as_series_info, None
    for library in series.libraries:
        if (interface := get_interface(library['interface_id'])):
            poster = interface.get_series_poster(
                library['name'], series_info, log=log
            )

        # Stop if poster was found
        if poster is not None:
            break

    # If no poster was returned, download from TMDb
    if poster is None:
        for _, interface in get_tmdb_interfaces():
            if (poster := interface.get_series_poster(series_info, log=log)):
                break

    # If no posters were returned, log and exit
    if poster is None:
        log.warning(f'{series.log_str} no posters found')
        return None

    # Get path to the poster to download
    path = get_preferences().asset_directory / str(series.id) / 'poster.jpg'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Write or download
        if isinstance(poster, bytes):
            path.write_bytes(poster)
        else:
            path.write_bytes(get(poster, timeout=30).content)
    except Exception as e:
        log.error(f'{series.log_str} Error downloading poster', e)
        return None
    series.poster_file = str(path)
    series.poster_url = f'/assets/{series.id}/poster.jpg'
    db.commit()

    # Create resized small poster
    resized_path = path.parent / 'poster-750.jpg'
    get_imagemagick_interface().resize_image(
        path, resized_path, by='width', width=750,
    )

    log.debug(f'Series[{series.id}] Downloaded poster {path.resolve()}')
    return None


def process_series(
        db: Session,
        series: Series,
        background_tasks: BackgroundTasks,
        *,
        log: Logger = log,
    ) -> None:
    """
    Completely process the given Series. This does all Title-Card tasks
    except loading the Cards.

    Args:
        db: Database connection.
        series: Series being processed.
        background_tasks: BackgroundTasks to queue processing into.
    """

    # Begin processing the Series
    # Refresh episode data, use BackgroundTasks for ID assignment
    log.debug(f'{series.log_str} Started refreshing Episode data')
    refresh_episode_data(db, series, log=log)

    # Update watch statuses
    get_watched_statuses(db, series, series.episodes, log=log)

    # Begin downloading Source images - use BackgroundTasks
    log.debug(f'{series.log_str} Started downloading source images')
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            download_episode_source_images,
            # Arguments
            db, episode, commit=False, raise_exc=False, log=log,
        )

    # Begin Episode translation - use BackgroundTasks
    log.debug(f'{series.log_str} Started adding translations')
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            translate_episode,
            # Arguments
            db, episode, commit=False, log=log,
        )
    db.commit()

    # Begin Card creation - use BackgroundTasks
    log.debug(f'{series.log_str} Starting Card creation')
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            create_episode_cards,
            # Arguments
            db, background_tasks, episode, raise_exc=False, log=log
        )


def update_series(
        db: Session,
        series: Series,
        update_series: UpdateSeries,
        *,
        commit: bool = True,
        log: Logger = log,
    ) -> bool:
    """
    Update the given Series with the changes defined in update_series.
    This verifies any specified Fonts or Templates exist.

    Args:
        db: Database to query for Font or Template objects and to
            commit changes to.
        series: Series to modify.
        update_series: Object defining changes to make to the Series.
        commit: Whether to commit any changes to the database.
        log: Logger for all log messages.

    Returns:
        Whether the given Series was modified.
    """

    # Get object as dictionary
    update_series_dict = update_series.dict()

    # If a Font is indicated, verify it exists
    get_font(db, update_series_dict.get('font_id', None), raise_exc=True)

    # Assign Templates if indicated
    changed = False
    if ((template_ids := update_series_dict.get('template_ids', None))
        not in (None, UNSPECIFIED)):
        if series.template_ids != template_ids:
            templates = get_all_templates(db, update_series_dict)
            series.assign_templates(templates, log=log)
            changed = True

    # Update each attribute of the object
    for attr, value in update_series_dict.items():
        if value != UNSPECIFIED and getattr(series, attr) != value:
            log.debug(f'Series[{series.id}].{attr} = {value}')
            setattr(series, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        refresh_remote_card_types(db, log=log)
        if commit:
            db.commit()

    return changed


def delete_series(
        db: Session,
        series: Series,
        *,
        commit_changes: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Delete the given Series, poster, and all child (Episode, Card, and
    Loaded) objects.

    Args:
        db: Database to commit any deletion to.
        series: Series to delete.
        commit_changes: Whether to commit Database changes.
        log: Logger for all log messages.
    """

    # Delete poster if not the placeholder
    series_poster = Path(series.poster_file)
    if series_poster.stem != 'placeholder' and series_poster.exists():
        series_poster.unlink(missing_ok=True)
        small_poster = series_poster.parent / 'poster-750.jpg'
        small_poster.unlink(missing_ok=True)

        log.debug(f'{series.log_str} Deleted poster(s)')

    # Delete Series; all child objects are deleted on cascade
    log.info(f'Deleting {series.log_str}')
    db.delete(series)

    # Commit changes if indicated
    if commit_changes:
        db.commit()


def load_series_title_cards(
        series: Series,
        library_name: str,
        interface_id: int,
        db: Session,
        interface: Union[EmbyInterface, JellyfinInterface, PlexInterface],
        force_reload: bool = False,
        *,
        log: Logger = log,
    ) -> None:
    """
    Load the Title Cards for the given Series into the associated
    library.

    Args:
        series: Series to load the Title Cards of.
        media_server: Where to load the Title Cards into.
        db: Database to look for and add Loaded records from/to.
        interface: Interfaces to the applicable Media Server to load
            Title Cards into.
        force_reload: Whether to reload Title Cards even if no changes
            are detected.
        log: Logger for all log messages.
    """

    # Determine if in single-library mode
    single_library_mode = (
        get_preferences().library_unique_cards or len(series.libraries) == 1
    )

    # Get list of Episodes to reload
    changed, episodes_to_load = False, []
    for episode in series.episodes:
        # Get associated Card
        if single_library_mode:
            card = db.query(Card).filter_by(episode_id=episode.id).first()
        else:
            card = db.query(Card)\
                .filter_by(episode_id=episode.id,
                           interface_id=interface_id,
                           library_name=library_name)\
                .first()

        # Only load if Episode has a Card
        if not card:
            log.debug(f'{series} {episode} - no associated Card')
            continue

        # Find existing associated Loaded object
        if single_library_mode:
            previously_loaded = db.query(Loaded).filter_by(card_id=card.id).all()
        else:
            previously_loaded = db.query(Loaded)\
                .filter_by(card_id=card.id,
                           interface_id=interface_id,
                           library_name=library_name)\
                .all()

        # No previously loaded Cards, load
        if not previously_loaded:
            episodes_to_load.append((episode, card))
            continue

        # There is a previously loaded Card, delete entry, reload
        if force_reload or (previously_loaded[0].filesize != card.filesize):
            # Delete previously loaded entries for this server
            for loaded in previously_loaded:
                db.delete(loaded)
            changed = True
            episodes_to_load.append((episode, card))
        # >1 loaded entry for this Card, delete first entries
        elif len(previously_loaded) > 1:
            for loaded in previously_loaded[:-1]:
                log.debug(f'Deleted {loaded}')
                db.delete(loaded)
        # Episode does not need to be reloaded
        else:
            continue

    # Load into indicated interface
    loaded_assets = interface.load_title_cards(
        library_name, series.as_series_info, episodes_to_load, log=log,
    )

    # Update database with loaded entries
    for loaded_episode, loaded_card in loaded_assets:
        try:
            db.add(Loaded(
                card_id=loaded_card.id,
                episode_id=loaded_episode.id,
                interface_id=interface_id,
                series_id=series.id,
                filesize=loaded_card.filesize,
                library_name=library_name,
            ))
            log.debug(f'{series} {loaded_episode} Loaded {card} into "{library_name}"')
        except InvalidRequestError:
            log.warning(f'Error creating Loaded asset for {loaded_episode} {card}')
            continue

    # If any cards were (re)loaded, commit updates to database
    if changed or loaded_assets:
        db.commit()
        log.info(f'{series} Loaded {len(loaded_assets)} Cards into "{library_name}"')


def load_all_series_title_cards(
        series: Series,
        db: Session,
        force_reload: bool = False,
        *,
        log: Logger = log,
    ) -> None:
    """
    Load the Title Cards for the given Series into all the Series
    assigned libraries and Connections.

    Args:
        series: Series to load the Cards of.
        media_server: Where to load the Cards into.
        db: Database to look for and add Loaded records from/to.
        force_reload: Whether to reload Cards even if no changes are
            detected.
        log: Logger for all log messages.
    """

    # Load into each assigned library
    for library in series.libraries:
        interface_id = library['interface_id']
        if (interface := get_interface(interface_id)):
            load_series_title_cards(
                series, library['name'], interface_id, db, interface,
                force_reload=force_reload, log=log,
            )
        else:
            raise HTTPException(
                status_code=409,
                detail=f'Unable to communicate with Connection {interface_id}',
            )


def load_episode_title_card(
        episode: Episode,
        db: Session,
        library_name: str,
        interface_id: int,
        interface: Union[EmbyInterface, JellyfinInterface, PlexInterface],
        *,
        attempts: int = 1,
        log: Logger = log,
    ) -> Optional[bool]:
    """
    Load the Title Card for the given Episode into the indicated media
    server. This is a forced reload, and any existing Loaded assets are
    deleted.

    Args:
        episode: Episode to load the Title Card of.
        db: Database to look for and add Loaded records from/to.
        media_server: Which media server to load Title Cards into.
        *_interface: Interface to load Title Cards into.
        attempts: How many times to attempt loading the given Card.
        log: Logger for all log messages.

    Returns:
        Whether the Episode's Card was loaded or not. None if there is
        no Card.
    """

    # Only load if Episode has a Card
    # Get associated Card
    card = db.query(Card)\
        .filter_by(episode_id=episode.id,
                    interface_id=interface_id,
                    library_name=library_name)\
        .first()

    # Only load if Episode has a Card
    if not card:
        log.debug(f'{episode.series} {episode} - no associated Card')
        return None

    # Get previously loaded asset for comparison
    previously_loaded = db.query(Loaded)\
        .filter_by(episode_id=episode.id,
                   interface_id=interface_id,
                   library_name=library_name)\
        .first()

    # If this asset's filesize has not changed, no need to reload
    if (previously_loaded is not None
        and previously_loaded.filesize == card.filesize):
        return True

    # New Card is different, delete Loaded entry
    if previously_loaded is not None:
        db.delete(previously_loaded)

    loaded_assets = []
    for _ in range(attempts):
        # Load Episode's Card; exit loop if loaded
        loaded_assets = interface.load_title_cards(
            library_name,
            episode.series.as_series_info,
            [(episode, card)],
            log=log,
        )
        if loaded_assets:
            break

        log.debug(f'{episode.series.log_str} {episode.log_str} not found - waiting')
        sleep(30)

    # Episode was not loaded, exit
    if not loaded_assets:
        return False

    # Episode loaded, create Loaded asset and commit to database
    db.add(Loaded(
        card_id=card.id,
        episode_id=episode.id,
        interface_id=interface_id,
        series_id=episode.series.id,
        filesize=card.filesize,
        library_name=library_name,
    ))
    log.debug(f'{episode.series} {episode} Loaded {card} into "{library_name}"')
    db.commit()
    return True


def add_series(
        new_series: NewSeries,
        background_tasks: BackgroundTasks,
        db: Session,
        *,
        log: Logger = log,
    ) -> Series:
    """
    Add the given NewSeries object to the database, and then perform all
    the initial Series processing - e.g. setting Series ID's,
    downloading a poster and logo, and refreshing Episode data.

    Args:
        new_series: NewSeries to add to the Database.
        background_tasks: BackgroundTasks to add the Episode data refresh
            task to.
        db: Database to add the Series to.
        *_interface: Interface to query.
        log: Logger for all log messages.

    Returns:
        The Created Series.

    Raises:
        HTTPException (404): Any specified linked objects do not exist.
    """

    # Convert object to dictionary
    new_series_dict = new_series.dict()

    # If a Font, Sync, or any Templates were indicated, verify they exist
    get_font(db, getattr(new_series, 'font_id', None), raise_exc=True)
    get_sync(db, getattr(new_series_dict, 'sync_id', None), raise_exc=True)
    templates = get_all_templates(db, new_series_dict, raise_exc=True)

    # Add to database
    series = Series(**new_series_dict)
    db.add(series)
    db.commit()
    log.info(f'Added {series.log_str} to Database')

    # Assign Templates
    series.assign_templates(templates, log=log)
    db.commit()

    # Create source directory if DNE
    Path(series.source_directory).mkdir(parents=True, exist_ok=True)

    # Set Series ID's, download poster and logo
    set_series_database_ids(series, db, log=log)
    download_series_poster(db, series, log=log)
    download_series_logo(series, log=log)

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    # Refresh Episode data
    background_tasks.add_task(
        # Function
        refresh_episode_data,
        # Arguments
        db, series, background_tasks=background_tasks, log=log,
    )

    return series


def lookup_series(
        db: Session,
        interface: EpisodeDataSourceInterface,
        name: str,
        *,
        max_results: int = 25,
        log: Logger = log,
    ) -> list[SearchResult]:
    """
    Get all the search results for the given name on the given
    interface.

    Args:
        db: Database to query for whether the Series exists or not.
        interface: Interface to query for results.
        max_results: Maximum number of results to return.
        log: Logger for all log messages.

    Returns:
        Search results from the specified Interface for the given
        Series name.
    """

    # Query Interface
    results = interface.query_series(name, log=log)[:max_results]

    # Update added attribute(s)
    for result in results:
        # Query database for this result
        existing = db.query(Series)\
            .filter(result.series_info.filter_conditions(Series))\
            .first()

        # Result has been added if there is an existing Series
        result.added = existing is not None

    return results
