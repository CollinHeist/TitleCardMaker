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
      // Refresh episode data for the newly added Series
      $.ajax({
        type: 'POST',
        url: `/api/episodes/${series.id}/refresh`,
        success: () => {
          $.toast({class: 'blue info', title: `Refreshed Episode data for "${series.name}"`});
        }, error: response2 => {
          $.toast({
            class: 'error',
            title: `Error refreshing Episode data for "${response2.name}"`,
            message: response2.responseJSON.message,
            showDuration: 0,
          });
        }
      });
    }, error: response => {
      $.toast({
        class: 'error',
        title: 'Error Adding series',
        message: response,
        showDuration: 0,
      });
    }, complete: () => {
      $('#add-series-modal').modal('hide');
    },
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
      // Refresh episode data for the newly added Series
      $.ajax({
        type: 'POST',
        url: `/api/episodes/${series.id}/refresh`,
        success: () => {
          $.toast({class: 'blue info', title: `Refreshed Episode data for "${series.name}"`});
        }, error: response2 => {
          $.toast({
            class: 'error',
            title: `Error refreshing episode data for "${response2.name}"`,
            message: response2.responseJSON.message,
            showDuration: 'auto',
          });
        },
      });
      // Submit API request to import blueprint
      $.ajax({
        type: 'PUT',
        url: `/api/blueprints/import/series/${series.id}`,
        contentType: 'application/json',
        data: JSON.stringify(blueprint),
        success: () => {
          $.toast({class: 'blue info', title: 'Blueprint Imported'});
        }, error: response => {
          $.toast({
            class: 'error',
            title: 'Error Importing Blueprint',
            message: response.responseJSON.detail,
            displayTime: 0,
          });
        },
      });
    }, error: response => {
      $.toast({
        class: 'error',
        title: 'Error adding Series',
        message: response,
        showDuration: 0,
      });
    }, complete: () => {
      $('#add-series-modal').modal('hide');
    },
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
    card.querySelector('a[data-action="import-blueprint"]').onclick = () => addSeriesImportBlueprint(result, blueprint, resultElementId);
    return card;
  });
  blueprintResults.replaceChildren(...blueprints);
  refreshTheme();
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
  console.log(generateNewSeriesObject(result));
  $.ajax({
    type: 'POST',
    url: '/api/series/new',
    data: JSON.stringify(generateNewSeriesObject(result)),
    contentType: 'application/json',
    success: series => {
      resultElement.classList.add('disabled');
      // $(`#${resultElementId}`).toggleClass('disabled', true);
      $.toast({class: 'blue info', title: `Added Series "${series.name}"`});
      // Refresh episode data for the newly added Series
      $.ajax({
        type: 'POST',
        url: `/api/episodes/${series.id}/refresh`,
        success: () => {
          $.toast({class: 'blue info', title: `Refreshed Episode data for "${series.name}"`});
        }, error: response2 => {
          $.toast({
            class: 'error',
            title: `Error refreshing Episode data for "${response2.name}"`,
            message: response2.responseJSON.message,
            showDuration: 0,
          });
        }
      });
    }, error: response => {
      $.toast({
        class: 'error',
        title: 'Error adding Series',
        message: response,
        showDuration: 0,
      });
    }, complete: () => {
      resultElement.classList.remove('loading');
    },
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
    const values = 
    $('.dropdown[data-value="emby_library_name"]').dropdown({
      values: embyLibraries.map(name => {
        return {name: name, value: name};
      }),
    });
  }

  if ($('.dropdown[data-value="jellyfin_library_name"]').length) {
    const jellyfinLibraries = await fetch('/api/available/libraries/jellyfin').then(resp => resp.json());
    const values = 
    $('.dropdown[data-value="emby_library_name"]').dropdown({
      values: jellyfinLibraries.map(name => {
        return {name: name, value: name};
      }),
    });
  }

  if ($('.dropdown[data-value="plex_library_name"]').length) {
    const plexLibraries = await fetch('/api/available/libraries/plex').then(resp => resp.json());
    $('.dropdown[data-value="plex_library_name"]').dropdown({
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
    values: await getActiveTemplates(undefined, allTemplates),
  });
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
  const interface = $('#search-interface').val();
  const allResults = await fetch(`/api/series/lookup?name=${query}&interface=${interface}`).then(resp => resp.json());
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
  refreshTheme();
}