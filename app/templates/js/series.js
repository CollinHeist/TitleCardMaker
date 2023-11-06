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
      $('#card-count')[0].innerHTML = `<i class="image outline icon"></i><span class="ui pulsate text" onclick="getStatistics();">${cardStat.value} Cards / ${episodeStat.value} Episodes</span>`;
      
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
 * Submit an API request to create the Title Card for the Episode with the given
 * ID. If successful, the card data of the current page is reloaded.
 * 
 * @param {int} episodeId - ID of the Episode whose Card is being created.
 */
function createEpisodeCard(episodeId) {
  $.ajax({
    type: 'POST',
    url: `/api/cards/episode/${episodeId}`,
    success: () => {
      showInfoToast('Created Title Card');
      getCardData();
    }, error: response => showErrorToast({title: 'Error Creating Title Card', response}),
  });
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
    url: `/api/episodes/episode/${episodeId}`,
    contentType: 'application/json',
    data: JSON.stringify(updateEpisodeObject),
    success: () => {
      showInfoToast('Updated Episode'),
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
let allStyles, availableTemplates, availableFonts;
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
  $('#card-config-form .dropdown[data-value="template_ids"]').dropdown({
    values: getActiveTemplates({{series.template_ids}}, availableTemplates),
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
  $('#card-config-form .dropdown[data-value="fonts"]').dropdown({
    values: availableFonts.map(({id, name}) => {
      return {name, value: id, selected: `${id}` === '{{series.font_id}}'};
    })
  });
  if ('{{series.font_id}}' === 'None') {
    $('.field a[data-value="font-link"]').remove();
  } else {
    $('.field a[data-value="font-link"]')[0].href = `/fonts#font-id{{series.font_id}}`;
  }
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
  // Extras
  {% if series.extras is not none %}
  if (Object.entries({{series.extras|safe}}).length > 0) {
    // Add field for each extra
    const extraField = document.querySelector('.field[data-value="extras"]');
    for (const [key, value] of Object.entries({{series.extras|safe}})) {
      const extra = document.getElementById('extra-template').content.cloneNode(true);
      extra.querySelector('input[name="extra_values"]').value = value;
      extraField.appendChild(extra);
    }
    // Initialize each extra dropdown
    for (const [index, [key, value]] of Object.entries({{series.extras|safe}}).entries()) {
      initializeExtraDropdowns(
        key,
        $(`#card-config-form .dropdown[data-value="extra_keys"]`).eq(index),
        $(`#card-config-form .field[data-value="extras"] .popup .header`).eq(index),
        $(`#card-config-form .field[data-value="extras"] .popup .description`).eq(index),
      );
    }
    $('#card-config-form .field[data-value="extras"] .link.icon').popup({inline: true});
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
  $('#episode-extras-modal .field > .field, #episode-extras-modal .fields > .field > input').remove();
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
  $('#episode-extras-modal .button[data-delete-field="translations"]').off('click').on('click', () => {
    deleteObject({
      url: `/api/episodes/episode/${episode.id}`,
      dataObject: {translations: {}},
      label: 'Translations',
      deleteElements: '#episode-extras-modal .field[data-value="translations"] input',
    });
  });
  // Add existing extras
  if (episode.extras !== null) {
    // Remove any existing fields
    $('#episode-extras-modal .field[data-value="extras"] .field').remove();
    // Add new fields
    const extraField = $('#episode-extras-modal .field[data-value="extras"]');
    for (const [key, value] of Object.entries(episode.extras)) {
      const extra = document.getElementById('extra-template').content.cloneNode(true);
      extra.querySelector('input[name="extra_values"]').value = value;
      extraField.append(extra);
      initializeExtraDropdowns(
        key,
        $(`#episode-extras-modal .dropdown[data-value="extra_keys"]`).first(),
        $(`#episode-extras-modal  .field[data-value="extras"] .popup .header`).first(),
        $(`#episode-extras-modal  .field[data-value="extras"] .popup .description`).first(),
      );
    }
    $('#episode-extras-modal .field[data-value="extras"] .link.icon').popup({inline: true});
  }
  // Assign functions to delete extra buttons
  $('#episode-extras-modal .button[data-delete-field="extras"]').off('click').on('click', () => {
    deleteObject({
      url: `/api/episodes/episode/${episode.id}`,
      dataObject: {extra_keys: null, extra_values: null},
      label: 'Extras',
      deleteElements: '#episode-extras-modal .field[data-value="extras"] .field',
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
      url: `/api/episodes/episode/${episode.id}`,
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: updatedEpisode => {
        showInfoToast('Updated Episode');
        // Update the extras/translation modal for this Episode
        $(`#episode-id${episode.id} td[data-column="extras"] a`)
          .off('click')
          .on('click', () => editEpisodeExtras(updatedEpisode));
      }, error: response => showErrorToast({title: 'Error Updating Episode', response}),
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

let currentFilePage = 1;
async function getFileData(page=currentFilePage) {
  const fileTemplate = document.getElementById('file-card-template');
  const rowTemplate = document.getElementById('file-row-template');
  const allFiles = await fetch(`/api/sources/series/{{series.id}}?page=${page}&size=12`).then(resp => resp.json());

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

  // Update source image table
  const sources = allFiles.items.map(source => {
    const elementId = `file-episode${source.episode_id}`;
    {% if preferences.sources_as_table %}
    const row = rowTemplate.content.cloneNode(true);
    row.querySelector('tr').id = elementId;
    // Season
    const season = row.querySelector('td[data-column="season_number"]');
    season.innerText = source.season_number;
    season.dataset.sortValue = source.season_number;
    // Episode
    const episode = row.querySelector('td[data-column="episode_number"]');
    episode.innerText = source.episode_number;
    episode.dataset.sortValue = source.episode_number;
    // Width
    const width = row.querySelector('td[data-column="width"]');
    width.innerText = source.width || 'Missing';
    width.dataset.sortValue = source.width;
    // Height
    const height = row.querySelector('td[data-column="height"]');
    height.innerHTML = source.height || 'Missing';
    height.dataset.sortValue = source.height;
    // Filesize
    const filesize = row.querySelector('td[data-column="filesize"]');
    if (source.exists) {
      filesize.innerText = formatBytes(source.filesize, 1);
      filesize.dataset.sortValue = source.filesize;
      row.querySelector('[data-column="search-tmdb"]').classList.add('disabled');
      row.querySelector('[data-column="search-tmdb"] i').classList.add('disabled');
    } else {
      filesize.innerText = 'Missing'; filesize.dataset.sortValue = 0;
      width.classList.add('error');
      height.classList.add('error');
      filesize.classList.add('error');
      row.querySelector('i[data-action="search-tmdb"]').onclick = () => getEpisodeSourceImage(source.episode_id, elementId);
    }
    // Launch TMDb browse modal when TMDb logo is clicked
    const tmdbLogo = row.querySelector('[data-action="browse-tmdb"]');
    if (tmdbLogo !== null) {
      tmdbLogo.onclick = () => browseTmdbImages(source.episode_id, elementId);
    }
    // Launch upload source modal when upload icon is clicked
    row.querySelector('i[data-action="upload"]').onclick = () => {
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

    return row;
    {% else %}
    const file = fileTemplate.content.cloneNode(true);
    // Fill in the card values present on all files
    file.querySelector('.card').id = elementId;
    file.querySelector('[data-value="index"]').innerHTML = `Season ${source.season_number} Episode ${source.episode_number}`;
    file.querySelector('[data-value="path"]').innerHTML = source.source_file_name;
    // Launch TMDb browse modal when TMDb logo is clicked
    const tmdbLogo = file.querySelector('[data-action="browse-tmdb"]');
    if (tmdbLogo !== null) {
      tmdbLogo.onclick = () => browseTmdbImages(source.episode_id, elementId);
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
      file.querySelector('i[data-action="search-tmdb"]').classList.add('disabled');
      // Remove missing label, fill in dimensions and filesize
      file.querySelector('[data-value="missing"]').remove();
      file.querySelector('[data-value="dimension"]').innerHTML = `${source.width}x${source.height}`;
      file.querySelector('[data-value="filesize"]').innerHTML = formatBytes(source.filesize, 1);
    } else {
      // Add download image function to icon click
      file.querySelector('i[data-action="search-tmdb"]').onclick = () => getEpisodeSourceImage(source.episode_id, elementId);
      // Make the card red, remove unnecessary elements
      file.querySelector('.card').classList.add('red');
      file.querySelector('[data-value="dimension"]').remove();
      file.querySelector('[data-value="filesize"]').remove();
    }

    return file;
    {% endif %}
  });
  document.getElementById('source-images').replaceChildren(...sources);

  // Update source image previews
  const sourceImages = allFiles.items.map(source => {
    // Clone template
    const image = document.getElementById('preview-image-template').content.cloneNode(true);
    if (source.exists) {
      image.querySelector('.dimmer .content').innerHTML = `<h4>Season ${source.season_number} Episode ${source.episode_number} (${source.source_file_name})</h4>`;
      image.querySelector('img').src = `${source.source_url}?${source.filesize}`;
    }

    return image;
  });
  document.getElementById('source-image-previews').replaceChildren(...sourceImages);

  // Update pagination
  currentFilePage = page;
  updatePagination({
    paginationElementId: 'file-pagination',
    navigateFunction: getFileData,
    page: allFiles.page,
    pages: allFiles.pages,
    amountVisible: isSmallScreen() ? 4 : 18,
  });
  refreshTheme();
  $('#source-image-previews .image .dimmer').dimmer({transition: 'fade up', on: 'hover'});
}

async function getEpisodeData(page=1) {
  // Get the parent table
  let episodeTable = document.getElementById('episode-data-table');
  if (episodeTable === null) { return; }

  // Get row template
  const rowTemplate = document.querySelector('#episode-row');
  if (rowTemplate === null) { return; }

  // Get page of episodes via API
  const episodeData = await fetch(`/api/episodes/series/{{series.id}}/all?size={{preferences.episode_data_page_size}}&page=${page}`).then(resp => resp.json());
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
    // Assign functions to onclick of <a> element
    row.querySelector('td[data-column="create"] a').onclick = () => createEpisodeCard(episode.id);
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
    {% if not preferences.simplified_data_table %}
      // Unwatched style
      // Watched style
    row.querySelector('input[name="font_color"]').value = episode.font_color;
    row.querySelector('input[name="font_size"]').value = episode.font_size;
    row.querySelector('input[name="font_stroke_width"]').value = episode.font_stroke_width;
    row.querySelector('input[name="font_interline_spacing"]').value = episode.font_interline_spacing;
    row.querySelector('input[name="font_interword_spacing"]').value = episode.font_interword_spacing;
    row.querySelector('input[name="font_vertical_shift"]').value = episode.font_vertical_shift;
    row.querySelector('input[name="source_file"]').value = episode.source_file;
    row.querySelector('input[name="card_file"]').value = episode.card_file;
    {% endif %}
    row.querySelector('td[data-column="extras"] a').onclick = () => editEpisodeExtras(episode);
    row.querySelector('td[data-column="watched"]').innerHTML = getIcon(episode.watched, false);
    {% if not preferences.simplified_data_table %}
    const embyIdInput = row.querySelector('input[name="emby_id"]');
    if (embyIdInput !== null) { embyIdInput.value = episode.emby_id; }
    row.querySelector('input[name="imdb_id"]').value = episode.imdb_id;
    const jellyfinIdInput = row.querySelector('input[name="jellyfin_id"]');
    if (jellyfinIdInput !== null) { jellyfinIdInput.value = episode.jellyfin_id; }
    const tmdbIdInput = row.querySelector('input[name="tmdb_id"]');
    if (tmdbIdInput !== null) { tmdbIdInput.value = episode.tmdb_id; }
    row.querySelector('input[name="tvdb_id"]').value = episode.tvdb_id;
    const tvrageIdInput = row.querySelector('input[name="tvrage_id"]')
    if (tvrageIdInput !== null) { tvrageIdInput.value = episode.tvrage_id; }
    {% endif %}
    row.querySelector('td[data-column="delete"] a').onclick = () => deleteEpisode(episode.id);
    return row;
  });
  episodeTable.replaceChildren(...rows);

  // Initialize dropdowns, assign form submit API request
  await getAllCardTypes();
  episodes.forEach(episode => {
    // Templates
    $(`#episode-id${episode.id} .dropdown[data-value="template_ids"]`).dropdown({
      values: getActiveTemplates(episode.template_ids, availableTemplates),
    });
    // Fonts
    $(`#episode-id${episode.id} .dropdown[data-value="font_id"]`).dropdown({
      values: availableFonts.map(({id, name}) => {
        return {name: name, value: id, selected: episode.font_id === id};
      })
    });
    // Card type
    loadCardTypes({
      element: `#episode-id${episode.id} .dropdown[data-value="card_type"]`,
      isSelected: (identifier) => identifier === episode.card_type,
      showExcluded: false,
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
    amountVisible: isSmallScreen() ? 4 : 18,
  });
}

/*
 * Submit an API request to load the given page of  Title Card previews.
 * If successful, then the cards are loaded into the page under the
 * appropriate element, and the pagination menu is updated.
 */
let currentCardPage = 1;
function getCardData(page=currentCardPage, transition=false) {
  $.ajax({
    type: 'GET',
    url: `/api/cards/series/{{series.id}}?page=${page}&size=9`,
    success: cards => {
      const previewTemplate = document.getElementById('preview-image-template');
      const previews = cards.items.map(card => {
        const preview = previewTemplate.content.cloneNode(true);
        // Fill out preview
        // Start hidden if transitioning
        if (transition) {
          preview.querySelector('.image').classList.add('transition', 'hidden');
        }
        preview.querySelector('.dimmer .content').innerHTML = `<h4>Season ${card.episode.season_number} Episode ${card.episode.episode_number}`;
        const modifiedUrl = card.card_file.replace('{{preferences.card_directory}}', '/cards')
        preview.querySelector('img').src = `${modifiedUrl}?${card.filesize}`;
        return preview;
      });
      // Add elements to page
      if (transition) {
        $('#card-previews .image').transition({transition: 'fade out', interval: 20});
        setTimeout(() => {
          document.getElementById('card-previews').replaceChildren(...previews);
          $('#card-previews .image').transition({transition: 'fade out', interval: 20});
        }, 500);
      } else {
        document.getElementById('card-previews').replaceChildren(...previews);
      }

      // Update pagination
      currentCardPage = page;
      updatePagination({
        paginationElementId: 'card-pagination',
        navigateFunction: getCardData,
        page: cards.page,
        pages: cards.pages,
        amountVisible: isSmallScreen() ? 4 : 15,
      });

      // Refresh theme, initialize dimmers
      refreshTheme();
      $('#card-previews .image .dimmer').dimmer({transition: 'fade up', on: 'hover'});
    },
    // error: response => showErrorToast({title: 'Error Getting Card Data', response}),
  });
}

async function initAll() {
  // Get global availables for initializing dropdowns
  allStyles = await fetch('/api/available/styles').then(resp => resp.json());
  availableTemplates = await fetch('/api/available/templates').then(resp => resp.json());
  availableFonts = await fetch('/api/available/fonts').then(resp => resp.json());

  // Initialize 
  initalizeSeriesConfig();
  getLibraries();
  getEpisodeData();
  initStyles();
  getCardData();
  getFileData();
  
  // Schedule recurring statistics query
  getStatistics();
  getStatisticsId = setInterval(getStatistics, 60000); // Refresh stats every 30s
  setInterval(getCardData, 60000);

  // Open tab indicated by URL param
  const tab = window.location.hash.substring(1) || 'options';
  $('.menu .item')
    .tab('change tab', tab)
    // When tab is changed, update hash URL field 
    .tab({
      onVisible: (tabPath) => history.replaceState(null, null, `#${tabPath}`),
    });

  // Enable all dropdowns, menus, and accordians
  $('.ui.dropdown').dropdown();
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
      },
    }
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
      if (Object.keys(listData).includes(key) && value !== '') {
        listData[key].push(value); 
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
  $('#new-episode-form').on('submit', event => {
    // Prevent page reload, do not submit if form is invalid
    event.preventDefault();
    if (!$('#new-episode-form').form('is valid')) { return; }
    addEpisode(event);
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

/*
 * Submit an API request clear some list values (e.g. extras, titles, or
 * translations) for this Series. If successful, the data is also removed from
 * the DOM.
 * 
 * @param {string} attribute - Name of the attribue being deleted. This should
 * be 'season_titles', 'translations', or 'extras'.
 */
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
        $('.field[data-value="season-title-range"] > input').remove();
        $('.field[data-value="season-title-value"] > input').remove();
      } else if (attribute === 'translations') {
        $('.field [data-value="translations"] >*').remove();
      } else if (attribute === 'extras') {
        $('.field[data-value="extras"] > .field').remove();
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
        showInfoToast('Started Monitoring Series');
        $('#monitor-status span').toggleClass('red', false).toggleClass('green', true);
        $('#monitor-status span')[0].innerHTML = '<i class="ui eye outline green icon"></i>Monitored<p class="help">Click to unmonitor</p>';
      } else {
        showInfoToast('Stopped Monitoring Series');
        $('#monitor-status span').toggleClass('red', true).toggleClass('green', false);
        $('#monitor-status span')[0].innerHTML = '<i class="ui eye slash outline red icon"></i>Unmonitored<p class="help">Click to monitor</p>';
      }
      refreshTheme();
    }, error: response => showErrorToast({title: 'Error Changing Status', response}),
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
    success: () => showInfoToast('Started Processing Series'),
    error: response => showErrorToast({title: 'Error Processing Series', response}),
    complete: () => {
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
    url: '/api/episodes/series/{{series.id}}/refresh',
    success: () => {
      showInfoToast('Refreshed Episode Data');
      getEpisodeData();
      getFileData();
      getStatistics();
    }, error: response => showErrorToast({title: 'Error Refreshing Data', response}),
    complete: () => {
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
  // Indicate loading
  document.getElementById(cardId).classList.add('slow', 'double', 'blue', 'loading');

  // Get any URL's for Fonts to download
  let fontsToDownload = [];
  blueprint.json.fonts.forEach(font => {
    if (font.file_download_url) {
      fontsToDownload.push(font.file_download_url);
    }
  });

  // Submit API request to import blueprint
  $.ajax({
    type: 'PUT',
    url: `/api/blueprints/import/series/{{series.id}}/blueprint/${blueprint.id}`,
    success: () => {
      if (fontsToDownload.length === 0) {
        showInfoToast({title: 'Blueprint Imported', message: 'Reloading page...'});
        setTimeout(() => location.reload(), 2000);
      } else {
        showInfoToast('Blueprint Imported');
      }
    }, error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
    complete: () => document.getElementById(cardId).classList.remove('slow', 'double', 'blue', 'loading'),
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
          click: () => {
            fontsToDownload.forEach(url => window.open(url, '_blank'));
            showInfoToast('Reloading page..');
            setTimeout(() => location.reload(), 10000);
          },
        }, {
          icon: 'ban',
          class: 'icon red',
          click: () => {
            showErrorToast({
              title: 'Blueprint Fonts',
              message: 'Blueprint Fonts will not be correct if files are not downloaded',
              displayTime: 10000,
            });
            showInfoToast('Reloading page..');
            setTimeout(() => location.reload(), 10000);
          },
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
    // Clone template, fill out card
    let card = blueprintTemplate.content.cloneNode(true);
    card = populateBlueprintCard(card, blueprint, `blueprint-id${blueprintId}`);
    // Assign import to button
    card.querySelector('a[data-action="import-blueprint"]').onclick = () => importBlueprint(`blueprint-id${blueprintId}`, blueprint);
    return card;
  });
  blueprintCards.replaceChildren(...blueprints);
  $('[data-value="file-count"]').popup({inline: true});
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

      // Get database ID string for this Series
      let databaseIds = [];
      if ('{{series.imdb_id}}' !== 'None') { databaseIds.push('imdb:{{series.imdb_id}}'); }
      if ('{{series.tmdb_id}}' !== 'None') { databaseIds.push('tmdb:{{series.tmdb_id}}'); }
      if ('{{series.tvdb_id}}' !== 'None') { databaseIds.push('tmdb:{{series.tvdb_id}}'); }
      const idStr = databaseIds.join(',');

      // Get URL to pre-fill Blueprint form
      let url = `series_year={{series.year}}&database_ids=${(idStr)}`
      + `&series_name=${encodeURIComponent('{{series.name}}')}`
      + `&title=[Blueprint] ${encodeURIComponent('{{series.name}}')}`;

      // Open window for Blueprint submission
      window.open(
        'https://github.com/CollinHeist/TitleCardMaker-Blueprints/issues/new?'
        + `assignees=CollinHeist&labels=blueprint&template=new_blueprint.yaml`
        + `&${url}`,
        '_blank'
      );
    }, error: response => showErrorToast({title: 'Error Exporting Blueprint', response}),
  })
}

/*
 * Submit an API request to download the given source image URL for the
 * Episode with the given ID. If successful, the Series file and Card
 * data is refreshed.
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
      getCardData();
    }, error: response => showErrorToast({title: 'Error Updating Source Image', response}),
  });
}

/*
 * Submit an API request to download the Series logo at the specified
 * URL.
 * 
 * @param {str} url - URL of the logo file to download.
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
      document.querySelector('#logo').src = `/source/{{series.path_safe_name}}/logo.png?${new Date().getTime()}`;
    },
    error: response => showErrorToast({title: 'Error Downloading Logo', response}),
  });
}

/*
 * Submit an API request to download the Series backdrop at the specified
 * URL.
 * 
 * @param {str} url - URL of the backdrop file to download.
 */
function downloadSeriesBackdrop(url) {
  // Create psuedo form for this URL
  const form = new FormData();
  form.set('url', url);
  // Submit API request to upload this URL
  $.ajax({
    type: 'POST',
    url: '/api/sources/series/{{series.id}}/backdrop/upload',
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Downloaded Backdrop');
      document.querySelector('#backdrop').src = `/source/{{series.path_safe_name}}/backdrop.jpg?${new Date().getTime()}`;
    },
    error: response => showErrorToast({title: 'Error Downloading Backdrop', response}),
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
 * Submit an API request to browse the available logos for this Series.
 * If successful, the relevant modal is shown.
 */
function browseLogos() {
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
 * Submit an API request to browse the available backdrops for this
 * Series. If successful, the relevant modal is shown.
 */
function browseBackdrops() {
  $.ajax({
    type: 'GET',
    url: `/api/sources/series/{{series.id}}/backdrop/browse`,
    success: images => {
      if (images.length === 0) {
        showErrorToast({title: 'TMDb returned no images'});
      } else {
        // Images returned, add to browse modal
        const imageElements = images.map(({url, width, height}, index) => {
          const location = index % 2 ? 'right' : 'left';
          return `<a class="ui image" onclick="downloadSeriesBackdrop('${url}')"><div class="ui blue ${location} ribbon label">${width}x${height}</div><img src="${url}"/></a>`;
        });
        $('#browse-tmdb-modal .content .images')[0].innerHTML = imageElements.join('');
        $('#browse-tmdb-modal').modal('show');
      }
    }, error: response => showErrorToast({title: 'Unable to Query TMDb', response}),
  });
}

/*
 * Get the uploaded logo file and upload it to this Series. If the logo
 * is an image, then the API request to upload the logo is submitted. If
 * successful, then the logo `img` element is updated.
 */
function uploadLogo() {
  // Get uploaded file
  const file = $('#logo-upload')[0].files[0];
  if (!file) { return; }

  // Verify file is an image
  if (file.type.indexOf('image') !== 0) {
    showErrorToast({title: 'Uploaded file is not an image'});
    return;
  }

  // Create Form with this file
  const form = new FormData();
  form.append('file', file);

  // Submit API request
  $.ajax({
    type: 'POST',
    url: `/api/sources/series/{{series.id}}/logo/upload`,
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Updated Logo');
      document.querySelector('#logo').src = `/source/{{series.path_safe_name}}/logo.png?${new Date().getTime()}`;
    }, error: response => showErrorToast({title: 'Error Updating Logo', response}),
  });
}

/*
 * Get the uploaded backdrop file and upload it to this Series. If the
 * backdrop is an image, then the API request to upload the file is
 * submitted. If successful, then the backdrop `img` element is updated.
 */
function uploadBackdrop() {
  // Get uploaded file
  const file = $('#backdrop-upload')[0].files[0];
  if (!file) { return; }

  // Verify file is an image
  if (file.type.indexOf('image') !== 0) {
    showErrorToast({title: 'Uploaded file is not an image'});
    return;
  }

  // Create Form with this file
  const form = new FormData();
  form.append('file', file);

  // Submit API request
  $.ajax({
    type: 'POST',
    url: `/api/sources/series/{{series.id}}/backdrop/upload`,
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Updated Backdrop');
      document.querySelector('#backdrop').src = `/source/{{series.path_safe_name}}/backdrop.jpg?${new Date().getTime()}`;
    }, error: response => showErrorToast({title: 'Error Updating Backdrop', response}),
  });
}

/*
 * Submit an API request to download the Source Image for the given Episode.
 * This marks the given cardElementId as loading while processing.
 */
function getEpisodeSourceImage(episodeId, sourceElementId) {
  document.getElementById(sourceElementId).classList.add('loading');
  $.ajax({
    type: 'POST',
    url: `/api/sources/episode/${episodeId}`,
    success: sourceImage => showInfoToast(sourceImage ? 'Downloaded Image' : 'Unable to Download Image'),
    error: response => showErrorToast({title: 'Error Downloading Source Image', response}),
    complete: () => document.getElementById(sourceElementId).classList.remove('loading'),
  });
}

/*
 * Submit an API request to gather source images for this Series. This
 * disables the button while processing, and if successful the File data
 * is refreshed.
 */
function getSourceImages() {
  $('.button[data-action="download-source-images"]').toggleClass('disabled', true);
  showInfoToast('Starting to Download Source Images');
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
 * disables the button while parsing, and if successful the Episode
 * data, statistics, and current Card page is refreshed.
 */
function createTitleCards() {
  $('.button[data-action="create-title-cards"]').toggleClass('disabled', true);
  $.ajax({
    type: 'POST',
    url: '/api/cards/series/{{series.id}}',
    success: () => {
      showInfoToast('Starting to create Title Cards');
      getEpisodeData();
      getStatistics();
      getCardData();
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
      getCardData();
    }, error: response => showErrorToast({title: 'Error Deleting Title Cards', response}),
    complete: () => getStatistics(),
  });
}

/*
 * Submit an API request to add/create the new Episode defined in the given
 * event's target. 
 */
function addEpisode(event) {
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
    success: episode => {
      const {season_number, episode_number} = episode;
      showInfoToast(`Created Season ${season_number} Episode ${episode_number}`);
      getEpisodeData();
      getStatistics();
    }, error: response => showErrorToast({title: 'Error Creating Episode', response}),
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
    url: `/api/episodes/episode/${id}`,
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
        window.location.href = `/series/${series.id}${window.location.hash}`;
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
  $.ajax({
    type: 'DELETE',
    url: `/api/series/{{series.id}}/plex-labels`,
    success: () => showInfoToast('Removed Labels'),
    error: response => showErrorToast({title: 'Error Removing Labels', response}),
  });
}

/*
 * Add a blank Series Extra field to the card configuration form.
 */
function addBlankSeriesExtra() {
  const newExtra = document.getElementById('extra-template').content.cloneNode(true);
  $('#card-config-form .field[data-value="extras"]').append(newExtra);
  initializeExtraDropdowns(
    null,
    $(`#card-config-form .dropdown[data-value="extra_keys"]`).last(),
    $(`#card-config-form .popup .header`).last(),
    $(`#card-config-form .popup .description`).last(),
  );
  refreshTheme();
  $('#card-config-form .field[data-value="extras"] .link.icon').popup({inline: true});
}

/*
 * Add a blank Episode Extra field to the Episode extra modal form.
 */
function addBlankEpisodeExtra() {
  const newExtra = document.getElementById('extra-template').content.cloneNode(true);
  $('#episode-extras-modal .field[data-value="extras"]').append(newExtra);
  initializeExtraDropdowns(
    null,
    $(`#episode-extras-modal .dropdown[data-value="extra_keys"]`).last(),
    $(`#episode-extras-modal .field[data-value="extras"] .popup .header`).last(),
    $(`#episode-extras-modal .field[data-value="extras"] .popup .description`).last(),
  );
  refreshTheme();
  $('#episode-extras-modal .field[data-value="extras"] .link.icon').popup({inline: true});
}
