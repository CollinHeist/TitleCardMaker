{% if False %}
import {
  AvailableTemplate, EpisodeDataSourceToggle, ImageSourceToggle,
  UpdatePreferences,
} from './.types.js';
{% endif %}

// Get all Connection data
let allConnections;
async function getAllConnections() {
  allConnections = await fetch('/api/connection/all').then(resp => resp.json());
}

// Get all available Templates
/** @type {AvailableTemplate[]} */
let allTemplates = [];
/**
 * Submit an API request to get all the available Templates, initializing the
 * dropdowns with these values (and a placeholder).
 */
function getTemplates() {
  $.ajax({
    type: 'GET',
    url: '/api/available/templates',
    /**
     * Initialize the Template ID dropdowns with the given values.
     * @param {AvailableTemplate[]} availableTemplates - All available
     * Templates.
     */
    success: availableTemplates => {
      allTemplates = availableTemplates;
      $('.dropdown[data-value="default_templates"]').dropdown({
        placeholder: 'None',
        values: getActiveTemplates({{preferences.default_templates}}, availableTemplates),
      });
    },
    error: response => showErrorToast({'title': 'Error Querying Templates', response}),
  })
}

/**
 * Get the global Episode data source and initialize the dropdown with all
 * valid Connections.
 */
function getEpisodeDataSources() {
  $.ajax({
    type: 'GET',
    url: '/api/settings/episode-data-source',
    /**
     * Episode Data Sources returned, update dropdown.
     * @param {EpisodeDataSourceToggle} sources - Selected Episode Data Sources.
     */
    success: sources => {
      $('.dropdown[data-value="episode_data_source"]').dropdown({
        values: sources.map(({interface_id, name, selected}) => {
          return {name, value: interface_id, selected};
        })
      });
    }, error: response => showErrorToast({title: 'Error Querying Episode Data Sources', response}),
  });  
}

/**
 * Get the global image source priority and initialize the dropdown with all
 * valid Connections.
 */
function getImageSourcePriority() {
  $.ajax({
    type: 'GET',
    url: '/api/settings/image-source-priority',
    /**
     * Image source priority returned.
     * @param {ImageSourceToggle} sources - Globally enabled image sources.
     */
    success: sources => {
      $('.dropdown[data-value="image_source_priority"]').dropdown({
        values: sources.map(({interface, interface_id, selected}) => {
          // Match this interface to a defined Connection (to get the name)
          for (let {id, name} of allConnections) {
            if (id === interface_id) {
              return {name, value: id, selected};
            }
          }
          return {name: interface, value: interface_id, selected};
        }),
      });
    },
    error: response => showErrorToast({title: 'Error Querying Image Source Priority', response}),
  });  
}

async function initCardTypeDropdowns() {
  // Load filtered types into default card type dropdown
  const allCards = await loadCardTypes({
    element: '#excluded-card-types',
    isSelected: (identifier) => {{preferences.excluded_card_types|safe}}.includes(identifier),
    showExcluded: true,
    dropdownArgs: {
      useLabels: false,
      placeholder: 'None',
    }
  });
  // Load default card type dropdown
  loadCardTypes({
    element: '#default-card-type',
    isSelected: (identifier) => identifier === '{{preferences.default_card_type}}',
    showExcluded: false,
    dropdownArgs: {
      onChange: (value, text, $selectedItem) => {
        $('#title-card-image')
          .fadeTo(250, 0, () => updatePreviewTitleCard(allCards, value))
          .fadeTo(250, 1);
      }
    }
  });
  return allCards;
}

/*
 * Update the preview title card for the given type. This updates all
 * elements of the preview card.
 */
function updatePreviewTitleCard(allCards, previewCardType) {
  for (let {name, identifier, example, creators, supports_custom_fonts,
            supports_custom_seasons, description} of allCards) {
    if (identifier == previewCardType) {
      // Update all attributes of the title card element for the given card
      $('#title-card-image')[0].src = example; 
      $('#title-card-name')[0].innerText = name;//`${name} Title Card`;
      $('#title-card-creators')[0].innerText = creators.join(', ');
      $('#title-card-font-support')[0].firstChild.className = supports_custom_fonts ? 'green check icon' : 'red times icon';
      $('#title-card-season-support')[0].firstChild.className = supports_custom_seasons ? 'green check icon' : 'red times icon';
      $('#title-card-description')[0].innerHTML = '<p>' + description.join('</p><p>') + '</p>';
      break;
    }
  }
}

/**
 * Submit an API request to set/update all global settings. This parses the
 * settings form into an object, and then submits a PATCH request. A toast is
 * shown with the results of the request.
 */
function updateGlobalSettings() {
  // Mark button as loading
  $('#save-changes').toggleClass('loading', true);

  // Parse extras
  const extras = {};
  $('section[aria-label="extras"] .tab').each(function() {
    const cardType = $(this).attr('data-tab'); // Current card type
    const currentExtras = {}; // Currently non-blank extras

    // Parse all non-blank extras for this type
    $(this).find('input').each(function() {
      if ($(this).val() !== '') {
        currentExtras[$(this).attr('name')] = $(this).val();
      }
    });

    // If current card type has extras, add to object
    if (Object.keys(currentExtras).length > 0) { extras[cardType] = currentExtras; }
  });

  const parseListString = (val) => val === '' ? [] : val.split(',');

  // Parse all settings data into one update object
  /** @type {UpdatePreferences} */
  const data = {
    // Root Folders
    card_directory: $('input[name="card_directory"]').val(),
    source_directory: $('input[name="source_directory"]').val(),
    completely_delete_series: $('input[name="completely_delete_series"]').is(':checked'),
    // Series and Episode Data
    episode_data_source: $('input[name="episode_data_source"]').val(),
    image_source_priority: $('input[name="image_source_priority"]').val().split(','),
    sync_specials: $('input[name="sync_specials"]').is(':checked'),
    delete_missing_episodes: $('input[name="delete_missing_episodes"]').is(':checked'),
    delete_unsynced_series: $('input[name="delete_unsynced_series"]').is(':checked'),
    // Title Cards
    default_card_type: $('input[name="default_card_type"]').val(),
    excluded_card_types: parseListString($('input[name="excluded_card_types"]').val()),
    default_watched_style: $('input[name="default_watched_style"]').val() || '{{preferences.default_watched_style}}',
    default_unwatched_style: $('input[name="default_unwatched_style"]').val() || '{{preferences.default_unwatched_style}}',
    default_templates: parseListString($('input[name="default_templates"]').val()),
    card_width: $('input[name="card_width"]').val(),
    card_height: $('input[name="card_height"]').val(),
    card_quality: $('.slider[data-value="card_quality"]').slider('get value'),
    global_extras: extras,
    // File naming
    card_extension: $('input[name="card_extension"]').val(),
    card_filename_format: $('input[name="card_filename_format"]').val(),
    specials_folder_format: $('input[name="specials_folder_format"]').val(),
    season_folder_format: $('input[name="season_folder_format"]').val(),
    library_unique_cards: $('input[name="library_unique_cards"]').is(':checked'),
    // Web interface
    home_page_size: $('input[name="home_page_size"]').val(),
    episode_data_page_size: $('input[name="episode_data_page_size"]').val(),
    home_page_table_view: $('input[name="home_page_table_view"]').is(':checked'),
    sources_as_table: $('input[name="sources_as_table"]').is(':checked'),
    simplified_data_table: $('input[name="simplified_data_table"]').is(':checked'),
    stylize_unmonitored_posters: $('input[name="stylize_unmonitored_posters"]').is(':checked'),
    colorblind_mode: $('input[name="colorblind_mode"]').is(':checked'),
    reduced_animations: $('input[name="reduced_animations"]').is(':checked'),
    interactive_card_previews: $('input[name="interactive_card_previews"]').is(':checked'),
  };

  // Submit API request
  $.ajax({
    type: 'PATCH',
    url: '/api/settings/update',
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: () => showInfoToast('Updated Settings'),
    error: response => showErrorToast({title: 'Unable to Update Settngs', response}),
    complete: () => $('#save-changes').toggleClass('loading', false),
  });
}

/** @type {number} Global card quality */
const cardQuality = {{preferences.card_quality}};

/**
 * Initialie the card quality slider. This makes the slider interactible,
 * adds labels, sets the start value and color to the current global value.
 */
function initializeCardQualitySlider() {
  /**
   * Update the color of the card quality slider based on the given value.
   * @param {number} newValue - New card quality.
   */
  const updateSliderColor = (newValue) => {
    $('.slider[data-value="card_quality"]')
      .toggleClass('blue', newValue > 80)
      .toggleClass('yellow', newValue > 70 && newValue <= 80)
      .toggleClass('orange', newValue > 50 && newValue <= 70)
      .toggleClass('red', newValue <= 50)
    ;
  }

  $('.slider[data-value="card_quality"]').slider({
    restrictedLabels: [10, 20, 30, 40, 50, 60, 70, 80, 90],
    autoAdjustLabels: false,
    showThumbTooltip: true,
    min: 1,
    max: 100,
    start: cardQuality,
    onMove: updateSliderColor,
  });

  // Initialize starting color
  updateSliderColor(cardQuality);
}

async function initAll() {
  // Enable dropdowns, checkboxes, etc.
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
  initializeCardQualitySlider();

  await getAllConnections();
  getEpisodeDataSources();
  getTemplates();
  getImageSourcePriority();

  // Global extras
  await initializeExtras(
    {% if preferences.global_extras %}
      {{preferences.global_extras|safe}},
    {% else %}
      [],
    {% endif %}
    '{{preferences.default_card_type}}',
    'section[aria-label="extras"]',
    document.getElementById('extra-input-template'),
    true,
    3,
  );
  refreshTheme();
  $('.ui.accordion').accordion();

  // Show extension warning based on starting extension
  let currentExtension = $('#card-extension-input').val();
  $('#card-extension-warning').toggleClass(
    'visible', currentExtension === '.png' || currentExtension === '.tiff'
  );

  // Launch style modal when helper buttons are clicked
  $('#style-modal')
    .modal('attach events', '.button[data-value="style-button"]', 'show')
    .modal('setting', 'transition', 'fade up')
    .modal({blurring: true});

  // Toggle card extension warning on input
  $('#card-extension')
    .dropdown()
    .dropdown(
      'setting',
      'onChange', function(value, text) {
        $('#card-extension-warning').toggleClass(
          'visible', value === '.png' || value === '.tiff'
        );
      }
    );
  
  $('#settings-form')
    // Add form validation
    .form({
      on: 'blur',
      // inline : true,
      fields: {
        card_directory: {
          rules: [{type: 'empty', prompt: 'Card directory is required'}]
        },
        source_directory: {
          rules: [{type: 'empty', prompt: 'Source directory is required'}]
        },
        episode_data_source: {
          rules: [{type: 'empty', prompt: 'Episode Data Source is required'}]
        },
        image_source_priority: {
          rules: [{type: 'minCount[1]', prompt: 'Select at least one Connection'}]
        },
        card_width: {
          rules: [{type: 'integer[1..]', prompt: 'Dimension must be a positive number'}]
        },
        card_height: {
          rules: [{type: 'integer[1..]', prompt: 'Dimension must be a positive number'}]
        },
        card_filename_format: {
          rules: [{type: 'minLength[1]', prompt: 'Filename format is required'}]
        },
        home_page_size: {
          rules: [{type: 'integer[1..999]', prompt: 'Page size must be between 1 and 999'}],
        },
        episode_data_page_size: {
          rules: [{type: 'integer[1..999]', prompt: 'Page size must be between 1 and 999'}],
        },
      },
    })
    // On form submission, submit API request to change settings
    .on('submit', (event) => {
      event.preventDefault();
      if (!$('#settings-form').form('is valid')) { return; }
      updateGlobalSettings();
    });

  let allCards = [];
  (async () => {
    allCards = await initCardTypeDropdowns();
    updatePreviewTitleCard(allCards, '{{preferences.default_card_type}}');
  })()
}
