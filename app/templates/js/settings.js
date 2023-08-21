// Get the latest episode data sources, update dropdown
async function getEpisodeDataSources() {
  const sources = await fetch('/api/available/episode-data-sources').then(resp => resp.json());
  $('#episode-data-source').dropdown({
    values: sources.map(({name, selected}) => {
      return {name: name, value: name, selected: selected};
    })
  });
}

// Get the latest image source priority, update dropdown
async function getImageSourcePriority() {
  const sources = await fetch('/api/settings/image-source-priority').then(resp => resp.json());
  $('#image-source-priority').dropdown({
    values: sources.map(({name, selected}) => {
      return {name: name, value: name, selected: selected};
    })
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
    }
  });
  // Load default card type dropdown
  loadCardTypes({
    element: '#default-card-type',
    isSelected: (identifier) => identifier === '{{preferences.default_card_type}}',
    showExcluded: false,
    // Dropdown args
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

// Function to update the preview title card
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

function initAll() {
  getEpisodeDataSources();
  getImageSourcePriority();

  // Filled in later
  let allCards = [];

  // Enable dropdowns, checkboxes, etc.
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
  $('.message .close').on('click', function() {$(this)
    .closest('.message')
    .transition('fade');
  });

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
          rules: [{type: 'minLength[1]', prompt: 'Card directory is required'}]
        }, source_directory: {
          rules: [{type: 'minLength[1]', prompt: 'Source directory is required'}]
        }, image_source_priority: {
          rules: [{type: 'minCount[1]', prompt: 'Select at least one source'}]
        }, card_width: {
          rules: [{type: 'integer[1..]', prompt: 'Dimension must be a positive number'}]
        }, card_height: {
          rules: [{type: 'integer[1..]', prompt: 'Dimension must be a positive number'}]
        }, card_filename_format: {
          rules: [{type: 'minLength[1]', prompt: 'Filename format is required'}]
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
      const imageSourcePriority = form.get('image_source_priority') === '' ? [] : form.get('image_source_priority').split(',');
      const excludedCardTypes = (form.get('excluded_card_types') === '') ? [] : form.get('excluded_card_types').split(',');
      form.delete('image_source_priority'); form.delete('excluded_card_types');
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