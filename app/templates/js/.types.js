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

/**
 * @typedef {Object} Extra
 * @property {string} name
 * @property {DictKey} identifier
 * @property {string} description
 * @property {?string} tooltip
 * @property {?string} card_type
 */

// Cards -----------------------------------------------------------------------

/**
 * @typedef {Object} TMDbLanguage
 * @property {string} english_name
 * @property {string} iso_639_1
 * @property {string} name
 */

/**
 * @typedef {Object} EpisodeData
 * @property {number} season_number
 * @property {number} episode_number
 * @property {?number} absolute_number
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
 * @property {SourceImage[]} items
 * @property {number} total
 * @property {number} size
 * @property {number} page
 * @property {number} pages
 */

/**
 * @typedef {Object} TitleCard
 * @property {number} id
 * @property {number} series_id
 * @property {number} episode_id
 * @property {EpisodeData} episode
 * @property {string} card_file
 * @property {number} filesize
 * @property {Object} model_json
 * @property {?string} library_name
 */

/**
 * @typedef {Object} TitleCardPage
 * @property {TitleCard[]} items
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
 * @property {SonarrLibrary[]} libraries
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
 * @property {string[]} logo_language_priority
 */

/**
 * @typedef {EmbyConnection | JellyfinConnection | PlexConnection |
 *           SonarrConnection | TMDbConnection} AnyConnection
 */

// Episodes --------------------------------------------------------------------

/**
 * @typedef {Object} Episode
 * @property {number} id
 * @property {number} series_id
 * @property {number[]} template_ids
 * @property {?number} font_id
 * @property {?string} source_file
 * @property {?string} card_file
 * @property {number} season_number
 * @property {number} episode_number
 * @property {?number} absolute_number
 * @property {string} title
 * @property {?boolean} match_title
 * @property {boolean} auto_split_title
 * @property {?string} card_type
 * @property {?boolean} hide_season_text
 * @property {?string} season_text
 * @property {?boolean} hide_episode_text
 * @property {?string} episode_text
 * @property {?string} unwatched_style
 * @property {?string} watched_style
 * @property {?string} font_color
 * @property {?number} font_size
 * @property {?number} font_kerning
 * @property {?number} font_stroke_width
 * @property {?number} font_interline_spacing
 * @property {?number} font_interword_spacing
 * @property {?number} font_vertical_shift
 * @property {?Date} airdate
 * @property {string} emby_id
 * @property {string} imdb_id
 * @property {string} jellyfin_id
 * @property {number} tmdb_id
 * @property {number} tvdb_id
 * @property {number} tvrage_id
 * @property {?Object.<string, any>} extras
 * @property {Object.<string, string>} translations
 * @property {Card[]} cards
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
 * @property {string[]} missing
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
 * @property {string[]} overview
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
 * @property {SearchResult[]} items
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
 * @property {number[]} template_ids
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
 * @property {Object.<string, string>} season_titles
 * @property {?boolean} hide_episode_text
 * @property {?string} episode_text_format
 * @property {?Translation[]} translations
 * @property {?Object.<string, string>[]} extras
 * @property {MediaServerLibrary[]} libraries
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
 * @property {number[]} template_ids
 * @property {string[]} required_tags
 * @property {string[]} excluded_tags
 * @property {string[]} required_libraries
 * @property {string[]} excluded_libraries
 * @property {string[]} required_root_folders
 */

// Blueprints ------------------------------------------------------------------

/**
 * @typedef {Object} BlueprintFont
 * @property {string} name - The name of the font.
 * @property {?string} color - The color of the font. Optional.
 * @property {boolean} delete_missing - Boolean flag for deleting missing elements.
 * @property {?string} file - The file associated with the font. Optional.
 * @property {?number} kerning - The kerning value for the font. Optional.
 * @property {?number} interline_spacing - The interline spacing for the font. Optional.
 * @property {?number} interword_spacing - The interword spacing for the font. Optional.
 * @property {?string[]} replacements_in - List of strings for replacements. Optional.
 * @property {?string[]} replacements_out - List of strings for replacements. Optional.
 * @property {?number} size - The size of the font. Optional.
 * @property {?number} stroke_width - The stroke width for the font. Optional.
 * @property {?TitleCase} title_case - TitleCase information. Optional.
 * @property {?number} vertical_shift - The vertical shift for the font. Optional.
 */

/**
 * @typedef {BlueprintFont} RemoteBlueprintFont
 * @property {?string} file_download_url
 */

/**
 * @typedef {Object} Blueprint
 * @property {BlueprintSeries} series
 * @property {BlueprintEpisode} episodes
 * @property {BlueprintTemplate[]} templates
 * @property {RemoteBlueprintFont[]} fonts
 * @property {string[]} previews
 * @property {string[]} description
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
 * @property {RemoteBlueprint[]} items
 * @property {number} total
 * @property {number} size
 * @property {number} page
 * @property {number} pages
 */

// Logs ------------------------------------------------------------------------

/**
 * @typedef {"DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"} LogLevel
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
 * @property {LogEntry[]} items
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