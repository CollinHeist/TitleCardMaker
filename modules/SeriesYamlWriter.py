from pathlib import Path
from typing import Literal, Optional

from ruamel.yaml import YAML, round_trip_dump, comments
from ruamel.yaml.constructor import DuplicateKeyError
from yaml import add_representer, dump

from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.EmbyInterface import EmbyInterface
from modules.JellyfinInterface import JellyfinInterface
from modules.PlexInterface import PlexInterface
from modules.SonarrInterface import SonarrInterface
from modules.SyncInterface import SyncInterface

SeriesYaml = dict[str, dict[str, str]]
SyncMode = Literal['append', 'match']

class SeriesYamlWriter:
    """
    This class describes a SeriesYamlWriter. This is an object that
    writes formatted series YAML files by syncing with Emby, Plex, or
    Sonarr.
    """

    """Keyword arguments for yaml.dump()"""
    __WRITE_OPTIONS = {'allow_unicode': True, 'width': 250}


    def __init__(self,
            file: CleanPath,
            sync_mode: SyncMode = 'append',
            compact_mode: bool = True,
            volume_map: dict[str, str] = {},
            template: Optional[str] = None,
            card_directory: Optional[CleanPath] = None) -> None:
        """
        Initialize an instance of a SeriesYamlWrite object.

        Args:
            file: File to read/write series YAML.
            sync_mode: How to write to this series YAML file. Must be
                either 'append' or 'match'.
            compact_mode: Whether to write this YAML in compact mode or
                not.
            volume_map: Mapping of interface paths to corresponding TCM
                paths.
            template: Template name to add to all synced series.
            card_directory: Override directory all cards should be
                directed to, instead of the series-specific directory
                reported by the sync source.
        """

        # Start as valid, Store base attributes
        self.valid = True
        self.file = file
        self.compact_mode = compact_mode

        # Convert volume map to string of sanitized paths
        self.volume_map = {}
        try:
            std = lambda p: str(CleanPath(p).sanitize())
            self.volume_map = {std(source): std(tcm) 
                               for source, tcm in volume_map.items()}
        except Exception as e:
            log.exception(f'Invalid "volumes" - must all be valid paths', e)
            self.valid = False

        # Validate/store sync mode
        if (sync_mode := sync_mode.lower()) in ('append', 'match'):
            self.sync_mode = sync_mode
        else:
            log.error(f'Invalid sync mode - must be "append" or "match"')
            self.valid = False

        # Store optional template to add
        self.template = template

        # Standardize card directory, create parent folders
        if card_directory is None:
            self.card_directory = None
        else:
            self.card_directory = card_directory.sanitize()
            self.card_directory.mkdir(parents=True, exist_ok=True)

        # Add representer for compact YAML writing
        # Pseudo-class for a flow map - i.e. dictionary
        class flowmap(dict): pass
        def flowmap_rep(dumper, data):
            return dumper.represent_mapping(
                u'tag:yaml.org,2002:map', data, flow_style=True
            )
        add_representer(flowmap, flowmap_rep)
        self.__compact_flowmap = flowmap

        # Create this file's parent folders
        self.file.parent.mkdir(parents=True, exist_ok=True)


    def __repr__(self) -> str:
        """Return an unambigious string representation of this object."""

        return (f'<SeriesYamlWriter {self.file=}, {self.sync_mode=}, '
                f'{self.compact_mode=}, {self.volume_map=}>')


    def __convert_path(self, path: str, *, media: bool) -> str:
        """
        Convert the given path string to its TCM-equivalent by using
        this  object's volume map and card (override) directory.

        Args:
            path: Path (as string) to convert.
            media: (Keyword only) Whether the path being converted
                corresponds to a specific piece of media.

        Returns:
            Converted Path (as string). If this object was initialized
            with an override card directory, the path (or base if media)
            is modified to that override directory. If no conversion was
            applied, then the original path is returned.
        """

        # An override directory has been provided
        if self.card_directory is not None:
            # Path is media, only substitute up to parent directory
            if media:
                clean_name = CleanPath(path).sanitize().name
                return str(self.card_directory / clean_name)
            # Non-media, override entire directory 
            else:
                return str(self.card_directory)

        # Use volume map to convert (standardized) path to TCM path
        standard_path = str(CleanPath(path).sanitize())
        for source_base, tcm_base in self.volume_map.items():
            if standard_path.startswith(source_base):
                return standard_path.replace(source_base, tcm_base)

        # No defined substitution, return original path
        return standard_path


    def __apply_exclusion(self,
            yaml: SeriesYaml,
            exclusions: list[dict[str, str]]) -> None:
        """
        Apply the given exclusions to the given YAML. This modifies the
        YAML object in-place.

        Args:
            yaml: YAML being modified.
            exclusions: List of labeled exclusions to apply to sync.
        """

        # No exclusions to apply, exit
        if len(exclusions) == 0 or len(yaml.get('series', {})) == 0:
            return None

        # Inner function to match case-insentively
        def yaml_contains(yaml: dict, key: str) -> tuple[bool, str]:
            # If present under given case
            if key in yaml.get('series', {}):
                return True, key
            # If present in lowercase
            for yaml_key in yaml.get('series', {}).keys():
                if key.lower() == yaml_key.lower():
                    return True, yaml_key
            # Not present at all
            return False, key

        # Go through each exclusion in the given list
        for exclusion in exclusions:
            # Validate this exclusion is a dictionary
            if not isinstance(exclusion, dict):
                log.error(f'Invalid exclusion {exclusion}')
                continue

            # Get exclusion label and value
            label, value = list(exclusion.items())[0]

            # If this exclusion is a YAML file, read and filter each series
            if (label := label.lower()) == 'yaml':
                # Attempt to read file, error and skip if invalid
                try:
                    with Path(value).open('r', encoding='utf-8') as file_handle:
                        read_yaml = YAML().load(file_handle)
                except Exception as e:
                    log.exception(f'Cannot read "{value}" as exclusion file', e)
                    continue

                # Delete each file's specified series
                all_series = read_yaml.get('series', {})
                if not isinstance(all_series, dict):
                    log.error(f'Exclusion YAML file "{value}" is invalid')
                    continue

                for series in all_series.keys():
                    contains, key = yaml_contains(yaml, series)
                    if contains:
                        del yaml['series'][key]
            # If this exclusion is a specific series, remove
            elif label == 'series':
                contains, key = yaml_contains(yaml, value)
                if contains:
                    del yaml['series'][key]


    def __write(self, yaml: SeriesYaml) -> None:
        """
        Write the given YAML to this Writer's file. This either utilizes
        compact or verbose style.

        Args:
            yaml: YAML (dictionary) to write.
        """

        # Compact mode, use custom flowmap style on each series
        if self.compact_mode:
            # Convert each series dictionary as a Flowmap dictionary
            yaml['series'] = {
                k: self.__compact_flowmap(x)
                for k, x in yaml.get('series', {}).items()
            }

        # Write modified YAML to this writer's file
        with self.file.open('w', encoding='utf-8') as file_handle:
            dump(yaml, file_handle, **self.__WRITE_OPTIONS)


    def __read_existing_file(self, yaml: SeriesYaml) -> SeriesYaml:
        """
        Read the existing YAML from this writer's file. If the file has
        no existing YAML to read, then just write the given YAML.

        Args:
            yaml: YAML (dictionary) to write.

        Returns:
            Dictionary that is the existing YAML. None if there is no
            existing YAML, or if an error occured during the read.
        """

        # If the file DNE, just use write technique
        if not self.file.exists():
            self.__write(yaml)
            return None

        # Read existing lines/YAML for future parsing
        try:
            with self.file.open('r', encoding='utf-8') as file_handle:
                existing_yaml = YAML().load(file_handle)
        except DuplicateKeyError as e:
            log.error(f'Cannot sync to file "{self.file.resolve()}"')
            log.error(f'Invalid YAML encountered {e}')
            return None
        except Exception as e:
            log.error(f'Cannot sync to file "{self.file.resolve()}"')
            log.error(f'Error occured {e}')
            return None

        # Write if file exists but is blank
        if existing_yaml is None or len(existing_yaml) == 0:
            self.__write(yaml)
            return None

        # If series or libraries are empty, set to empty dictionary 
        if existing_yaml.get('series') is None:
            existing_yaml['series'] = {}
        if existing_yaml.get('libraries') is None:
            existing_yaml['libraries'] = {}

        return existing_yaml


    def __append(self, yaml: SeriesYaml) -> None:
        """
        Append the given YAML to this Writer's file. This either utilizes
        compact or verbose style. Appending does not modify library or series
        entries whose keys already exist.

        Args:
            yaml: YAML (dictionary) to write.
        """

        # Read existing YAML, exit if nothing else to parse
        if (existing_yaml := self.__read_existing_file(yaml)) is None:
            return None

        # Identify which libraries DNE in existing YAML that need to be added
        for library_name, library in yaml.get('libraries', {}).items():
            # Skip entries that exist
            if library_name in existing_yaml.get('libraries', {}).keys():
                continue
            existing_yaml['libraries'][library_name] = library

        # Identify which series DNE in existing YAML that need to be aded
        for series_name, series in yaml.get('series', {}).items():
            # Skip entries that already exist
            if series_name in existing_yaml.get('series', {}).keys():
                continue

            # If writing compact mode, set flow stype for this entry
            if self.compact_mode:
                add_obj = comments.CommentedMap(series)
                add_obj.fa.set_flow_style()
            else:
                add_obj = series

            # Add to YAML
            existing_yaml['series'][series_name] = add_obj

        # Write YAML to file
        with self.file.open('w', encoding='utf-8') as file_handle:
            round_trip_dump(existing_yaml, file_handle, **self.__WRITE_OPTIONS)


    def __match(self, yaml: SeriesYaml) -> None:
        """
        Match this Writer's file to the given YAML - i.e. remove series
        that shouldn't be present, and add series that should. Does not
        modify anything except the series of the file.

        Args:
            yaml: YAML (dictionary) to write.
        """

        # Read existing YAML, exit if nothing else to parse
        if (existing_yaml := self.__read_existing_file(yaml)) is None:
            return None

        # Add series that aren't present in existing YAML
        for series_name, series in yaml.get('series', {}).items():
            # If this series already exists, skip
            if series_name in existing_yaml.get('series', {}).keys():
                continue

            # If writing compact mode, set flow stype for this entry
            if self.compact_mode:
                add_obj = comments.CommentedMap(series)
                add_obj.fa.set_flow_style()
            else:
                add_obj = series

            # Series DNE, add to existing YAML
            existing_yaml['series'][series_name] = add_obj
            log.debug(f'Added {series_name} to "{self.file}"')

        # Remove series that shouldn't be present in existing YAML
        existing_series = tuple(existing_yaml.get('series', {}).keys())
        actual_series = yaml.get('series', {}).keys()
        for series_name in existing_series:
            if series_name not in actual_series:
                existing_yaml['series'].pop(series_name, None)
                log.debug(f'Removed {series_name} from "{self.file}"')

        # Write YAML to file
        with self.file.open('w', encoding='utf-8') as file_handle:
            round_trip_dump(existing_yaml, file_handle)


    def __get_yaml_from_sonarr(self,
            sonarr_interface: SonarrInterface,
            plex_libraries: dict[str, str],
            required_tags: list[str],
            monitored_only: bool,
            downloaded_only: bool,
            series_type: str,
            exclusions: list[dict[str, str]]
        ) -> SeriesYaml:
        """
        Get the YAML from Sonarr, as filtered by the given attributes.

        Args:
            sonarr_interface: SonarrInterface to sync from.
            plex_libraries: Dictionary of TCM paths to their
                corresponding libraries.
            required_tags: List of requried tags to filter the Sonarr
                sync with.
            monitored_only: Whether to only sync monitored series from
                Sonarr.
            downloaded_only: Whether to only sync downloaded series from
                Sonarr.
            series_type: Type of series to filter sync with.
            exclusions: List of labelled exclusions to apply to sync.

        Returns:
            Series YAML as reported by Sonarr. Keys are series names,
            and each contains the YAML for that series, such as the
            'name', 'year', 'media_directory', and 'library'.
        """

        # Get list of excluded tags
        excluded_tags = [
               list(exclusion.items())[0][1] for exclusion in exclusions
            if list(exclusion.items())[0][0] == 'tag'
        ]

        # Get list of SeriesInfo and paths from Sonarr
        all_series = sonarr_interface.get_all_series(
            required_tags, excluded_tags, monitored_only,
            downloaded_only, series_type,
        )

        # Exit if no series were returned
        if len(all_series) == 0:
            return {}

        # Generate YAML to write
        series_yaml = {}
        for series_info, sonarr_path in all_series:
            # Convert Sonarr path to TCM path, keep original for library
            original_path = sonarr_path
            sonarr_path = self.__convert_path(sonarr_path, media=True)

            # Attempt to find matching Plex library
            library = None
            for tcm_base, library_name in plex_libraries.items():
                if original_path.startswith(tcm_base):
                    library = library_name
                    break

            # Add details to eventual YAML object
            this_entry = {} if library is None else {'library': library}
            if self.template is not None:
                this_entry['template'] = self.template

            # Add under "full name", then "name [sonarr:sonarr_id]""
            key = series_info.full_name
            if key in series_yaml:
                this_entry['name'] = series_info.name
                this_entry['year'] = series_info.year
                key = f'{series_info.name} [sonarr:{series_info.sonarr_id}]'

            # Add media directory if path doesn't match default
            if (library is None
                or Path(sonarr_path).name != series_info.full_clean_name):
                this_entry['media_directory'] = sonarr_path

            # Add this entry to main supposed YAML
            series_yaml[key] = this_entry

        # Create libraries YAML
        libraries_yaml = {}
        for path, library in plex_libraries.items():
            if self.card_directory is None:
                path = self.__convert_path(path, media=False)
            else:
                path = str(self.card_directory)
            libraries_yaml[library] = {'path': path}

        # Create end-YAML as combination of series and libraries
        yaml = {'libraries': libraries_yaml, 'series': series_yaml}

        # Apply exclusions and return yaml
        self.__apply_exclusion(yaml, exclusions)
        return yaml


    def __get_yaml_from_interface(self,
            interface: SyncInterface,
            media_server: Literal['emby', 'jellyfin', 'plex'],
            duplicate_key_id: str,
            filter_libraries: list[str],
            required_tags: list[str],
            exclusions: list[dict[str, str]] = [],
        ) -> SeriesYaml:
        """
        Get the YAML from the given MediaServerInterface, as filtered by
        the given libraries.

        Args:
            interface: Interface to a MediaServer to sync from.
            media_server: Which media server is being synced from.
            duplicate_key_id: Which database ID should be used when
                there is duplicate series YAML.
            filter_libraries: List of libraries to filter the returned
                YAML by.
            required_tags: List of tags to filter the sync with.
            exclusions: List of labeled exclusions to apply to sync.

        Returns:
            Series YAML as reported by the given interface.
        """

        # Get list of SeriesInfo, media paths, and library names from interface
        all_series = interface.get_all_series(filter_libraries, required_tags)

        # Exit if no series were returned blank YAML
        if len(all_series) == 0:
            return {}

        # Get dictionary of libraries and their directories from interface
        libraries = interface.get_library_paths(filter_libraries)

        # Create libraries YAML
        libraries_yaml = {}
        for library, paths in libraries.items():
            # If this library has multiple directories, create entry for 
            # each if no override card directory is provided
            if len(paths) > 1 and self.card_directory is None:
                for index, path in enumerate(paths):
                    libraries_yaml[f'{library} - Directory {index+1}'] = {
                        'path': self.__convert_path(path, media=False),
                        'library_name': library,
                        'media_server': media_server,
                    }
            # Library only has one directory, add directly
            else:
                libraries_yaml[library] = {
                    'path': self.__convert_path(paths[0], media=False),
                    'media_server': media_server,
                }

        # Create series YAML
        series_yaml = {}
        for series_info, server_path, library in all_series:
            # Convert Emby path to TCM path
            series_path = self.__convert_path(server_path, media=True)

            # If part of a multi-directory library, use adjusted library name
            if libraries_yaml.get(library) is None:
                for library_key, library_yaml in libraries_yaml.items():
                    # Find matching library 
                    if (library_yaml.get('library_name') == library
                        and series_path.startswith(library_yaml['path'])):
                        library = library_key
                        break

            # Add details to eventual YAML object
            this_entry = {'library': library}
            if self.template is not None:
                this_entry['template'] = self.template

            # Add under key: "full name" then "name [tvdb:tvdb_id]"
            if (key := series_info.full_name) in series_yaml:
                this_entry['name'] = series_info.name
                this_entry['year'] = series_info.year
                key = (f'{series_info.full_name} [{duplicate_key_id}'
                       f':{getattr(series_info, duplicate_key_id)}]')

            # Add media directory if path doesn't match default
            if Path(series_path).name != series_info.full_clean_name:
                this_entry['media_directory'] = series_path

            # Add this entry to main supposed YAML
            series_yaml[key] = this_entry

        # Create end-YAML as combination of series and libraries
        yaml = {'libraries': libraries_yaml, 'series': series_yaml}

        # Apply exclusions, then return yaml finalized YAML
        self.__apply_exclusion(yaml, exclusions)
        return yaml


    def update_from_sonarr(self,
            sonarr_interface: SonarrInterface,
            plex_libraries: dict[str, str] = {},
            required_tags: list[str] = [],
            monitored_only: bool = False,
            downloaded_only: bool = False,
            series_type: Optional[str] = None,
            exclusions: list[dict[str, str]] = []) -> None:
        """
        Update this object's file from Sonarr.

        Args:
            sonarr_interface: SonarrInterface to sync from.
            plex_libraries: Dictionary of TCM paths to their 
                corresponding libraries.
            required_tags: List of tags to filter the Sonarr sync from.
            exclusions: List of labeled exclusions to apply to sync.
            monitored_only: Whether to only sync monitored series from
                Sonarr.
            downloaded_only: Whether to only sync downloaded series from
                Sonarr.
        """

        # Get complete file YAML from Sonarr
        yaml = self.__get_yaml_from_sonarr(
            sonarr_interface, plex_libraries, required_tags, 
            monitored_only, downloaded_only, series_type, exclusions,
        )

        # Either sync of append this YAML to this object's file
        if self.sync_mode == 'match':
            self.__match(yaml)
        elif self.sync_mode == 'append':
            self.__append(yaml)

        log.info(f'Synced {self.file.resolve()} from Sonarr')


    def update_from_plex(self,
            plex_interface: PlexInterface,
            filter_libraries: list[str] = [],
            required_tags: list[str] = [],
            exclusions: list[dict[str, str]] = []) -> None:
        """
        Update this object's file from Plex.

        Args:
            plex_interface: PlexInterface to sync from.
            filter_libraries: List of libraries to filter Plex sync from.
            required_tags: List of tags to filter the sync with.
            exclusions: List of labeled exclusions to apply to sync.
        """

        if not isinstance(filter_libraries, (list, tuple)):
            log.critical(f'Invalid Plex library filter list')
            exit(1)

        # Get complete file YAML from Plex
        yaml = self.__get_yaml_from_interface(
            plex_interface, 'plex', 'imdb_id', filter_libraries, required_tags,
            exclusions,
        )

        # Either sync of append this YAML to this object's file
        if self.sync_mode == 'match':
            self.__match(yaml)
        elif self.sync_mode == 'append':
            self.__append(yaml)

        log.info(f'Synced {self.file.resolve()} from Plex')


    def update_from_emby(self,
            emby_interface: EmbyInterface,
            filter_libraries: list[str] = [],
            required_tags: list[str] = [],
            exclusions: list[dict[str, str]] = []) -> None:
        """
        Update this object's file from Emby.

        Args:
            emby_interface: EmbyInterface to sync from.
            filter_libraries: List of libraries to filter sync from.
            required_tags: List of tags to filter the sync with.
            exclusions: List of labeled exclusions to apply to sync.
        """

        if not isinstance(filter_libraries, (list, tuple)):
            log.critical(f'Invalid Emby library filter list')
            exit(1)

        yaml = self.__get_yaml_from_interface(
            emby_interface, 'emby', 'emby_id', filter_libraries,
            required_tags, exclusions
        )

        # Either sync of append this YAML to this object's file
        if self.sync_mode == 'match':
            self.__match(yaml)
        elif self.sync_mode == 'append':
            self.__append(yaml)

        log.info(f'Synced {self.file.resolve()} from Emby')


    def update_from_jellyfin(self,
            jellyfin_interface: JellyfinInterface,
            filter_libraries: list[str] = [],
            required_tags: list[str] = [],
            exclusions: list[dict[str, str]] = []) -> None:
        """
        Update this object's file from Jellyfin.

        Args:
            jellyfin_interface: Interface to sync from.
            filter_libraries: List of libraries to filter sync from.
            required_tags: List of tags to filter the sync with.
            exclusions: List of labeled exclusions to apply to sync.
        """

        if not isinstance(filter_libraries, (list, tuple)):
            log.critical(f'Invalid Jellyfin library filter list')
            exit(1)

        # Get complete file YAML from Jellyfin
        yaml = self.__get_yaml_from_interface(
            jellyfin_interface, 'jellyfin', 'jellyfin_id', filter_libraries,
            required_tags, exclusions
        )

        # Either sync of append this YAML to this object's file
        if self.sync_mode == 'match':
            self.__match(yaml)
        elif self.sync_mode == 'append':
            self.__append(yaml)

        log.info(f'Synced {self.file.resolve()} from Jellyfin')