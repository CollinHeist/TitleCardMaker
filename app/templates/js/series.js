/*
 * Submit an API request to get updated Series statistics. If successful,
 * then the card stats text and progress bar are updated.
 */
let getStatisticsId;
function getStatistics() {
  $.ajax({
    type: 'GET',
    url: '/api/statistics/series/{{series.id}}',
    success: statistics => {
      // Update card count text
      const [cardStat, episodeStat] = statistics;
      $('#card-count')[0].innerHTML = `<i class="image outline icon"></i><span class="ui text">${cardStat.value} Cards / ${episodeStat.value} Episodes</span>`;
      
      // Update progress bar
      let cardVal = Math.min(cardStat.value, episodeStat.value);
      $('#card-progress').progress({
        total: episodeStat.value,
        value: `${cardVal},${episodeStat.value-cardVal}`,
        duration: 1500,
      });
    }, error: response => {
      if (response.status === 401) {
        clearInterval(getStatisticsId);
      }
    },
  });
}

async function getLibraries() {
  if (document.getElementById('emby-library') != null) {
    const embyLibraries = await fetch('/api/available/libraries/emby').then(resp => resp.json());
    $('#emby-library').dropdown({
      values: embyLibraries.map(name => {
        return {name: name, value: name, selected: name === '{{series.emby_library_name}}'};
      })
    });
  }

  if (document.getElementById('jellyfin-library') != null) {
    const jellyfinLibraries = await fetch('/api/available/libraries/jellyfin').then(resp => resp.json());
    $('#jellyfin-library').dropdown({
      values: jellyfinLibraries.map(name => {
        return {name: name, value: name, selected: name === '{{series.jellyfin_library_name}}'};
      })
    });
  }

  if (document.getElementById('plex-library') != null) {
    const plexLibraries = await fetch('/api/available/libraries/plex').then(resp => resp.json());
    $('#plex-library').dropdown({
      values: plexLibraries.map(name => {
        return {name: name, value: name, selected: name === '{{series.plex_library_name}}'};
      })
    });
  }
}

let editedEpisodeIds = [];
function getUpdateEpisodeObject(episodeId) {
  // Get all inputs for this episode
  const episodeInputs = $(`#episode-id${episodeId} input`);
  // Construct updateEpisode object
  let updateEpisode = {},
      template_ids = [];
  Object.entries(episodeInputs).forEach(([index, input]) => {
    if (input.name !== undefined) {
      // Handle Templates
      if (input.name === 'template_ids' && input.value !== '') {
        template_ids = input.value.split(','); 
      }
      // Handle percentage values
      else if (input.value != '' && ['font_size', 'font_kerning', 'font_stroke_width'].includes(input.name)) {
        updateEpisode[input.name] = input.value/100.0;
      } else {
        updateEpisode[input.name] = input.value;
      }
    }
  });
  // Append boolean state icons to object as none/true/false
  $(`#episode-id${episodeId} td[data-type="boolean"]`).each((index, value) => {
    const iconClassList = value.firstChild.classList;
    if (iconClassList.contains('question')) {
      updateEpisode[value.dataset['column']] = null;
    } else if (iconClassList.contains('check')) {
      updateEpisode[value.dataset['column']] = true;
    } else {
      updateEpisode[value.dataset['column']] = false;
    }
  });

  return {...updateEpisode, template_ids: template_ids};
}

/*
 * Submit an API request to save the modified Episode configuration
 * for the given Episode.
 * 
 * @param {int} episodeId - ID of the Episode whose config is being changed.
 */
function saveEpisodeConfig(episodeId) {
  const updateEpisodeObject = getUpdateEpisodeObject(episodeId);
  $.ajax({
    type: 'PATCH',
    url: `/api/episodes/${episodeId}`,
    contentType: 'application/json',
    data: JSON.stringify(updateEpisodeObject),
    success: () => {
      $.toast({ class: 'blue info', title: 'Updated Episode'}),
      // Remove this ID from the array of edited Episodes
      editedEpisodeIds = editedEpisodeIds.filter(id => id !== episodeId);
    }, error: response => showErrorToast({title: 'Error Updating Episode', response}),
  });
}

/*
 * Submit an API request to batch save all modified Episode configurations. This
 * uses the Episode ID's in the global `editedEpisodeIds` array.
 */

function saveAllEpisodes() {
  // Get update objects
  const updateEpisodeObjects = editedEpisodeIds.map(episodeId => {
    return {
      episode_id: episodeId,
      update_episode: getUpdateEpisodeObject(episodeId),
    };
  });

  // Submit API request
  $.ajax({
    type: 'PATCH',
    url: '/api/episodes/batch',
    contentType: 'application/json',
    data: JSON.stringify(updateEpisodeObjects),
    success: () => {
      // Updated successfully, show toast and reset list
      showInfoToast(`Updated ${updateEpisodeObjects.length} Episodes`);
      editedEpisodeIds = [];
    }, error: response => showErrorToast({title: 'Error Updating Episodes', response}),
  });
}

// Initialize series specific dropdowns
async function initalizeSeriesConfig() {
  // Episode data sources
  const sources = await fetch('/api/available/episode-data-sources').then(resp => resp.json());
  const placeholder = '{{series.episode_data_source}}' === 'None' ? 'Global Default' : '{{series.episode_data_source}}';
  $('#episode-data-source').dropdown({
    placeholder: placeholder,
    values: sources.map(({name, selected}) => {
      return {name: name, value: name, selected: name == '{{series.episode_data_source}}'};
    })
  });
  // Special syncing
  initializeNullableBoolean({
    dropdownElement: $('#series-config-form .dropdown[data-value="sync_specials"]'),
    value: '{{series.sync_specials}}',
  });
  // Skip localized images
  initializeNullableBoolean({
    dropdownElement: $('#series-config-form .dropdown[data-value="skip_localized_images"]'),
    value: '{{series.skip_localized_images}}',
  });
  // Template
  const templates = await fetch('/api/templates/all').then(resp => resp.json());
  $('#card-config-form .dropdown[data-value="template_ids"]').dropdown({
    values: getActiveTemplates({{series.template_ids}}, templates),
  });
  // Card types
  loadCardTypes({
    element: '#card-config-form .dropdown[data-value="card-types"]',
    isSelected: (identifier) => identifier === '{{series.card_type}}',
    showExcluded: false,
    // Dropdown args
    dropdownArgs: {
      placeholder: 'Default',
    }
  });
  // Styles
  const allStyles = await fetch('/api/available/styles').then(resp => resp.json());
  $('#card-config-form .dropdown[data-value="watched-style"]').dropdown({
    values: [
      {name: 'Art Variations', type: 'header'},
      ...allStyles.filter(({style_type}) => style_type === 'art').map(({name, value}) => {
        return {name: name, value: value, selected: value === '{{series.watched_style}}'};
      }),
      {name: 'Unique Variations', type: 'header'},
      ...allStyles.filter(({style_type}) => style_type === 'unique').map(({name, value}) => {
        return {name: name, value: value, selected: value === '{{series.watched_style}}'};
      }),
    ],
  });
  // Unwatched style
  $('#card-config-form .dropdown[data-value="unwatched-style"]').dropdown({
    values: [
      {name: 'Art Variations', type: 'header'},
      ...allStyles.filter(({style_type}) => style_type === 'art').map(({name, value}) => {
        return {name: name, value: value, selected: value === '{{series.unwatched_style}}'};
      }),
      {name: 'Unique Variations', type: 'header'},
      ...allStyles.filter(({style_type}) => style_type === 'unique').map(({name, value}) => {
        return {name: name, value: value, selected: value === '{{series.unwatched_style}}'};
      }),
    ]
  });
  // Fonts
  const fonts = await fetch('/api/fonts/all').then(resp => resp.json());
  $('#card-config-form .dropdown[data-value="fonts"]').dropdown({
    values: fonts.map(({id, name}) => {
      return {name: name, value: id, selected: `${id}` === '{{series.font_id}}'};
    })
  });
  // Font card case
  $('#card-config-form .dropdown[data-value="font_title_case"]').dropdown({
    values: [
      {name: 'Blank', value: 'blank', selected: '{{series.font_title_case}}' === 'blank'},
      {name: 'Lowercase', value: 'lower', selected: '{{series.font_title_case}}' === 'lower'},
      {name: 'Source', value: 'source', selected: '{{series.font_title_case}}' === 'source'},
      {name: 'Titlecase', value: 'title', selected: '{{series.font_title_case}}' === 'title'},
      {name: 'Uppercase', value: 'upper', selected: '{{series.font_title_case}}' === 'upper'},
    ],
  });
  // Hide season text
  initializeNullableBoolean({
    dropdownElement: $('#card-config-form .dropdown[data-value="hide_season_text"]'),
    value: '{{series.hide_season_text}}',
  });
  // Hide episode text
  initializeNullableBoolean({
    dropdownElement: $('#card-config-form .dropdown[data-value="hide_episode_text"]'),
    value: '{{series.hide_episode_text}}',
  });
  // Translations
  const allTranslations = await fetch('/api/available/translations').then(resp => resp.json());
  {% if series.translations is not none %}
  if ({{series.translations|safe}}.length > 0) { 
    const translationSegment = $('#card-config-form [data-value="translations"]');
    for (const translation of {{series.translations|safe}}) {
      const newTranslation = document.querySelector('#translation-template').content.cloneNode(true);
      translationSegment.append(newTranslation);
      $(`#card-config-form .dropdown[data-value="language_code"]`).last().dropdown({
        values: [
          {name: 'Language', type: 'header'},
          ...allTranslations.map(({language_code, language}) => {
            return {name: language, value: language_code, selected: translation.language_code === language_code};
          })
        ],
      });
      let extraValue = [];
      if (translation.data_key !== 'preferred_title' && translation.data_key !== 'kanji') {
        extraValue.push({name: translation.data_key, value: translation.data_key, selected: true});
      }
      $(`#card-config-form .dropdown[data-value="data_key"]`).last().dropdown({
        allowAdditions: true,
        values: [
          {name: 'Key', type: 'header'},
          {name: 'Preferred title', text: 'the preferred title', value: 'preferred_title', selected: translation.data_key === 'preferred_title'},
          {name: 'Kanji', text: 'kanji', value: 'kanji', selected: translation.data_key === 'kanji'},
          ...extraValue,
        ]
      });
    }
  }
  {% endif %}
  // Add season title on button press
  $('#card-config-form .button[data-value="addTitle"]').on('click', () => {
    const newRange = document.createElement('input');
    newRange.name = 'season_title_ranges'; newRange.type = 'text';
    newRange.setAttribute('data-value', 'season-titles');
    const newTitle = document.createElement('input');
    newTitle.name = 'season_title_values'; newTitle.type = 'text';
    $('#card-config-form .field[data-value="season-title-range"]').append(newRange);
    $('#card-config-form .field[data-value="season-title-value"]').append(newTitle);
  });
  // Add translation on button press
  $(`#card-config-form .button[data-add-field="translation"]`).on('click', () => {
    const newTranslation = document.querySelector('#translation-template').content.cloneNode(true);
    $(`#card-config-form [data-value="translations"]`).append(newTranslation);
    // Language code dropdown
    $(`#card-config-form .dropdown[data-value="language_code"]`).last().dropdown({
      values: [
        {name: 'Language', type: 'header'},
        ...allTranslations.map(({language_code, language}) => {
          return {name: language, value: language_code};
        })
      ],
    });
    // Data key dropdown
    $(`#card-config-form .dropdown[data-value="data_key"]`).last().dropdown({
      allowAdditions: true,
      values: [
        {name: 'Key', type: 'header'},
        {name: 'Preferred title', text: 'the preferred title', value: 'preferred_title'},
        {name: 'Kanji', text: 'kanji', value: 'kanji'},
      ]
    });
  });
  // Add extra on button press
  $('#card-config-form .button[data-add-field="extra"]').on('click', () => {
    const newKey = document.createElement('input');
    newKey.name = 'extra_keys'; newKey.type = 'text';
    const newValue = document.createElement('input');
    newValue.name = 'extra_values'; newValue.type = 'text';
    $('#card-config-form .field[data-value="extra-key"]').append(newKey);
    $('#card-config-form .field[data-value="extra-value"]').append(newValue);
  });
}

/*
 * Submit an API request to query TPDb for this Series' poster. If
 * successful, the URL field of the edit poster modal is populated.
 */
function queryTMDbPoster() {
  $.ajax({
    type: 'PUT',
    url: '/api/series/{{series.id}}/poster/query',
    success: posterUrl => {
      if (posterUrl === null) {
        $.ajax({class: 'error', title: 'TMDb returned no images'});
      } else {
        $('#edit-poster-modal input[name="poster_url"]').val(posterUrl);
      }
    }, error: () => $.ajax({class: 'error', title: 'TMDb returned no images'}),
  });
}

function deleteObject(args) {
  const {url, dataObject, label, deleteElements} = args;
  $.ajax({
    type: 'PATCH',
    url: url,
    data: JSON.stringify(dataObject),
    contentType: 'application/json',
    success: () => {
      showInfoToast(`Deleted ${label}`);
      $(deleteElements).remove();
    }, error: response => showErrorToast({title: `Error Deleting ${label}`, response}),
  });
}

function editEpisodeExtras(episode) {
  // Clear existing values
  $('#episode-extras-modal input').remove();
  // Add existing translations
  for (let [data_key, value] of Object.entries(episode.translations)) {
    const newKey = document.createElement('input');
    newKey.name = 'translation_key'; newKey.value = data_key;
    const newValue = document.createElement('input');
    newValue.name = 'translation_value'; newValue.value = value;
    $('#episode-extras-modal .field[data-value="translation-key"]').append(newKey);
    $('#episode-extras-modal .field[data-value="translation-value"]').append(newValue);
  }
  // Assign functions to add/delete translation buttons
  $('#episode-extras-modal .button[data-delete-field="translations"]').on('click', () => {
    deleteObject({
      url: `/api/episodes/${episode.id}`,
      dataObject: {translations: {}},
      label: 'Translations',
      deleteElements: '#episode-extras-modal .field[data-value="translations"] input',
    });
  });
  // Add existing extras
  if (episode.extras !== null) {
    for (let [key, value] of Object.entries(episode.extras)) {
      const newKey = document.createElement('input');
      newKey.name = 'extra_keys'; newKey.value = key;
      const newValue = document.createElement('input');
      newValue.name = 'extra_values'; newValue.value = value;
      $('#episode-extras-modal .field[data-value="extra-key"]').append(newKey);
      $('#episode-extras-modal .field[data-value="extra-value"]').append(newValue);
    }
  }
  // Assign functions to delete extra buttons
  $('#episode-extras-modal .button[data-delete-field="extras"]').off('click').on('click', () => {
    deleteObject({
      url: `/api/episodes/${episode.id}`,
      dataObject: {extra_keys: null, extra_values: null},
      label: 'Extras',
      deleteElements: '#episode-extras-modal .field[data-value="extras"] input',
    });
  });
  // Show modal
  $('#episode-extras-modal').modal('show');
  // Submit episode extras form
  $('#episode-extras-form').off('submit').on('submit', event => {
    event.preventDefault();
    if (!$('#episode-extras-form').form('is valid')) { return; }
    const translationKeys = $('#episode-extras-modal input[name="translation_key"]');
    const translationValues = $('#episode-extras-modal input[name="translation_value"]');
    const data = {
      extra_keys: $('#episode-extras-modal input[name="extra_keys"]').map((ind, element) => element.value).toArray(),
      extra_values: $('#episode-extras-modal input[name="extra_values"]').map((ind, element) => element.value).toArray(),
    };
    if (translationKeys.length) { 
      data.translations = Object.assign(...translationKeys.map((k, i) => ({ [i.value]: translationValues[k].value })));
    }
    $.ajax({
      type: 'PATCH',
      url: `/api/episodes/${episode.id}`,
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: () => showInfoToast('Updated Episode'),
      error: response => showErrorToast({title: 'Error Updating Episode', response}),
    });
  });
}

function initStyles() {
  // Toggle icons on click
  $('.table .togglable.icon').on('click', (event) => {
    // Non-tristate icons toggle check <-> x
    // Tristate icons toggle ? -> check -> x -> [...]
    if (event.target.classList.contains('check')) {
      event.target.classList.remove('green', 'check');
      event.target.classList.add('red', 'times', 'circle', 'outline');
    } else if (event.target.classList.contains('question')) {
      event.target.classList.remove('gray', 'question');
      event.target.classList.add('green', 'check');
    } else {
      event.target.classList.remove('red', 'times', 'circle', 'outline');
      // Tristate x goes to ?, bistate x goes to check
      if (event.target.classList.contains('tristate')) {
        event.target.classList.add('gray', 'question');
      } else {
        event.target.classList.add('green', 'check'); 
      }
    }
  });
  // Update input widths when typing
  $('.table .transparent.input:not(.id) input').on('input', (event) => {
    event.target.style.width = Math.max(`${event.target.value}`.length + 1, 8) + 'ch';
  });

  // Refresh theme for any newly added HTML
  refreshTheme();
}

async function getFileData() {
  const fileHolder = document.getElementById('files-list');
  const fileTemplate = document.getElementById('file-template');
  if (fileHolder === null || fileTemplate === null) { return; }
  const allFiles = await fetch('/api/sources/series/{{series.id}}').then(resp => resp.json());

  // Some error occured, toast and exit
  if (allFiles.detail !== undefined) {
    $.toast({
      class: 'error',
      title: 'Error getting Source details',
      message: allFiles.detail,
      displayTime: 0,
    });
    return;
  }

  const files = allFiles.map(source => {
    const file = fileTemplate.content.cloneNode(true);
    // Fill in the card values present on all files
    const cardId = `file-episode${source.episode_id}`;
    file.querySelector('.card').id = cardId;
    file.querySelector('[data-value="index"]').innerHTML = `Season ${source.season_number} Episode ${source.episode_number}`;
    file.querySelector('[data-value="path"]').innerHTML = source.source_file_name;
    // Launch TMDb browse modal when TMDb logo is clicked
    const tmdbLogo = file.querySelector('[data-action="browse-tmdb"]');
    if (tmdbLogo !== null) {
      tmdbLogo.onclick = () => browseTmdbImages(source.episode_id, cardId);
    }
    // Launch upload source modal when upload icon is clicked
    file.querySelector('i[data-action="upload"]').onclick = () => {
      $('#upload-source-form').off('submit').on('submit', event => {
        event.preventDefault();
        $.ajax({
          type: 'POST',
          url: `/api/sources/episode/${source.episode_id}/upload`,
          data: new FormData(event.target),
          cache: false,
          contentType: false,
          processData: false,
          success: () => {
            showInfoToast('Updated source image');
            getFileData();
          }, error: response => showErrorToast({title: 'Error updating source image', response}),
          complete: () => $('#upload-source-form')[0].reset(),
        });
      });
      $('#upload-source-modal').modal('show');
    }
    if (source.exists) {
      // Disable search icon
      file.querySelector('i[data-action="search"]').classList.add('disabled');
      // Remove missing label, fill in dimensions and filesize
      file.querySelector('[data-value="missing"]').remove();
      file.querySelector('[data-value="dimension"]').innerHTML = `${source.width}x${source.height}`;
      file.querySelector('[data-value="filesize"]').innerHTML = formatBytes(source.filesize, 1);
    } else {
      // Add download image function to icon click
      file.querySelector('i[data-action="search"]').onclick = () => getEpisodeSourceImage(source.episode_id, cardId);
      // Make the card red, remove unnecessary elements
      file.querySelector('.card').classList.add('red');
      file.querySelector('[data-value="dimension"]').remove();
      file.querySelector('[data-value="filesize"]').remove();
    }

    return file;
  });
  fileHolder.replaceChildren(...files);
  refreshTheme();
}

async function getEpisodeData(page=1) {
  // Get the parent table
  let episodeTable = document.getElementById('episode-data-table');
  if (episodeTable === null) { return; }

  // Get row template
  const rowTemplate = document.querySelector('#episode-row');
  if (rowTemplate === null) { return; }

  // Get page of episodes via API
  const episodeData = await fetch(`/api/episodes/{{series.id}}/all?size=50&page=${page}`).then(resp => resp.json());
  if (episodeData === null || episodeData.items.length === 0) { return; }
  const episodes = episodeData.items;

  // Different HTML for each togglable boolean icon
  function getIcon(value, triState=true) {
    const triStateClass = triState ? ' tristate' : '';
    if (value === null) {
      return `<i class="ui gray question${triStateClass} togglable icon"></i>`;
    } else if (value === true) {
      return `<i class="ui green check${triStateClass} togglable icon"></i>`;
    } else {
      return `<i class="ui red times circle outline${triStateClass} togglable icon"></i>`;
    }
  }

  // Create 
  const rows = episodes.map(episode => {
    // Create new row for this episode
    const row = rowTemplate.content.cloneNode(true);
    // Set row ID
    row.querySelector('tr').id = `episode-id${episode.id}`;
    row.querySelector('tr').dataset.episodeId = episode.id;
    // Assign function to onclick of <a> element
    row.querySelector('td[data-column="edit"] a').onclick = () => saveEpisodeConfig(episode.id);
    // Fill in row data
    row.querySelector('td[data-column="season_number"]').innerHTML = episode.season_number;
    row.querySelector('td[data-column="season_number"]').dataset.sortValue = episode.season_number;
    row.querySelector('td[data-column="episode_number"]').innerHTML = episode.episode_number;
    row.querySelector('td[data-column="episode_number"]').dataset.sortValue = episode.episode_number;
    row.querySelector('input[name="absolute_number"]').value = episode.absolute_number;
    row.querySelector('td[data-column="absolute_number"]').dataset.sortValue = episode.absolute_number;
    row.querySelector('input[name="title"]').value = episode.title;
    row.querySelector('td[data-column="title"]').dataset.sortValue = episode.title;
    row.querySelector('td[data-column="match_title"]').innerHTML = getIcon(episode.match_title, true);
    row.querySelector('td[data-column="auto_split_title"]').innerHTML = getIcon(episode.auto_split_title, false);
      // Template ID
      // Font ID
      // Card type
    row.querySelector('td[data-column="hide_season_text"]').innerHTML = getIcon(episode.hide_season_text, true);
    row.querySelector('input[name="season_text"]').value = episode.season_text;
    row.querySelector('td[data-column="hide_episode_text"]').innerHTML = getIcon(episode.hide_episode_text, true);
    row.querySelector('input[name="episode_text"]').value = episode.episode_text;
      // Unwatched style
      // Watched style
    row.querySelector('input[name="font_color"]').value = episode.font_color;
    row.querySelector('input[name="font_size"]').value = episode.font_size;
    row.querySelector('input[name="font_stroke_width"]').value = episode.font_stroke_width;
    row.querySelector('input[name="font_interline_spacing"]').value = episode.font_interline_spacing;
    row.querySelector('input[name="font_vertical_shift"]').value = episode.font_vertical_shift;
    row.querySelector('td[data-column="extras"] a').onclick = () => editEpisodeExtras(episode);
    row.querySelector('input[name="source_file"]').value = episode.source_file;
    row.querySelector('input[name="card_file"]').value = episode.card_file;
    row.querySelector('td[data-column="watched"]').innerHTML = getIcon(episode.watched, false);
    const embyIdInput = row.querySelector('input[name="emby_id"]');
    if (embyIdInput !== null) { embyIdInput.value = episode.emby_id; }
    row.querySelector('input[name="imdb_id"]').value = episode.imdb_id;
    const jellyfinIdInput = row.querySelector('input[name="jellyfin_id"]');
    if (jellyfinIdInput !== null) { jellyfinIdInput.value = episode.jellyfin_id; }
    row.querySelector('input[name="tmdb_id"]').value = episode.tmdb_id;
    row.querySelector('input[name="tvdb_id"]').value = episode.tvdb_id;
    const tvrageIdInput = row.querySelector('input[name="tvrage_id"]')
    if (tvrageIdInput !== null) { tvrageIdInput.value = episode.tvrage_id; }
    row.querySelector('td[data-column="delete"] a').onclick = () => deleteEpisode(episode.id);
    return row;
  });
  episodeTable.replaceChildren(...rows);

  // Get all available elements for initializing dropdowns
  const allCardTypes = await getAllCardTypes(false);
  const allTemplates = await fetch('/api/templates/all').then(resp => resp.json());
  const allFonts = await fetch('/api/fonts/all').then(resp => resp.json());
  const allStyles = await fetch('/api/available/styles').then(resp => resp.json());

  // Initialize dropdowns, assign form submit API request
  episodes.forEach(episode => {
    // Templates
    $(`#episode-id${episode.id} .dropdown[data-value="template_ids"]`).dropdown({
      values: getActiveTemplates(episode.template_ids, allTemplates),
    });
    // Fonts
    $(`#episode-id${episode.id} .dropdown[data-value="font_id"]`).dropdown({
      values: allFonts.map(({id, name}) => {
        return {name: name, value: id, selected: episode.font_id === id};
      })
    });
    // Card type
    loadCardTypes({
      allCardTypes: allCardTypes,
      element: `#episode-id${episode.id} .dropdown[data-value="card_type"]`,
      isSelected: (identifier) => identifier === episode.card_type,
      showExcluded: false,
      // Dropdown args
      dropdownArgs: {}
    });
    // Unwatched style
    $(`#episode-id${episode.id} .dropdown[data-value="unwatched_style"]`).dropdown({
      values: [
        {name: 'Art Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'art').map(({name, value}) => {
          return {name: name, value: value, selected: value === episode.unwatched_style};
        }),
        {name: 'Unique Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'unique').map(({name, value}) => {
          return {name: name, value: value, selected: value === episode.unwatched_style};
        }),
      ],
    });
    // Watched style
    $(`#episode-id${episode.id} .dropdown[data-value="watched_style"]`).dropdown({
      values: [
        {name: 'Art Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'art').map(({name, value}) => {
          return {name: name, value: value, selected: value === episode.watched_style};
        }),
        {name: 'Unique Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'unique').map(({name, value}) => {
          return {name: name, value: value, selected: value === episode.watched_style};
        }),
      ],
    });
  });
  $('.sortable.table').tablesort()
  initStyles();

  // Update Episode pagination
  updatePagination({
    paginationElementId: 'pagination',
    navigateFunction: getEpisodeData,
    page: episodeData.page,
    pages: episodeData.pages,
    amountVisible: isSmallScreen() ? 4 : 15,
  });
}

async function initAll() {
  initalizeSeriesConfig();
  getStatistics();
  getLibraries();
  getEpisodeData();
  getFileData();
  initStyles();

  // Schedule recurring statistics query
  getStatisticsId = setInterval(getStatistics, 30000); // Refresh stats every 30s

  // Enable all dropdowns, menus, and accordians
  $('.ui.dropdown').dropdown();
  // $('.ui.checkbox').checkbox();
  $('.menu .item').tab()
  $('.ui.accordion').accordion();
  $('.ui.checkbox').checkbox();
  // Enable IOS hover on the series poster
  $('.ui.special.card .image').dimmer({
    on: 'ontouchstart' in document.documentElement ? 'click' : 'hover'
  });

  // Make clearable dropdowns clearable
  $('.ui.clearable.dropdown').dropdown({
    'clearable': true,
    'placeholder': 'None',
  });

  // Show season title helper popup
  $('.field[data-value="season-titles"] label i').popup({
    popup : $('#season-title-popup'),
    position: 'right center',
  });

  // Enable edit poster modal, attach to the edit poster button
  $('#edit-poster-modal')
    .modal('attach events', '#poster', 'show')  // Show modal on add button press
    .modal('setting', 'transition', 'fade up')  // Fade up modal on reveal
    .modal('setting', 'closable', false)        // Don't allow closing by clicking outside modal
    .modal({
      blurring: true,                           // Blur background when shown
      onHidden: ($element) => {                 // Reset input on close
        $('#edit-poster-form')[0].reset();
      }}
    );

  // Delete series modal
  $('#delete-series-modal').modal('attach events', '#delete-series');

  // Configure new episode modal
  $('#new-episode-modal')
    .modal('attach events', '#new-episode', 'show') // Show modal on add buton press
    .modal('setting', 'transition', 'fade up')      // Fade up modal on reveal
    .modal('setting', 'closable', false)            // Don't allow closing by clicking outside modal
    .modal({
      onApprove: () => {                            // Don't close if form is invalid
        return $('#new-episode-form').form('is valid');
      }, blurring: true,                            // Blur background when shown
    });

  // On edit poster modal submission, submit API request
  $('#edit-poster-form').on('submit', event => {
    event.preventDefault();
    $('#submit-poster-button').toggleClass('loading', true);
    $.ajax({
      type: 'POST',
      url: '/api/series/{{series.id}}/poster',
      data: new FormData(event.target),
      cache: false,
      contentType: false,
      processData: false,
      success: response => {
        showInfoToast('Updated poster');
        // Reload image
        $('#poster-image')[0].src = `${response}?${new Date().getTime()}`;
      }, error: response => showErrorToast({title: 'Error updating poster', response}),
      complete: () =>  setTimeout(() => $('#submit-poster-button').toggleClass('loading', false), 750),
    });
  });

  // Add card config form validation
  $('#card-config-form').form({
    on: 'blur',
    inline: true,
    fields: {
      font_color: {
        optional: true,
        rules: [{type: 'minLength[1]'}],
      },
      font_size: {
        optional: true,
        rules: [{type: 'number', value: 'minValue[1]'}],
      }, font_kerning: {
        optional: true,
        rules: [{type: 'number'}],
      }, font_stroke_width: {
        optional: true,
        rules: [{type: 'number'}],
      }, font_interline_spacing: {
        optional: true,
        rules: [{type: 'number', value: 'integer'}],
      }, font_vertical_shift: {
        optional: true,
        rules: [{type: 'number', value: 'integer'}],
      },
      season_title_ranges: {
        optional: true,
        rules: [{type: 'regExp', value: /^(\d+-\d+)|^(\d+)|^(s\d+e\d+-s\d+e\d+)|^$/i}]
      }, season_title_values: {
        depends: 'season_title_ranges',
        // rules: [{type: 'minLength[1]'}],
      }, language_code: {
        optional: true,
      }, data_key: {
        optional: true,
        depends: 'language_code',
        rules: [{type: 'regExp', value: /^$|^[a-z]+[^ ]*$/i}],
      }, extra_keys: {
        optional: true,
        rules: [{type: 'regExp', value: /^([a-z]+[^ ]*|)$/i}],
      }, extra_values: {
        optional: true,
        depends: 'extra_keys',
        // rules: [{type: 'minLength[1]'}],
      },
    },
  });

  // Add episode extras form validation
  $('#episode-extras-form').form({
    on: 'blur',
    inline: true,
    fields: {
      translation_key: {
        rules: [{type: 'regExp', value: /^[a-z]+[^ ]*$/i}],
      }, translation_value: {
        rules: [{type: 'minLength[1]'}],
      }, extra_keys: {
        optional: true,
        rules: [{type: 'regExp', value: /^[a-z]+[^ ]*$/i}],
      },
    }
  });
  // Add episode extra button press
  $('#episode-extras-modal .button[data-add-field="extras"]').on('click', () => {
    const newKey = document.createElement('input');
    newKey.name = 'extra_keys'; newKey.type = 'text';
    const newValue = document.createElement('input');
    newValue.name = 'extra_values'; newValue.type = 'text';
    $(`#episode-extras-modal .field[data-value="extra-key"]`).append(newKey);
    $(`#episode-extras-modal .field[data-value="extra-value"]`).append(newValue);
  });

  // Submit the updated series config
  $('#series-config-form, #card-config-form, #series-ids-form').on('submit', event => {
    event.preventDefault();
    if (!$('#series-config-form').form('is valid') || !$('#card-config-form').form('is valid')) { return; }
    $('#submit-changes').toggleClass('loading', true);
    // Prepare form data
    let form = new FormData(event.target);
    let listData = {
      extra_keys: [], extra_values: [],
      season_title_ranges: [], season_title_values: [],
      language_code: [], data_key: [],
    };
    let template_ids = [];
    for (const [key, value] of [...form.entries()]) {
      // Handle Templates
      if (key === 'template_ids' && value != '') {
        template_ids = value.split(',');
      }
      // Add list data fields to listData object
      if (Object.keys(listData).includes(key)) {
        if (value !== '') { listData[key].push(value);  }
      }
      // Handle percentage values
      else if (value != '' && ['font_size', 'font_kerning', 'font_stroke_width'].includes(key)) {
        form.set(key, value/100.0);
      }
    }
    // Add translations
    if (listData.language_code.length > 0) {
      let translations = [];
      listData.language_code.forEach((val, index) => {
        if (val !== '') {
          translations.push({language_code: val, data_key: listData.data_key[index]});
        }
      });
      listData.translations = translations;
    }
    // Remove empty list values, and remove list data keys from form
    for (let [key, value] of [...Object.entries(listData)]) {
      if (value.length === 0) { delete listData[key]; }
      form.delete(key);
    }
    // Add checkbox status as true/false
    $.each($("#series-config-form, #card-config-form, #series-ids-form").find('input[type=checkbox]'), (key, val) => {
      form.append($(val).attr('name'), $(val).is(':checked'));
    });

    // Add Templates if the correct form
    if (event.target.id === 'card-config-form') {
      listData.template_ids = template_ids;
    }

    // Submit API request
    $.ajax({
      type: 'PATCH',
      url: '/api/series/{{series.id}}',
      data: JSON.stringify({...Object.fromEntries(form.entries()), ...listData}),
      contentType: 'application/json',
      success: () => showInfoToast('Updated Configuration Values'),
      error: response => showErrorToast({title: 'Error Updating Configuration', response}),
      complete: () => $('#submit-changes').toggleClass('loading', false),
    });
  });

  // Create a new episode
  $('#new-episode-form').form({
    on: 'blur',
    fields: {
      season_number: ['empty'],
      episode_number: ['empty'],
      title: ['empty', 'minLength[1]'],
    },
  });
  $('#new-episode-form').on('submit', (event) => {
    // Prevent page reload, do not submit if form is invalid
    event.preventDefault();
    if (!$('#new-episode-form').form('is valid')) { return; }
    // Prep form
    let form = new FormData(event.target);
    for (const [key, value] of [...form.entries()]) {
      if (value === '') { form.delete(key); }
    }
    form.append('series_id', '{{series.id}}');

    $.ajax({
      type: 'POST',
      url: '/api/episodes/new',
      data: JSON.stringify(Object.fromEntries(form)),
      contentType: 'application/json',
      success: (episode) => {
        const {season_number, episode_number} = episode;
        $.toast({
          class: 'blue info',
          title: `Created Season ${season_number} Episode ${episode_number}`,
        });
        getEpisodeData();
        getStatistics();
      }, error: response => showErrorToast({title: 'Error Creating Episode', response}),
    });
  });

  // Update list of Episode ID's when the input is changed
  $('#episode-data-table')
    .on('change', 'tr input', (e) => {
      const episodeId = $(e.target).closest('tr').data('episode-id')*1;
      if (!editedEpisodeIds.includes(episodeId*1)) { editedEpisodeIds.push(episodeId*1); }
    })
    .on('click', 'tr .icon', (e) => {
      const episodeId = $(e.target).closest('tr').data('episode-id')*1;
      if (!editedEpisodeIds.includes(episodeId*1)) { editedEpisodeIds.push(episodeId*1); }
    });
}

// Delete season titles/translations/extras on button press
function deleteListValues(attribute) {
  let data;
  if (attribute === 'season_titles') {
    data = {season_title_ranges: null, season_title_values: null};
  } else if (attribute === 'translations') {
    data = {translations: null};
  } else if (attribute === 'extras') {
    data = {extra_keys: null, extra_values: null};
  } else { data = {}; }
  $.ajax({
    type: 'PATCH',
    url: '/api/series/{{series.id}}',
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: () => {
      if (attribute === 'season_titles') {
        $('.field[data-value="season-title-range"] input').remove();
        $('.field[data-value="season-title-value"] input').remove();
      } else if (attribute === 'translations') {
        $('.field [data-value="translations"] >*').remove();
      } else if (attribute === 'extras') {
        $('.field[data-value="extra-key"] input').remove();
        $('.field[data-value="extra-value"] input').remove();
      }
      showInfoToast('Deleted Values');
    }, error: response => showErrorToast({title: 'Error Deleting Values', response}),
  })
}

/*
 * Submit an API request to toggle the monitored status of this Series.
 * If successful, this updates the HTML of the monitored icon.
 */
function toggleMonitorStatus() {
  $.ajax({
    type: 'POST',
    url: '/api/series/{{series.id}}/toggle-monitor',
    success: response => {
      // Show toast, toggle text and icon to show new status
      if (response.monitored) {
        $.toast({class: 'blue info', title: 'Started Monitoring Series'});
        $('#monitor-status span').toggleClass('red', false).toggleClass('green', true);
        $('#monitor-status span')[0].innerHTML = '<i class="ui eye outline green icon"></i>Monitored';
      } else {
        $.toast({class: 'blue info', title: 'Stopped Monitoring Series'});
        $('#monitor-status span').toggleClass('red', true).toggleClass('green', false);
        $('#monitor-status span')[0].innerHTML = '<i class="ui eye slash outline red icon"></i>Unmonitored';
      }
      refreshTheme();
    }, error: response => {
      $.toast({
        class: 'error',
        title: 'Error Changing Status',
        message: response.responseJSON.detail,
        displayTime: 0,
      });
    },
  });
}

/*
 * Submit an API request to completely process this Series. While
 * processing, all applicable buttons are disabled.
 */
function processSeries() {
  $('#action-buttons .button[data-action="process"] i').toggleClass('loading', true);
  $('#action-buttons .button').toggleClass('disabled', true);
  $.ajax({
    type: 'POST',
    url: '/api/series/{{series.id}}/process',
    success: () => {
      $.toast({class: 'blue info', title: 'Started Processing Series'});
    }, error: response => {
      showErrorToast({title: 'Error Processing Series', response});
    }, complete: () => {
      $('#action-buttons .button[data-action="process"] i').toggleClass('loading', false);
      $('#action-buttons .button').toggleClass('disabled', false);
    }
  });
}

/*
 * Submit an API request to refresh Episode data for this Series. If
 * successful, then the Episode, file, and statistics data are refreshed.
 */
function refreshEpisodeData() {
  document.getElementById('refresh').classList.add('disabled');
  $('#refresh > i').toggleClass('loading', true);
  $.ajax({
    type: 'POST',
    url: '/api/episodes/{{series.id}}/refresh',
    success: () => {
      $.toast({class: 'blue info', title: 'Refreshed Episode Data'});
      getEpisodeData();
      getFileData();
      getStatistics();
    }, error: response => {
      showErrorToast({title: 'Error Refreshing Data', response});
    }, complete: () => {
      document.getElementById('refresh').classList.remove('disabled');
      $('#refresh > i').toggleClass('loading', false);
    }
  });
}

/*
 * Submit an API request to add translations for this Series. This marks
 * the button as loading while processing.
 */
function addTranslations() {
  $('#add-translations > i').toggleClass('loading', true);
  $.ajax({
    type: 'POST',
    url: '/api/translate/series/{{series.id}}',
    success: () => showInfoToast('Adding Translations'),
    error: response => showErrorToast({title: 'Error Adding Translations', response}),
    complete: () => $('#add-translations > i').toggleClass('loading', false),
  });
}

/*
 * Submit an API request to import the given Blueprint for this Series.
 * While processing, the card element with the given ID is marked as
 * loading. If successful, the page is reloaded.
 */
function importBlueprint(cardId, blueprint) {
  // Turn on loading
  document.getElementById(cardId).classList.add('slow', 'double', 'blue', 'loading');
  // Submit API request to import blueprint
  $.ajax({
    type: 'PUT',
    url: '/api/blueprints/import/series/{{series.id}}',
    data: JSON.stringify(blueprint),
    contentType: 'application/json',
    success: () => showInfoToast('Blueprint Imported'),
    error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
    complete: () => document.getElementById(cardId).classList.remove('slow', 'double', 'blue', 'loading'),
  });
  // Get any URL's for Fonts to download
  let fontsToDownload = [];
  blueprint.fonts.forEach(font => {
    if (font.file_download_url) {
      fontsToDownload.push(font.file_download_url);
    }
  });
  // If any Fonts need downloaded, show toast
  if (fontsToDownload.length > 0) {
    $.toast({
      class: 'blue info',
      title: 'Font Files',
      message: 'This Blueprint specifies Named Fonts that require manually downloaded files.',
      displayTime: 0,
      classActions: 'basic left',
      actions: [
        {
          text: 'Open Pages',
          click: () => fontsToDownload.forEach(url => window.open(url, '_blank')),
        }, {
          icon: 'ban',
          class: 'icon red',
          click: () => showErrorToast({
            title: 'Blueprint Fonts',
            message: 'Blueprint Fonts will not be correct if files are not downloaded',
            displayTime: 10000,
          }),
        }
      ],
    });
  }
}

async function queryBlueprints() {
  // Get templates
  const blueprintCards = document.getElementById('blueprint-cards');
  const blueprintTemplate = document.getElementById('blueprint-template');
  if (blueprintCards === null || blueprintTemplate === null) { return; }
  // Show loading message
  $('.tab[data-tab="blueprints"] .info.message').toggleClass('hidden', false);
  // Query for Blueprints
  const allBlueprints = await fetch(`/api/blueprints/query/series/{{series.id}}`).then(resp => resp.json());
  $('.tab[data-tab="blueprints"] .info.message').toggleClass('hidden', true);
  // Disable query button
  $('.tab[data-tab="blueprints"] .button[data-action="search"]').toggleClass('disabled', true);
  // No blueprints available, hide loading and show warning message
  if (allBlueprints === null || allBlueprints.length === 0) {
    $('.tab[data-tab="blueprints"] .warning.message').toggleClass('hidden', false);
    return;
  }
  // Blueprints available, create cards
  const blueprints = allBlueprints.map((blueprint, blueprintId) => {
    // Clone template
    const card = blueprintTemplate.content.cloneNode(true);
    // Fill out card
    card.querySelector('.card').id = `blueprint-id${blueprintId}`;
    card.querySelector('img').src = blueprint.preview;
    card.querySelector('[data-value="creator"]').innerText = blueprint.creator;
    if (blueprint.fonts.length === 0) {
      card.querySelector('[data-value="font-count"]').remove();
    } else {
      let text = `<b>${blueprint.fonts.length}</b> Named Font` + (blueprint.fonts.length > 1 ? 's' : '');
      card.querySelector('[data-value="font-count"]').innerHTML = text;
    }
    if (blueprint.templates.length === 0) {
      card.querySelector('[data-value="template-count"]').remove();
    } else {
      let text = `<b>${blueprint.templates.length}</b> Template` + (blueprint.templates.length > 1 ? 's' : '');
      card.querySelector('[data-value="template-count"]').innerHTML = text;
    }
    if (Object.keys(blueprint.episodes).length === 0) {
      card.querySelector('[data-value="episode-count"]').remove();
    } else {
      let text = `<b>${Object.keys(blueprint.episodes).length}</b> Episode Override` + (blueprint.episodes.length > 1 ? 's' : '');
      card.querySelector('[data-value="episode-count"]').innerHTML = text;
    }
    card.querySelector('[data-value="description"]').innerHTML = '<p>' + blueprint.description.join('</p><p>') + '</p>';
    // Assign import to button
    card.querySelector('a[data-action="import-blueprint"]').onclick = () => importBlueprint(`blueprint-id${blueprintId}`, blueprint);
    return card;
  });
  blueprintCards.replaceChildren(...blueprints);
}

/*
 * Submit an API request to export the Blueprint for this Series. If
 * successful, the Blueprint zip file is downloaded.
 */
function exportBlueprint() {
  $.ajax({
    type: 'GET',
    url: '/api/blueprints/export/series/{{series.id}}/zip',
    xhrFields: {responseType: 'blob'},
    success: zipBlob => {
      // Download zip file
      downloadFileBlob('{{series.full_name}} Blueprint.zip', zipBlob);
      $.toast({
        class: 'warning',
        title: 'Font Files',
        message: 'Verify any applicable Font licenses allow the Fonts to be shared.',
        displayTime: 15000,
      });
      // Open window for Blueprint submission
      window.open(
        'https://github.com/CollinHeist/TitleCardMaker-Blueprints/issues/new?assignees=CollinHeist&labels=blueprint&projects=&template=new_blueprint.yml&title=[Blueprint] {{series.name}}&series_name={{series.name}}&series_year={{series.year}}',
        '_blank'
      );
    }, error: response => showErrorToast({title: 'Error Exporting Blueprint', response}),
  })
}

/*
 * Submit an API request to download the given source image URL for the
 * Episode with the given ID. If successful, the Series file data is
 * refreshed.
 */
function selectTmdbImage(episodeId, url) {
  // Create psuedo form for this URL
  const form = new FormData();
  form.set('url', url);
  // Submit API request to upload this URL
  $.ajax({
    type: 'POST',
    url: `/api/sources/episode/${episodeId}/upload`,
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Updated source image');
      getFileData();
    }, error: response => showErrorToast({title: 'Error Updating Source Image', response}),
  });
}

/*
 * Submit an API request to download the Series logo at the specified
 * URL.
 */
function downloadSeriesLogo(url) {
  // Create psuedo form for this URL
  const form = new FormData();
  form.set('url', url);
  // Submit API request to upload this URL
  $.ajax({
    type: 'POST',
    url: '/api/sources/series/{{series.id}}/logo/upload',
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Downloaded Logo');
      // Update logo source to force refresh
      $('#logoImage img')[0].src = `/source/{{series.path_safe_name}}/logo.png?${new Date().getTime()}`;
    },
    error: response => showErrorToast({title: 'Error Downloading Logo', response}),
  });
}

/*
 * Submit an API request to browse the available TMDb images for the
 * given Episode. 
 */
function browseTmdbImages(episodeId, cardElementId) {
  document.getElementById(cardElementId).classList.add('loading');
  $.ajax({
    type: 'GET',
    url: `/api/sources/episode/${episodeId}/browse`,
    success: images => {
      if (images === null) {
        showErrorToast({title: 'Unable to Query TMDb'});
      } else {
        // Images returned, add to browse modal
        const imageElements = images.map(({url, width, height}, index) => {
          const location = index % 2 ? 'right' : 'left';
          return `<a class="ui image" onclick="selectTmdbImage(${episodeId}, '${url}')"><div class="ui blue ${location} ribbon label">${width}x${height}</div><img src="${url}"/></a>`;
        });
        $('#browse-tmdb-modal .content .images')[0].innerHTML = imageElements.join('');
        $('#browse-tmdb-modal').modal('show');
      }
    }, error: response => showErrorToast({title: 'Unable to Query TMDb', response}),
    complete: () => document.getElementById(cardElementId).classList.remove('loading'),
  });
}

/*
 * Submit an API request to browse the available TMDb logos for this
 * Series. If successful, the relevant modal is shown.
 */
function browseTmdbLogos() {
  $.ajax({
    type: 'GET',
    url: '/api/sources/series/{{series.id}}/logo/browse',
    success: images => {
      if (images.length === 0) {
        showErrorToast({title: 'TMDb has no logos'});
      } else {
        const imageElements = images.map(({url}) => {
          return `<a class="ui image" onclick="downloadSeriesLogo('${url}')"><img src="${url}"/></a>`;
        });
        $('#browse-tmdb-logo-modal .content .images')[0].innerHTML = imageElements.join('');
        $('#browse-tmdb-logo-modal').modal('show');
      }
    }, error: response => showErrorToast({title: 'Unable to Query TMDb', response}),
  });
}

/*
 * Submit an API request to download the Source Image for the given Episode.
 * This marks the given cardElementId as loading while processing.
 */
function getEpisodeSourceImage(episodeId, cardElementId) {
  document.getElementById(cardElementId).classList.add('loading');
  $.ajax({
    type: 'POST',
    url: `/api/sources/episode/${episodeId}`,
    success: sourceImage => showInfoToast(sourceImage ? 'Downloaded Image' : 'Unable to Download Image'),
    error: response => showErrorToast({title: 'Error Downloading Source Image', response}),
    complete: () => document.getElementById(cardElementId).classList.remove('loading'),
  });
}

/*
 * Submit an API request to gather source images for this Series. This
 * disables the button while processing, and if successful the File data
 * is refreshed.
 */
function getSourceImages() {
  $('.button[data-action="download-source-images"]').toggleClass('disabled', true);
  $.toast({class: 'blue info', title: 'Starting to Download Source Images'});
  $.ajax({
    type: 'POST',
    url: '/api/sources/series/{{series.id}}',
    success: () => getFileData(),
    error: response => showErrorToast({title: 'Error Download Source Images', response}),
    complete: () => $('.button[data-action="download-source-images"]').toggleClass('disabled', false),
  });
}

/*
 * Submit an API request to initiate Card creation for this Series. This
 * disables the button while parsing, and if successful the Episode and
 * statistics are refreshed.
 */
function createTitleCards() {
  $('.button[data-action="create-title-cards"]').toggleClass('disabled', true);
  $.ajax({
    type: 'POST',
    url: '/api/cards/series/{{series.id}}',
    success: () => {
      showInfoToast('Starting to Create Title Cards');
      getEpisodeData();
      getStatistics();
    }, error: response => showErrorToast({title: 'Error creating Title Cards', response}),
    complete: () => $('.button[data-action="create-title-cards"]').toggleClass('disabled', false),
  });
}

/*
 * Submit an API request to delete this Series' Title Cards. Series
 * statistics are re-queried if successful.
 * 
 * @param {string} mediaServer - Which server the cards are being loaded into.
 * @param {bool} reload - Whether to force reload the cards.
 */
function loadCards(mediaServer, reload) {
  const endpoint = (reload ? 'reload/' : 'load/') + mediaServer;
  $.ajax({
    type: 'POST',
    url:`/api/series/{{series.id}}/${endpoint}`,
    success: () => {
      showInfoToast('Loaded Title Cards');
      getStatistics();
    }, error: response => showErrorToast({title: 'Error Loading Title Cards', response}),
  });
}

/*
 * Submit an API request to delete this Series. If successful, this
 * redirects to the home page.
 */
function deleteSeries() {
  $.ajax({
    type: 'DELETE',
    url: '/api/series/{{series.id}}',
    success: () => window.location.href = '/',
    error: response => showErrorToast({title: 'Error Deleting Series', response}),
  });
}

/*
 * Submit an API request to delete this Series' Title Cards. Series
 * statistics are re-queried after calling this.
 */
function deleteTitleCards(onSuccess) {
  $.ajax({
    type: 'DELETE',
    url: '/api/cards/series/{{series.id}}',
    success: response => {
      showInfoToast(`Deleted ${response.deleted} Cards`);
      if (onSuccess !== undefined) { onSuccess(); }
    }, error: response => showErrorToast({title: 'Error Deleting Title Cards', response}),
    complete: () => getStatistics(),
  });
}

/*
 * Submit an API request to delete all Episodes of this Series. If
 * successful, then the Episode, file, and statistics data are re-queried.
 */
function deleteAllEpisodes() {
  $.ajax({
    type: 'DELETE',
    url: '/api/episodes/series/{{series.id}}',
    success: response => {
      showInfoToast(`Deleted ${response.length} Episodes`);
      getEpisodeData();
      getFileData();
      getStatistics();
    }, error: response => showErrorToast({title: 'Error Deleting Episodes', response}),
  });
}

/*
 * Submit an API request to delete the Episode with the given ID. If successful,
 * then the statistics are re-queried and the Episode and file associated with
 * this Episode are removed from the DOM.
 * 
 * @param {int} id - Episode ID of the Episode to delete.
 */
function deleteEpisode(id) {
  $.ajax({
    type: 'DELETE',
    url: `/api/episodes/${id}`,
    success: () => {
      showInfoToast('Deleted Episode');
      // Remove this Episode's data row and file
      $(`#episode-id${id}`).transition({animation: 'slide down', duration: 1000});
      setTimeout(() => document.getElementById(`episode-id${id}`).remove(), 1000);
      document.getElementById(`file-episode${id}`).remove();
      getStatistics();
    }, error: response => showErrorToast({title: 'Error Deleting Episode', response}),
  });
}

/*
 * Submit an API request to navigate to the next or previous Series. If
 * successful (and there is a Series to navigate to), then the page is
 * redirected. If successful but there is no next/previous Series, the
 * appropriate nav button is disabled.
 * 
 * @param {string} next_or_previous - 'next' or 'previous'; where to navigate
 * the page.
 */
function navigateSeries(next_or_previous) {
  $.ajax({
    type: 'GET',
    url: `/api/series/{{series.id}}/${next_or_previous}`,
    success: series => {
      // No Series to navigate, disable button
      if (series === null) {
        $(`i[data-action="${next_or_previous}-series"]`).toggleClass('disabled', true);
      } else {
        window.location.href = `/series/${series.id}`;
      }
    }, error: response => showErrorToast({title: 'Navigation Failed', response}),
  });
}

/*
 * Submit an API request to remove the TCM/PMM labels from this Series in Plex.
 * 
 * @param {HTMLElement} buttonElement - Element to disable to signify it's been
 * clicked.
 */
function removePlexLabels(buttonElement) {  
  // Submit API request
  buttonElement.classList.add('disabled');
  document.getElementById()
  $.ajax({
    type: 'DELETE',
    url: `/api/series/{{series.id}}/plex-labels`,
    success: () => showInfoToast('Removed Labels'),
    error: response => showErrorToast({title: 'Error Updating Episode', response}),
  });
}