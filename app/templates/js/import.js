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
  const seriesResults = await fetch('/api/series/all?size=9999&page=1').then(resp => resp.json());
  const allSeries = seriesResults.items;
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
    ], onChange: (value, text, $selectedItem) => {
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
    }, onActionable: (value, text, $selected) => {
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
  // Toggle media server dropdown with load checkbox
  $('.checkbox[data-value="load_afterwards"]').checkbox({
    onChecked: () => $('.field[data-value="media_server"]').toggleClass('disabled', false),
    onUnchecked: () => $('.field[data-value="media_server"]').toggleClass('disabled', true),
  });
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

  // Preferences form submission
  $('#preferences-form').on('submit', event => {
    // Prevent page reload
    event.preventDefault();
    const form = new FormData(event.target);
    // Determine which queries to submit
    if ($('#preferences-form .checkbox[data-value="options"]').checkbox('is checked')) {
      submitYamlForm({
        url: '/api/import/preferences/options',
        data: Object.fromEntries(form),
        formId: '#preferences-form',
        name: 'Options',
      });
    }
    if ($('#preferences-form .checkbox[data-value="connections"]').checkbox('is checked')) {
      submitYamlForm({
        url: '/api/import/preferences/connection/all',
        data: Object.fromEntries(form),
        formId: '#preferences-form',
        name: 'Connections',
      });
    }
    if ($('#preferences-form .checkbox[data-value="syncs"]').checkbox('is checked')) {
      submitYamlForm({
        url: '/api/import/preferences/sync',
        data: Object.fromEntries(form),
        formId: '#preferences-form',
        name: 'Syncs',
      });
    }
  });

  // Series YAML form submission
  $('#series-form').on('submit', event => {
    // Prevent page reload
    event.preventDefault();
    const form = new FormData(event.target);
    // Turn off error status of the form
    $('#series-form').toggleClass('error', false);
    // Determine which queries to submit
    if ($('#series-form .checkbox[data-value="fonts"]').checkbox('is checked')) {
      submitYamlForm({
        url: '/api/import/fonts',
        data: Object.fromEntries(form),
        formId: '#series-form',
        name: 'Fonts',
        successMessage: newFonts => `Created ${newFonts.length} Custom Fonts`,
      });
    }
    if ($('#series-form .checkbox[data-value="templates"]').checkbox('is checked')) {
      submitYamlForm({
        url: '/api/import/templates',
        data: Object.fromEntries(form),
        formId: '#series-form',
        name: 'Templates',
        successMessage: newTemplates => `Created ${newTemplates.length} Templates`,
      });
    }
    if ($('#series-form .checkbox[data-value="series"]').checkbox('is checked')) {
      submitYamlForm({
        url: '/api/import/series',
        data: Object.fromEntries(form),
        formId: '#series-form',
        name: 'Series',
        successMessage: newSeries => `Created ${newSeries.length} Series`,
      });
    }
  })
}

function loadCards(seriesId) {
  // Get associated Media Server to load cards into, default Plex
  let mediaServer = $('input[name="media_server"]')[0].value;
  mediaServer = mediaServer === '' ? 'Plex' : mediaServer;
  $.ajax({
    type: 'POST',
    url: `/api/series/${seriesId}/load/${mediaServer}`,
    success: response => {
      $.toast({class: 'blue info', title: 'Loaded Title Cards'});
    }, error: response => {
      $.toast({class: 'error', title: 'Error loading Title Cards', message: response.responseJSON.detail});
    }, complete: () => {},
  });
}

function importSeries() {
  // Get associated Series
  let seriesIds = $('input[name="series_id"]')[0].value;
  if (seriesIds === '') {
    $('.dropdown[data-value="series_id"]').toggleClass('error', true);
    return;
  }
  $('.dropdown[data-value="series_id"]').toggleClass('error', false);
  seriesIds = seriesIds.split(',');
  // Data for request
  const directoryValue = $('input[name="directory"]')[0].value
  const data = {
    series_ids: seriesIds,
    directory: directoryValue === '' ? null : directoryValue,
    image_extension: $('input[name="image_extension"]')[0].value,
    force_reload: $('.checkbox[data-value="force_reload"]').checkbox('is unchecked'),
  };
  // URL for request if submitting >1 series
  const url = seriesIds.length > 1 ? '/api/import/series/cards' : `/api/import/series/${seriesIds[0]}/cards`;
  // Submit request
  $('.segment .dimmer').toggleClass('active', true);
  $.ajax({
    type: 'POST',
    url: url,
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: () => {
      $.toast({class: 'blue info',title: `Imported Title Cards`});
      if ($('.checkbox[data-value="load_afterwards"]').checkbox('is checked')) {
        for (let series_id of seriesIds) { loadCards(series_id); }
      }
    }, error: response => {
      $.toast({class: 'error', title: 'Error importing Cards', message: response.responseJSON.detail});
    }, complete: () => {
      $('.segment .dimmer').toggleClass('active', false);
    },
  });
}

function submitYamlForm(args) {
  const {url, data, formId, name, successMessage} = args;
  $(`${formId} button`).toggleClass('loading', true);
  $.ajax({
    type: 'POST',
    url: url,
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: response => { 
      if (successMessage === undefined) {
        $.toast({class: 'blue info', title: `Imported ${name} YAML`});
      } else {
        const message = successMessage(response);
        $.toast({class: 'blue info', title: `Imported ${name} YAML`, message: message});
      }
      $(`${formId} .error.message[data-value="${name}"]`)[0].innerHTML = '';
    }, error: response => {
      $(formId).toggleClass('error', true);
      $.toast({class: 'error', title: `Unable to Import ${name} YAML`, displayTime: 5000});
      const messageHtml = `<div class="header">${name} YAML Parsing Error</div><p>${response.responseJSON.detail}</p>`
      $(`${formId} .error.message[data-value="${name}"]`)[0].innerHTML = messageHtml;
    }, complete: () => {
      $(`${formId} button`).toggleClass('loading', false);
    },
  });
}