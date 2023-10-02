const changeLog = [
  {
    version: 'v2.0-alpha.6.0',
    changelog: `
<h2>Major Changes</h2>
<div class="ui ordered list">
  <div class="item">Add API endpoint to trigger Card creation via Sonarr webhook - this is practically identical to the Tautulli trigger (but not for watched-status changes) but works for all Media Servers - setup docs are <a href="https://titlecardmaker.readthedocs.io/en/latest/getting_started/connections/sonarr/#webhook-integration" target="_blank">here</a></div>
  <div class="item">Create new Calligraphy card type
    <div class="list">
      <img class="ui large image" src="https://user-images.githubusercontent.com/17693271/271875869-2473a1bf-bfb6-4a98-a643-988a43100189.jpg">
    </div>  
  </div>
  <div class="item">Create new Marvel card type
    <div class="list">
      <img class="ui large image" src="https://user-images.githubusercontent.com/17693271/271876124-8c596987-1a82-4a9d-a937-406002aab136.jpg">
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
</div>
<h2>Major Fixes</h2>
<div class="ui ordered list">
  <div class="item">Correctly display and edit extras in Episode modals</div>
  <div class="item">Use bottom-heavy titling in Overline card</div>
  <div class="item">Make Blueprint search case-agnostic - e.g. <b>ONE PIECE (2023)</b> will match <b>One Piece (2023)</b></div>
  <div class="item">Correct YAML importing to properly sequence imports of Fonts, then Templates, then Series</div>
  <div class="item">Properly apply custom Fonts to Series when importing YAML</div>
  <div class="item">Correctly convert season folder format variables when importing YAML</div>
  <div class="item">Hide home page statistics on mobile to improve formatting</div>
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
  <div class="item">Handle explicit newlines (<b>\n</b>) in titles for preview card creation</div>
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

  // This version hasn't been displayed
  const last = versionToNumber(lastVersion);

  let changes = '';
  for (let {version, changelog} of changeLog) {
    // Subsequent versions were previously notified; changelog is complete
    if (!forceDisplay && v_gt_v(last, versionToNumber(version))) { break; }
    // Version not notified, add to changelog
    changes += `<h1 class="ui top attached inverted blue header">${version}</h1><div class="ui attached segment">${changelog}</div>`;
  }

  // Changes to display, show modal
  if (changes) {
    $.modal({
      title: 'Changelog',
      class: 'uninvertible',
      closeIcon: true,
      content: changes,
    }).modal('show');
  }

  // Changelog displayed, update local storage
  window.localStorage.setItem('version', currentVersion);
}
