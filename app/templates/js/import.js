async function initSeriesImport() {
  // Extension selector
  $('.dropdown[data-value="image_extension"]').dropdown({
    values: [
      {name: '.jpg',  value: '.jpg',  selected: '.jpg' === '{{preferences.card_extension}}'},
      {name: '.jpeg', value: '.jpeg', selected: '.jpeg' === '{{preferences.card_extension}}'},
      {name: '.png',  value: '.png',  selected: '.png' === '{{preferences.card_extension}}'},
      {name: '.tiff', value: '.tiff', selected: '.tiff' === '{{preferences.card_extension}}'},
      {name: '.gif',  value: '.gif',  selected: '.gif' === '{{preferences.card_extension}}'},
      {name: '.webp', value: '.webp', selected: '.webp' === '{{preferences.card_extension}}'},
    ],
  });
  // Series selector
  $('#import-cards-form .dropdown[data-value="series_id"]').toggleClass('loading', true);
  const allSeries = await fetch('/api/available/series').then(resp => resp.json());
  let seriesMap = {};
  for (series of allSeries) { seriesMap[series.id] = series; }
  $('.dropdown[data-value="series_id"]').dropdown({
    ignoreDiacritics: true,
    sortSelect: true,
    placeholder: 'Select 1+ Series',
    useLabels: false,
    values: [
        // All series toggle
        {name: 'Select All Series', actionable: true},
        {name: 'Series', type: 'header'},
        // All series
        ...allSeries.sort((a, b) => a.name.localeCompare(b.name)).map(series => {
          return {
            name: series.name,
            value: series.id,
            text: series.name,
            description: series.year,
            sortSelect: true,
            descriptionVertical: true,
          };
        }),
      ],
    onChange: (value, text, $selectedItem) => {
        // Disable directory field if multiple series are selected
        if (value.includes(',')) {
          $('.field[data-value="directory"]').toggleClass('disabled', true);
        // Single series selected, enable field and update with series directory
        } else {
          $('.field[data-value="directory"]').toggleClass('disabled', false);
          if (seriesMap[value] === undefined || seriesMap[value].directory === null) {
            $('input[name="directory"]')[0].value = '';
          } else {
            $('input[name="directory"]')[0].value = seriesMap[value].directory;
          }
        }
      },
    onActionable: (value, text, $selected) => {
        $('.dropdown[data-value="series_id"]').dropdown({
          ignoreDiacritics: true,
          sortSelect: true,
          placeholder: 'Select 1+ Series',
          useLabels: false,
          values: allSeries.sort((a, b) => a.name.localeCompare(b.name)).map(series => {
            return {
              name: series.name,
              value: series.id,
              selected: true,
              text: series.name,
              description: series.year,
              sortSelect: true,
              descriptionVertical: true,
            };
          }),
        });
      },
  });
  $('#import-cards-form .dropdown[data-value="series_id"]').toggleClass('loading', false);
}

async function importSeriesForm(form) {
  // Determine which queries to submit
  if ($('#series-form .checkbox[data-value="fonts"]').checkbox('is checked')) {
    await submitYamlForm({
      url: '/api/import/fonts',
      data: Object.fromEntries(form),
      formId: '#series-form',
      name: 'Fonts',
      successMessage: newFonts => `Created ${newFonts.length} Custom Fonts`,
    });
  }
  if ($('#series-form .checkbox[data-value="templates"]').checkbox('is checked')) {
    await submitYamlForm({
      url: '/api/import/templates',
      data: Object.fromEntries(form),
      formId: '#series-form',
      name: 'Templates',
      successMessage: newTemplates => `Created ${newTemplates.length} Templates`,
    });
  }
  if ($('#series-form .checkbox[data-value="series"]').checkbox('is checked')) {
    await submitYamlForm({
      url: '/api/import/series',
      data: Object.fromEntries(form),
      formId: '#series-form',
      name: 'Series',
      successMessage: newSeries => `Created ${newSeries.length} Series`,
    });
  }
}

async function initAll() {
  initSeriesImport();

  $('.ui.checkbox').checkbox();
  $('.ui.dropdown').dropdown();

  // Import cards form submission
  $('#import-cards-form').on('submit', event => {
    // Prevent page reload
    event.preventDefault();
    importSeries();
  });

  // Series YAML form submission
  $('#series-form').on('submit', event => {
    // Prevent page reload
    event.preventDefault();
    const form = new FormData(event.target);

    // Turn off error status of the form
    $('#series-form').toggleClass('error', false);

    importSeriesForm(form);
  });
}

/**
 * Submit an API request to load the Cards for the Series with the given ID.
 * @param {number} seriesId - ID of the Series whose Cards are being loaded.
 */
function loadCards(seriesId) {
  // Get associated Media Server to load cards into, default Plex
  $.ajax({
    type: 'POST',
    url: `/api/series/${seriesId}/load/all`,
    success: () => showInfoToast('Loaded Title Cards'),
    error: response => showErrorToast({title: 'Error loading Title Cards', response}),
  });
}

/**
 * Convert the given `data` object into a `FormData` object. Modifies `formData`
 * in-place. Stolen from https://stackoverflow.com/a/42483509/8706916.
 * @param {FormData} formData - Form being populated.
 * @param {Object} data - Arbitrary data used to populate `formData`.
 * @param {?string} parentKey - Parent key to store the data in, used for
 * recursive object conversion.
 */
function _buildFormData(formData, data, parentKey) {
  if (data && typeof data === 'object' && !(data instanceof Date)
      && !(data instanceof File) && !(data instanceof Blob)) {
    Object.keys(data).forEach(key => {
      _buildFormData(formData, data[key], parentKey ? `${parentKey}[${key}]` : key);
    });
  } else {
    const value = data == null ? '' : data;

    formData.append(parentKey, value);
  }
}

function importSeries() {
  // Get associated Series
  let seriesIds = $('input[name="series_id"]')[0].value;
  if (seriesIds === '') {
    $('.dropdown[data-value="series_id"]').toggleClass('error', true);
    return;
  }
  $('.dropdown[data-value="series_id"]').toggleClass('error', false);
  seriesIds = seriesIds.split(',').map(id => parseInt(id));

  // Data for request
  const directoryValue = $('input[name="directory"]')[0].value
  let rawData = {
    series_ids: seriesIds,
    directory: directoryValue === '' ? null : directoryValue,
    image_extension: $('input[name="image_extension"]')[0].value,
    force_reload: $('.checkbox[data-value="force_reload"]').checkbox('is unchecked'),
  };

  // Submit request
  $('.segment .dimmer').toggleClass('active', true);
  const url = seriesIds.length > 1
    ? '/api/import/series/cards'
    : `/api/import/series/${seriesIds[0]}/cards/directory`
  ;

  $.ajax({
    type: 'POST',
    url,
    data: JSON.stringify(rawData),
    contentType: 'application/json',
    success: () => {
      showInfoToast('Imported Title Cards');
      if ($('.checkbox[data-value="load_afterwards"]').checkbox('is checked')) {
        for (let series_id of seriesIds) { loadCards(series_id); }
      }
    },
    error: response => showErrorToast({title: 'Error importing Cards', response}),
    complete: () => $('.segment .dimmer').toggleClass('active', false),
  });
}

async function submitYamlForm(args) {
  const {url, data, formId, name, successMessage} = args;

  try {
    $(`${formId} button`).toggleClass('loading', true);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error(JSON.stringify(responseData));
    }

    if (successMessage === undefined) {
      showInfoToast(`Imported ${name} YAML`);
    } else {
      const message = successMessage(responseData);
      showInfoToast(`Imported ${name} YAML`, { message });
    }

    $(`${formId} .error.message[data-value="${name}"]`)[0].innerHTML = '';
  } catch (error) {
    $(formId).toggleClass('error', true);
    $.toast({ class: 'error', title: `Unable to Import ${name} YAML`, displayTime: 5000 });

    const messageHtml = `<div class="header">${name} YAML Parsing Error</div><p>${error.message}</p>`;
    $(`${formId} .error.message[data-value="${name}"]`)[0].innerHTML = messageHtml;
  } finally {
    $(`${formId} button`).toggleClass('loading', false);
  }
}
