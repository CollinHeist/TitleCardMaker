from logging import Logger

from sqlalchemy.sql import func

from app.dependencies import get_database, get_preferences
from app import models
from app.schemas.statistic import NewSnapshot


from modules.Debug import log


def snapshot_database(*, log: Logger = log) -> None:
    """
    _summary_

    Args:
        db: _description_
        log: _description_. Defaults to log.
    """

    """
    Schedule-able function to re/create all Title Cards for all Series
    and Episodes in the Database.

    Args:
        log: Logger for all log messages.
    """

    try:
        preferences = get_preferences()
        # Get the Database
        with next(get_database()) as db:
            db.add(NewSnapshot(
                blueprints=len(preferences.imported_blueprints),
                cards=db.query(models.card.Card).count(),
                episodes=db.query(models.episode.Episode).count(),
                fonts=db.query(models.font.Font).count(),
                loaded=db.query(models.loaded.Loaded).count(),
                series=db.query(models.series.Series).count(),
                syncs=db.query(models.sync.Sync).count(),
                templates=db.query(models.template.Template).count(),
                users=db.query(models.user.User).count(),
                filesize=db.query(models.card.Card)\
                    .with_entities(func.sum(models.card.Card.filesize))\
                    .scalar(),
            ))
    except Exception as exc:
        log.exception(f'Failed to take snapshot', exc)
