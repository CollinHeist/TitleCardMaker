/**
 * @typedef {'Emby' | 'Jellyfin' | 'Plex' | 'Sonarr'| 'TMDb'} InterfaceType
 */

/**
 * @typedef {'art' | 'art blur' | 'art grayscale' | 'art blur grayscale' |
 *           'unique' | 'blur unique' | 'grayscale unique' |
 *           'blur grayscale unique'} Style
 */

/**
 * @typedef {"blank" | "lower" | "source" | "title" | "upper"} TitleCase
 */

// Availability ----------------------------------------------------------------

/**
 * @typedef {Object} AvailableTemplate
 * @property {number} id
 * @property {string} name
 */

// Cards -----------------------------------------------------------------------

/**
 * @typedef {Object} TMDbLanguage
 * @property {string} english_name
 * @property {string} iso_639_1
 * @property {string} name
 */

/**
 * @typedef {Object} ExternalSourceImage
 * @property {string} url
 * @property {?number} width
 * @property {?number} height
 * @property {?TMDbLanguage} language
 */

/**
 * @typedef {Object} SourceImage
 * @property {number} episode_id
 * @property {number} season_number
 * @property {number} season_number
 * @property {number} source_file_name
 * @property {string} source_file
 * @property {string} source_url
 * @property {boolean} exists
 * @property {number} filesize
 * @property {number} width
 * @property {number} height
 */

/**
 * @typedef {Object} SourceImagePage
 * @property {Array<SourceImage>} items
 * @property {number} total
 * @property {number} size
 * @property {number} page
 * @property {number} pages
 */

// Connections -----------------------------------------------------------------

/**
 * @typedef {Object} EmbyConnection
 * @property {number} id
 * @property {"Emby"} interface_type
 * @property {boolean} enabled
 * @property {string} name
 * @property {string} url
 * @property {string} api_key
 * @property {boolean} use_ssl
 * @property {?string} username
 * @property {string} filesize_limit
 */

/**
 * @typedef {Object} JellyfinConnection
 * @property {number} id
 * @property {"Jellyfin"} interface_type
 * @property {boolean} enabled
 * @property {string} name
 * @property {string} url
 * @property {string} api_key
 * @property {boolean} use_ssl
 * @property {?string} username
 * @property {string} filesize_limit
 */

/**
 * @typedef {Object} PlexConnection
 * @property {number} id
 * @property {"Plex"} interface_type
 * @property {boolean} enabled
 * @property {string} name
 * @property {string} url
 * @property {string} api_key
 * @property {boolean} use_ssl
 * @property {boolean} integrate_with_pmm
 * @property {string} filesize_limit
 */

/**
 * @typedef {Object} SonarrLibrary
 * @property {number} interface_id
 * @property {string} name
 * @property {string} name
 */

/**
 * @typedef {Object} SonarrConnection
 * @property {number} id
 * @property {"Sonarr"} interface_type
 * @property {boolean} enabled
 * @property {string} name
 * @property {string} url
 * @property {string} api_key
 * @property {boolean} use_ssl
 * @property {boolean} downloaded_only
 * @property {Array<SonarrLibrary>} libraries
 */

/**
 * @typedef {Object} TMDbConnection
 * @property {number} id
 * @property {"TMDb"} interface_type 
 * @property {boolean} enabled
 * @property {string} name
 * @property {string} api_key
 * @property {string} minimum_dimensions
 * @property {boolean} skip_localized
 * @property {Array<string>} logo_language_priority
 */

/**
 * @typedef {EmbyConnection | JellyfinConnection | PlexConnection |
 *           SonarrConnection | TMDbConnection} AnyConnection
 */

// Preferences -----------------------------------------------------------------

/**
 * @typedef {Object} ToggleOption
 * @property {string} name
 * @property {string} value
 * @property {boolean} selected
 */

/**
 * @typedef {Object} EpisodeDataSourceToggle
 * @property {InterfaceType} interface
 * @property {number} interface_id
 * @property {string} name
 * @property {boolean} selected
 */

/**
 * @typedef {Object} ImageSourceToggle
 * @property {InterfaceType} interface
 * @property {number} interface_id
 * @property {string} name
 * @property {boolean} selected
 */

// Fonts -----------------------------------------------------------------------

/**
 * @typedef {Object} FontAnalysis
 * @property {Object} replacements
 * @property {Array<string>} missing
 */

/**
 * @typedef {Object} NamedFont
 * @property {number} id
 * @property {string} name
 * @property {string} sort_name
 * @property {?string} color
 * @property {?TitleCase} title_case
 * @property {number} size
 * @property {number} kerning
 * @property {number} stroke_width
 * @property {number} interline_spacing
 * @property {number} interword_spacing
 * @property {number} vertical_shift
 * @property {boolean} delete_missing
 * @property {?string} file
 * @property {?string} file_name
 * @property {Object} replacements
 */

// Series ----------------------------------------------------------------------

/**
 * @typedef {Object} Translation
 * @property {string} language_code
 * @property {string} data_key
 */

/**
 * @typedef {Object} MediaServerLibrary
 * @property {"Emby" | "Jellyfin" | "Plex"} interface
 * @property {number} interface_id
 * @property {string} name
 */

/**
 * @typedef {Object} SearchResult
 * @property {string} name
 * @property {number} year
 * @property {Array<string>} overview
 * @property {?string} poster
 * @property {?boolean} ongoing
 * @property {?string} emby_id
 * @property {?string} imdb_id
 * @property {?string} jellyfin_id
 * @property {?string} sonarr_id
 * @property {?string} tmdb_id
 * @property {?string} tvdb_id
 * @property {?string} tvrage_id
 * @property {boolean} added
 */

/**
 * @typedef {Object} SearchResultsPage
 * @property {Array<SearchResult>} items
 * @property {number} total
 * @property {number} size
 * @property {number} page
 * @property {number} pages
*/

/**
 * @typedef {Object} Series
 * @property {string} name
 * @property {number} year
 * @property {string} full_name
 * @property {string} sort_name
 * @property {number} id
 * @property {?number} sync_id
 * @property {?number} font_id
 * @property {Array<number>} template_ids
 * @property {boolean} monitored
 * @property {boolean} match_titles
 * @property {?boolean} sync_specials
 * @property {?boolean} skip_localized_images
 * @property {?boolean} card_filename_format
 * @property {?number} data_source_id
 * @property {?string} card_type
 * @property {?Style} watched_style
 * @property {?Style} unwatched_style
 * @property {?boolean} hide_season_text
 * @property {Array<Object>} season_titles
 * @property {?boolean} hide_episode_text
 * @property {?string} episode_text_format
 * @property {?Array<Translation>} translations
 * @property {Array<Object>} extras
 * @property {Array<MediaServerLibrary>} libraries
 * @property {?string} font_color
 * @property {?TitleCase} title_case
 * @property {?number} font_size
 * @property {?number} font_kerning
 * @property {?number} font_stroke_width
 * @property {?number} font_interline_spacing
 * @property {?number} font_interword_spacing
 * @property {?number} font_vertical_shift
 * @property {string} emby_id
 * @property {?string} imdb_id
 * @property {string} jellyfin_id
 * @property {?number} tmdb_id
 * @property {?number} tvdb_id
 * @property {?number} tvrage_id
 * @property {?string} directory
 * @property {?string} poster_path
 * @property {string} poster_url
 * @property {?string} small_poster_url
 * @property {number} episode_count
 * @property {number} card_count
 */

/**
 * @typedef {Object} Template
 * 
 */

// Syncs -----------------------------------------------------------------------

/**
 * @typedef {Object} Sync
 * @property {int} id
 * @property {"Emby" | "Jellyfin" | "Plex" | "Sonarr"} interface
 * @property {string} name
 * @property {int} interface_id
 * @property {Array<int>} template_ids
 * @property {Array<string>} required_tags
 * @property {Array<string>} excluded_tags
 * @property {Array<string>} required_libraries
 * @property {Array<string>} excluded_libraries
 * @property {Array<string>} required_root_folders
 */

// Blueprints ------------------------------------------------------------------

/**
 * @typedef {Object} Blueprint
 * @property {BlueprintSeries} series
 * @property {BlueprintEpisode} episodes
 * @property {Array<BlueprintTemplate>} templates
 * @property {Array<BlueprintFont>} fonts
 * @property {Array<string>} previews
 * @property {Array<string>} description
 */

/**
 * @typedef {Object} RemoteBlueprintSeries
 * @property {string} name
 * @property {number} year
 * @property {?string} imdb_id
 * @property {?number} tmdb_id
 * @property {?number} tvdb_id
 */

/**
 * @typedef {Object} RemoteBlueprint
 * @property {number} id
 * @property {number} blueprint_number
 * @property {string} creator
 * @property {Date} created
 * @property {RemoteBlueprintSeries} series
 * @property {Blueprint} json
 */

/**
 * @typedef {Object} RemoteBlueprintPage
 * @property {Array<RemoteBlueprint>} items
 * @property {number} total
 * @property {number} size
 * @property {number} page
 * @property {number} pages
 */

// Logs ------------------------------------------------------------------------

/**
 * @typedef {"debug" | "info" | "warning" | "error" | "critical"} LogLevel
 */

/**
 * @typedef {Object} LogEntry
 * @property {LogLevel} level
 * @property {string} context_id
 * @property {string} time
 * @property {string} message
 */

/**
 * @typedef {Object} LogEntryPage
 * @property {Array<LogEntry>} items
 * @property {number} total
 * @property {number} size
 * @property {number} page
 * @property {number} pages
 * 
 */

// Statistics ------------------------------------------------------------------

/**
 * @typedef {Object} Snapshot
 * @property {number} blueprints
 * @property {number} cards
 * @property {number} episodes
 * @property {number} fonts
 * @property {number} loaded
 * @property {number} series
 * @property {number} syncs
 * @property {number} templates
 * @property {number} users
 * @property {number} filesize
 * @property {number} cards_created
 * @property {string} timestamp
 */

export const Types = {};