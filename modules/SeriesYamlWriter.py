from pathlib import Path

from ruamel.yaml import YAML, round_trip_dump, comments
from ruamel.yaml.constructor import DuplicateKeyError
from yaml import add_representer, dump

from modules.Debug import log

class SeriesYamlWriter:
    """
    This class describes a SeriesYamlWriter. This is an object that writes
    formatted series YAML files by syncing with Sonarr or Plex.
    """

    """Keyword arguments for yaml.dump()"""
    __WRITE_OPTIONS = {'allow_unicode': True, 'width': 200}


    def __init__(self, file: Path, sync_mode: str='append',
                 compact_mode: bool=True, volume_map: dict[str: str]={},
                 template: str=None) ->None:
        """
        Initialize an instance of a SeriesYamlWrite object.

        Args:
            file: File to read/write series YAML.
            sync_mode: How to write to this series YAML file. Must be either
                'append' or 'match'.
            compact_mode: Whether to write this YAML in compact mode or not.
            volume_map: Mapping of interface paths to corresponding TCM paths.
            template: Template name to add to all synced series.
        """

        # Start as valid, Store base attributes
        self.valid = True
        self.file = file
        self.compact_mode = compact_mode

        # Convert volume map to POSIX (unix) fully resolved directories with /
        try:
            posix_eq = lambda p: f'{Path(p).resolve().as_posix()}/'
            self.volume_map = {posix_eq(source): posix_eq(tcm)
                               for source, tcm in volume_map.items()}
        except Exception as e:
            log.error(f'Invalid "volumes" - must all be paths')
            log.debug(f'Error[{e}]')
            self.valid = False
        
        # Validate/store sync mode
        if (sync_mode := sync_mode.lower()) not in ('append', 'match'):
            log.error(f'Invalid sync mode - must be "append" or "match"')
            self.valid = False
        else:
            self.sync_mode = sync_mode

        # Store optional template to add
        self.template = template

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


    def __convert_path(self, path: str) -> str:
        """
        Convert the given path string to its TCM-equivalent by using this 
        object's volume map.

        Args:
            path: Path (as string) to convert.

        Returns:
            Converted Path (as string). If no conversion was applied, then the 
            original path is returned.
        """

        # Use volume map to convert path to TCM path
        posix_path = Path(path).resolve().as_posix()
        for source_base, tcm_base in self.volume_map.items():
            # Apply substitution on their POSIX equivalent strings
            if posix_path.startswith(source_base):
                return posix_path.replace(source_base, tcm_base)

        # No defined substituion, return original path
        return path


    def __apply_exclusion(self, yaml: dict[str: dict[str: str]],
                          exclusions: list[dict[str: str]]) -> None:
        """
        Apply the given exclusions to the given YAML. This modifies the YAML
        object in-place.

        Args:
            yaml: YAML being modified.
            exclusions: List of labelled exclusions to apply to sync.
        """

        # No exclusions to apply, exit
        if len(exclusions) == 0 or len(yaml.get('series', {})) == 0:
            return None
        
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
                    log.error(f'Cannot read "{value}" as exclusion file - {e}')
                    continue
                
                # Delete each file's specified series
                for series in read_yaml.get('series', {}).keys():
                    if series in yaml.get('series', {}):
                        del yaml['series'][series]
            # If this exclusion is a specific series, remove
            elif label == 'series':
                if value in yaml.get('series', {}):
                    del yaml['series'][value]


    def __write(self, yaml: dict[str: dict[str: str]]) -> None:
        """
        Write the given YAML to this Writer's file. This either utilizes compact
        or verbose style.

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


    def __read_existing_file(self,  yaml: dict[str: dict[str: str]]
                             ) -> dict[str: dict[str: str]]:
        """
        Read the existing YAML from this writer's file. If the file has no
        existing YAML to read, then just write the given YAML.

        Args:
            yaml: YAML (dictionary) to write.

        Returns:
            Dictionary that is the existing YAML. None if there is no existing
            YAML, or if an error occured during the read.
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


    def __append(self, yaml: dict[str: dict[str: str]]) -> None:
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
            round_trip_dump(existing_yaml, file_handle)


    def __match(self, yaml: dict[str: dict[str: str]]) -> None:
        """
        Match this Writer's file to the given YAML - i.e. remove series that
        shouldn't be present, and add series that should. Does not modify
        anything except the series of the file.

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


    def __get_yaml_from_sonarr(self, sonarr_interface: 'SonarrInterface',
                               plex_libraries: dict[str: str],
                               required_tags: list[str],
                               exclusions: list[dict[str: str]],
                               monitored_only: bool)->dict[str: dict[str: str]]:
        """
        Get the YAML from Sonarr, as filtered by the given attributes.

        Args:
            sonarr_interface: SonarrInterface to sync from.
            plex_libraries: Dictionary of TCM paths to their corresponding
                libraries.
            required_tags: List of requried tags to filter the Sonarr sync with.
            exclusions: List of labelled exclusions to apply to sync.
            monitored_only: Whether to only sync monitored series from Sonarr.

        Returns:
            Series YAML as reported by Sonarr. Keys are series names, and each
            contains the YAML for that series, such as the 'name', 'year',
            'media_directory', and 'library'.
        """

        # Get list of excluded tags
        excluded_tags = [
               list(exclusion.items())[0][1] for exclusion in exclusions
            if list(exclusion.items())[0][0] == 'tag'
        ]
        
        # Get list of SeriesInfo and paths from Sonarr
        all_series = sonarr_interface.get_all_series(
            required_tags, excluded_tags, monitored_only
        )

        # Exit if no series were returned
        if len(all_series) == 0:
            return {}

        # Generate YAML to write
        series_yaml = {}
        for series_info, sonarr_path in all_series:
            # Use volume map to convert Sonarr path to TCM path
            sonarr_path = self.__convert_path(sonarr_path)

            # Attempt to find matching Plex library
            library = None
            for tcm_base, library_name in plex_libraries.items():
                if tcm_base in sonarr_path:
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
                or Path(sonarr_path).name != series_info.legal_path):
                this_entry['media_directory'] = sonarr_path

            # Add this entry to main supposed YAML
            series_yaml[key] = this_entry

        # Create libraries YAML
        libraries_yaml = {}
        for path, library in plex_libraries.items():
            libraries_yaml[library] = {'path': path}

        # Create end-YAML as combination of series and libraries
        yaml = {'libraries': libraries_yaml, 'series': series_yaml}
        
        # Apply exclusions and return yaml
        self.__apply_exclusion(yaml, exclusions)
        return yaml


    def update_from_sonarr(self, sonarr_interface: 'SonarrInterface',
                           plex_libraries: dict[str: str]={},
                           required_tags: list[str]=[],
                           exclusions: list[dict[str: str]]=[],
                           monitored_only: bool=False,
                           downloaded_only: bool=False) -> None:
        """
        Update this object's file from Sonarr.

        Args:
            sonarr_interface: SonarrInterface to sync from.
            plex_libraries: Dictionary of TCM paths to their corresponding
                libraries.
            required_tags: List of tags to filter the Sonarr sync from.
            exclusions: List of labelled exclusions to apply to sync.
            monitored_only: Whether to only sync monitored series from Sonarr.
            downloaded_only: Whether to only sync downloaded series from Sonarr.
        """

        # Get complete file YAML from Sonarr
        yaml = self.__get_yaml_from_sonarr(
            sonarr_interface, plex_libraries, required_tags, exclusions,
            monitored_only, downloaded_only
        )

        # Either sync of append this YAML to this object's file
        if self.sync_mode == 'match':
            self.__match(yaml)
        elif self.sync_mode == 'append':
            self.__append(yaml)

        log.info(f'Synced {self.file.resolve()} from Sonarr')


    def __get_yaml_from_plex(self, plex_interface: 'PlexInterface',
                             filter_libraries: list[str],
                             exclusions: list[dict[str: str]]=[]
                             ) -> dict[str: dict[str: str]]:
        """
       Get the YAML from Plex, as filtered by the given libraries.

        Args:
            plex_interface: PlexInterface to sync from.
            filter_libraries: List of libraries to filter the returned YAML by.
            exclusions: List of labelled exclusions to apply to sync.

        Returns:
            Series YAML as reported by Plex. Keys are series names, and each
            contains the YAML for that series, such as the 'name', 'year',
            'media_directory', and 'library'.
        """

        # Get list of SeriesInfo, media paths, and library names from Plex
        all_series = plex_interface.get_all_series(filter_libraries)

        # Exit if no series were returned
        if len(all_series) == 0:
            return {}

        # Get dictionary of libraries and their directories from Plex
        libraries = plex_interface.get_library_paths(filter_libraries)

        # Create libraries YAML
        libraries_yaml = {}
        for library, paths in libraries.items():
            # If this library has multiple directories, create entry for each
            if len(paths) > 1:
                for index, path in enumerate(paths):
                    libraries_yaml[f'{library} - Directory {index+1}'] = {
                        'path': self.__convert_path(path),
                        'plex_name': library,
                    }
            # Library only has one directory, add directly
            else:
                libraries_yaml[library]={'path':self.__convert_path(paths[0])}

        # Create series YAML
        series_yaml = {}
        for series_info, plex_path, library in all_series:
            # Use volume map to convert Plex path to TCM path
            series_path = self.__convert_path(plex_path)

            # If part of a multi-directory library, use adjusted library name
            if libraries_yaml.get(library) is None:
                for library_key, library_yaml in libraries_yaml.items():
                    # Find matching library 
                    if (library_yaml.get('plex_name') == library
                        and series_path.startswith(library_yaml['path'])):
                        library = library_key
                        break

            # Add details to eventual YAML object
            this_entry = {'library': library}
            if self.template is not None:
                this_entry['template'] = self.template

            # Add under key: "full name" then "name [imdb:imdb_id]"
            if (key := series_info.full_name) in series_yaml:
                this_entry['name'] = series_info.name
                this_entry['year'] = series_info.year
                key = f'{series_info.name} [imdb:{series_info.imdb_id}]'

            # Add media directory if path doesn't match default
            if Path(series_path).name != series_info.legal_path:
                this_entry['media_directory'] = series_path

            # Add this entry to main supposed YAML
            series_yaml[key] = this_entry

        # Create end-YAML as combination of series and libraries
        yaml = {'libraries': libraries_yaml, 'series': series_yaml}

         # Apply exclusions, then return yaml finalized YAML
        self.__apply_exclusion(yaml, exclusions)
        return yaml


    def update_from_plex(self, plex_interface: 'PlexInterface',
                         filter_libraries: list[str]=[],
                         exclusions: list[dict[str: str]]=[]) -> None:
        """
        Update this object's file from Plex.

        Args:
            plex_interface: PlexInterface to sync from.
            filter_libraries: List of libraries to filter Plex sync from.
            exclusions: List of labeled exclusions to apply to sync.
        """

        if not isinstance(filter_libraries, (list, tuple)):
            log.critical(f'Invalid Plex library filter list')
            exit(1)

        # Get complete file YAML from Sonarr
        yaml = self.__get_yaml_from_plex(
            plex_interface, filter_libraries, exclusions
        )

        # Either sync of append this YAML to this object's file
        if self.sync_mode == 'match':
            self.__match(yaml)
        elif self.sync_mode == 'append':
            self.__append(yaml)

        log.info(f'Synced {self.file.resolve()} from Plex')