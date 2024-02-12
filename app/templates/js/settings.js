{% if False %}
import {AvailableTemplate, EpisodeDataSourceToggle, ImageSourceToggle} from './.types.js';
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

async function initAll() {
  // Enable dropdowns, checkboxes, etc.
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
  $('.slider[data-value="card_quality"]').slider({
    restrictedLabels: [10, 20, 30, 40, 50, 60, 70, 80, 90],
    autoAdjustLabels: false,
    showThumbTooltip: true,
    min: 1,
    max: 100,
    start: {{preferences.card_quality}},
  });

  await getAllConnections();
  getEpisodeDataSources();
  getTemplates();
  getImageSourcePriority();

  // Filled in later
  let allCards = [];

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
      inline : true,
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
      $('#save-changes').toggleClass('loading', true);
      // Prep form
      let form = new FormData(event.target);

      // Parse comma-separated fields
      const imageSourcePriority = form.get('image_source_priority').split(',');
      form.delete('image_source_priority');
      const excludedCardTypes = form.get('excluded_card_types') === ''
        ? []
        : form.get('excluded_card_types').split(',');
      form.delete('excluded_card_types');
      const defaultTemplates = form.get('default_templates') === ''
        ? []
        : form.get('default_templates').split(',');
      form.delete('default_templates');

      // Delete blank values
      for (const [key, value] of [...form.entries()]) {
        if (value === '') { form.delete(key); }
      }
      // Add checkbox status as true/false
      $.each($("#settings-form").find('input[type=checkbox]'), (key, val) => {
        form.append($(val).attr('name'), $(val).is(':checked'))
      });

      $.ajax({
        type: 'PATCH',
        url: '/api/settings/update',
        data: JSON.stringify({
          ...Object.fromEntries(form),
          image_source_priority: imageSourcePriority,
          excluded_card_types: excludedCardTypes,
          default_templates: defaultTemplates,
          card_quality: $('.slider[data-value="card_quality"]').slider('get value'),
        }),
        contentType: 'application/json',
        success: () => showInfoToast('Updated Settings'),
        error: response => showErrorToast({title: 'Unable to Update Settngs', response}),
        complete: () => $('#save-changes').toggleClass('loading', false),
      });
    });

  (async () => {
    allCards = await initCardTypeDropdowns();
    updatePreviewTitleCard(allCards, '{{preferences.default_card_type}}');
  })()
}