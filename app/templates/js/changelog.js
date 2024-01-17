const changeLog = [
  {
    version: 'v2.0-alpha.8.0',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Add support for multiple of each type of Connection - e.g. two Sonarr servers, two Plex servers, etc.
    <div class="list">
      <div class="item">Rewrite a majority of the backend to support an arbitrary number of Connections and libraries</div>
      <div class="item">Automatically convert "Episode is Watched" Template Filter arguments</div>
      <div class="item">Allow for multiple libraries per-server per-Series and library-specific Title Card creation - e.g. you can now have a Plex TV, TV 4K, Emby TV, TV 4K,<i>and</i>Jellyfin TV, TV 4K library for a single Series (but why would you?)</div>
      <div class="item">Add global option to enable per-library Card naming; this is required to keep separate Cards with separate watched statuses per library</div>
      <div class="item">Display a Card's library name in the hover text within UI (if setting is enabled)</div>
      <div class="item">Display error on Settings/Connections sidebar when a Connection is invalid</div>
      <div class="item"><b>Sonarr libraries will need to be re-assigned</b></div>
    </div>
  </div>
  <div class="item">Rewrite Tautulli notification agent integration and endpoint to work with multiple Plex servers
    <div class="list">
      <div class="item">Tautulli is now a sub-component of a Plex Connection, no longer a separate section on the page</div>
      <div class="item"><b>Tautulli agents will need to be re-created</b></div>
    </div>
  </div>
  <div class="item">Create new Banner, Graph, Inset, and Shape card types
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/d57120cd-8048-4243-9970-27b2652c4fb9">
    </div>
  
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/bb1eb690-5a8e-49ea-8777-d73458d387e8">
    </div>
  
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/7a5b452d-6577-462e-835b-42c4c75342a8">
    </div>
  
    <div class="list">
      <img width="50%" src="https://raw.githubusercontent.com/CollinHeist/TitleCardMaker/web-ui/app/assets/cards/shape.jpg">
    </div>
  </div>
  <div class="item">Combine "Refresh Episode Data," "Download Source Images," and "Add Translation" tasks / functionality into the "Create Title Cards" task / interactions - this replaces the "Process Series" buttons/terminology
    <div class="list">
      <div class="item">This was done because each of these tasks was meaningless without Card creation, and if triggered out-of-sync, then would trigger needless Card re-creations</div>
      <div class="item">Remove "Process Series" button from Series page</div>
      <div class="item">Change default interval of "Create Title Cards" task to every 12 hours</div>
    </div>
  </div>
  <div class="item">Create tabular view for home page (default view is table; can be toggled in Settings)
    <div class="list">
      <div class="item">This view allows performing "batch" operations to multiple Series at once</div>
      <div class="item">Shift-clicking/selection functionality is implemented</div>
    </div>
  </div>
  <div class="item">Create Snapshot SQL table where TCM will periodically take a "snapshot" of your DB
    <div class="list">
      <div class="item">This snapshot notes how many Episodes, Series, Fonts, Title Cards you have; as well as total number of Title Cards created, etc.</div>
      <div class="item">These snapshots can be visualized into a fully interactive graph by clicking <b>View Graphs</b> at the bottom of the home page, like so:
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/f61c7949-b81c-4bda-8501-ca16f3899e46">
    </div>
  </div>
    </div>
  </div>
  <div class="item">Rework home page statistics
    <div class="list">
      <div class="item">Now they are located at the bottom of the home page</div>
      <div class="item">Display more types of statistics (e.g. number of Fonts, Templates, etc.)</div>
    </div>
  </div>
  <div class="item">Automatically redact "secrets" from logs (this applies to URLs and API keys)</div>
  <div class="item">Allow arbitrary Python code inside format strings - not just base <b>str.format</b> data
    <div class="list">
      <div class="item">Can access any Card variables, as well as <b>NEWLINE</b> for <b>\n</b>, and <b>to_roman_numeral</b> to convert a number to a roman numeral</div>
      <div class="item">For example, a title text format of <b>{NEWLINE.join([' '.join(['.'.join(word) for word in line.split(' ')]) for line in title_text.splitlines()])}</b> will automatically insert a period between all non-line splitting letters of each word in the title text - I used this to create Title Cards for Friends like so:
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/2ad83847-857f-4c26-b5f9-3cace17e6a73">
    </div>
  </div>
    </div>
  </div>
  <div class="item">Allow pre- and post- case-function application (i.e. upper/lower-case) specific Font character replacements
    <div class="list">
      <div class="item">Any character replacements prefixed with <b>pre:</b> or <b>post:</b> will only apply that replacement once</div>
    </div>
  </div>
  <div class="item">Add new global settings:
    <div class="list">
      <div class="item">Option to delete a Series' Source Images when the Series is deleted from the UI</div>
      <div class="item">Option to delete any "missing" Episodes which are in TCM but<i>not</i>in the assigned Episode Data Source</div>
      <div class="item">Option to reduce in-UI animations (for performance and/or accessibility)</div>
    </div>
  </div>
</div>
<h2>Major Fixes </h2>
<div class="ui ordered list">
  <div class="item">Fix Episode source image uploading via UI</div>
  <div class="item">Fix source image downloading from Emby</div>
  <div class="item">Utilize SQL cascade orphan deletion to clean up Episode, Card, and Loaded assets when a Series or Episode is deleted</div>
  <div class="item">Handle invalid cron expressions in Scheduler table initialization</div>
  <div class="item">Properly utilize a Series' sort name in the repository URL evaluation</div>
  <div class="item">Properly import Blueprints with multiple pre-existing Templates and Fonts</div>
  <div class="item">Correct Template ID assignment in the add new Episode endpoint</div>
  <div class="item">Handle new types of Tautulli API keys (was hexstrings, now can be any string)</div>
  <div class="item">Correct small-screen size detection (was using monitor size, not window size)</div>
  <div class="item">Handle bad formatting (mainly newlines) in Scheduler cron expressions</div>
  <div class="item">Handle explicit line breaks (<b>\n</b>) in season and episode text</div>
  <div class="item">Correctly parse some language codes in title translation </div>
  <div class="item">Automatically retry un-initialized Connections when making requests (previously would require a restart of TCM)</div>
  <div class="item">Reject bad Source content when manually selecting and uploading an image via the UI</div>
  <div class="item">Prevent one Task from running multiple times if triggered manually and then a scheduled trigger occurs</div>
  <div class="item">Escape backslash characters<i>before</i>other command characters to handle titles that start and end with quotes (<b>"</b>)</div>
  <div class="item">Add a new scheduled Task to "clean" the database and remove duplicate and outdated entries</div>
  <div class="item">Correctly identify changes to the Card source file (i.e. switching between Art and Unique styles)</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Also display images from Plex when browsing Episode Source Images within UI
    <div class="list">
      <div class="item">Utilize proxied URL to avoid sending the header X-Plex-Token in the URL (for MITM)</div>
      <div class="item">Update Source Image download endpoint to reverse-proxy Plex URLs </div>
    </div>
  </div>
  <div class="item">Do not ignore temporary / placeholder titles from Sonarr or Plex if title matching is enabled - this means Cards will be created with titles like "TBA" if triggered via an integration (Tautulli or Sonarr webhook), but will be updated during the next Title Card creation (if new titles are available)</div>
  <div class="item">Add row-marking to Episode data tables if that Episode is missing a Card</div>
  <div class="item">Trigger Card (re)creation by clicking on it in the Files tab of the UI</div>
  <div class="item">Add 'Episode Extras' Template Filter variable (supported operations are listed <a href="https://titlecardmaker.com/user_guide/templates/#filters)" target="_blank">in the docs</a></div>
  <div class="item">Utilize SQLAlchemy 2.0 ORM mappings in all tables for better TA and intellisence</div>
  <div class="item">Utilize randomly selected Title Card as preview in Blueprint export to add variety when exporting multiple Blueprints for a Series (was always the first Card)</div>
  <div class="item">Compress images with Pillow, not ImageMagick</div>
  <div class="item">Change input background color for dark mode to <b>#e4e4e4</b> from <b>#ffffff</b> (for those with picky eyes like me)</div>
  <div class="item">Change search icon for browsing Source Images in UI</div>
  <div class="item">Automatically restore from backup if SQL migration failed during boot (to avoid future migration changes created by existing intermediate alembic tables)</div>
  <div class="item">Change <b>Card</b> SQL table primary key to auto-increment (meaning Card IDs will not be reused)</div>
  <div class="item">Log new Episodes in batches (e.g. <b>Added 20 new Episodes</b> instead of 20x <b>Added new Episode ..</b>)</div>
  <div class="item">List some builtin variable overrides in extra dropdowns</div>
  <div class="item">Report filesize statistics in *ibytes not *ibibits</div>
  <div class="item">Automatically open new Font accordion after creation</div>
  <div class="item">Allow and handle multi-season season title ranges - e.g. <b>s1e2-s2e3</b></div>
  <div class="item">Add ability to force refresh the Blueprint database by right clicking the <b>Browse Blueprints</b> button on the Add Series page</div>
  <div class="item">Display the Source Image data as a table by default</div>
  <div class="item">Log Title Card loading as it happens, not after the fact</div>
  <div class="item">Do not use background tasks for manual Series Episode data refreshing</div>
  <div class="item">Add input for TCM URL to the Tautulli setup modal (for users whose Web UI is not the same URL as their TCM backend)</div>
  <div class="item">Log when there are no title translations available from TMDB</div>
  <div class="item">Create (and make available) various "metric" data, like:
    <div class="list">
      <div class="item"><b>season_episode_count</b> as the number of Episodes in a season; <b>season_episode_max</b> as the maximum episode number in a season; <b>season_absolute_max</b> as the maximum absolute episode number in a season; <b>series_episode_count</b> as the total number of Episodes in a Series; <b>series_episode_max</b> as the maximum episode number in a Series; and <b>series_absolute_max</b> as the maximum absolute episode number in a Series</div>
    </div>
  </div>
  <div class="item">Use <b>Debug</b> log level by default when loading the logs page</div>
  <div class="item">Expire all login tokens after 7 days (was 2)</div>
  <div class="item">Add new <b>Episode Identifier</b> (e.g. <b>S01E03</b>) Template filter to easily allow filtering by specific Episode(s)</div>
  <div class="item">Change logging context IDs to 6 characters (from 12)</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Display less pagination menus on the files tab to avoid overflow for Series with more than 100 tabs</div>
  <div class="item">Correctly identify (and do not display) blank change logs</div>
  <div class="item">Query Episode watched statuses<i>before</i>Source Image selection (in case some Template filter or styling changes the effective source or style)</div>
  <div class="item">Handle bad Episode data from Jellyfin (caused by bad Series ID)</div>
  <div class="item">Reduce login animation speed by 300ms</div>
  <div class="item">Do not require Source Image to exist for Roman Numeral card creation</div>
  <div class="item">Correctly calculate the bounding box boundaries when using a custom interword spacing with the Landscape card</div>
  <div class="item">Fix kanji vertical spacing for multi-line titles with custom Fonts in the Anime card</div>
  <div class="item">Handle more types of generic uncaught exceptions from the TMDb API </div>
  <div class="item">Refresh Card and File data after Episode deletion</div>
  <div class="item">Only wait 5 seconds to delete intermediate Blueprint files (down from 15)</div>
  <div class="item">Fix <b>pyyaml</b> package version 6.0.1 to fix cython bug present in 6.0.0</div>
  <div class="item">Unescape <b>\(</b> and <b>\)</b> in ImageMagick commands on Windows</div>
  <div class="item">Remove placeholder elements if Series search fails (to avoid appearance of permanent loading)</div>
  <div class="item">Handle search results without an assigned watch status in Emby and Jellyfin </div>
  <div class="item">Do not stack Font replacement and season title range input fields on mobile</div>
  <div class="item">Add minimum 5 second delay between adding Series on the front-end</div>
  <div class="item">Do not add Source Image HTML elements for images which do not exist</div>
  <div class="item">Correct the Blueprints repository link on the "no Blueprints" popup</div>
  <div class="item">Add <b>charset-normalizer</b> requirement to Pipfile (fixes some Windows installs)</div>
  <div class="item">Add pre-pool pinging to DB connection creation, and change connection timeout to 30 seconds -<i>should</i>help with multi-threaded DB reliability</div>
  <div class="item">Add poster filesize to the Series poster URL to prevent bad browser caches</div>
  <div class="item">Fix IMDb ID parsing from Emby</div>
  <div class="item">Do not buffer Python logging (fixes batched logging on some machines)</div>
  <div class="item">Commit to the Database after each Sync to avoid potential duplication of Series</div>
  <div class="item">Handle scheduled Tasks whose "next run" is in the future during boot</div>
  <div class="item">Correct the Episode extras modal when an Episode has >1 extra</div>
  <div class="item">Fix the Template preview generation for when an explicit style is indicated</div>
  <div class="item">Display extras from local Card types in Extra dropdown fields</div>
</div>
<h2>Title Card Changes</h2>
<div class="ui ordered list">
  <div class="item">Generalize mask overlays, now "mask" images can be added to (almost) every single type of Card - for example:
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/10beb3ab-378c-45c2-860b-636ba3041a37">
    </div>
  </div>
  <div class="item">Calligraphy
    <div class="list">
      <div class="item">Add a shadow color extra</div>
      <div class="item">Reduce the maximum logo height to 725px (From 750px)</div>
    </div>
  </div>
  <div class="item">Cutout
    <div class="list">
      <div class="item">Allow transparent overlay colors in Cutout card</div>
    </div>
  </div>
  <div class="item">Divider
    <div class="list">
      <div class="item">Add a Text Gravity extra</div>
    </div>
  </div>
  <div class="item">Landscape
    <div class="list">
      <div class="item">Change the shadow opacity to 85% (was 80%)</div>
      <div class="item">Add a shadow color extra</div>
      <div class="item">Enable the bounding box (and use box darkening) by default</div>
    </div>
  </div>
  <div class="item">Overline
    <div class="list">
      <div class="item">Change the default line thickness to 9px (from 7)</div>
      <div class="item">Adjust default interline spacing for title text when the line position is bottom</div>
    </div>
  </div>
  <div class="item">Standard
    <div class="list">
      <div class="item">Add episode text font size extra</div>
    </div>
  </div>
  <div class="item">Star Wars
    <div class="list">
      <div class="item">Add support for custom Font vertical shifts</div>
    </div>
  </div>
  <div class="item">Tinted Frame
    <div class="list">
      <div class="item">Position the logo below the frame, index, and title text in the Tinted Frame card</div>
      <div class="item">Add a drop shadow to the logo when specified as the middle element</div>
      <div class="item">Add a shadow color extra</div>
      <div class="item">Change the shadow opacity to 85% (was 80%)</div>
      <div class="item">Shift top index text down 3px</div>
      <div class="item">Utilize even title line splitting</div>
      <div class="item">Change the title splitting length to 42 characters</div>
    </div>
  </div>
  <div class="item">White Border
    <div class="list">
      <div class="item">Add episode text font size extra</div>
      <div class="item">Add border color extra</div>
    </div>
  </div>
</div>
<h2>Documentation Changes</h2>
<div class="ui ordered list">
  <div class="item">Move setup instructions to the <a href="https://titlecardmaker.com/getting_started/" target="_blank">Getting Started</a> landing page</div>
  <div class="item">Add scrolling image marquee to the home page with example screenshots from the UI</div>
  <div class="item">Stylize references to in-UI buttons </div>
  <div class="item">Create <a href="https://titlecardmaker.com/user_guide/templates/" target="_blank">Templates</a> User Guide page</div>
  <div class="item">No longer publish docs to RTD - now all docs are on <a href="titlecardmaker.com" target="_blank">titlecardmaker.com</a></div>
  <div class="item">Create <a href="https://titlecardmaker.com/user_guide/logs/" target="_blank">Logs</a> User Guide page</div>
  <div class="item">Replace doc <b>.png</b> assets with <b>.webp</b> for smaller filesize and faster loading</div>
  <div class="item">Rewrite Connection docs to reflect multi-connection support</div>
  <div class="item">Create <a href="https://titlecardmaker.com/user_guide/scheduler/#advanced-mode" target="_blank">Scheduler</a> User Guide page</div>
  <div class="item">Revise Getting Started instructions to explicitly mention the <b>TitleCardMaker-WebUI</b> install directory</div>
  <div class="item">Add note about Docker "invalid reference format" errors and potential fixes</div>
</div>
<h2>API Changes</h2>
<div class="ui ordered list">
  <div class="item">Change default page size for all paginated API endpoints to 100 (from 250)</div>
  <div class="item">Add API endpoints to perform batch operations like Series deletion, Title Card deletion, un/monitoring, Card loading, etc.</div>
  <div class="item">Standardize API endpoints in the <b>/series</b> router to match other routers</div>
  <div class="item">Create API endpoint to delete an Episode's Source Image file(s)</div>
  <div class="item">Always force reload Title Cards in trigger API endpoints</div>
  <div class="item">Only refresh card types in Episode PATCH endpoint if change occurred</div>
  <div class="item">Do not perform unmonitored Tasks in the process Series endpoint</div>
  <div class="item">Add API endpoint to delete a Series within TCM via the Sonarr delete-series API webhook
    <div class="list">
      <div class="item">The webhook should be configured to <b>POST</b> to <b>{TCM URL}/api/series/sonarr/delete</b></div>
    </div>
  </div>
  <div class="item">Do not always re-query Episode watched statuses in Card creation endpoints</div>
</div>`
  },
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
  },
  {
    version: 'v2.0-alpha.5.0',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Completely revamp the process new Series are added to TCM
    <div class="list">
      <div class="item">Now the <b>+ New Series</b> button takes you to a separate page where you can interactively search any enabled interface (Emby/Jellyfin/Plex/Sonarr/TMDb) for the Series - a slightly outdated example:
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/63f18412-0ef5-4f4c-9a71-9764802f2b81">
    </div>
  </div>
      <div class="item">When a Series is selected, you can easily browse any available Blueprints to add the Series and Blueprint immediately</div>
      <div class="item">Series can also be quickly added to TCM without opening the menu by clicking the Quick-Add button, which uses the last-selected Libraries and Templates</div>
    </div>
  </div>
  <div class="item">Browse all available Blueprints within the UI
    <div class="list">
      <div class="item">Below the aforementioned new series adding, any defined Blueprints can be browsed - for example:
    <div class="list">
      <img width="50%" src="https://cdn.discordapp.com/attachments/1112497724080795649/1134612605525295144/image.png">
    </div>
  </div>
      <div class="item">These Blueprints can then be imported _directly_, without explicitly searching for the Series - this will import the Series if it does not exist, as well as the Blueprint</div>
      <div class="item">Any Blueprints you aren't interested in (or have already imported) can be permanently hidden from this part of the UI, but will still appear when searching for that Series explicitly.</div>
    </div>
  </div>
  <div class="item">Allow toggling of an "Advanced" Scheduler mode - to allow Tasks to be scheduled via Cron expressions, not just intervals</div>
  <div class="item">View and browse Series logos within the UI - at the bottom of the Files tab on the Series page the current logo can be viewed; and all available logos on TMDb can be browsed and downloaded</div>
  <div class="item">Create White Border title card</div>
  <div class="item">Implement optional authorization to require a valid username/password to access TCM (and the API) - example of the login screen:
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/a10f610a-73b3-4905-9c6d-a55ca91a96f4">
    </div>
  </div>
</div>
<h2>Major Fixes </h2>
<div class="ui ordered list">
  <div class="item">Correctly read Version file during initialization</div>
  <div class="item">Correct the automated validation tests run on all Blueprint submissions</div>
  <div class="item">Fix logos for the Fade title card not being automatically passed into Cards</div>
  <div class="item">Fix loading of global Preferences when using remote card types forcing a settings reset on each boot</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Only update Preference attributes if changed</div>
  <div class="item">Separate all CSS/HTML/JS files</div>
  <div class="item">Order Fonts and Templates by their name</div>
  <div class="item">Combine un/watched style fields to be more compact</div>
  <div class="item">Use lazy loading on Blueprint images in Series page </div>
  <div class="item">Cache remote card types for 6 hours (from 30 minutes)</div>
  <div class="item">Add tooltip to the theme toggle button</div>
  <div class="item">Add <b>box_color</b> extra to Landscape card</div>
  <div class="item">Display total Card progress / percentage beneath the Series poster on the home page</div>
  <div class="item">Only query Emby/Jellyfin usernames on Connections page load if enabled</div>
  <div class="item">Add various keyboard navigations:
    <div class="list">
      <div class="item">Allow tabbing between Series on the home page, and hitting Enter to open page</div>
      <div class="item">Hitting <b>f</b> or <b>s</b> anywhere to start typing in the Series search box</div>
      <div class="item">Hit Shift + <b>H</b> anywhere to return to the home page</div>
    </div>
  </div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Raise a 404 Exception if a non-existent Font file is deleted via the API</div>
  <div class="item">Require unique Template specifications in Series, Fonts, Syncs, and Episodes</div>
  <div class="item">Use contextual logger in Source image replacement endpoint</div>
  <div class="item">Make some UI formatting improvements for mobile:
    <div class="list">
      <div class="item">Do not stack the Episode data table</div>
      <div class="item">Vertically center align header buttons</div>
      <div class="item">Hide support button</div>
      <div class="item">Increase sidebar vertical padding</div>
      <div class="item">Stack file cards</div>
      <div class="item">Center log table</div>
      <div class="item">Stack Template columns </div>
    </div>
  </div>
  <div class="item">Fix race condition triggered by deleting Series and Cards at the same time</div>
  <div class="item">Only commit changes to global connections<i>after</i>refreshing interface</div>
  <div class="item">Correct method calls when a Series cannot be found in Emby or Jellyfin</div>
  <div class="item">Fix contextual logging of uncaught TMDb exceptions</div>
</div>`
  },
  {
    version: 'v2.0-alpha.4.1',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Rework global Preferences to be a bit less error-prone (purely a behind the scenes change)</div>
  <div class="item">Only read the most recent log file when querying for new messages within the UI</div>
  <div class="item">Add option to Sonarr Connection details to only grab Episode data for Episodes that are downloaded (this is a global setting)</div>
  <div class="item">No longer skip loading remaining Cards into a Series when >3 Card uploads fail</div>
  <div class="item">Completely overhaul Blueprint submission
    <div class="list">
      <div class="item">Blueprints are now submitted by just filling out an Issue form on the GitHub, and then automated workflows parse and validate your submission to create and merge the actual Blueprint</div>
    </div>
  </div>
</div>
<h2>Major Fixes </h2>
<div class="ui ordered list">
  <div class="item">Remove default <b>--workers 4</b> server argument from the Dockerfile</div>
  <div class="item">Require <b>plexapi</b> 4.14.0 to fix PMM integration failing on some servers
    <div class="list">
      <div class="item">To fix the PMM integration if you are<i>not</i>using Docker, you might need to run <b>pipenv clean</b> then a clean<b>pipenv install</b></div>
    </div>
  </div>
  <div class="item">Prevent TCM from grabbing source images of previously loaded Title Cards</div>
  <div class="item">Require Series match when creating Cards via Tautulli/rating key - it was possible to remake the Card for the wrong Series if the two had the exact same Episode index + title (i.e.<i>Pilot</i>for S01E01)</div>
  <div class="item">Fix Emby/Jellyfin Syncs</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Add improved documentation to pretty much all of the code</div>
  <div class="item">Use <b>raise .. from ..</b> syntax where applicable</div>
  <div class="item">Add <b>maxsplit=1</b> arguments to improve string splitting speed where applicable</div>
  <div class="item">Move <b>require_kanji</b> logic into Anime card model </div>
  <div class="item">Paginate <b>/api/templates/all</b> endpoint return</div>
  <div class="item">Use HTML tooltips instead of titles on the Connections page</div>
  <div class="item">Standardize all MediaServer and EpisodeDataSource subclasses to use the same method argument structure</div>
  <div class="item">Use contextual logger in decorated functions to log failed GET requests</div>
  <div class="item">Use <b>sys.exit</b> instead of built-in <b>exit</b> function</div>
  <div class="item">Add request method to method start log messages (e.g. <b>GET</b>, <b>POST</b>, etc.)</div>
  <div class="item">Change Emby and Jellyfin to query for Series ID's at runtime (to handle database ID shuffling, which seems to happen?)</div>
  <div class="item">Change the default global filename format to <b>{series_full_name} - S{season_number:02}E{episode_number:02}</b></div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Add explicit 10-30 second timeouts to all remote content queries to prevent the program from possibly locking</div>
  <div class="item">Use contextual Logger for:
    <div class="list">
      <div class="item">Refreshing remote card types when importing Preference YAML</div>
      <div class="item">Season title range evaluation</div>
    </div>
  </div>
  <div class="item">Raise 404 if requesting Statistics for a Series, or deleting a Template that DNE via the API</div>
  <div class="item">Use updated image size methods in AspectRatioFixer and StandardSummary creation via fixer</div>
  <div class="item">No longer use deprecated <b>ABC.abstractproperty</b> decorator</div>
  <div class="item">Use correct <b><b>slots</b></b> iterable in <b>SeasonTitleRanges</b> class</div>
  <div class="item">Correct<i>Process Series</i>button tooltip to not reference Card loading</div>
  <div class="item">Explicitly pass connection URLs to <b><b>init</b></b> methods</div>
  <div class="item">Correct language in the delete Sync toast </div>
</div>`
  }, {
    version: 'v2.0-alpha.4.0',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Add scheduled task to perform automatic database backups - default interval is 1 day, and backups are kept for 4 weeks</div>
  <div class="item">Allow import and exporting of Blueprints
    <div class="list">
      <div class="item">A Blueprint is a customization that applies to a specific Series</div>
      <div class="item">A Blueprint can include any number of Templates, Fonts, Series customizations,<i>and</i>Episode customizations </div>
      <div class="item">Blueprints are hosted on the new <a href="https://github.com/CollinHeist/TitleCardMaker-Blueprints/" target="_blank">Blueprints</a> repository, which I've started adding some of my own Blueprints to, both as examples and for use</div>
      <div class="item">Blueprints can be imported into a Series via the new <b>Blueprints</b> tab on the Series page</div>
      <div class="item">If there are Blueprints available, an example of each will be displayed in the UI, along with the creator, a brief description, and a list of what is included in the Blueprint
    <div class="list">
      <img width="50%" src="https://github.com/CollinHeist/TitleCardMaker/assets/17693271/1a42589e-bf54-48d2-bddf-823cf55097bd">
    </div>
  </div>
      <div class="item">A Blueprint can be easily exported by clicking the<i>Export Blueprint</i>Button, which will download a .zip file of the Blueprint (as JSON) that you can edit, any associated Font files, and a preview image for the Series.</div>
    </div>
  </div>
  <div class="item">Refresh Episode data for each Series immediately after being Synced</div>
  <div class="item">Add button (and endpoint) to process entire Series at once, including proper sequencing of Source Image downloading and Card creation</div>
  <div class="item">Use explicit<i>Refresh Preview</i>button in Named Font card preview instead of auto-change detection</div>
  <div class="item">Reflect Font title case specification in Named Font card preview</div>
  <div class="item">Allow Syncs to be edited within the UI</div>
</div>
<h2>Major Fixes </h2>
<div class="ui ordered list">
  <div class="item">Correctly commit changes when updating multiple Episodes via endpoint if last Episode object is unchanged</div>
  <div class="item">Filter out any messages from the "future" when displaying them in the UI (typically caused by misaligned timezone)</div>
  <div class="item">Use the correct Series<i>unwatched</i>style in Episode source file resolution (was using<i>watched</i>style)</div>
  <div class="item">Allow deletion of any individual season titles (not just the last title) from the UI</div>
  <div class="item">Fix effective Template determination for _Episodes_</div>
  <div class="item">Fix homepage sorting by Series name for Series that have numeric names (e.g. <b>1923</b>)</div>
  <div class="item">Allow specification of manually split Titles by disabling Auto-Split title for that Episode and then putting <b>\n</b> in the title where you want to force a split</div>
  <div class="item">Always commit changes to the global Preferences<i>even if</i>the interface is disabled</div>
  <div class="item">Do not error on bad Series database ID's</div>
  <div class="item">Properly display the names of uploaded Named Font files within the UI</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Add <b>interword_spacing</b> extra to Frame and Olivier card types</div>
  <div class="item">Use contextual logger for:
    <div class="list">
      <div class="item">Failed image download logging</div>
      <div class="item">Template creation endpoint</div>
      <div class="item">Interface refreshing </div>
      <div class="item">Remote Card Type evaluation</div>
      <div class="item">Changes to the global Preferences</div>
      <div class="item">ImageMagick prefix determination</div>
    </div>
  </div>
  <div class="item">Enforce a minimum task interval of 10 minutes (to prevent freezing up the UI if scheduled too frequently)</div>
  <div class="item">Skip Jellyfin Series ID assignment if all ID's are present</div>
  <div class="item">Use updated versions of most packages in Pipfile
    <div class="list">
      <div class="item">Require <b>1.x</b> for Pydantic as I haven't validated v2</div>
      <div class="item">Move <b>mkdocs</b> to a dev package</div>
    </div>
  </div>
  <div class="item">Remove "URL" form validation from Connections page to allow URL's without a TLD</div>
  <div class="item">Use hard drive icon instead of sever icon for "Load Cards into ..." Buttons to not use the same design for logs and </div>
  <div class="item">Do not return <b>CardActions</b> object from Card creation or import endpoints</div>
  <div class="item">Add font replacement for <b>é</b> and <b>É</b> to Comic Book card type</div>
  <div class="item">Add "progress bar" to show percentage of Title Cards created below Series poster</div>
  <div class="item">Do not show Sync sections for disabled interfaces</div>
  <div class="item">Change maximum ImageMagick thread count to 12</div>
  <div class="item">Use <b>magick</b> IM prefix _by default_</div>
  <div class="item">Disable various buttons on the Series page after clicking to prevent making duplicate requests</div>
  <div class="item">Use orange icons on<i>Force Reload ..</i>buttons</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Improve handling of objects with no Template IDs on YAML imports</div>
  <div class="item">Remove redundant text from error message when there is missing data from an Episode Text Format string</div>
  <div class="item">Handle SQL <b>OperationalError</b> in TranslateSeries task </div>
  <div class="item">Disable caching in Sonarr to catch changes in sequential API requests (e.g. Syncing, adding tag, re-Syncing)</div>
</div>`
  },
  {
    version: 'v2.0-alpha.3.0',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Improve Sonarr Interface initialization times by no longer querying all Series ID's upon init, instead search for the Series via the <b>/lookup</b> API endpoint when querying for a Series</div>
  <div class="item">Completely overhaul all logging and log messages
    <div class="list">
      <div class="item">Every API request and top-level function (e.g. scheduled tasks) generate a unique Context ID like <b>aafa3e9eedaf</b> that is logged in all messages corresponding to that function</div>
      <div class="item">Create <b>/logs</b> API router to query log files</div>
      <div class="item">Display the status of background tasks in small toasts that in the bottom right corner. These differ from info toasts that directly respond to an action taken (like a button press) which appear in the top right</div>
    </div>
  </div>
  <div class="item">Allow logs to be viewed within the UI
    <div class="list">
      <div class="item">Accessible from the green server button / icon on the page header</div>
      <div class="item">Logs can be filtered within the UI by log level, context ID(s), message substring, start and end time</div>
      <div class="item">A context ID or start/end time can be clicked on to add as a filter</div>
    </div>
  </div>
  <div class="item">Use UMASK of <b>002</b> in Dockerfile</div>
  <div class="item">Handle overriding source files with extras (including format strings) - specify as <b>source_file</b></div>
</div>
<h2>Major Fixes </h2>
<div class="ui ordered list">
  <div class="item">Allow Template booleans to be cleared (False -> True) from within the UI</div>
  <div class="item">Handle unspecified arguments in connections YAML importing</div>
  <div class="item">Handle invalid page landings by redirecting to the homepage</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Sort Series on the server rather than client</div>
  <div class="item">Paginate Episode data table (and corresponding API endpoint) on Series page</div>
  <div class="item">Only show home page Series navigation menu if there at least two pages</div>
  <div class="item">Specify four worker processes in Dockerfile (will eventually make this a variable)</div>
  <div class="item">Remove logging of Preference file changes</div>
  <div class="item">Remove log message for existing translations</div>
  <div class="item">Remove log message for failure to meet Template Filter criteria</div>
  <div class="item">Remove log messages for using cached remote card contents</div>
  <div class="item">Parse Episode airdates when initializing EpisodeInfo objects from Plex</div>
  <div class="item">Do not log missing Source images in the scheduled task</div>
  <div class="item">Use <b>runuser</b> instead of <b>gosu</b> in Dockerfile</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Remove double <b>magick</b> ImageMagick prefix from TintedFrame card </div>
  <div class="item">Add slight shadow to separate page header from dark themed page contenxt</div>
  <div class="item">Remove blank toast from Title Card creation response handler</div>
  <div class="item">Include fake Series name and Episode indices in Card preview generation</div>
  <div class="item">Log the correct number of identified entries from a Plex Rating Key</div>
  <div class="item">Remove unequal margin from page header button icons</div>
  <div class="item">Retry PersistentDatabase transactions up to 5 times to reduce DB corruptions caused by multi-process access</div>
  <div class="item">Remove some Debug messages erroneously labeled as critical</div>
  <div class="item">Handle uncaught exceptions during interface dependency refreshing</div>
</div>`
  }, {
    version: 'v2.0-alpha.2.2',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Paginate Series homepage for faster loads for very large servers</div>
  <div class="item">Fix selection of uppercase title case for custom Fonts via UI</div>
  <div class="item">Fix Card importing force reload for Card importer (checked/unchecked were reversed)</div>
</div>
<h2>Major Fixes </h2>
<div class="ui ordered list">
  <div class="item">Pass Episode cardinal/ordinal numbers to all Card types (fixes Olivier / other Card Types)</div>
  <div class="item">Fix Tautulli integration API endpoints</div>
  <div class="item">Relocate preferences JSON file to be persistent between Docker instances (now at <b>/config/source/prefs.json</b>)</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Allow Plex rating key API endpoint to work with lists of keys (not just single)</div>
  <div class="item">Add lazy loading to Series posters on home page</div>
  <div class="item">Show list of affected Series when deleting a Template via UI</div>
  <div class="item">Show info toast when starting to source image downloading is initiated via UI</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Increase bottom margin between statistics and series cards on home page</div>
  <div class="item">Correctly initialize default card extension for Card importer based on global card extension</div>
  <div class="item">Fix IMDb Series ID for Series with unassigned IMDb ID's (label was showing TVDb)</div>
  <div class="item">Utilize <b>magick</b> IM 7.0 Command Prefix in Tinted Frame card (this is kind of a test)</div>
  <div class="item">Add 10 minute misfire grace period to Scheduler -<i>should</i>allow tasks to finish if delayed</div>
  <div class="item">Fix default <b>box_adjustments</b> in Landscape and Tinted Glass cards</div>
</div>`
  }, {
    version: 'v2.0-alpha.2.1',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Add internal task to query for and set missing Series ID's every 24 hours by default</div>
</div>
<h2>Major Fixes </h2>
<div class="ui ordered list">
  <div class="item">Fix error where logos were being downloaded from TMDb as posters</div>
  <div class="item">Correct default box adjustments in Landscape and Tinted Glass card Pydantic models</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Remove blank Sync name from Sync delete toast</div>
  <div class="item">Add green checkmark next to selected Series in Importer dropdown to improve legibiliy</div>
  <div class="item">Sleep for 30 seconds on SQL OperationalErrors in Sync and Episode Data Refresh tasks</div>
  <div class="item">Use full width textarea elements on mobile on Importer page</div>
  <div class="item">Center align the Scheduler table on mobile</div>
  <div class="item">Make Series page input elements full width</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Correct URI path to blank image in Font preview </div>
  <div class="item">Minor CSS / layout improvements for the home page on mobile</div>
  <div class="item">Fix Sonarr library field auto population</div>
  <div class="item">Fix logo positioning on mobile (was offcenter)</div>
</div>`
  },
  {
    version: 'v2.0-alpha.2.0',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Add scheduled Task to download any missing Series posters</div>
  <div class="item">Download Series posters from associated Media Server (e.g. Plex, Emby, Jellyfin)<i>before</i>trying TMDb</div>
  <div class="item">Add functionality for TCM to "guess" and auto-fill the Libraries setting based on your Sonarr root folders</div>
  <div class="item">Simplify HTML/CSS on all pages so that the header and sidebar are non-sticky elements (reducing weird scrolling oddities)</div>
  <div class="item">Fix background "image" gradient not filling the page on some pages in Chrome</div>
  <div class="item">Add navigation buttons to Series pages to quickly move between Series (alphabetically)</div>
  <div class="item">Add Comic Book title card (https://github.com/CollinHeist/TitleCardMaker/issues/343)</div>
  <div class="item">Vastly improve Emby Syncs:
    <div class="list">
      <div class="item">Make them much faster by not making individual API requests per-year (weird API bug..)</div>
      <div class="item">Apply exclusion tags</div>
      <div class="item">Directly parse Series database ID's while Syncing</div>
    </div>
  </div>
  <div class="item">Handle changing Jellyfin Series ID's (maybe)</div>
</div>
<h2>Major Fixes </h2>
<div class="ui ordered list">
  <div class="item">Properly merge Episode translations into extras</div>
  <div class="item">Fix Card preview generation for Templates and Fonts</div>
  <div class="item">Handle any type of Tautulli API Key (pre API v3.6, API keys were hexstrings, but they are now randomly generated Base64 strings)</div>
  <div class="item">Allow changing the Font title case from the UI</div>
</div>
<h2>Minor Changes</h2>
<div class="ui ordered list">
  <div class="item">Change images used in Card preview generation</div>
  <div class="item">Skip and do not warn if a disabled interface is part of the global image source priority in source selection</div>
  <div class="item">Download Series poster, assign ID's, and refresh Episode data<i>before</i>returning from add new Series API endpoint</div>
  <div class="item">Update "get all Series" API endpoint to optionally order return by name, year, or ID</div>
  <div class="item">Add additional type annotations</div>
</div>
<h2>Minor Fixes</h2>
<div class="ui ordered list">
  <div class="item">Catch SQL OperationalError exceptions in Episode data refresh scheduled task</div>
  <div class="item">Handle <b>transparent</b> in Color Title Card fields (this is a bug in the Pydantic modules that I've submitted a PR/fix for, but will only be released in Pydantic v2.0)</div>
  <div class="item">Fix CSS resulting in a small white rectangle on some browsers for the card type preview on the Settings page</div>
  <div class="item">Handle Episodes without season/episode numbers in Emby and Jellyfin</div>
</div>`
  },{
    version: 'v2.0-alpha.1.0',
    changelog: `<h2>Initial Release</h2>`
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

  // This version hasn't been displayed
  const last = versionToNumber(lastVersion);

  let changes = '<div class="ui styled fluid uninvertible accordion">';
  for (let {version, changelog} of changeLog) {
    if (!forceDisplay && v_gt_v(last, versionToNumber(version))) { break; }
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
  if (changes && changes !== '<div class="ui styled fluid uninvertible accordion"></div>') {
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
