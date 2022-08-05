from pathlib import Path
from re import match, sub, IGNORECASE

from yaml import add_representer, dump, safe_load

from modules.Debug import log

class SeriesYamlWriter:
    """
    This class describes a SeriesYamlWriter. This is an object that writes
    formatted series YAML files.
    """

    """Default arguments for initializing an object"""
    DEFAULT_ARGUMENTS = {
        'sync_mode': 'append', 'compact_mode': True, 'volume_map': {}
    }

    """Temporary file to read/write YAML from for string conversion"""
    __TEMPORARY_FILE = Path(__file__).parent / '.objects' / 'tmp.yml'

    """Keyword arguments for yaml.dump()"""
    __WRITE_OPTIONS = {'allow_unicode': True, 'width': 200}

    """Valid sections for determining YAML indents"""
    __VALID_SECTIONS = ('libraries:', 'templates:', 'fonts:', 'series:')

    def __init__(self, file: Path, sync_mode: str='append',
                 compact_mode: bool=True, volume_map: dict[str: str]={}) ->None:
        """
        Initialize an instance of a SeriesYamlWrite object.

        Args:
            file: File to read/write series YAML.
            sync_mode: How to write to this series YAML file. Must be either
                'sync' or 'append'.
            compact_mode: Whether to write this YAML in compact mode or not.
            volume_map: Mapping of interface paths to corresponding TCM paths.
            
        Raises:
            ValueError: If sync mode isn't 'sync' or 'append'.
        """

        # Store base attributes
        self.file = file
        self.compact_mode = compact_mode
        self.volume_map = volume_map

        # Validate/store sync mode
        if (sync_mode := sync_mode.lower()) not in ('sync', 'append'):
            raise ValueError(f'Sync mode must be "sync" or "append"')
        self.sync_mode = sync_mode

        # Add representer for compact YAML writing
        # Pseudo-class for a flow map - i.e. dictionary
        class flowmap(dict): pass

        # Representor using flow style
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

        # Use volume map to convert Sonarr path to TCM path
        for source_base, tcm_base in self.volume_map.items():
            # If modification occurs, update Sonarr path, stop substitution
            if (adj_path := sub(fr'^{source_base}', tcm_base, path, 1)) != path:
                return adj_path

        return path


    def __yaml_as_string(self, yaml: dict[str: dict[str: str]],
                         indent: int) -> list[str]:
        """
        Get the given YAML as a list of strings that are that YAML written to
        a file.

        Args:
            yaml: YAML dictionary to write and convert to a string.
            indent: Indentation to use for writing the YAML.

        Returns:
            List of strings that are the lines of the converted YAML object.
        """

        # Empty YAML, no equivalent lines
        if len(yaml) == 0:
            return []

        # Write given YAML to temporary file so formatting is correct
        with self.__TEMPORARY_FILE.open('w', encoding='utf-8') as file_handle:
            __temp_yaml = {'header': yaml}
            dump(__temp_yaml, file_handle, indent=indent,**self.__WRITE_OPTIONS)

        # Read written YAML as lines
        with self.__TEMPORARY_FILE.open('r', encoding='utf-8') as file_handle:
            lines = file_handle.readlines()

        # Delete temporary file
        self.__TEMPORARY_FILE.unlink()
        
        # Return string lines, adding newline and skipping header
        return ['\n'] + lines[1:]


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
                for k, x in yaml['series'].items()
            }

        # Write modified YAML to this writer's file
        with self.file.open('w', encoding='utf-8') as file_handle:
            dump(yaml, file_handle, **self.__WRITE_OPTIONS)


    def __append(self, yaml: dict[str: dict[str: str]]) -> None:
        """
        Append the given YAML to this Writer's file. This either utilizes
        compact or verbose style. Appending does not modify library or series
        entries whose keys already exist.

        Args:
            yaml: YAML (dictionary) to write.
        """

        # If the file DNE, just use write technique
        if not self.file.exists():
            self.__write(yaml)
            return None

        # Compact mode, use custom flowmap style on each series
        if self.compact_mode:
            # Convert each series dictionary as a Flowmap dictionary
            yaml['series'] = {
                k: self.__compact_flowmap(x)
                for k, x in yaml['series'].items()
            }

        # Read existing lines/YAML for future parsing
        existing_lines, existing_yaml = [], {}
        with self.file.open('r', encoding='utf-8') as file_handle:
            existing_yaml = safe_load(file_handle)
            file_handle.seek(0, 0)
            existing_lines = file_handle.readlines()
        existing_line_count = len(existing_lines)

        # Identify which libraries DNE in existing YAML that need to be added
        add_libraries = {}
        for library_name, library in yaml.get('libraries', {}).items():
            if library_name in existing_yaml.get('libraries', {}).keys():
                continue
            add_libraries[library_name] = library

        # Identify which series DNE in existing YAML that need to be aded
        add_series = {}
        for series_name, series in yaml.get('series', {}).items():
            if series_name in existing_yaml.get('series', {}).keys():
                continue
            add_series[series_name] = series

         # Determine existing indent
        indent = 2
        check_indent = False
        for line in existing_lines:
            if check_indent:
                indent = len(match(r'^(\s+)[a-zA-Z]+', line).group(1))
                break
            if line.startswith(self.__VALID_SECTIONS):
                check_indent = True

        # Get string lines for the library/series entries to add
        library_lines = self.__yaml_as_string(add_libraries, indent)
        series_lines = self.__yaml_as_string(add_series, indent)

        # File the lines which the libraries and series_end on, for append
        library_line_number = existing_line_count
        series_line_number = existing_line_count
        counting_libraries, counting_series = False, False
        for line_number, line in enumerate(existing_lines):
            if line.startswith('libraries:'):
                # If entering library section, start counting
                counting_libraries = True
                if counting_series:
                    # Stop counting series, note line number
                    series_line_number = line_number - 1
                    counting_series = False
            elif line.startswith('series:'):
                # If entering series section, start counting
                counting_series = True
                if counting_libraries:
                    library_line_number = line_number - 1
                    counting_series = False

        # Insert last elements first (to not mess up prior index)
        order = [(series_lines, series_line_number),
                 (library_lines, library_line_number)]
        if library_line_number > series_line_number:
            order = order[::-1]
        for _lines, _base in order:
            for line_number, line in enumerate(_lines):
                existing_lines.insert(_base+line_number+1, line)
        
        # Write modified line array to file
        with self.file.open('w', encoding='utf-8') as file_handle:
            file_handle.writelines(existing_lines)


    def __get_yaml_from_sonarr(self, sonarr_interface: 'SonarrInterface',
                               plex_libraries: dict[str: str],
                               filter_tags: list[str],
                               monitored_only: bool) ->dict[str: dict[str: str]]:
        """
        Get the YAML from Sonarr, as filtered by the given attributes.

        Args:
            sonarr_interface: SonarrInterface to sync from.
            plex_libraries: Dictionary of TCM paths to their corresponding
                libraries.
            filter_tags: List of tags to filter the Sonarr sync from.
            monitored_only: Whether to only sync monitored series from Sonarr.

        Returns:
            Series YAML as reported by Sonarr. Keys are series names, and each
            contains the YAML for that series, such as the 'name', 'year',
            'media_directory', and 'library'.
        """
        
        # Get list of SeriesInfo and paths from Sonarr
        all_series = sonarr_interface.get_all_series(filter_tags,monitored_only)

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
            this_entry = {'year': series_info.year}

            # Add under key: name > full name > full name (sonarr_id)
            key = series_info.name
            if key in series_yaml:
                if series_info.full_name not in series_yaml:
                    this_entry = {'name': series_info.name}
                    key = series_info.full_name
                else:
                    this_entry = {'name': series_info.name}
                    key = f'{series_info.full_name} ({series_info.sonarr_id})'

            # Add media directory if path doesn't match default
            if Path(sonarr_path).name != series_info.legal_path:
                this_entry['media_directory'] = sonarr_path

            # Add library key to this entry
            if library is not None:
                this_entry['library'] = library

            # Add this entry to main supposed YAML
            series_yaml[key] = this_entry

        # Create libraries YAML
        libraries_yaml = {}
        for path, library in plex_libraries.items():
            libraries_yaml[library] = {'path': path}

        # Create end-YAML as combination of series and libraries
        return {'libraries': libraries_yaml, 'series': series_yaml}


    def update_from_sonarr(self, sonarr_interface: 'SonarrInterface',
                           plex_libraries: dict[str: str],
                           filter_tags: list[str]=[],
                           monitored_only: bool=False) -> None:
        """
        Update this object's file from Sonarr.

        Args:
            sonarr_interface: SonarrInterface to sync from.
            plex_libraries: Dictionary of TCM paths to their corresponding
                libraries.
            filter_tags: List of tags to filter the Sonarr sync from.
            monitored_only: Whether to only sync monitored series from Sonarr.
        """

        # Get complete file YAML from Sonarr
        yaml = self.__get_yaml_from_sonarr(
            sonarr_interface, plex_libraries, filter_tags, monitored_only
        )

        # Either sync of append this YAML to this object's file
        if self.sync_mode == 'sync':
            self.__write(yaml)
        elif self.sync_mode == 'append':
            self.__append(yaml)


    def __get_yaml_from_plex(self, plex_interface: 'PlexInterface',
                             filter_libraries: list[str]
                             ) -> dict[str: dict[str: str]]:
        """
       Get the YAML from Plex, as filtered by the given libraries.

        Args:
            plex_interface: PlexInterface to sync from.
            filter_libraries: List of libraries to filter the returned YAML
                by.

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

        # Generate YAML to write
        series_yaml = {}
        for series_info, plex_path, library in all_series:
            # Use volume map to convert Plex path to TCM path
            series_path = self.__convert_path(plex_path)

            # Add details to eventual YAML object
            this_entry = {'year': series_info.year, 'library': library}

            # Add under key: name > full name > full name (imdb_id)
            key = series_info.name
            if key in series_yaml:
                if series_info.full_name not in series_yaml:
                    this_entry = {'name': series_info.name}
                    key = series_info.full_name
                else:
                    this_entry = {'name': series_info.name}
                    key = f'{series_info.full_name} ({series_info.imdb_id})'

            # Add media directory if path doesn't match default
            if Path(series_path).name != series_info.legal_path:
                this_entry['media_directory'] = series_path

            # Add this entry to main supposed YAML
            series_yaml[key] = this_entry

        # Create libraries YAML
        libraries_yaml = {
            library: {'path': self.__convert_path(path)}
            for library, path in
            plex_interface.get_library_paths(filter_libraries).items()
        }

        # Create end-YAML as combination of series and libraries
        return {'libraries': libraries_yaml, 'series': series_yaml}


    def update_from_plex(self, plex_interface: 'PlexInterface',
                         filter_libraries: list[str]=[]) -> None:
        """
        Update this object's file from Plex.

        Args:
            plex_interface: PlexInterface to sync from.
            filter_libraries: List of libraries to filter Plex sync from.
        """

        if not isinstance(filter_libraries, (list, tuple)):
            log.critical(f'Invalid Plex library filter list')
            exit(1)

        # Get complete file YAML from Sonarr
        yaml = self.__get_yaml_from_plex(plex_interface, filter_libraries)

        # Either sync of append this YAML to this object's file
        if self.sync_mode == 'sync':
            self.__write(yaml)
        elif self.sync_mode == 'append':
            self.__append(yaml)
