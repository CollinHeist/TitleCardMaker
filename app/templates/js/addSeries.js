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
      $(`#${resultElementId}`).toggleClass('disabled', true);
      $.toast({class: 'blue info', title: `Added Series "${series.name}"`});
    }, error: response => showErrorToast({title: 'Error Adding Series', response}),
    complete: () => $('#add-series-modal').modal('hide'),
  });
}

/*
 * Submit the API requests to add the Series indicated by the given
 * result, and then import the given Blueprint to that Series.
 */
function addSeriesImportBlueprint(result, blueprint, resultElementId) {
  $('#add-series-modal form').toggleClass('loading', true);
  // Create Series
  $.ajax({
    type: 'POST',
    url: '/api/series/new',
    data: JSON.stringify(generateNewSeriesObject(result)),
    contentType: 'application/json',
    success: series => {
      $(`#${resultElementId}`).toggleClass('disabled', true);
      $.toast({class: 'blue info', title: `Added Series "${series.name}"`});
      // API request to import blueprint
      $.ajax({
        type: 'PUT',
        url: `/api/blueprints/import/series/${series.id}`,
        contentType: 'application/json',
        data: JSON.stringify(blueprint),
        success: () => {
          $.toast({class: 'blue info', title: 'Blueprint Imported'});
        }, error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
      });
    }, error: response => showErrorToast({title: 'Error adding Series', response}),
    complete: () => $('#add-series-modal').modal('hide'),
  });
}

/*
 * Import the given global Blueprint - creating the associated Series if
 * it does not exist.
 */
function importBlueprint(blueprint, elementId) {
  // Import Blueprint to Series - creating if necessary
  $.ajax({
    type: 'PUT',
    url: '/api/blueprints/import/blueprint',
    data: JSON.stringify(blueprint),
    contentType: 'application/json',
    success: series => {
      $.toast({class: 'blue info', title: `Imported Blueprint to "${series.full_name}"`});
      document.getElementById(elementId).classList.add('disabled');
    }, error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
  });
}

/*
 * Fill out the given Blueprint card element with the details - i.e. the
 * creator, title, image, description, etc.
 */
function populateBlueprintCard(card, blueprint, blueprintId) {
  // Fill out card
  card.querySelector('.card').id = blueprintId;
  card.querySelector('img').src = blueprint.preview;
  card.querySelector('[data-value="creator"]').innerText = blueprint.creator;
  // If there is a Series name element, fill out
  if (card.querySelector('[data-value="series_full_name"')) {
    card.querySelector('[data-value="series_full_name"').innerText = blueprint.series_full_name;
  }
  if (blueprint.fonts.length === 0) {
    card.querySelector('[data-value="font-count"]').remove();
  } else {
    let text = `<b>${blueprint.fonts.length}</b> Font` + (blueprint.fonts.length > 1 ? 's' : '');
    card.querySelector('[data-value="font-count"]').innerHTML = text;
  }
  if (blueprint.templates.length === 0) {
    card.querySelector('[data-value="template-count"]').remove();
  } else {
    let text = `<b>${blueprint.templates.length}</b> Template` + (blueprint.templates.length > 1 ? 's' : '');
    card.querySelector('[data-value="template-count"]').innerHTML = text;
  }
  const episodeOverrideCount = Object.keys(blueprint.episodes).length;
  if (episodeOverrideCount === 0) {
    card.querySelector('[data-value="episode-count"]').remove();
  } else {
    let text = `<b>${episodeOverrideCount}</b> Episode Override` + (episodeOverrideCount > 1 ? 's' : '');
    card.querySelector('[data-value="episode-count"]').innerHTML = text;
  }
  card.querySelector('[data-value="description"]').innerHTML = '<p>' + blueprint.description.join('</p><p>') + '</p>';
  return card;
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
    card.querySelector('a[data-action="import-blueprint"]').onclick = () => addSeriesImportBlueprint(result, blueprint, resultElementId);
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
  // Only add placeholders if on page 1 (first load)
  if (page === 1) {
    addPlaceholders(blueprintResults, 9, 'blueprint-placeholder-template');
  }
  $.ajax({
    type: 'GET',
    url: `/api/blueprints/query/all?page=${page}&size=15&order_by=${orderBy}`,
    success: allBlueprints => {
      const blueprintCards = allBlueprints.items.map((blueprint, blueprintId) => {
        // Clone template, fill out basic info
        let card = blueprintTemplate.content.cloneNode(true);
        card = populateBlueprintCard(card, blueprint, `blueprint-id${blueprintId}`);
        // Assign function to import button
        card.querySelector('[data-action="import-blueprint"]').onclick = () => importBlueprint(blueprint, `blueprint-id${blueprintId}`);
        // Assign blacklist function to hide button
        card.querySelector('[data-action="blacklist-blueprint"]').onclick = () => {
          $(`#blueprint-id${blueprintId}`).transition({animation: 'fade', duration: 1000});
          $.ajax({
            type: 'PUT',
            url: `/api/blueprints/query/blacklist?series_full_name=${blueprint.series_full_name}&blueprint_id=${blueprint.id}`,
            success: () => {
              // Remove Blueprint card from display
              $(`#blueprint-id${blueprintId}`).transition({animation: 'fade', duration: 1000});
              setTimeout(() => {
                document.getElementById(`blueprint-id${blueprintId}`).remove();
                $.toast({class: 'blue info', title: 'Blueprint Hidden'});
              }, 1000);
            }, error: response => showErrorToast({title: 'Error Blacklisting Blueprint', response}),
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
async function quickAddSeries(result, resultElementId) {
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
async function initializeSearchSource() {
  const eds = await fetch('/api/available/episode-data-sources').then(resp => resp.json());
  $('#search-source').dropdown({
      values: eds,
  })
}

/*
 * Initialize the library dropdowns for all enabled media servers. This
 * only makes API requests for enabled connections.
 */
async function initializeLibraryDropdowns() {
  if ($('.dropdown[data-value="emby_library_name"]').length) {
    const embyLibraries = await fetch('/api/available/libraries/emby').then(resp => resp.json());
    $('.dropdown[data-value="emby_library_name"]').dropdown({
      placeholder: 'None',
      values: embyLibraries.map(name => {
        return {name: name, value: name};
      }),
    });
  }

  if ($('.dropdown[data-value="jellyfin_library_name"]').length) {
    const jellyfinLibraries = await fetch('/api/available/libraries/jellyfin').then(resp => resp.json());
    $('.dropdown[data-value="jellyfin_library_name"]').dropdown({
      placeholder: 'None',
      values: jellyfinLibraries.map(name => {
        return {name: name, value: name};
      }),
    });
  }

  if ($('.dropdown[data-value="plex_library_name"]').length) {
    const plexLibraries = await fetch('/api/available/libraries/plex').then(resp => resp.json());
    $('.dropdown[data-value="plex_library_name"]').dropdown({
      placeholder: 'None',
      values: plexLibraries.map(name => {
        return {name: name, value: name};
      }),
    });
  }
}

/*
 * Initialize the page.
 */
async function initAll() {
  initializeSearchSource();
  initializeLibraryDropdowns();

  const allTemplates = await fetch('/api/templates/all').then(resp => resp.json());
  $('.dropdown[data-value="template_ids"]').dropdown({
    placeholder: 'None',
    values: await getActiveTemplates(undefined, allTemplates),
  });
  $('.ui.dropdown').dropdown();
}

/*
 * Query for a series. This reads the input, makes the API call and then
 * displays the results as cards.
 */
async function querySeries() {
  const resultTemplate = document.getElementById('search-result-template');
  const resultSegment = document.getElementById('search-results');
  const query = $('#search-query').val();
  if (resultTemplate === null || resultSegment === null || !query) { return; }
  addPlaceholders(resultSegment, 10);
  const interfaceName = $('#search-interface').val();
  const allResults = await fetch(`/api/series/lookup?name=${query}&interface=${interfaceName}`).then(resp => resp.json());
  const results = allResults.items.map((result, index) => {
    // Clone template
    const card = resultTemplate.content.cloneNode(true);
    // Assign ID
    card.querySelector('.card').id = `result${index}`;
    // Fill out content
    card.querySelector('img').src = result.poster;
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
