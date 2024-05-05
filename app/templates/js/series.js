// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-nocheck

{% if False %}
import {
  Blueprint, Episode, EpisodePage, ExternalSourceImage, LogEntryPage,
  MediaServerLibrary, PreviewTitleCard, RemoteBlueprint, Series, Statistic,
  SourceImagePage, TitleCardPage, UpdateEpisode
} from './.types.js';
{% endif %}

/** @type {string} */
const series_name = {{series.name|tojson}};
/** @type {string} */
const series_full_name = {{series.full_name|tojson}};
/** @type {boolean} */
const global_library_unique_cards = {{preferences.library_unique_cards|tojson}};
/** @type {MediaServerLibrary[]} */
const series_libraries = {{series.libraries|safe}};
/** @type {boolean} */
const reduced_animations = {{preferences.reduced_animations|tojson}};
/** @type {boolean} */
const interactive_card_previews = {{preferences.interactive_card_previews|tojson}};
/** @type {boolean} */
const simplified_data_table = {{preferences.simplified_data_table|tojson}};
/** @type {boolean} */
const sources_as_table = {{preferences.sources_as_table|tojson}};

/**
 * Get the DOM element ID of the Episode with the given ID.
 * @param {number} episode_id - ID of the Episode.
 * @returns {string} Element ID of the row for this Episode.
 */
const getEpisodeElementId = (episode_id) => `episode-id${episode_id}`;

/**
 * Get the DOM element ID of the Episode with the given ID.
 * @param {number} episode_id - ID of the Episode.
 * @returns {string} Element ID of the source image for this Episode.
 */
const getSourceImageElementId = (episode_id) => `file-episode${episode_id}`;

/** @type {number} */
let getStatisticsId;

/**
 * Submit an API request to get updated Series statistics. If successful, then
 * the card stats text and progress bar are updated.
 */
function getStatistics() {
  $.ajax({
    type: 'GET',
    url: '/api/statistics/series/{{series.id}}',
    /**
     * Statistics queried. Update progress bar and count stats text.
     * @param {Statistic[]} statistics 
     */
    success: statistics => {
      // Update card count text
      const [cardStat, episodeStat] = statistics;
      $('#card-count').html(`<i class="image outline icon"></i><span class="ui pulsate text" onclick="getStatistics();">${cardStat.value} Cards / ${episodeStat.value} Episodes</span>`);
      
      // Determine maximum number of cards
      const maxCards = global_library_unique_cards
        ? episodeStat.value * series_libraries.length
        : episodeStat.value
      ;

      // Update progress bar
      $('#card-progress').progress({
        total: maxCards,
        value: `${cardStat.value},${maxCards-cardStat.value}`,
        duration: 1500,
      });
    },
    error: response => {
      if (response.status === 401) {
        clearInterval(getStatisticsId);
      }
    },
  });
}

/** @type {number[]} Array of edited Episode IDs. */
let editedEpisodeIds = [];

/**
 * 
 * @param {number} episodeId - ID of the Episode whose object is being
 * generated.
 * @param {boolean} [excludeBlank] - Whether to exclude blank (`''`) values.
 * @returns {UpdateEpisode} Object which defines the given Episode.
 */
function getUpdateEpisodeObject(episodeId, excludeBlank=false) {
  // Get all inputs for this episode
  const episodeInputs = $(`#${getEpisodeElementId(episodeId)} input`);
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
      } else if (!excludeBlank || (excludeBlank && input.value !== '')) {
        updateEpisode[input.name] = input.value;
      }
    }
  });
  // Append boolean state icons to object as none/true/false
  $(`#${getEpisodeElementId(episodeId)} td[data-type="boolean"]`).each((index, value) => {
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

/**
 * Submit an API request to delete the Title Card(s) for the Episode with the
 * given ID.
 * @param {number} episodeId - ID of the Episode whose Cards are being deleted.
 * @param {Function} onComplete - Function to call after the Cards have been
 * deleted.
 */
function deleteEpisodeCard(episodeId, onComplete) {
  $.ajax({
    type: 'DELETE',
    url: `/api/cards/episode/${episodeId}`,
    success: () => showInfoToast('Deleted Title Card(s)'),
    error: response => showErrorToast({title: 'Error Creating Title Card(s)', response}),
    success: onComplete,
  });
}

/**
 * Submit an API request to create the Title Card for the Episode with the given
 * ID. If successful, the card data of the current page is reloaded and the
 * Episode's row marking is removed.
 * @param {number} episodeId - ID of the Episode whose Card is being created.
 */
function createEpisodeCard(episodeId) {
  $.ajax({
    type: 'POST',
    url: `/api/cards/episode/${episodeId}`,
    success: () => {
      showInfoToast('Created Title Card');
      getCardData();
      $(`#${getEpisodeElementId(episodeId)}`).toggleClass('left red marked', false);
    },
    error: response => showErrorToast({title: 'Error Creating Title Card', response}),
  });
}

/**
 * Submit an API request to save the modified Episode configuration for the
 * given Episode.
 * @param {number} episodeId - ID of the Episode whose config is being changed.
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
    },
    error: response => showErrorToast({title: 'Error Updating Episode', response}),
  });
}

/** Submit an API request to refresh the Episode data for this Series. */
function refreshEpisodes() {
  $('.button[data-action="refresh-episodes"]').toggleClass('disabled', true);
  $.ajax({
    type: 'POST',
    url: '/api/episodes/series/{{series.id}}/refresh',
    success: () => {
      showInfoToast('Refreshed Episode Data');
      getEpisodeData();
    },
    error: response => showErrorToast({title: 'Failed to Refresh Episode Data', response}),
    complete: () => $('.button[data-action="refresh-episodes"]').toggleClass('disabled', false),
  });
}

/**
 * Submit an API request to batch save all modified Episode configurations. This
 * uses the Episode ID's in the global `editedEpisodeIds` array.
 */
function saveAllEpisodes() {
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
    },
    error: response => showErrorToast({title: 'Error Updating Episodes', response}),
  });
}

// Initialize series config data
let allStyles, availableTemplates, availableFonts;
async function initalizeSeriesConfig() {
  // Get all connections
  const allConnections = await fetch('/api/connection/all').then(resp => resp.json());
  // Libraries
  $.ajax({
    type: 'GET',
    url: '/api/available/libraries/all',
    success: libraries => {
      // Start library value list with those selected by the Series
      let values = series_libraries.map(library => {
        return {
          interface: library.interface,
          interface_id: library.interface_id,
          name: library.name,
          selected: true
        };
      });
      // Add each library not already added to the Series
      libraries.forEach(({interface, interface_id, name}) => {
        if (!(values.some(library => library.interface_id === interface_id && library.name === name))) {
          values.push({interface, interface_id, name, selected: false});
        }
      });

      $('.dropdown[data-value="libraries"]').dropdown({
        placeholder: 'None',
        values: values.map(({interface, interface_id, name, selected}) => {
          const serverName = allConnections.filter(connection => connection.id === interface_id)[0].name || interface;
          return {
            name: name,
            text: `${name} (${serverName})`,
            value: `${interface}::${interface_id}::${name}`,
            description: serverName,
            descriptionVertical: true,
            selected: selected,
          };
        }),
      });
    },
    error: response => showErrorToast({title: 'Error Querying Libraries', response}),
  });

  // Episode data sources
  const allEpisodeDataSources = await fetch('/api/settings/episode-data-source').then(resp => resp.json());
  $('.dropdown[data-value="data_source_id"]').dropdown({
    placeholder: 'Default',
    values: allEpisodeDataSources.map(({name, interface_id}) => {
      return {name, value: interface_id, selected: `${interface_id}` === '{{series.data_source_id}}'};
    }),
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
  // Font color
  $('#card-config-form input[name="font_color"]').on('input', function () {
    document.querySelector('#card-config-form .field[data-value="font_color"] .color.circle').style.setProperty('--color', $(this).val());
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
  // Extras
  await initializeExtras(
    {% if series.extras %}
      {{series.extras|safe}},
    {% else %}
      [],
    {% endif %}
    {% if series.card_type %}
      '{{series.card_type}}',
    {% else %}
      '{{preferences.default_card_type}}',
    {% endif %}
    '#card-config-form section[aria-label="extras"]',
    document.getElementById('extra-input-template'),
    false,
    3,
  );
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
  refreshTheme();
}

/**
 * Submit an API request to query TPDb for this Series' poster. If successful,
 * the URL field of the edit poster modal is populated.
 */
function queryTMDbPoster() {
  $.ajax({
    type: 'GET',
    url: '/api/series/series/{{series.id}}/poster/query',
    /**
     * Query successful, populate the URL field or display a toast of no poster
     * returned.
     * @param {?string} posterUrl - URL to the poster returned by TMDb
     */
    success: posterUrl => {
      if (posterUrl === null) {
        $.toast({class: 'error', title: 'TMDb returned no images'});
      } else {
        $('#edit-poster-modal input[name="poster_url"]').val(posterUrl);
      }
    },
    error: () => $.ajax({class: 'error', title: 'TMDb returned no images'}),
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
    },
    error: response => showErrorToast({title: `Error Deleting ${label}`, response}),
  });
}

/**
 * Launch a modal to edit the extras (and translations) for the given Episode.
 * @param {Episode} episode - Episode whose extras are being edited.
 * @param {Episode[]} allEpisodes - Sorted array of Episodes for sequencing
 * through modals.
 */
async function editEpisodeExtras(episode, allEpisodes) {
  // Clear existing values
  $('#episode-extras-modal .field > .field, ' +
    '#episode-extras-modal .fields > .field > input').remove();

  // Update header
  $('#episode-extras-modal .header span').text(`Season ${episode.season_number} Episode ${episode.episode_number}`);

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
  $('#episode-extras-modal .button[data-delete-field="translations"]')
    .off('click')
    .on('click', () => {
      deleteObject({
        url: `/api/episodes/episode/${episode.id}`,
        dataObject: {translations: {}},
        label: 'Translations',
        deleteElements: '#episode-extras-modal .field[data-value="translations"] input',
      });
    });

  // Remove any existing extras
  $('#episode-extras-modal section[aria-label="extras"] > .tab, ' +
    '#episode-extras-modal section[aria-label="extras"] > .menu .item').remove();

  // Initialze extras
  await initializeExtras(
    episode.extras || [],
    episode.card_type || ('{{series.card_type}}' !== 'None' ? '{{series.card_type}}' : '{{preferences.default_card_type}}'),
    '#episode-extras-modal section[aria-label="extras"]',
    document.getElementById('extra-input-template'),
  );
  refreshTheme();

  // Assign functions to previous/next buttons
  const assignButtonNavs = (ep) => {
    $('#episode-extras-modal [data-action="previous-episode"]')
      .off('click')
      .on('click', () => {
        const previousEpisode = allEpisodes[allEpisodes.indexOf(ep) - 1];
        if (previousEpisode) { editEpisodeExtras(previousEpisode, allEpisodes);      }
        else {                 showInfoToast('No previous Episode on current page'); }
      });
    $('#episode-extras-modal [data-action="next-episode"]')
      .off('click')
      .on('click', () => {
        const nextEpisode = allEpisodes[allEpisodes.indexOf(ep) + 1];
        if (nextEpisode) {
          editEpisodeExtras(nextEpisode, allEpisodes);
        } else {
          showInfoToast('No next Episode on current page');
        }
      });
  };
  assignButtonNavs(episode);

  // Show modal
  $('#episode-extras-modal').modal('show');

  // Submit episode extras form
  $('#episode-extras-form')
    .off('submit')
    .on('submit', /** @param {SubmitEvent} event */ event => {
      // Prevent page reload
      event.preventDefault();

      // Mark button as loading
      $('#episode-extras-modal .button[type="submit"]').toggleClass('loading', true);

      /** Parse some list value, converting empty lists to null */
      const parseList = (value, _default) => value.length ? value : _default;

      // Convert form to data
      /** @type {UpdateEpisode} */
      const data = {
        translations: parseList(
            Array.from(document.querySelectorAll('#episode-extras-modal input[name="language_code"]')).map((input, index) => {
              return {
                language_code: input.value,
                data_key: document.querySelectorAll('#episode-extras-modal input[name="data_key"]')[index].value,
              };
            }),
            {},
          ),
        extra_keys: parseList(
            $('#episode-extras-modal section[aria-label="extras"] input').map(function() {
              if ($(this).val() !== '') { 
                return $(this).attr('name'); 
              }
            }).get()
          ),
        extra_values: parseList(
            $('#episode-extras-modal section[aria-label="extras"] input').map(function() {
              if ($(this).val() !== '') {
                return $(this).val(); 
              }
            }).get(),
          ),
      };

      // Submit API request
      $.ajax({
        type: 'PATCH',
        url: `/api/episodes/episode/${episode.id}`,
        data: JSON.stringify(data),
        contentType: 'application/json',
        /**
         * Edit successful, show toast and update the extras for this Episode.
         * @param {Episode} updatedEpisode - Newly edited Episode.
         */
        success: updatedEpisode => {
          showInfoToast('Updated Episode');
          // Update the extras/translation modal for this Episode
          allEpisodes[allEpisodes.indexOf(episode)] = updatedEpisode;
          $(`#${getEpisodeElementId(episode.id)} td[data-column="extras"] a`)
            .off('click')
            .on('click', () => editEpisodeExtras(updatedEpisode, allEpisodes));
          assignButtonNavs(updatedEpisode);
        },
        error: response => showErrorToast({title: 'Error Updating Episode', response}),
        complete: () => $('#episode-extras-modal .button[type="submit"]').toggleClass('loading', false),
      });
    });
}

/**
 * Initialize all toggle icons in the episode data table. This assigns the
 * onclick method to these icons to toggle the icons.
 */
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

/**
 * Submit an API request to open the upload source image modal and then submit
 * an API request to upload that image when the modal form is submitted.
 * @param {number} episodeId - ID of the Episode whose source image is being
 * uploaded.
 */
function uploadEpisodeSource(episodeId) {
  $('#upload-source-form').off('submit').on('submit', event => {
    event.preventDefault();
    $.ajax({
      type: 'PUT',
      url: `/api/sources/episode/${episodeId}/upload`,
      data: new FormData(event.target),
      cache: false,
      contentType: false,
      processData: false,
      success: () => {
        showInfoToast('Updated Source Image');
        getSourceFileData();
      },
      error: response => showErrorToast({title: 'Error Updating Source Image', response}),
      complete: () => $('#upload-source-form')[0].reset(),
    });
  });
  $('#upload-source-modal').modal('show');
}

/**
 * Submit an API request to mirror the source image of the given Episode. If
 * successful, then re-query the File and Card data.
 * @param {number} episodeId: ID of the Episode whose Source Image is being
 * modified.
 */
function mirrorSourceImage(episodeId) {
  $.ajax({
    type: 'PUT',
    url: `/api/sources/episode/${episodeId}/mirror`,
    success: () => {
      showInfoToast('Mirrored Source Image');
      getSourceFileData();
      getCardData();
      $(`#${getEpisodeElementId(episodeId)}`).toggleClass('left red marked', true);
    },
    error: response => showErrorToast({title: 'Error Mirroring Source Image', response}),
  });
}

/** @type {number} Current page number for the source files. */
let currentFilePage = 1;

/**
 * Query and display the Source Images on the webpage.
 * @param {number} page - Page number of source files to query and display.
 */
async function getSourceFileData(page=currentFilePage) {
  const fileTemplate = document.getElementById('file-card-template');
  const rowTemplate = document.getElementById('file-row-template');

  $.ajax({
    type: 'GET',
    url: `/api/sources/series/{{series.id}}?page=${page}&size=12`,
    /**
     * Sources queried, create elements to display on the page.
     * @param {SourceImagePage} allFiles - Page of Source Images for this Series.
     */
    success: allFiles => {
      // Get sequential list of element IDs
      const episodeIds = allFiles.items.map(({episode_id}) => episode_id);

      const sources = allFiles.items.map(source => {
        // Current element ID on the page
        const elementId = getSourceImageElementId(source.episode_id);

        // Create row for this Source
        if (sources_as_table) {
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
            // Disable search cell
            row.querySelector('[data-column="search"]').classList.add('disabled');
            row.querySelector('[data-column="search"] i').classList.add('disabled');
            // Add mirror API request to mirror icon
            row.querySelector('a[data-action="mirror"]').onclick = () => mirrorSourceImage(source.episode_id);
          } else {
            filesize.innerText = 'Missing'; filesize.dataset.sortValue = 0;
            width.classList.add('error');
            height.classList.add('error');
            filesize.classList.add('error');
            row.querySelector('a[data-action="search"]').onclick = () => searchEpisodeSourceImage(source.episode_id, elementId);
            row.querySelector('[data-column="mirror"]').classList.add('disabled');
            row.querySelector('[data-column="mirror"] i').classList.add('disabled');
          }
          // Launch browse modal when clicked
          row.querySelector('a[data-action="browse"]').onclick = () => browseSourceImages(source.episode_id, elementId, episodeIds);
          // Launch upload source modal when upload icon is clicked
          row.querySelector('a[data-action="upload"]').onclick = () => uploadEpisodeSource(source.episode_id);
      
          return row;
        // Create "Card" for this Source
        } else {
          const file = fileTemplate.content.cloneNode(true);
          // Fill in the card values present on all files
          file.querySelector('.card').id = elementId;
          file.querySelector('[data-value="index"]').innerHTML = `Season ${source.season_number} Episode ${source.episode_number}`;
          file.querySelector('[data-value="path"]').innerHTML = source.source_file_name;
          // Launch TMDb browse modal when TMDb logo is clicked
          file.querySelector('[data-action="browse"]').onclick = () => browseSourceImages(source.episode_id, elementId, episodeIds);
          // Launch upload source modal when upload icon is clicked
          file.querySelector('i[data-action="upload"]').onclick = () => uploadEpisodeSource(source.episode_id);
          if (source.exists) {
            // Remove search icon
            file.querySelector('i[data-action="search"]').remove();
            // Add mirror API request to mirror icon
            file.querySelector('i[data-action="mirror"]').onclick = () => mirrorSourceImage(source.episode_id);
            // Remove missing label, fill in dimensions and filesize
            file.querySelector('[data-value="missing"]').remove();
            file.querySelector('[data-value="dimension"]').innerHTML = `${source.width}x${source.height}`;
            file.querySelector('[data-value="filesize"]').innerHTML = formatBytes(source.filesize, 1);
          } else {
            // Add download image function to icon click
            file.querySelector('i[data-action="search"]').onclick = () => searchEpisodeSourceImage(source.episode_id, elementId);
            // Remove mirror icon
            file.querySelector('i[data-action="mirror"]').remove();
            // Make the card red, remove unnecessary elements
            file.querySelector('.card').classList.add('red');
            file.querySelector('[data-value="dimension"]').remove();
            file.querySelector('[data-value="filesize"]').remove();
          }
      
          return file;
        }
      });
      document.getElementById('source-images').replaceChildren(...sources);
    
      // Update source image previews
      const sourceImages = [];
      allFiles.items.forEach(source => {
        if (!source.exists) { return; }
        // Clone template
        const image = document.getElementById('preview-image-template').content.cloneNode(true);
        image.querySelector('.dimmer .content').innerHTML = `<h4>Season ${source.season_number} Episode ${source.episode_number} (${source.source_file_name})</h4>`;
        image.querySelector('img').src = `${source.source_url}?${source.filesize}`;
        image.querySelector('img').onclick = () => browseSourceImages(source.episode_id, getSourceImageElementId(source.episode_id), episodeIds);
        sourceImages.push(image);
      });
      document.getElementById('source-image-previews').replaceChildren(...sourceImages);
    
      // Update pagination
      currentFilePage = page;
      updatePagination({
        paginationElementId: 'file-pagination',
        navigateFunction: getSourceFileData,
        page: allFiles.page,
        pages: allFiles.pages,
        amountVisible: isSmallScreen() ? 8 : 16,
      });
      refreshTheme();
      $('#source-image-previews .image .dimmer').dimmer({transition: 'fade up', on: 'hover'});
    },
    error: response => showErrorToast({title: 'Error Loading Series Source Images', response}),
  });
}

/**
 * Submit an API request to get the number of Blueprints available for this
 * Series, and then update the blueprint tab text.
 */
function getBlueprintCount() {
  $.ajax({
    type: 'GET',
    url: '/api/blueprints/query/series/{{series.id}}?allow_refresh=false',
    /**
     * Query successful, update count of available Blueprints.
     * @param {Blueprint[]} blueprints - List of Blueprints available for
     * this Series.
     */
    success: blueprints => {
      if (blueprints.length > 0) {
        $('.menu [data-tab="blueprints"] [data-value="blueprint-count"]').html(`&nbsp;(${blueprints.length})`);
      }
    },
  });
}

/**
 * 
 * @param {number} page - Page number of Episode data to query.
 */
async function getEpisodeData(page=1) {
  // Get the parent table
  let episodeTable = document.getElementById('episode-data-table');
  if (episodeTable === null) { return; }

  // Get row template
  const rowTemplate = document.querySelector('#episode-row');
  if (rowTemplate === null) { return; }

  // Get page of episodes via API
  /** @type {EpisodePage} */
  const episodeData = await fetch(`/api/episodes/series/{{series.id}}?size={{preferences.episode_data_page_size}}&page=${page}`).then(resp => resp.json());
  if (episodeData === null || episodeData.items.length === 0) { return; }

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

  // Create row for each Episode
  const rows = episodeData.items.map(episode => {
    // Create new row for this episode
    const row = rowTemplate.content.cloneNode(true);

    // Set row ID
    row.querySelector('tr').id = `${getEpisodeElementId(episode.id)}`;
    row.querySelector('tr').dataset.episodeId = episode.id;
    // Add red mark if no Card is present
    if (episode.cards.length == 0) { row.querySelector('tr').classList.add('left', 'red', 'marked'); }
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
    row.querySelector('td[data-column="auto_split_title"]').innerHTML = getIcon(episode.auto_split_title, true);
    // Template ID
    // Font ID
    // Card type
    row.querySelector('td[data-column="hide_season_text"]').innerHTML = getIcon(episode.hide_season_text, true);
    row.querySelector('input[name="season_text"]').value = episode.season_text;
    row.querySelector('td[data-column="hide_episode_text"]').innerHTML = getIcon(episode.hide_episode_text, true);
    row.querySelector('input[name="episode_text"]').value = episode.episode_text;
    if (!simplified_data_table) {
      // Unwatched style
      // Watched style
      row.querySelector('input[name="font_color"]').value = episode.font_color;
      row.querySelector('input[name="font_size"]').value = episode.font_size === null ? episode.font_size : episode.font_size * 100;
      row.querySelector('input[name="font_kerning"]').value = episode.font_kerning === null ? episode.font_kerning : episode.font_kerning * 100;
      row.querySelector('input[name="font_stroke_width"]').value = episode.font_stroke_width === null ? episode.font_stroke_width : episode.font_stroke_width * 100;
      row.querySelector('input[name="font_interline_spacing"]').value = episode.font_interline_spacing;
      row.querySelector('input[name="font_interword_spacing"]').value = episode.font_interword_spacing;
      row.querySelector('input[name="font_vertical_shift"]').value = episode.font_vertical_shift;
      row.querySelector('input[name="source_file"]').value = episode.source_file;
      row.querySelector('input[name="card_file"]').value = episode.card_file;
    }
    row.querySelector('td[data-column="extras"] a').onclick = () => editEpisodeExtras(episode, episodeData.items);
    if (!simplified_data_table) {
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
      row.querySelector('input[name="airdate"]').value = episode.airdate;
    }
    row.querySelector('td[data-column="delete"] a').onclick = () => deleteEpisode(episode.id);
    return row;
  });
  episodeTable.replaceChildren(...rows);

  // Initialize dropdowns, assign form submit API request
  await getAllCardTypes();
  episodeData.items.forEach(episode => {
    // Templates
    $(`#${getEpisodeElementId(episode.id)} .dropdown[data-value="template_ids"]`).dropdown({
      values: getActiveTemplates(episode.template_ids, availableTemplates),
    });
    // Fonts
    $(`#${getEpisodeElementId(episode.id)} .dropdown[data-value="font_id"]`).dropdown({
      values: availableFonts.map(({id, name}) => {
        return {name: name, value: id, selected: episode.font_id === id};
      })
    });
    // Card type
    loadCardTypes({
      element: `#${getEpisodeElementId(episode.id)} .dropdown[data-value="card_type"]`,
      isSelected: (identifier) => identifier === episode.card_type,
      showExcluded: false,
      dropdownArgs: {}
    });
    // Unwatched style
    $(`#${getEpisodeElementId(episode.id)} .dropdown[data-value="unwatched_style"]`).dropdown({
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
    $(`#${getEpisodeElementId(episode.id)} .dropdown[data-value="watched_style"]`).dropdown({
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
    amountVisible: isSmallScreen() ? 8 : 16,
  });
}

/**
 * Submit an API request to query all logs associated with this Series, adding
 * these messages to the log timeline/page.
 */
function querySeriesLogs() {
  const toTitleCase = (text) => text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
  $.ajax({
    type: 'GET',
    url: `/api/logs/query?contains=Series[{{series.id}}]|${series_full_name}&level=DEBUG&size=100`,
    /**
     * Logs queried, add elements to the timeline in the DOM.
     * @param {LogEntryPage} logs - Logs associated with this Series.
     */
    success: logs => {
      const eventTemplate = document.getElementById('log-event-template');

      const events = logs.items.map(log => {
        const event = eventTemplate.content.cloneNode(true);
        const color = {
          'CRITICAL': 'red', 'ERROR': 'orange', 'WARNING': 'yellow',
          'INFO': 'blue', 'DEBUG': 'grey'
        }[log.level];

        event.querySelector('.label .icon').classList.add(color);
        event.querySelector('.summary span').innerText = `${toTitleCase(log.level)} Message`;
        event.querySelector('.date').innerText = timeDiffString(log.time);
        event.querySelector('.extra').innerText = log.message
          .replace(`Series[{{series.id}}] ${series_full_name}`, series_full_name);

        return event;
      })

      document.querySelector('.feed').replaceChildren(...events);
      refreshTheme();
    },
  });
}

let currentCardPage = 1;
/**
 * Submit an API request to load the given page of  Title Card previews. If
 * successful, then the cards are loaded into the page under the appropriate
 * element, and the pagination menu is updated.
 * @param {number} [page] - The page number of card data to query.
 * @param {boolean} [transition] - Whether to transition the HTMLElements when
 * updating the DOM.
 * @param {boolean} [scroll] - Whether to scroll to the top of the Card display.
 */
function getCardData(page=currentCardPage, transition=false, scroll=false) {
  const pageSize = isSmallScreen() ? 3 : 12;
  $.ajax({
    type: 'GET',
    url: `/api/cards/series/{{series.id}}?page=${page}&size=${pageSize}`,
    /**
     * Cards queried, populate page / table of Card data.
     * @param {TitleCardPage} cards - Current page of Title Card data.
     */
    success: cards => {
      const previewTemplate = document.getElementById('preview-image-template');
      const previews = cards.items.map(card => {
        const preview = previewTemplate.content.cloneNode(true);
        // Start hidden if transitioning
        if (!reduced_animations && transition && !isSmallScreen()) {
          preview.querySelector('.image').classList.add('transition', 'hidden');
        }

        // Re-create Card when image is clicked or right-clicked (if enabled)
        if (interactive_card_previews) {
          preview.querySelector('img').onclick = () => createEpisodeCard(card.episode_id);
          // Delete Card and then recreate when image is clicked
          preview.querySelector('img').oncontextmenu = () => {
            deleteEpisodeCard(
              card.episode_id,
              () => createEpisodeCard(card.episode_id),
            );
          }
        }

        // If library unique mode is enabled, add the library name to the text (if present)
        if (global_library_unique_cards) {
          if (card.library_name) {
            preview.querySelector('.dimmer .content').innerHTML = `<h5>Season ${card.episode.season_number} Episode ${card.episode.episode_number} (${card.library_name})</h5>`;
          } else {
            preview.querySelector('.dimmer .content').innerHTML = `<h5>Season ${card.episode.season_number} Episode ${card.episode.episode_number}</h5>`;
          }
        } else {
          preview.querySelector('.dimmer .content').innerHTML = `<h5>Season ${card.episode.season_number} Episode ${card.episode.episode_number}</h5>`;
        }

        preview.querySelector('img').src = `${card.file_url}?${card.filesize}`;

        return preview;
      });

      // Add elements to page
      const previewElement = document.getElementById('card-previews');
      if (reduced_animations) {
        previewElement.replaceChildren(...previews);
      } else {
        if (transition && !isSmallScreen()) {
          $('#card-previews .image').transition({transition: 'fade up', interval: 20});
          setTimeout(() => {
            previewElement.replaceChildren(...previews);
            $('#card-previews .image').transition({transition: 'fade down', interval: 20});
          }, 500);
        } else {
          previewElement.replaceChildren(...previews);
        }
      }
      if (scroll) {
        previewElement.scrollIntoView({behavior: 'smooth', block: 'start'});
      }

      // Update pagination
      currentCardPage = page;
      updatePagination({
        paginationElementId: 'card-pagination',
        navigateFunction: (p, t) => getCardData(p, t, true),
        page: cards.page,
        pages: cards.pages,
        amountVisible: isSmallScreen() ? 6 : 12,
      });

      // Refresh theme, initialize dimmers
      setTimeout(() => {
        refreshTheme();
        $('#card-previews .image .dimmer').dimmer({transition: 'fade up', on: 'hover'})
      }, 525);
    },
  });
}

async function initAll() {
  // Get global availables for initializing dropdowns
  allStyles = await fetch('/api/available/styles').then(resp => resp.json());
  availableTemplates = await fetch('/api/available/templates').then(resp => resp.json());
  availableFonts = await fetch('/api/available/fonts').then(resp => resp.json());

  // Initialize 
  initalizeSeriesConfig();
  getEpisodeData();
  initStyles();
  getCardData();
  getSourceFileData();
  getBlueprintCount();
  refreshTheme();
  getEpisodeOverviews();
  
  // Schedule recurring statistics query
  getStatistics();
  getStatisticsId = setInterval(getStatistics, 90000);
  setInterval(getCardData, 90000);
  querySeriesLogs();

  // Open tab indicated by URL param
  const tab = window.location.hash.substring(1) || 'options';
  $('#series-tabs-menu .item')
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
  // On edit poster modal submission, submit API request
  $('#edit-poster-form').on('submit', event => {
    event.preventDefault();
    $('#submit-poster-button').toggleClass('loading', true);
    $.ajax({
      type: 'PUT',
      url: '/api/series/series/{{series.id}}/poster',
      data: new FormData(event.target),
      cache: false,
      contentType: false,
      processData: false,
      success: response => {
        showInfoToast('Updated poster');
        // Reload image
        $('#poster-image')[0].src = `${response}?${new Date().getTime()}`;
      },
      error: response => showErrorToast({title: 'Error updating poster', response}),
      complete: () =>  setTimeout(() => $('#submit-poster-button').toggleClass('loading', false), 750),
    });
  });

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

  // Add card config form validation
  $('#card-config-form').form({
    on: 'blur',
    inline: true,
    fields: {
      font_size: {
        optional: true,
        rules: [{type: 'number', value: 'minValue[1]'}],
      },
      font_kerning: {
        optional: true,
        rules: [{type: 'number'}],
      },
      font_stroke_width: {
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

  // Prevent page reload for form submission
  $('#series-config-form, #card-config-form, #series-ids-form').on('submit', event => {
    event.preventDefault();
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

/**
 * Submit an API request clear some list values for this Series. If successful,
 * the data is also removed from the DOM.
 * @param {"season_titles" | "translations"} attribute - Name of the attribute
 * being deleted.
 */
function deleteListValues(attribute) {
  let data = {};
  if (attribute === 'season_titles') {
    data = {season_title_ranges: null, season_title_values: null};
  } else if (attribute === 'translations') {
    data = {translations: null};
  }

  $.ajax({
    type: 'PATCH',
    url: '/api/series/series/{{series.id}}',
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
    },
    error: response => showErrorToast({title: 'Error Deleting Values', response}),
  })
}

/**
 * Submit an API request to toggle the monitored status of this Series. If
 * successful, this updates the HTML of the monitored icon.
 */
function toggleMonitorStatus() {
  $.ajax({
    type: 'PUT',
    url: '/api/series/series/{{series.id}}/toggle-monitor',
    /**
     * Status changed, display toast and modify icons.
     * @param {Series} response - Modified Series config.
     */
    success: response => {
      // Show toast, toggle text and icon to show new status
      if (response.monitored) {
        showInfoToast('Started Monitoring Series');
        $('#monitor-status .icon').toggleClass('red slash', false).toggleClass('green', true);
      } else {
        showInfoToast('Stopped Monitoring Series');
        $('#monitor-status .icon').toggleClass('red slash', true).toggleClass('green', false);
      }
      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Changing Status', response}),
  });
}

/**
 * Submit an API request to completely process this Series. While processing,
 * all applicable buttons are disabled.
 */
function processSeries() {
  $('#action-buttons .button[data-action="process"] i').toggleClass('loading', true);
  $('#action-buttons .button').toggleClass('disabled', true);
  $.ajax({
    type: 'POST',
    url: '/api/series/series/{{series.id}}/process',
    success: () => showInfoToast('Started Processing Series'),
    error: response => showErrorToast({title: 'Error Processing Series', response}),
    complete: () => {
      $('#action-buttons .button[data-action="process"] i').toggleClass('loading', false);
      $('#action-buttons .button').toggleClass('disabled', false);
    }
  });
}

/**
 * Submit an API request to import the given Blueprint. While processing, the
 * card element with the given ID is marked as loading. If successful (and not
 * a Set), the page is reloaded.
 * @param {string} cardId - ID of the HTMLElement to mark as loading.
 * @param {RemoteBlueprint} blueprint - Blueprint object to import.
 * @param {boolean} [isSet] - Whether this Blueprint is associated with a Set;
 * if so, then the Blueprint is imported via ID NOT to this Series directly.
 */
function importBlueprint(cardId, blueprint, isSet=false) {
  // Indicate loading
  document.getElementById(cardId).classList.add('slow', 'double', 'blue', 'loading');

  // Get any URLs for Fonts to download
  let fontsToDownload = blueprint.json.fonts
    .filter(font => font.file_download_url)
    .map(font => font.file_download_url)
  ;

  // Submit API request to import blueprint
  if (isSet) {
    // Import Set
    $.ajax({
      type: 'POST',
      url: `/api/blueprints/import/blueprint/${blueprint.id}`,
      /**
       * Blueprint (and potentially Series) were imported. Show toast.
       * @param {Series} series - Series which the Blueprint was imported to.
       */
      success: series => {
        showInfoToast(`Blueprint Imported to ${series.name}`);
      },
      error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
      complete: document.getElementById(cardId).classList.remove('slow', 'double', 'blue', 'loading'),
    });
  } else {
    // Submit request to import directly to this Series
    $.ajax({
      type: 'PUT',
      url: `/api/blueprints/import/series/{{series.id}}/blueprint/${blueprint.id}`,
      /**
       * Blueprint imported successfully. Reload the page if there are no Fonts
       * to download. Show success toast.
       */
      success: () => {
        if (fontsToDownload.length === 0) {
          showInfoToast({title: 'Blueprint Imported', message: 'Reloading page...'});
          setTimeout(() => location.reload(), 2000);
        } else {
          showInfoToast('Blueprint Imported');
        }
      },
      error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
      complete: () => document.getElementById(cardId).classList.remove('slow', 'double', 'blue', 'loading'),
    });
  }
  
  // If any Fonts need to be downloaded, show toast
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

/**
 * Display the Blueprint Sets associated with the given Blueprint. This submits
 * an API request to query these, and then populates the appropiate element on
 * the page.
 * @param {number} blueprintId - ID of the Blueprint whose Sets to query and
 * display.
 */
function viewBlueprintSets(blueprintId) {
  $.ajax({
    type: 'GET',
    url: `/api/blueprints/sets/blueprint/${blueprintId}`,
    /** @param {RemoteBlueprintSet[]} blueprintSets */
    success: blueprintSets => {
      const blueprintTemplate = document.getElementById('blueprint-template');
      const setSection = document.getElementById('blueprint-sets');
      setSection.replaceChildren();
      setSection.style.display = 'block';

      for (let set of blueprintSets) {
        const header = document.createElement('h3');
        header.innerText = set.name; header.className = 'ui header';
        setSection.appendChild(header);

        const bpCards = document.createElement('div');
        bpCards.className = 'ui two stackable raised cards';
        setSection.appendChild(bpCards);

        for (let blueprint of set.blueprints) {
          const elementId = `blueprint-set-id${blueprint.id}`;
          blueprint.set_ids = [];
          const card = populateBlueprintCard(
            blueprintTemplate.content.cloneNode(true), blueprint, elementId
          );

          // Assign function to import button
          card.querySelector('[data-action="import"]').onclick = () => importBlueprint(elementId, blueprint, true);

          bpCards.appendChild(card);
        }
      }

      refreshTheme();
      setSection.scrollIntoView({behavior: 'smooth', block: 'start'});
    },
    error: response => showErrorToast({title: 'Error Querying Blueprint Sets', response}),
  });
}

/**
 * Submit an API request to query for all available Blueprints of this Series.
 * If successful and there are Blueprints, the card elements are added to the
 * DOM.
 */
function queryBlueprints() {
  // Get templates
  const blueprintCards = document.getElementById('blueprint-cards');
  const blueprintTemplate = document.getElementById('blueprint-template');
  if (blueprintCards === null || blueprintTemplate === null) { return; }

  // Show loading message
  $('.tab[data-tab="blueprints"] .info.message').toggleClass('hidden', false);

  // Query for Blueprints
  $.ajax({
    type: 'GET',
    url: '/api/blueprints/query/series/{{series.id}}',
    /**
     * Query successful, display available blueprints, or display a warning
     * message if none are.
     * @param {Blueprint[]} allBlueprints - List of Blueprints available for
     * this Series.
     */
    success: allBlueprints => {
      // Hide info message and disable search button
      $('.tab[data-tab="blueprints"] .info.message').toggleClass('hidden', true);
      $('.tab[data-tab="blueprints"] .button[data-action="search"]').toggleClass('disabled', true);

      // No Blueprints available, hide loading and show warning message
      if (allBlueprints === null || allBlueprints.length === 0) {
        $('.tab[data-tab="blueprints"] .warning.message').toggleClass('hidden', false);
        return;
      } 
      
      // Blueprints available, create elements
      const blueprints = allBlueprints.map((blueprint, blueprintId) => {
        // Clone template, fill out card
        let card = blueprintTemplate.content.cloneNode(true);
        card = populateBlueprintCard(card, blueprint, `blueprint-id${blueprintId}`);

        // Assign import to button
        card.querySelector('[data-action="import"]').onclick = () => importBlueprint(`blueprint-id${blueprintId}`, blueprint);

        // Toggle Set viewer on button 
        if (card.querySelector('[data-action="view-set"]')) {
          card.querySelector('[data-action="view-set"]').onclick = () => viewBlueprintSets(blueprint.id);
        }

        return card;
      });
      blueprintCards.replaceChildren(...blueprints);
      $('[data-value="file-count"]').popup({inline: true});
    },
    error: response => showErrorToast({title: 'Error Querying Blueprints', response}),
  });
}

/**
 * Submit an API request to export the Blueprint for this Series. If successful,
 * the Blueprint zip file is downloaded.
 */
function exportBlueprint() {
  $.ajax({
    type: 'GET',
    url: '/api/blueprints/export/series/{{series.id}}/zip',
    xhrFields: {responseType: 'blob'},
    success: zipBlob => {
      // Download zip file
      downloadFileBlob(`${series_full_name} Blueprint.zip`, zipBlob);
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
      if ('{{series.tvdb_id}}' !== 'None') { databaseIds.push('tvdb:{{series.tvdb_id}}'); }
      const idStr = databaseIds.join(',');

      // Get URL to pre-fill Blueprint form
      let url = `series_year={{series.year}}&database_ids=${(idStr)}`
        + `&series_name=${encodeURIComponent(series_name)}`
        + `&title=[Blueprint] ${encodeURIComponent(series_name)}`;

      // Open window for Blueprint submission
      window.open(
        'https://github.com/TitleCardMaker/Blueprints/issues/new?'
        + 'assignees=CollinHeist&labels=blueprint&template=new_blueprint.yaml'
        + `&${url}`,
        '_blank'
      );
    },
    error: response => showErrorToast({title: 'Error Exporting Blueprint', response}),
  })
}

/**
 * Submit an API request to download the given Source Image URL for the Episode
 * with the given ID. If successful, the Series file and Card data is refreshed.
 * @param {number} episodeId - ID of the Episode associated with this image.
 * @param {string} url - URL (or Base64 encoded bytes) to download.
 */
function selectTmdbImage(episodeId, url) {
  // Create psuedo form for this URL
  const form = new FormData();
  form.set('url', url);
  // Submit API request to upload this URL
  $.ajax({
    type: 'PUT',
    url: `/api/sources/episode/${episodeId}/upload`,
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Updated Source Image');
      getSourceFileData();
      getCardData();
    },
    error: response => showErrorToast({title: 'Error Updating Source Image', response}),
  });
}

/**
 * Submit an API request to download the Series logo at the specified URL.
 * @param {string} url - URL of the logo file to download.
 */
function downloadSeriesLogo(url) {
  // Create psuedo form for this URL
  const form = new FormData();
  form.set('url', url);

  // Submit API request to upload this URL
  $.ajax({
    type: 'PUT',
    url: '/api/sources/series/{{series.id}}/logo/upload',
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Downloaded Logo');
      // Update logo source to force refresh
      logo = document.getElementById('logo');
      logo.src = `/source/{{series.path_safe_name}}/logo.png?${new Date().getTime()}`;
      logo.style.display = 'block';
    },
    error: response => showErrorToast({title: 'Error Downloading Logo', response}),
  });
}

/**
 * Submit an API request to download the Series backdrop at the specified URL.
 * @param {string} url - URL of the backdrop file to download.
 */
function downloadSeriesBackdrop(url) {
  // Create psuedo form for this URL
  const form = new FormData();
  form.set('url', url);

  // Submit API request to upload this URL
  $.ajax({
    type: 'PUT',
    url: '/api/sources/series/{{series.id}}/backdrop/upload',
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Downloaded Backdrop');
      const backdrop = document.getElementById('backdrop');
      backdrop.src = `/source/{{series.path_safe_name}}/backdrop.jpg?${new Date().getTime()}`;
      backdrop.style.display = 'block';
    },
    error: response => showErrorToast({title: 'Error Downloading Backdrop', response}),
  });
}

/**
 * Submit an API request to browse the available Source Images for the given
 * Episode.
 * @param {number} episodeId - ID of the Episode whose Source Images are being
 * browsed.
 * @param {string} cardElementId - DOM Element ID of the card to mark as
 * loading.
 * @param {?number[]} episodeIds - Sequential array of Episode IDs for
 * navigating through Source Images.
 */
function browseSourceImages(episodeId, cardElementId, episodeIds) {
  document.getElementById(cardElementId).classList.add('loading');
  $.ajax({
    type: 'GET',
    url: `/api/sources/episode/${episodeId}/browse`,
    /**
     * Images available, create image elements for them, add to modal.
     * @param {ExternalSourceImage[]} images - List of Source Images for this
     * Episode.
     */
    success: images => {
      // Update modal header
      const season = $(`#${cardElementId} [data-column="season_number"]`).text();
      const episode = $(`#${cardElementId} [data-column="episode_number"]`).text();
      if (season === '' || episode === '') {
        const label = $(`#${cardElementId} [data-value="index"]`).text();
        $('#browse-tmdb-modal .header span').text(`Source Images - ${label}`);
      } else {
        $('#browse-tmdb-modal .header span').text(`Source Images - Season ${season} Episode ${episode}`);
      }

      // Create image elements
      const imageElements = images.map(({url, data, width, height, interface_type}, index) => {
        // Alternate ribbon location; choose color of ribbon based on interface
        const location = index % 2 ? 'right' : 'left';
        const color = {'Emby': 'green', 'Jellyfin': 'purple', 'Plex': 'yellow', 'TMDb': 'blue'}[interface_type];

        // Return image
        return `<a class="ui image" onclick="selectTmdbImage(${episodeId}, '${url || data}')">`
          + `<div class="ui ${color} ${location} ribbon label">`
          + (interface_type == 'TMDb' ? `${width}x${height}` : interface_type)
          + `</div><img src="${url || data}"/></a>`;
      });

      // Add to the modal
      $('#browse-tmdb-modal .content .images')[0].innerHTML = imageElements.join('');

      // Update next/previous links
      const previousEpisodeId = episodeIds[episodeIds.indexOf(episodeId) - 1];
      $('#browse-tmdb-modal [data-action="previous-episode"]')[0].onclick =
        (previousEpisodeId
        ? () => browseSourceImages(previousEpisodeId, getSourceImageElementId(previousEpisodeId), episodeIds)
        : () => showInfoToast('No previous Episode on current Page'))
      ;

      const nextEpisodeId = episodeIds[episodeIds.indexOf(episodeId) + 1];
      $('#browse-tmdb-modal [data-action="next-episode"]')[0].onclick =
        (nextEpisodeId
        ? () => browseSourceImages(nextEpisodeId, getSourceImageElementId(nextEpisodeId), episodeIds)
        : () => showInfoToast('No next Episode on current Page'))
      ;

      // Display modal
      $('#browse-tmdb-modal').modal('show');
    },
    error: response => showErrorToast({title: 'Unable to Query Images', response}),
    complete: () => document.getElementById(cardElementId).classList.remove('loading'),
  });
}

/**
 * Submit an API request to browse the available logos for this Series. If
 * successful, the relevant modal is shown.
 */
function browseLogos() {
  $.ajax({
    type: 'GET',
    url: '/api/sources/series/{{series.id}}/logo/browse',
    /**
     * Logos returned, add to modal and display.
     * @param {ExternalSourceImage[]} images - List of logos from TMDb for
     * this Series.
     */
    success: images => {
      if (images.length === 0) {
        showErrorToast({title: 'TMDb has no logos'});
      } else {
        const imageElements = images.map(({url}) => {
          return `<a class="ui image" onclick="downloadSeriesLogo('${url}')"><img src="${url}"/></a>`;
        });
        $('#browse-tmdb-logo-modal .content .images')[0].innerHTML = imageElements.join('');
        $('#browse-tmdb-modal .header span').text('Logos');
        $('#browse-tmdb-logo-modal').modal('show');
      }
    },
    error: response => showErrorToast({title: 'Unable to Query TMDb', response}),
  });
}

/**
 * Submit an API request to browse the available backdrops for this Series. If
 * successful, the relevant modal is shown.
 */
function browseBackdrops() {
  $.ajax({
    type: 'GET',
    url: `/api/sources/series/{{series.id}}/backdrop/browse`,
    /**
     * Backdrops returned, add to modal and display.
     * @param {ExternalSourceImage[]} images - List of backdrops from TMDb
     * for this Series.
     */
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
        $('#browse-tmdb-modal .header span').text('Backdrops');
        $('#browse-tmdb-modal').modal('show');
      }
    },
    error: response => showErrorToast({title: 'Unable to Query TMDb', response}),
  });
}

/**
 * Get the uploaded logo file and upload it to this Series. If the logo is an
 * image, then the API request to upload the logo is submitted. If successful,
 * then the logo `img` element is updated.
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
    type: 'PUT',
    url: '/api/sources/series/{{series.id}}/logo/upload',
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Updated Logo');
      const logo = document.querySelector('#logo');
      logo.src = `/source/{{series.path_safe_name}}/logo.png?${new Date().getTime()}`;
      logo.style.display = 'block';
    },
    error: response => showErrorToast({title: 'Error Updating Logo', response}),
  });
}

/**
 * Get the uploaded backdrop file and upload it to this Series. If the backdrop
 * is an image, then the API request to upload the file is submitted. If
 * successful, then the backdrop `img` element is updated.
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
    type: 'PUT',
    url: `/api/sources/series/{{series.id}}/backdrop/upload`,
    data: form,
    cache: false,
    contentType: false,
    processData: false,
    success: () => {
      showInfoToast('Updated Backdrop');
      const backdrop = document.getElementById('backdrop');
      backdrop.src = `/source/{{series.path_safe_name}}/backdrop.jpg?${new Date().getTime()}`;
      backdrop.style.display = 'block';
    },
    error: response => showErrorToast({title: 'Error Updating Backdrop', response}),
  });
}

/**
 * Submit an API request to download the Source Image for the given Episode.
 * This marks the given cardElementId as loading while processing.
 */
function searchEpisodeSourceImage(episodeId, sourceElementId) {
  document.getElementById(sourceElementId).classList.add('loading');
  $.ajax({
    type: 'POST',
    url: `/api/sources/episode/${episodeId}`,
    success: sourceImage => showInfoToast(sourceImage ? 'Downloaded Image' : 'Unable to Download Image'),
    error: response => showErrorToast({title: 'Error Downloading Source Image', response}),
    complete: () => document.getElementById(sourceElementId).classList.remove('loading'),
  });
}

/**
 * Submit an API request to gather source images for this Series. This disables
 * the button while processing, and if successful the File data is refreshed.
 */
function getSourceImages() {
  $('.button[data-action="download-source-images"]').toggleClass('disabled', true);
  showInfoToast('Starting to Download Source Images');
  $.ajax({
    type: 'POST',
    url: '/api/sources/series/{{series.id}}',
    success: () => getSourceFileData(),
    error: response => showErrorToast({title: 'Error Download Source Images', response}),
    complete: () => $('.button[data-action="download-source-images"]').toggleClass('disabled', false),
  });
}

/**
 * Submit an API request to initiate Card creation for this Series. This
 * disables the button while parsing, and if successful the Episode data,
 * statistics, and current Card page is refreshed.
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
    },
    error: response => showErrorToast({title: 'Error creating Title Cards', response}),
    complete: () => $('.button[data-action="create-title-cards"]').toggleClass('disabled', false),
  });
}

/**
 * Submit an API request to delete this Series' Title Cards. Series statistics
 * are re-queried if successful.
 * @param {number} interfaceId - ID of the library's interface.
 * @param {string} libraryName - Name of the library to load cards into.
 * @param {bool} [reload] - Whether to force reload the cards.
 */
function loadCards(interfaceId, libraryName, reload=false) {
  const params = new URLSearchParams({
    interface_id: interfaceId,
    library_name: libraryName,
    reload: reload,
  });

  $.ajax({
    type: 'PUT',
    url:`/api/cards/series/{{series.id}}/load/library?${params.toString()}`,
    success: () => {
      showInfoToast('Loaded Title Cards');
      getStatistics();
    },
    error: response => showErrorToast({title: 'Error Loading Title Cards', response}),
  });
}

/**
 * Submit an API request to delete this Series. If successful, this redirects to
 * the home page.
 */
function deleteSeries() {
  $.ajax({
    type: 'DELETE',
    url: '/api/series/series/{{series.id}}',
    success: () => window.location.href = '/',
    error: response => showErrorToast({title: 'Error Deleting Series', response}),
  });
}

/**
 * Get the config data for this Series' Card Form.
 * @returns {Series}
 */
function getSeriesCardConfigData() {
  /** Parse a percentage input field. */
  const parsePercentageField = value => value === '' ? null : value / 100.0;

  /** Parse some list value, converting empty lists to null */
  const parseList = value => value.length ? value : null;

  return {
    template_ids: $('#card-config-form input[name="template_ids"]').val()
      ? $('#card-config-form input[name="template_ids"]').val().split(',')
      : [],
    card_type: $('#card-config-form input[name="card_type"]').val() || null,
    font_id: $('#card-config-form input[name="font_id"]').val() || null,
    watched_style: $('#card-config-form input[name="watched_style"]').val() || null,
    unwatched_style: $('#card-config-form input[name="unwatched_style"]').val() || null,
    font_color: $('#card-config-form input[name="font_color"]').val() || null,
    font_title_case: $('#card-config-form input[name="font_title_case"]').val() || null,
    font_size: parsePercentageField($('#card-config-form input[name="font_size"]').val()),
    font_kerning: parsePercentageField($('#card-config-form input[name="font_kerning"]').val()),
    font_stroke_width: parsePercentageField($('#card-config-form input[name="font_stroke_width"]').val()),
    font_interline_spacing: $('#card-config-form input[name="font_interline_spacing"]').val() || null,
    font_interword_spacing: $('#card-config-form input[name="font_interword_spacing"]').val() || null,
    font_vertical_shift: $('#card-config-form input[name="font_vertical_shift"]').val() || null,
    hide_season_text: $('#card-config-form input[name="hide_season_text"]').val() || null,
    season_title_ranges: parseList(
        Array.from(document.querySelectorAll('#card-config-form input[name="season_title_ranges"]')).map(input => input.value)
      ),
    season_title_values: parseList(
        Array.from(document.querySelectorAll('#card-config-form input[name="season_title_values"]')).map(input => input.value)
      ),
    hide_episode_text: $('#card-config-form input[name="hide_episode_text"]').val() || null,
    episode_text_format: $('#card-config-form input[name="episode_text_format"]').val() || null,
    translations: parseList(
        Array.from(document.querySelectorAll('#card-config-form input[name="language_code"]')).map((input, index) => {
          return {
            language_code: input.value,
            data_key: document.querySelectorAll('#card-config-form input[name="data_key"]')[index].value,
          };
        })
      ),
    extra_keys: parseList(
        $('#card-config-form section[aria-label="extras"] input').map(function() {
          if ($(this).val() !== '') { 
            return $(this).attr('name'); 
          }
        }).get()
      ),
    extra_values: parseList(
        $('#card-config-form section[aria-label="extras"] input').map(function() {
          if ($(this).val() !== '') {
            return $(this).val(); 
          }
        }).get(),
      ),
  }
}

/**
 * 
 * @param {"card" | "options" | "ids"} formName 
 */
function updateSeries(formName) {
  // Parse card config data
  let data = {};
  if (formName === 'card') {
    // Validate form
    if (!$('#card-config-form').form('is valid')) { return; }
    data = getSeriesCardConfigData();
  }
  // Parse options data
  else if (formName === 'options') {
    data = {
      libraries: $('#series-config-form input[name="libraries"]').val()
        ? $('#series-config-form input[name="libraries"]').val().split(',').map(libraryStr => {
            const libraryData = libraryStr.split('::');
            return {
              interface: libraryData[0],
              interface_id: libraryData[1],
              name: libraryData[2],
            };
          })
        : [],
      data_source_id: $('#series-config-form input[name="data_source_id"]').val() || null,
      match_titles: $('#series-config-form input[name="match_titles"]').is(':checked'),
      auto_split_title: $('#series-config-form input[name="auto_split_title"]').is(':checked'),
      sync_specials: $('#series-config-form input[name="sync_specials"]').val() || null,
      skip_localized_images: $('#series-config-form input[name="skip_localized_images"]').val() || null,
      directory: $('#series-config-form input[name="directory"]').val() || null,
      card_filename_format: $('#series-config-form input[name="card_filename_format"]').val() || null,
    };
  } else if (formName === 'ids') {
    data = {
      emby_id: $('#series-ids-form input[name="emby_id"]').val() || null,
      imdb_id: $('#series-ids-form input[name="imdb_id"]').val() || null,
      jellyfin_id: $('#series-ids-form input[name="jellyfinid"]').val() || null,
      sonarr_id: $('#series-ids-form input[name="sonarr_id"]').val() || null,
      tmdb_id: $('#series-ids-form input[name="tmdb_id"]').val() || null,
      tvdb_id: $('#series-ids-form input[name="tvdb_id"]').val() || null,
      tvrage_id: $('#series-ids-form input[name="tvrage_id"]').val() || null,
    };
  }

  // Submit API request
  $('#submit-changes').toggleClass('loading', true); // Mark buttons as loading
  $.ajax({
    type: 'PATCH',
    url: '/api/series/series/{{series.id}}',
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: () => showInfoToast('Updated Series'),
    error: response => showErrorToast({title: 'Error Updating Series', response}),
    complete: () => $('#submit-changes').toggleClass('loading', false),
  });
}

/**
 * Submit an API request to delete this Series' Title Cards. Series
 * statistics are re-queried after calling this.
 * @param {function} [onSuccess] - Function to call if the API request is
 * successful.
 */
function deleteTitleCards(onSuccess) {
  $.ajax({
    type: 'DELETE',
    url: '/api/cards/series/{{series.id}}',
    success: response => {
      showInfoToast(`Deleted ${response.deleted} Cards`);
      if (onSuccess !== undefined) { onSuccess(); }
      getCardData();
    },
    error: response => showErrorToast({title: 'Error Deleting Title Cards', response}),
    complete: () => getStatistics(),
  });
}

/**
 * Submit an API request to add/create the new Episode defined in the given
 * event's target.
 * @param {Event} event - Triggering Event for the Form submission of the new
 * Episode.
 * @param {HTMLFormElement} event.target - Target of the event; i.e. the new
 * Episode Form.
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
    /**
     * Episode created successfully, show toast and re-query data and statistics
     * @param {Episode} episode - Newly created Episode.
     */
    success: episode => {
      const {season_number, episode_number} = episode;
      showInfoToast(`Created Season ${season_number} Episode ${episode_number}`);
      getEpisodeData();
      getStatistics();
    },
    error: response => showErrorToast({title: 'Error Creating Episode', response}),
  });
}

/**
 * Submit an API request to delete all Episodes of this Series. If successful,
 * then the Episode, file, and statistics data are re-queried.
 */
function deleteAllEpisodes() {
  $.ajax({
    type: 'DELETE',
    url: '/api/episodes/series/{{series.id}}',
    /**
     * Episodes deleted, show toast and re-fresh Episode and File data.
     * @param {number[]} episodeIds - IDs of the Episodes which were deleted.
     */
    success: episodeIds => {
      showInfoToast(`Deleted ${episodeIds.length} Episodes`);
      $('#episode-data-table tr').remove();
      getSourceFileData();
      getStatistics();
    },
    error: response => showErrorToast({title: 'Error Deleting Episodes', response}),
  });
}

/**
 * Submit an API request to delete the Episode with the given ID. If successful,
 * then the statistics are re-queried and the Episode and file associated with
 * this Episode are removed from the DOM.
 * @param {number} id - Episode ID of the Episode to delete.
 */
function deleteEpisode(id) {
  $.ajax({
    type: 'DELETE',
    url: `/api/episodes/episode/${id}`,
    success: () => {
      showInfoToast('Deleted Episode');
      // Remove this Episode's data row and file
      $(`#${getEpisodeElementId(id)}`).transition({animation: 'slide down', duration: 1000});
      setTimeout(() => document.getElementById(getEpisodeElementId(id)).remove(), 1000);
      document.getElementById(getSourceImageElementId(id)).remove();
      getStatistics();
      getCardData();
      getSourceFileData();
    },
    error: response => showErrorToast({title: 'Error Deleting Episode', response}),
  });
}

/**
 * Submit an API request to navigate to the next or previous Series. If
 * successful (and there is a Series to navigate to), then the page is
 * redirected. If successful but there is no next/previous Series, the
 * appropriate nav button is disabled.
 * @param {"next" | "previous"} next_or_previous - Where to navigate the page.
 */
function navigateSeries(next_or_previous) {
  $.ajax({
    type: 'GET',
    url: `/api/series/series/{{series.id}}/${next_or_previous}`,
    /**
     * There is a next/previous Series, redirect the current page.
     * @param {?Series} series - Series to navigate to.
     */
    success: series => {
      // No Series to navigate, disable button
      if (series === null) {
        $(`i[data-action="${next_or_previous}-series"]`).toggleClass('disabled', true);
      } else {
        window.location.href = `/series/${series.id}${window.location.hash}`;
      }
    },
    error: response => showErrorToast({title: 'Navigation Failed', response}),
  });
}

/**
 * Submit an API request to remove the TCM/PMM labels from this Series in Plex.
 * @param {number} interface_id - ID of the library's interface.
 * @param {string} library_name - Name of the library to load cards into.
 */
function removePlexLabels(interface_id, library_name) {  
  const params = new URLSearchParams({interface_id, library_name}).toString();
  $.ajax({
    type: 'DELETE',
    url: `/api/series/series/{{series.id}}/plex-labels/library?${params}`,
    success: () => showInfoToast('Removed Labels'),
    error: response => showErrorToast({title: 'Error Removing Labels', response}),
  });
}

/** @type {File[]} */
let pendingFiles = [];

/** Display the Card upload modal. */
function showCardUpload() {
  $('#upload-cards-modal table').css('display', 'none');
  $('#upload-cards-modal table tbody tr').remove();
  $('#upload-cards-modal').modal('show');
  pendingFiles = [];
}

/**
 * Handler function to parse drag-n-dropped Cards in the upload Card dialog.
 * This parses the filenames of the uploads for season and episode numbers, and
 * then adds that data to the modal table.
 * @param {DragEvent} event - Event of the uploaded files.
 */
function dropHandler(event) {
  // Prevent default behavior (Prevent file from being opened)
  event.preventDefault();

  /**
   * Parse the season and episode number from the given string (filename).
   * @param {string} name - Name of the file being parsed for indices.
   * @returns {?[number, number]} Array of the season and episode number parsed
   * from the given name.
   */
  const parseFilename = (name) => name.match(/.*s(\d+).*e(\d+)/i)?.slice(1).map(Number);

  /**
   * 
   * @param {File} file - File to create an entry out of.
   */
  const newFile = (file) => {
    // Fill out row
    const table = document.querySelector('#upload-cards-modal table tbody');
    const newRow = document.getElementById('file-upload-template').content.cloneNode(true);

    // Populate file name; when clicked, remove from table and file list
    newRow.querySelector('[data-row="file"] a').innerText = file.name;
    newRow.querySelector('[data-row="file"] a').onclick = () => {
      pendingFiles = pendingFiles.filter(thisFile => thisFile.name !== file.name);
      $(`#upload-cards-modal tr[data-filename="${file.name}"]`).remove();
    }
    // Add file name to dataset so CSS query works
    newRow.querySelector('tr').dataset.filename = file.name;

    // Try and parse season and episode indices from filename
    const indices = parseFilename(file.name);
    if (indices) {
      newRow.querySelector('[data-row="season"]').innerText = indices[0];
      newRow.querySelector('[data-row="episode"]').innerText = indices[1];
      pendingFiles.push(file);
    } else {
      // Cannot parse; mark row as error
      newRow.querySelector('tr').className = 'error';
      newRow.querySelector('[data-row="season"]').innerText = 'Cannot Determine';
      newRow.querySelector('[data-row="episode"]').innerText = 'Cannot Determine';
    }
    table.appendChild(newRow);
  }
  $('#upload-cards-modal table').css('display', 'table');

  // Iterate through all uploaded files, add a table row for each valid upload
  [...event.dataTransfer.items || event.dataTransfer.files].forEach((item) => {
    if (item.kind === 'file' && item.type !== '') {
      newFile(item.getAsFile() || item);
    }
  });
  refreshTheme();
}

/**
 * Submit an API request to upload and import the cards which are currently
 * loaded. After the request is finished, all series-data is re-queried.
 * @param {boolean} setTextless - Whether to set the Episodes as textless on
 * import.
 */
function uploadCards(setTextless=false) {
  // No files uploaded, exit
  if (pendingFiles.length === 0) {
    showInfoToast('No Cards to Upload');
    return;
  }

  // Add files to FormData object
  const f = new FormData();
  pendingFiles.forEach(file => f.append('cards', file));

  // Submit API request
  $.ajax({
    type: 'POST',
    url: `/api/import/series/{{series.id}}/cards/files?textless=${setTextless}`,
    data: f,
    cache: false,
    contentType: false,
    processData: false,
    /** Cards uploaded and imported. Show success toast. */
    success: () => showInfoToast('Title Cards Uploaded and Imported'),
    error: response => showErrorToast({title: 'Error Uploading Cards', response}),
    /** Re-query statistics, card data, and file data */
    complete: () => {
      getStatistics();
      getCardData();
      getSourceFileData();
    }
  });
}

function getEpisodeOverviews() {
  const disableDropdown = () => {
    $('.dropdown[data-value="episode_id"]').dropdown({
      values: [],
      placeholder: 'No Episodes'
    });
    $('#preview-episode-dropdown').toggleClass('disabled', true);
  };

  // Custom comparison function
  function compareEpisodes(a, b) {
    if (a.season_number === 0 && b.season_number !== 0) {
      // Season 0 comes after all other seasons
      return 1;
    } else if (a.season_number !== 0 && b.season_number === 0) {
      // All other seasons come before season 0
      return -1;
    } else if (a.season_number !== b.season_number) {
      // Sort by season number
      return a.season_number - b.season_number; 
    } else {
      // If seasons are equal, sort by episode number
      return a.episode_number - b.episode_number; 
    }
  }

  $.ajax({
    type: 'GET',
    url: '/api/episodes/series/{{series.id}}/overview?size=500',
    success: overviews => {
      if (overviews.items.length === 0) {
        disableDropdown();
      } else {
        const firstEpisodeId = overviews.items.sort(compareEpisodes)[0].id;
        $('.dropdown[data-value="episode_id"]').dropdown({
          onChange: refreshPreview,
          values: overviews.items.map(({id, season_number, episode_number}) => {
            return {
              name: `Season ${season_number} Episode ${episode_number}`,
              value: id,
              selected: id === firstEpisodeId,
            };
          }),
        });
      }
    },
    error: response => {
      showErrorToast({title: 'Error Querying Episodes', response});
      disableDropdown();
    },
  });
}

function refreshPreview() {
  // Get Episode ID to generate preview of
  const episodeId = $('#preview-episode-dropdown input[name="episode_id"]').val();
  if (episodeId === undefined) {
    showErrorToast({title: 'No Episode to display Preview of'});
    return;
  }

  // Get preview data
  const data = {
    update_episode: getUpdateEpisodeObject(episodeId),
    update_series: getSeriesCardConfigData(),
  }

  // Mark dropdown as loading
  $('#preview-episode-dropdown .dropdown').toggleClass('loading', true),

  // Submit API request
  $.ajax({
    type: 'POST',
    url: `/api/cards/preview/episode/${episodeId}`,
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: preview_uri => {
      document.getElementById('live-preview').src = `${preview_uri}?${new Date().getTime()}`;
    },
    error: response => showErrorToast({title: 'Error Updating Preview', response}),
    complete: () => $('#preview-episode-dropdown .dropdown').toggleClass('loading', false),
  });
}
