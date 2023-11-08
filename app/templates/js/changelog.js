const changeLog = [
  {
    version: 'v2.0-alpha.7.0',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Use new logo
    <div class="list">
      <img style="background: rgb(28, 28, 28); border-radius: 0.4em;" width="50%" src="https://raw.githubusercontent.com/CollinHeist/TitleCardMaker/web-ui/app/assets/logo.png">
    </div>
  </div>
  <div class="item">Major documentation revisions
    <div class="list">
      <div class="item">Relocate all v2 documentation to <a href="https://titlecardmaker.com" target="_blank">titlecardmaker.com</a></div>
      <div class="item">Create dynamic auto-generated "social cards" for richer link previews in Discord (and other site) - for example:</div>
      <div class="item"><img width="50%" src="https://raw.githubusercontent.com/CollinHeist/TitleCardMaker/gh-pages/assets/images/social/blueprints.png"></div>
      <div class="item">Use site-wide banner for navigation, move table of contents to sidebar (more room for content)</div>
      <div class="item">Add various pages (including starter Docker and Docker compose pages)</div>
    </div>
  </div>
  <div class="item">Various Blueprint improvements
    <div class="list">
      <div class="item">Allow multiple preview files on all Blueprints - hovering over the preview will show a small animation indicating >1 preview file which can be cycled through by clicking</div>
      <div class="item">Allow arbitrary files to be added to Blueprints. These files are then downloaded into the relevant Source directory when imported</div>
      <div class="item">Add toggle to the Blueprint browser to only show Blueprints for Series which you have already added to TCM</div>
      <div class="item">Add toggle to the Blueprint browser to exclude Blueprints which have already been imported (does not work retroactively)</div>
      <div class="item">Limit the height of Blueprint description fields</div>
      <div class="item">Add pre-populated database IDs to Blueprint issue forms (when opened via the UI)</div>
      <div class="item">Relocate repository to TitleCardMaker organization - now at <a href="https://github.com/TitleCardMaker/Blueprints" target="_blank">TitleCardMaker/Blueprints</a></div>
    </div>
  </div>
  <div class="item">Use "fuzzy" string matching in search toolbar (using Levenshtein Distance between strings)</div>
  <div class="item">View Title Cards and Source Images within the UI (on the Files tab of a Series' page)</div>
  <div class="item">Added ability to analyze custom Font files and make character replacement suggestions
    <div class="list">
      <div class="item">New <b>Analyze Font Replacements</b> button which performs an analysis of the Font for missing characters and makes suggestions for replacements (and warns about irreplaceable characters)</div>
      <div class="item">Suggestions now look to decompose Unicode characters in their normalized equivalents when searching for replacements - e.g. if <b>é</b> is missing, it will look for <b>É</b>, <b>e</b>, then <b>E</b>, etc.</div>
      <div class="item">Font analysis now looks at empty glyphs in addition to missing glyphs - this should catch instances where the Font was created with blank spaces instead of the glyph being omitted</div>
      <div class="item">The analysis looks at the titles and translations of all Episodes associated with (even by proxy) the Font</div>
    </div>
  </div>
  <div class="item">Allow for card-type specific generic season title specification
    <div class="list">
      <div class="item">Cards can define a <b>SEASON_TEXT_FORMATTER</b> attribute of type <b>Callable[[EpisodeInfo], str]</b> to change the season title text when there is no customization</div>
    </div>
  </div>
  <div class="item">Various front-end changes
    <div class="list">
      <div class="item">Make the background color on dark mode slightly darker</div>
      <div class="item">Move the Connections, Scheduler, and Import tabs under the Settings tab on the side bar</div>
      <div class="item">Create new Add Series tab under the home page on the side bar (and remove floating button)</div>
      <div class="item">Add animated loading logo when waiting for Series to load on the home page</div>
    </div>
  </div>
  <div class="item">Add new <b>absolute_episode_number</b> variable which can be used in variable formats (e.g. episode text formats) and is the absolute number <i>if available</i>, and the episode number if not</div>
  <div class="item">Add new human readable cron expressions to the Scheduler table (in advanced scheduler mode) - e.g. <b>20 */10 * * *</b> is described as <b>At 20 minutes past the hour, every 10 hours</b></div>
  <div class="item">Add healthcheck command, and API endpoint, to Docker container</div>
  <div class="item">Automatically perform backups of the database and global options before attempting any SQL schema migrations</div>
</div>
<h2>Major Fixes</h2>
<div class="ui ordered list">
  <div class="item">Correctly utilize Template ordering
    <div class="list">
      <div class="item">The SQL template relationships <i>were</i> utilizing implicit ordering by Template ID, but if a non-sequential Template order was applied to a Sync/Series/Episode, then the order would constantly be reset</div>
      <div class="item">Update SQL schema to <b>25490125daaf</b> which adds an explicit <b>order</b> column to all many-to-many association tables</div>
      <div class="item">Correctly initialize Sync Template dropdowns with the correct order of Template specifications</div>
    </div>
  </div>
  <div class="item">Allow force-resetting of passwords by specifying the <b>TCM_DISABLE_AUTH</b> environment variable while booting to avoid potential lockouts</div>
  <div class="item">Fix name mismatches when importing Blueprints causing duplicate Series entries (matching is now done with database IDs)</div>
  <div class="item">Use hashed image URLs for source images so they properly reload when modified</div>
  <div class="item">Fix Episode ID assignment in Jellyfin</div>
  <div class="item">Correctly load Title Cards into multiple servers when Series has more than one library</div>
  <div class="item">Correctly apply Plex Sync exclusion tags</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Relocate the y-position of the index text on the Calligraphy card. It is now dynamic with the logo height</div>
  <div class="item">Paginate the <b>/api/cards/series/{series_id}</b> API endpoint</div>
  <div class="item">Minor visual changes to the login page
    <div class="list">
      <div class="item">Add logo above login header</div>
      <div class="item">Add link to new <a href="https://titlecardmaker.com/user_guide/connections/#forgotten-login" target="_blank">forgotten password</a> instructions</div>
    </div>
  </div>
  <div class="item">Modified "help" tooltips on various pages to not use popups but instead inline help text - this looks better and makes this info always visible (even on mobile)</div>
  <div class="item">Only keep backups for up to 3 weeks</div>
  <div class="item">Add connection-thematic-specific coloring to Sync elements</div>
  <div class="item">Start loading Font preview when directed from Font link</div>
  <div class="item">Sleep 30 seconds between attempts to load Episode Cards via API endpoints (Tautulli, Sonarr, excplit) - up from 15</div>
  <div class="item">Add new "does not contain" Template Filter condition - can be used for strings and list variables</div>
  <div class="item">Change Template sidebar icon to not conflict with new logo</div>
  <div class="item">Add help text to the (un)monitor button below Series posters (was hoverable tooltip)</div>
  <div class="item">Also open Series search bar by pressing <kbd class="ui label">/</kbd> key</div>
  <div class="item">Auto-redirect from login page if authentication is disabled</div>
  <div class="item">Add global "colorblind" accessibility option to utilize more distinct colors (primarily in progress bars)</div>
  <div class="item">Add global option for enabled language codes to allow specification of translated numbers (i.e. Season and Episode text)</div>
  <div class="item">Refresh (and animate the reloading of) Card statistics when clicked </div>
  <div class="item">Query Series statistics every 60 seconds (increased from 30)</div>
  <div class="item">Add header button which links to the current page's relevant documentation if available</div>
  <div class="item">Modify the sidebar toggle logic - clicking the logo will return to home page if you are not on mobile</div>
  <div class="item">Add a loading indicator to Blueprint elements while being imported</div>
  <div class="item">Revise changelog to utilize accordions to make navigation easier</div>
  <div class="item">Add a note to the Sync page if no Connections are defined</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Handle non-404 errors when downloading Font files from Blueprints</div>
  <div class="item">Handle permission errors for root folders creation when starting TCM</div>
  <div class="item">Left-align Blueprint actions on mobile</div>
  <div class="item">Remove temporary title-match logging when evaluating EpisodeInfo comparisons</div>
  <div class="item">Add default <b>TZ</b> of <b>UTC</b> to Docker build</div>
  <div class="item">Add missing placeholder text to some card type dropdowns</div>
  <div class="item">Change default season text on Calligraphy card to <b>Season {season_number_cardinal}</b> - e.g. <b>Season One</b> (was <b>Season 1</b>)</div>
  <div class="item">Limit length of file name path components of cards, folders, etc. to 254 characters (could be exceeded if the title was included in the filename)</div>
  <div class="item">Correctly utilize Card <i>type</i> default Font replacements in Title Card creation</div>
  <div class="item">Return Series search results by the Series <i>sort</i> name (so case and special character-agnostic)</div>
  <div class="item">Properly clear new Sync forms after creation</div>
  <div class="item">Do not show error toasts when statistics cannot be queried on the home page</div>
  <div class="item">Correctly handle all supported TMDb language codes (was using outdated list)</div>
  <div class="item">Correct logo downloading from Emby and Jellyfin</div>
  <div class="item">Wrap pagination menus on the home page on mobile to avoid overflow</div>
  <div class="item">Do not auto-zoom into text boxes on mobile (particularly iOS) by dynamically adjusting font size to 16px when selected</div>
  <div class="item">Properly color the "outside page" background in some mobile browsers</div>
  <div class="item">Handle explicitly raised errors (caused by bad Episode data sources) in Refresh Episode Data task</div>
  <div class="item">Properly handle deleting attributes from the Preferences model without resetting object</div>
  <div class="item">Correct next/previous navigation between same-named Series</div>
  <div class="item">Correctly set <i>Options</i> tab as active tab by default to avoid flicker when loading page</div>
  <div class="item">Only remake Cards for changes to attributes which are actually reflected in the selected Card's card type model
    <div class="list">
      <div class="item">Remove individual variable columns of the Card SQL table; instead store generic <b>model_json</b> data</div>
      <div class="item">Update SQL schema to <b>caec4f618689</b> to convert existing Card objects</div>
      <div class="item">Non-builtin Cards will be remade after migration</div>
    </div>
  </div>
  <div class="item">Re-query the current page of Series when the sort order is changed on the home page</div>
  <div class="item">Do not submit separate API requests for adding a Series and importing a Blueprint in one operation</div>
  <div class="item">Reflect global un/watched style settings in Template previews</div>
  <div class="item">Attempt to refresh Episode data up to three times in Sonarr webhook API endpoints (for when your EDS is a Media Server and is slow to refresh)</div>
  <div class="item">Properly detect mobile devices in JS</div>
  <div class="item">Correctly clear Episode translations in Episode modals</div>
</div>`
  },
  {
    version: 'v2.0-alpha.6.0',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Add API endpoint to trigger Card creation via Sonarr webhook - this is practically identical to the Tautulli trigger (but not for watched-status changes) but works for all Media Servers - setup docs are <a href="https://titlecardmaker.readthedocs.io/en/latest/getting_started/connections/sonarr/#webhook-integration" target="_blank">here</a></div>
  <div class="item">Create new Calligraphy card type
    <div class="list">
      <img class="ui large image" src="/internal_assets/cards/calligraphy.jpg">
    </div>  
  </div>
  <div class="item">Create new Marvel card type
    <div class="list">
      <img class="ui large image" src="/internal_assets/cards/marvel.jpg">
    </div>
  </div>
  <div class="item">Simplify default directory structure
    <div class="list">
      <div class="item">Move <b>assets</b>, <b>backups</b>, <b>logs</b>, and <b>source</b> directories under <b>config</b>.</div>
      <div class="item">Move the Database and global options files under <b>config</b></div>
    </div>
  </div>
  <div class="item">Explicitly handle and integrate local Python card types into the UI 
    <div class="list">
      <div class="item">Any <b>*.py</b> file will be parsed when launched and on trigger of the <b>RefreshCardTypes</b> task</div>
      <div class="item">Documentation for integrating cards is available <a href="https://titlecardmaker.readthedocs.io/en/latest/card_types/local/" target="_blank">here</a></div>
    </div>
  </div>
  <div class="item">Back up global settings / preferences when performing the <b>BackupDatabase</b> task</div>
  <div class="item">Toggle side navigation bar completely when the TCM icon is clicked</div>
  <div class="item">Display changelogs within the UI (<i>you're looking at it!</i>)</div>
  <div class="item">Write EXIF data to all Plex uploaded images when PMM Integration is enabled</div>
</div>
<h2>Major Fixes</h2>
<div class="ui ordered list">
  <div class="item">Correctly display and edit extras in Episode modals</div>
  <div class="item">Use bottom-heavy titling in Overline card</div>
  <div class="item">Correct YAML importing to properly sequence imports of Fonts, then Templates, then Series</div>
  <div class="item">Properly apply custom Fonts to Series when importing YAML</div>
  <div class="item">Correctly convert season folder format variables when importing YAML</div>
  <div class="item">Hide home page statistics on mobile to improve formatting</div>
  <div class="item">Properly initialize, enable, and display the Template special syncing dropdown</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Only query card types once per load on Templates page</div>
  <div class="item">Filter file browser to accept Font files in upload dialog</div>
  <div class="item">Filter file browser to accept image files in source, poster, and logo upload dialogues</div>
  <div class="item">Add note about what Blueprints are to Series page</div>
  <div class="item">Use global card file type for preview image generation (should be ~50% faster for those with <b>.jpg</b> as their card extension)</div>
  <div class="item">Modify the Star Wars and Landscape card type descriptions</div>
  <div class="item">Modify <b>Font.file</b> SQL schema and data to <b>Font.file_name</b></div>
  <div class="item">Add <b>--logo</b> mini argument to mini_maker.py to add logo files to created cards</div>
  <div class="item">Apply Font replacements before and after title text case function and title splitting is applied</div>
  <div class="item">Add button to quickly add all letters of the alphabet to the preview title in the Font preview</div>
  <div class="item">Make season title popups uninvertible</div>
  <div class="item">Add button to add all A-Z/a-z to the example title on Fonts preview</div>
  <div class="item">Allow specification of "even" splitting style in card types (instead of just top / bottom)</div>
  <div class="item">Add variables for the "title-case" version of spelled episode text cardinal and ordinal numbers - i.e. "One" instead of "one" (only applies to Cards with non-fix cased season/episode text)</div>
  <div class="item">Add episode text font size extra to Olivier card</div>
  <div class="item">Add dynamic links to the assigned Fonts for Templates and Series which opens the Font page for easier editing</div>
  <div class="item">Export Series and Template localized image rejection in Blueprints</div>
  <div class="item">Add navbar and header via Jinja2 templates, not AJAX injection</div>
  <div class="item">Add contextual logging to each Alembic SQL schema migration</div>
  <div class="item">Add logo vertical shift extra to Tinted Frame card</div>
  <div class="item">Highlight the active page in the nav bar</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Handle bad f-strings in Card <b>logo_file</b> format strings</div>
  <div class="item">Add more TMDb language codes for translations and logo language prioritization</div>
  <div class="item">Explicitly attempt the Sonarr and Tautulli integration endpoints multiple (up to 6) times - this should handle instances where the media server is slow to add the new Episode to the server, causing TCM to fail to upload the new Card</div>
  <div class="item">Only generate number word translations when requested for Card creation</div>
  <div class="item">Correct preview episode text in card preview endpoint</div>
  <div class="item">Pass watched attribute into Preview card model so that watched-status specific toggles (not styles) are applied</div>
  <div class="item">Properly apply blurred grayscale style modifiers to preview cards if watched and unwatched styles are both blurred and grayscale</div>
  <div class="item">Correctly import the <b>logo_language_priority</b> YAML option</div>
  <div class="item">Fix v1 Summary image creation</div>
  <div class="item">Handle bad <b>TZ</b> environment declarations in Docker</div>
  <div class="item">Export Series <b>match_titles</b> property in Blueprints</div>
  <div class="item">Use TVDb <b>/dereferrer</b> endpoint in TVDb links</div>
</div>`
  },
  {
    version: 'v2.0-alpha.5.2',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Match existing Fonts and Templates (by name) when importing Blueprints</div>
  <div class="item">Add various UI global options:
    <div class="list">
      <div class="item">How many Series to display per page on the home page</div>
      <div class="item">How many Episodes to display per page</div>
      <div class="item">Whether to stylize un-monitored Series posters on the home page</div>
      <div class="item">Whether to display simplified Episode data tables which only display the most commonly edited columns</div>
    </div>
  </div>
  <div class="item">Export Font files in a separate sub-zip directory when exporting Blueprints</div>
  <div class="item">Add warnings to the Series page if the Series is not matched in Emby/Jellyfin/Sonarr/TMDb</div>
  <div class="item">Add display to start adding a new Series for given query if no results are found in search bar</div>
  <div class="item">Create Overline card type
    <div class="list">
      <img class="ui large image" src="https://user-images.githubusercontent.com/17693271/271863029-e82e411c-8d43-4de8-89f0-470fe007c626.jpg"/>
    </div>
  </div>
  <div class="item">Automatically search for "mask" images to overlay on top of the frame and frame edges in the Tinted Frame card
    <div class="list">
      <div class="item">TCM will search for files named like <code>{filename}-mask.png</code> - e.g. <code>s1e1-mask.png</code> in the source folder</div>
      <div class="item">If provided, this mask image is overlayed after the text and frame is drawn</div>
      <div class="item">This can be used to give the appearance of part of the image extending beyond the boundaries of the frame - for example:</div>
        <img class="ui large image" src="https://user-images.githubusercontent.com/17693271/271863036-3e55a94c-b9a6-4e7b-8735-ee8b8fc0c33c.jpg"/>
    </div>
  </div>
  <div class="item">Merge new user card type <code>azuravian/SciFiTitleCard</code></div>
</div>
<h2>Major Fixes</h2>
<div class="ui ordered list">
  <div class="item">Use version number in Javascript filenames to avoid caching files between versions</div>
  <div class="item">Correct page load error when loading Series pages with non-default Font kerning and default stroke widths</div>
  <div class="item">Improve reliability and speed of Tautulli Plex rating key endpoint </div>
  <div class="item">Delete old Blueprint zips</div>
  <div class="item">Actually use Font replacements</div>
  <div class="item">Update <code>Wdvh/WhiteTextStandard</code> to be much faster and integrate better with the UI</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Do not refresh ImageMagickInterfaces after updating global Settings</div>
  <div class="item">Reduce remote card type API endpoint queries on the Series page (improves loading time)</div>
  <div class="item">Globally query available data on the Series page to significantly improve Episode table loading times</div>
  <div class="item">Add blank Templates at the top of the Templates list</div>
  <div class="item">Utilize persistent Jellyfin IDs</div>
  <div class="item">Add Glass Color extra in Tinted Glass card</div>
  <div class="item">Use better Series title matching in Plex (for Series without database IDs)</div>
  <div class="item">Don't display erroneous placeholders for Font values</div>
  <div class="item">Add additional info to tooltips on the default values of some extras</div>
  <div class="item">Do not blur edges of source images in the Tinted Frame card when entire image is already blurred (should improve card creation time when blurring is enabled)</div>
  <div class="item">Remove explicit logo extra from imported Templates YAML</div>
  <div class="item">Add episode text vertical shift extra to Olivier card</div>
  <div class="item">Remove warning about Episode missing an absolute number in season title range evaluations</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Handle SQL errors in load all Title Cards task</div>
  <div class="item">Display more pagination elements by default</div>
  <div class="item">Properly detect contextual Loggers in decorated functions</div>
  <div class="item">Do not invert modal un-invertible subconten</div>
  <div class="item">Correct CreateTitleCards Task description</div>
  <div class="item">Correct plural of Episode override count when browsing the Blueprints on the Series page</div>
  <div class="item">Use contextual logger in Remote card type initialization</div>
  <div class="item">Explicitly sanitize card filenames (should handle explicit \n in card filenames)</div>
  <div class="item">Correctly detect hidden episode text in Olivier card</div>
  <div class="item">Refer to the web-ui branch of the CardTypes repository for all RemoteFile objects</div>
  <div class="item">Handle more instances of busy databases in scheduled Tasks</div>
  <div class="item">Handle explicit newlines (<b>\\n</b>) in titles for preview card creation</div>
</div>`
  },
  {
    version: 'v2.0-alpha.5.1',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Rewrite various PlexInterface functions to significantly improve speed of Plex as a Sync and Episode data source</div>
  <div class="item">Add buttons to the Series page to remove all TCM / PMM labels from within Plex</div>
  <div class="item">Add scheduled Task to remove "bad" Card entries (e.g. duplicates, unlinked, etc.)</div>
  <div class="item">Use separate colors for "progress" bars to differentiate un/monitored Series on the home page</div>
  <div class="item">Overhaul extra selection to display all supported extras in dropdowns</div>
  <div class="item">Add various extras to the Tinted Frame card:
    <div class="list">
      <div class="item">Add <b>episode_text_font</b> to override the Font used for the Episode Text</div>
      <div class="item">Add <b>episode_text_font_size</b> to adjust the size of the Episode text</div>
      <div class="item">Add <b>episode_text_vertical_shift</b> to adjust vertical position of Episode text</div>
      <div class="item">Add <b>frame_width</b> to adjust the width of the frame</div>
    </div>
  </div>
  <div class="item">Add column to the Episode data table to create a singular Card</div>
  <div class="item">Add new Font customization option for interword spacing</div>
</div>
<h2>Major Fixes</h2>
<div class="ui ordered list">
  <div class="item">Fix logo as the top/middle element in Tinted Frame card</div>
  <div class="item">Correctly export Episode extras in Blueprints</div>
  <div class="item">Keep records of advanced scheduling crontabs between restarts</div>
  <div class="item">Respect logo size scalar in Tinted Frame boundaries</div>
  <div class="item">Permit <b>{title}</b> in the global filename format option</div>
  <div class="item">Fix direction of vertical shifts in the Tinted Glass card (was opposite to the glass box)</div>
  <div class="item">Fix the Cutout title card on some versions of ImageMagick</div>
  <div class="item">Handle SVG logos selected via the UI</div>
  <div class="item">Add button to query TMDb for logos if a Series logo does not already exist</div>
  <div class="item">Correctly display previously modified extras in the Episode extras modal</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Automatically open and start populating Issue when the "Export Blueprint" button is pressed</div>
  <div class="item">Allow ordering Blueprints by creation or Series name</div>
  <div class="item">Log "missing" Series triggers by Tautulli endpoint as info, not errors</div>
  <div class="item">Remove deleted row from Episode data table without re-querying all Episodes</div>
  <div class="item">Sequentially transition in Posters on home page, and search results on the new Series page</div>
  <div class="item">Use dark theme by default</div>
  <div class="item">Display up to 15 page selectors on the Episode data tab, up to 4 on mobile</div>
  <div class="item">Only display 50 Episodes/page on Episode data table</div>
  <div class="item">Use a container size of 500 in PlexInterface functions</div>
  <div class="item">Add global support for <b>title_text_format</b> extra to apply automatic formatting to title text</div>
  <div class="item">Show "internal" tasks within the UI when Advanced Scheduling is enabled</div>
  <div class="item">Add new Fonts and Templates to the top of their respective lists</div>
  <div class="item">Automatically convert filename format arguments from v1 to their v2 equivalents</div>
  <div class="item">Change default interval for the refresh Episode data Task to 8 hours (from 6)</div>
  <div class="item">Add headers between Fonts when more than 20 are defined</div>
  <div class="item">Permit custom Font files in the Roman Numeral card</div>
  <div class="item">Show up to 15 (5 on mobile) page selectors for Blueprints</div>
  <div class="item">Add API endpoint to get all Cards, unblacklist Blueprint</div>
  <div class="item">Display more verbose errors in toasts for 422 validation errors</div>
  <div class="item">Autofocus on the search field on the new Series page</div>
  <div class="item">Add <b>blur_profile</b> extra to the Cutout card</div>
  <div class="item">Add divider_color extra to the Divider card</div>
  <div class="item">Parse Font interline spacing in the Roman Numeral card</div>
  <div class="item">Parse Font interline spacing and Kerning in the Cutout card</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Correct interface refreshing triggered by toggling the connection</div>
  <div class="item">Stop querying or displaying logs, and Series statistics when cookie / session expires</div>
  <div class="item">Correct contextual logger reference in error decorators</div>
  <div class="item">Fix Sync modals on mobile (they were too wide)</div>
  <div class="item">Fix Emby and Jellyfin library dropdown population in Sync modals</div>
  <div class="item">Do not automatically uppercase season and episode text in Divider card</div>
  <div class="item">Do not automatically expire DB sessions after commiting</div>
  <div class="item">Include disabled auto title splitting in Episode Blueprint exports</div>
  <div class="item">Properly handle missing logos on Fade and Poster title cards</div>
  <div class="item">Do not display "negative" previous Task durations</div>
  <div class="item">Use the correct slashes in the card directory placeholder text on the Series page</div>
  <div class="item">Remove Episode ID's from list of batch ID's when manually saved</div>
  <div class="item">Log the relevant Episode labels when preventing source image selection within Plex</div>
  <div class="item">Allow empty character replacements in custom Fonts</div>
  <div class="item">Use inline Form validation on Form page</div>
  <div class="item">Correctly parse unchecking the "Delete Missing" checkbox</div>
  <div class="item">Fix exporting Episode data in Blueprints when Plex is used as the Episode data source</div>
  <div class="item">Handle more instances of "bad" search results from Sonarr</div>
  <div class="item">Parse background extra for the Logo card</div>
  <div class="item">Make Template Filter reference values optional</div>
  <div class="item">Refresh HTML theme after adding new Template Filter conditions</div>
  <div class="item">Do not use Background Tasks in the Tautulli / Plex rating key endpoint to avoid race conditions where no cards are loaded if task sequences quickly after card creation</div>
  <div class="item">Do not "manually" refresh Series Episode data after adding a Series from the UI (redundant)</div>
  <div class="item">Utilize Font stroke width in the Divider card</div>
</div>`
  }
]

/*
 * Turn the given version string into an array of version numbers. For
 * example:
 *   versionToNumber('v2.0-alpha.3.0-webui14') => [2, 0, 3, 0, 14]
 */
function versionToNumber(versionString) {
  return versionString.match(/(\d+)/g).map(v => parseInt(v));
}

/*
 * Evaluate whether the version numbers of v1 are greater than v2; i.e.
 * v1 > v2. This returns true if v1 is a higher version that v2; and
 * false otherwise.
 */
function v_gt_v(v1, v2) {
  for (let i = 0; i < v1.length; i++) {
    // v1 is explicitly > v2
    if (v1[i] > v2[i]) { return true; }
    // v1 is explicitly < v2
    if (v1[i] < v2[i]) { return false; }
  }
  return false;
}

/*
 * Show a modal displaying the changelog between the current version and the
 * last displayed version. The last displayed version is queried from the site
 * local storage.
 */
function notifyChanges(currentVersion, forceDisplay=false) {
  // Get last version whose changelog was displayed to user, exit if was this version
  const lastVersion =  window.localStorage.getItem('version') || 'v2.0-alpha.5.2';
  if (!forceDisplay && currentVersion === lastVersion) { return; }

  let changes = '<div class="ui styled fluid accordion">';
  for (let {version, changelog} of changeLog) {
    // Version not notified, add to changelog
    changes += `
<div class="title">
  <i class="dropdown icon"></i>
  ${version}
</div>
<div class="content">
  ${changelog}
</div>`;
  }
  changes += '</div>'

  // Changes to display, show modal
  if (changes) {
    $.modal({
      title: 'Changelog',
      class: 'uninvertible large',
      closeIcon: true,
      content: changes,
      classContent: 'internal scrolling',
    }).modal('show');
    $('.ui.accordion').accordion();
  }

  // Changelog displayed, update local storage
  window.localStorage.setItem('version', currentVersion);
}
