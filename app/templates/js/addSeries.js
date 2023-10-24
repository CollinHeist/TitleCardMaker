/*
 * Add the indicated number of placeholder elements.
 */
function addPlaceholders(element, amount=10, placeholderElementId='result-placeholder-template') {
  const placeholders = Array.from({length: amount}).map(() => {
    return document.getElementById(placeholderElementId).content.cloneNode(true);
  });
  element.replaceChildren(...placeholders);
  refreshTheme();
}

/*
 * Create a NewSeries object for the given result.
 */
function generateNewSeriesObject(result) {
  const template_string = $('#add-series-modal .dropdown[data-value="template_ids"]').dropdown('get value');
  const template_ids = template_string === '' ? [] : template_string.split(',');
  return {
    name: result.name,
    year: result.year,
    template_ids: template_ids,
    emby_library_name: $('#add-series-modal input[name="emby_library_name"]').val() || null,
    jellyfin_library_name: $('#add-series-modal input[name="jellyfin_library_name"]').val() || null,
    plex_library_name: $('#add-series-modal input[name="plex_library_name"]').val() || null,
    emby_id: result.emby_id,
    imdb_id: result.imdb_id,
    jellyfin_id: result.jellyfin_id,
    sonarr_id: result.sonarr_id,
    tmdb_id: result.tmdb_id,
    tvdb_id: result.tvdb_id,
    tvrage_id: result.tvrage_id,
  };
}

/*
 * Submit the API request to add the Series indicated by the given result.
 */
function addSeries(result, resultElementId) {
  $('#add-series-modal form').toggleClass('loading', true);
  $.ajax({
    type: 'POST',
    url: '/api/series/new',
    data: JSON.stringify(generateNewSeriesObject(result)),
    contentType: 'application/json',
    success: series => {
      document.getElementById(resultElementId).classList.add('disabled');
      showInfoToast(`Added Series "${series.name}"`);
    }, error: response => showErrorToast({title: 'Error Adding Series', response}),
    complete: () => $('#add-series-modal').modal('hide'),
  });
}

/*
 * Submit the API requests to add the Series indicated by the given
 * result, and then import the given Blueprint to that Series.
 */
function addSeriesImportBlueprint(result, blueprintId, resultElementId) {
  $('#add-series-modal form').toggleClass('loading', true);
  // Create Series
  $.ajax({
    type: 'POST',
    url: '/api/series/new',
    data: JSON.stringify(generateNewSeriesObject(result)),
    contentType: 'application/json',
    success: series => {
      document.getElementById(resultElementId).classList.add('disabled');
      showInfoToast(`Added Series "${series.name}"`);
      // API request to import blueprint
      $.ajax({
        type: 'PUT',
        url: `/api/blueprints/import/series/${series.id}/blueprint/${blueprintId}`,
        contentType: 'application/json',
        success: () => showInfoToast('Blueprint Imported'),
        error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
      });
    }, error: response => showErrorToast({title: 'Error adding Series', response}),
    complete: () => $('#add-series-modal').modal('hide'),
  });
}

/*
 * Submit an API request to import the given global Blueprint - creating
 * the associated Series if it does not exist.
 */
function importBlueprint(blueprintId, elementId) {
  $.ajax({
    type: 'PUT',
    url: `/api/blueprints/import/blueprint/${blueprintId}`,
    success: series => {
      showInfoToast(`Imported Blueprint to "${series.full_name}"`);
      document.getElementById(elementId).classList.add('disabled');
    }, error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
  });
}

/*
 * Look for any Blueprints for the given series. Loading the results into
 * the add-Series modal.
 */
async function queryBlueprints(result, resultElementId) {
  const blueprintResults = document.getElementById('blueprint-results');
  const blueprintTemplate = document.getElementById('blueprint-template');
  addPlaceholders(blueprintResults, 2, 'blueprint-placeholder-template');
  const allBlueprints = await fetch(`/api/blueprints/query/series?name=${result.name}&year=${result.year}`).then(resp => resp.json());
  if (allBlueprints === null || allBlueprints.length === 0) {
    $('#add-series-modal .warning.message').toggleClass('hidden', false).toggleClass('visible', true);
    $('#blueprint-results .card').remove();
    return;
  }
  // Blueprints available, create cards
  const blueprintCards = allBlueprints.map((blueprint, blueprintId) => {
    // Clone template, fill out basic info
    let card = blueprintTemplate.content.cloneNode(true);
    card = populateBlueprintCard(card, blueprint, `series-blueprint-id${blueprintId}`);
    // Assign function to import button
    card.querySelector('a[data-action="import-blueprint"]').onclick = () => addSeriesImportBlueprint(result, blueprint.id, resultElementId);
    return card;
  });
  blueprintResults.replaceChildren(...blueprintCards);
  refreshTheme();
}

/*
 * Query for all Blueprints defined for all Series - load the given page
 * number.
 */
function queryAllBlueprints(page=1) {
  const blueprintResults = document.getElementById('all-blueprint-results');
  const blueprintTemplate = document.getElementById('all-blueprint-template');
  const orderBy = $('[data-value="order_by"]').val();
  const includeMissing = $('.checkbox[data-value="include_missing_series"]').checkbox('is unchecked');
  const includeImported = $('.checkbox[data-value="included_imported"]').checkbox('is checked');
  // Only add placeholders if on page 1 (first load)
  if (page === 1) {
    addPlaceholders(blueprintResults, 9, 'blueprint-placeholder-template');
  }
  $.ajax({
    type: 'GET',
    url: `/api/blueprints/query/all?page=${page}&size=15&order_by=${orderBy}&include_missing_series=${includeMissing}&include_imported=${includeImported}`,
    success: allBlueprints => {
      const blueprintCards = allBlueprints.items.map((blueprint, blueprintId) => {
        // Clone template, fill out basic info
        let card = blueprintTemplate.content.cloneNode(true);
        card = populateBlueprintCard(card, blueprint, `blueprint-id${blueprintId}`);
        // Assign function to import button
        card.querySelector('[data-action="import-blueprint"]').onclick = () => importBlueprint(blueprint.id, `blueprint-id${blueprintId}`);
        // Assign blacklist function to hide button
        card.querySelector('[data-action="blacklist-blueprint"]').onclick = () => {
          $(`#blueprint-id${blueprintId}`).transition({animation: 'fade', duration: 1000});
          $.ajax({
            type: 'PUT',
            url: `/api/blueprints/blacklist/${blueprint.id}`,
            success: () => {
              // Remove Blueprint card from display
              $(`#blueprint-id${blueprintId}`).transition({animation: 'fade', duration: 800});
              setTimeout(() => {
                document.getElementById(`blueprint-id${blueprintId}`).remove();
                showInfoToast('Blueprint Hidden');
              }, 800);
            }, error: response => showErrorToast({title: 'Error Hiding Blueprint', response}),
          });
        }
        return card;
      });
      // Add Blueprints to page
      blueprintResults.replaceChildren(...blueprintCards);
      updatePagination({
        paginationElementId: 'blueprint-pagination',
        navigateFunction: queryAllBlueprints,
        page: allBlueprints.page,
        pages: allBlueprints.pages,
        amountVisible: isSmallScreen() ? 5 : 15,
        hideIfSinglePage: true,
      });
      // Transition elements in
      $('#all-blueprint-results .card').transition({animation: 'scale', interval: 40});
      $('[data-value="file-count"]').popup({inline: true});
      refreshTheme();
    }, error: response => showErrorToast({title: 'Unable to Query Blueprints', response}),
  });
}

/*
 * Show the modal to add a Series. Launched by clicking a search result.
 */
function showAddSeriesModal(result, resultElementId) {
  // Update the elements of the modal before showing
  // Update title
  $('#add-series-modal [data-value="series-name-header"]')[0].innerText = `Add Series "${result.name} (${result.year})"`;
  // Query for Blueprints when button is pressed
  $('#add-series-modal button[data-action="search-blueprints"]').off('click').on('click', (event) => {
    // Do not refresh page
    event.preventDefault();
    queryBlueprints(result, resultElementId);
  });
  // Add Series when button is pressed
  $('#add-series-modal button[data-action="add-series"]').off('click').on('click', (event) => {
    // Do not refresh page
    event.preventDefault();
    addSeries(result, resultElementId);
  });

  // Hide no Blueprints warning message
  $('#add-series-modal .warning.message').toggleClass('hidden', true).toggleClass('visible', false);
  // Clear any previously loaded Blueprint cards
  $('#blueprint-results .card').remove();
  // Turn off loading status of the form
  $('#add-series-modal form').toggleClass('loading', false);

  $('#add-series-modal')
    .modal({blurring: true})
    .modal('setting', 'transition', 'fade up')
    .modal('show');
}

/*
 * Quick-add the indicated result. This uses the last-selected Templates/libraries.
 */
function quickAddSeries(result, resultElementId) {
  let resultElement = document.getElementById(resultElementId)
  resultElement.classList.add('loading');
  resultElement.classList.remove('transition');
  $.ajax({
    type: 'POST',
    url: '/api/series/new',
    data: JSON.stringify(generateNewSeriesObject(result)),
    contentType: 'application/json',
    success: series => {
      resultElement.classList.add('disabled');
      showInfoToast(`Added Series "${series.name}"`);
    }, error: response => showErrorToast({title: 'Error adding Series', response}),
    complete: () => {
      resultElement.classList.remove('loading');
      resultElement.classList.add('transition');
    }
  });
}

/*
 * Load the interface search dropdown.
 */
function initializeSearchSource() {
  $.ajax({
    type: 'GET',
    url: '/api/settings/episode-data-source',
    success: dataSources => {
      $('.dropdown[data-value="interface_id"]').dropdown({
        placeholder: 'Default',
        values: dataSources.map(({name, interface_id, selected}) => {
          return {name, value: interface_id, selected};
        }),
      });
    },
    error: response => showErrorToast({title: 'Error Querying Episode Data Sources', response}),
  });
}

/*
 * Initialize the library dropdowns.
 */
async function initializeLibraryDropdowns() {
  const allConnections = await fetch('/api/connection/all').then(resp => resp.json());
  $.ajax({
    type: 'GET',
    url: '/api/available/libraries/all',
    success: libraries => {
      $('.dropdown[data-value="libraries"]').dropdown({
        placeholder: 'None',
        values: libraries.map(({interface, interface_id, name}) => {
          const serverName = allConnections.filter(connection => connection.id === interface_id)[0].name || interface;
          return {
            name: name,
            text: `${name} (${serverName})`,
            value: `${interface}::${interface_id}::${name}`,
            description: serverName,
            descriptionVertical: true,
            selected: false,
          };
        }),
      });
    }, error: response => showErrorToast({title: 'Error Querying Libraries', response}),
  });
}

/*
 * Initialize the page.
 */
async function initAll() {
  initializeSearchSource();
  await initializeLibraryDropdowns();

  // Initialize search input with query param if provided
  const query = new URLSearchParams(window.location.search).get('q');
  if (query) {
    document.getElementById('search-query').value = query;
    querySeries();
  }

  const allTemplates = await fetch('/api/available/templates').then(resp => resp.json());
  $('.dropdown[data-value="template_ids"]').dropdown({
    placeholder: 'None',
    values: await getActiveTemplates(undefined, allTemplates),
  });
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
}

/*
 * Query for a series. This reads the input, makes the API call and then
 * displays the results as cards.
 */
async function querySeries() {
  const resultTemplate = document.getElementById('search-result-template');
  const resultSegment = document.getElementById('search-results');
  let query = $('#search-query').val();

  // Exit if are no HTML elements or query
  if (resultTemplate === null || resultSegment === null || !query) { return; }

  // Add placeholders while searching
  addPlaceholders(resultSegment, 10);
  const interfaceId = $('input[name="interface_id"]').val() || {{preferences.episode_data_source}};

  // Submit API request
  const allResults = await fetch(`/api/series/lookup?name=${query}&interface_id=${interfaceId}`).then(resp => resp.json());
  const results = allResults.items.map((result, index) => {
    // Clone template
    const card = resultTemplate.content.cloneNode(true);
    // Assign ID
    card.querySelector('.card').id = `result${index}`;
    // Add DB ID to image src string in case a proxy URL is needed
    card.querySelector('img').src = result.poster;
    // Fill out content
    card.querySelector('[data-value="name"]').innerText = result.name;
    card.querySelector('[data-value="year"]').innerText = result.year;
    if (result.ongoing === null) {
      card.querySelector('[data-value="ongoing"]').remove();
    } else {
      card.querySelector('[data-value="ongoing"]').innerText = result.ongoing ? 'Ongoing' : 'Ended';
    }
    card.querySelector('[data-value="overview"]').innerHTML = '<p>' + result.overview.join('</p><p>') + '</p>';
    // Disable card if already added
    if (result.added) {
      card.querySelector('img').classList.add('disabled');
      card.querySelector('.card').classList.add('disabled'); 
    } else {
      // Launch add Series modal when card is clicked
      card.querySelector('.card').onclick = () => showAddSeriesModal(result, `result${index}`);
      // Quick-add Series when button is pressed
      card.querySelector('button[data-action="quick-add"]').onclick = (event) => {
        // Do not execute parent card onclick function
        event.stopPropagation();
        quickAddSeries(result, `result${index}`);
      }
    }

    return card;
  });
  resultSegment.replaceChildren(...results);
  $('#search-results .card').transition({animation: 'fade', interval: 75});
  refreshTheme();
}
