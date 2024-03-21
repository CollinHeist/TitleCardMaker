{% if False %}
import {
  RemoteBlueprintPage, RemoteBlueprintSet, SearchResult, Series
} from './.types.js';
{% endif %}

/** @type {number} Minimum interval between calls to add a new series */
const _ADD_INTERVAL_MS = 5000;
/** @type {number} Last execution time (from `Date().getTime()`) of adding a Series */
let _lastAdded;

/**
 * Add the indicated number of placeholder elements.
 * @param {HTMLElement} element - Element whose children are being replaced with
 * placeholders.
 * @param {number} [amount=10] - Number of elements to add to the DOM.
 * @param {string} [placeholderElementId='result-placeholder-template'] - ID of
 * the template of the placeholder to clone and add to the DOM.
 */
function addPlaceholders(element, amount=10, placeholderElementId='result-placeholder-template') {
  const placeholders = Array.from({length: amount}).map(() => {
    return document.getElementById(placeholderElementId).content.cloneNode(true);
  });
  element.replaceChildren(...placeholders);
  refreshTheme();
}

/**
 * Create a NewSeries object for the given result.
 * @param {SearchResult} result - Result to parse and convert.
 * @returns {Object} NewSeries object of the given result.
 */
function generateNewSeriesObject(result) {
  // Comma separate Template IDs
  const template_string = $('#add-series-modal .dropdown[data-value="template_ids"]').dropdown('get value');
  const template_ids = template_string === '' ? [] : template_string.split(',');
  
  // Parse libraries
  const library_vals = $('#add-series-modal .dropdown[data-value="libraries"]').dropdown('get value');
  let libraries = [];
  if (library_vals) {
    libraries = library_vals.split(',')
      .map(libraryStr => {
        const libraryData = libraryStr.split('::');
        return {
          interface: libraryData[0],
          interface_id: libraryData[1],
          name: libraryData[2]
        };
      });
  }

  return {
    name: result.name,
    year: result.year,
    template_ids: template_ids,
    libraries: libraries,
    emby_id: result.emby_id || '',
    imdb_id: result.imdb_id,
    jellyfin_id: result.jellyfin_id || '',
    sonarr_id: result.sonarr_id || '',
    tmdb_id: result.tmdb_id,
    tvdb_id: result.tvdb_id,
    tvrage_id: result.tvrage_id,
  };
}

/**
 * Submit the API request to add the Series indicated by the given result.
 * @param {SearchResult} result - Result being added.
 * @param {string} resultElementId - ID of the element in the DOM to modify.
 */
function addSeries(result, resultElementId) {
  // Indicate loading
  $('#add-series-modal form').toggleClass('loading', true);
  $('#add-series-modal .actions .button').toggleClass('disabled', false);

  // Wait between calls
  const remainingTime = _lastAdded ? _ADD_INTERVAL_MS - (new Date().getTime() - _lastAdded) : 0;
  setTimeout(() => {
    $.ajax({
      type: 'POST',
      url: '/api/series/new',
      data: JSON.stringify(generateNewSeriesObject(result)),
      contentType: 'application/json',
      /**
       * Series added successfully, disable element in DOM and show a success toast.
       * @param {Series} series - Newly added Series.
       */
      success: series => {
        document.getElementById(resultElementId).classList.add('disabled');
        showInfoToast(`Added Series "${series.name}"`);
      },
      error: response => showErrorToast({title: 'Error Adding Series', response}),
      complete: () => {
        $('#add-series-modal').modal('hide');
        $('#add-series-modal .actions .button').toggleClass('disabled', false);
        _lastAdded = new Date().getTime();
      },
    });
  }, remainingTime);

}

/**
 * Submit an API request to import the given global Blueprint - creating
 * the associated Series if it does not exist.
 * @param {number} blueprintId - ID of the Blueprint to import.
 * @param {string} elementId - ID of the element in the DOM to modify.
 */
function importBlueprint(blueprintId, elementId) {
  $(`#${elementId}`).toggleClass('loading', true).toggleClass('transition', false);
  $.ajax({
    type: 'POST',
    url: `/api/blueprints/import/blueprint/${blueprintId}`,
    /**
     * Blueprint successfully imported, show toast and mark element as disabled.
     * @param {Series} series - Series which the Blueprint was imported to.
     */
    success: series => {
      showInfoToast(`Imported Blueprint to "${series.full_name}"`);
      $(`#${elementId}`).toggleClass('loading', false).toggleClass('disabled', true);
    },
    error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
  });
}

/**
 * Look for any Blueprints for the given series. Loading the results into
 * the add-Series modal.
 * @param {SearchResult} result - ID of the result whose Blueprints are being
 * queried.
 * @param {string} resultElementId - ID of the element in the DOM to modify.
 */
function queryBlueprints(result, resultElementId) {
  // Add placeholder Blueprints while loading
  addPlaceholders(document.getElementById(resultElementId), 2, 'blueprint-placeholder-template');

  // Generate query URL
  let query = `name=${result.name}&year=${result.year}`;
  if (result.imdb_id) { query += `&imdb_id=${result.imdb_id}`; }
  if (result.tmdb_id) { query += `&tmdb_id=${result.tmdb_id}`; }
  if (result.tvdb_id) { query += `&tvdb_id=${result.tvdb_id}`; }

  // Query for Blueprints
  $.ajax({
    type: 'GET',
    url: `/api/blueprints/query/series?${query}`,
    /**
     * 
     * @param {Array<import('./.types.js').RemoteBlueprint>} blueprints - Blueprints associated with
     * this search result.
     */
    success: blueprints => {
      // No results, show warning
      if (!blueprints || blueprints.length === 0) {
        $('#add-series-modal .warning.message').toggleClass('hidden', false).toggleClass('visible', true);
        $('#blueprint-results .card').remove();
        return;
      }

      // Blueprints available, create card elements
      const blueprintTemplate = document.getElementById('blueprint-template');
      const blueprintCards = blueprints.map((blueprint, blueprintId) => {
        // Clone template and populate with info
        const card = populateBlueprintCard(blueprintTemplate.content.cloneNode(true), blueprint, `series-blueprint-id${blueprintId}`);

        // Assign function to import button
        card.querySelector('a[data-action="import"]').onclick = () => importBlueprint(blueprint.id, resultElementId);
        return card;
      });

      // Populate page
      document.getElementById('blueprint-results').replaceChildren(...blueprintCards);
      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Querying Blueprints', response}),
  });
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
      const blueprintTemplate = document.getElementById('all-blueprint-template');
      const setSection = document.getElementById('blueprint-sets');
      setSection.replaceChildren();

      for (let set of blueprintSets) {
        const header = document.createElement('h4');
        header.innerText = set.name; header.className = 'ui header';
        setSection.appendChild(header);

        const bpCards = document.createElement('div');
        bpCards.className = 'ui three stackable raised cards';
        setSection.appendChild(bpCards);

        for (let blueprint of set.blueprints) {
          const elementId = `blueprint-set-id${blueprint.id}`;
          blueprint.set_ids = [];
          const card = populateBlueprintCard(
            blueprintTemplate.content.cloneNode(true), blueprint, elementId
          );

          // Assign function to import button
          card.querySelector('[data-action="import"]').onclick = () => importBlueprint(blueprint.id, elementId);

          bpCards.appendChild(card);
        }
      }

      $('#blueprint-sets .card').transition({animation: 'scale', interval: 40});
      refreshTheme();
      setSection.scrollIntoView({behavior: 'smooth', block: 'start'});
    },
    error: response => showErrorToast({title: 'Error Querying Blueprint Sets', response}),
  });
}

/**
 * Query for all Blueprints defined for all Series - load the given page
 * number.
 * @param {number} [page=1] - Page number of Blueprints to query and display.
 * @param {boolean} [refresh=false] - Whether to force refresh the database.
 */
function queryAllBlueprints(page=1, refresh=false) {
  // Generate endpoint URL
  const orderBy = $('[data-value="order_by"]').val();
  const includeMissing = $('.checkbox[data-value="include_missing_series"]').checkbox('is unchecked');
  const includeImported = $('.checkbox[data-value="included_imported"]').checkbox('is checked');
  const query = `page=${page}`
    + `&size=15`
    + `&order_by=${orderBy}`
    + `&include_missing_series=${includeMissing}`
    + `&include_imported=${includeImported}`
    + `&force_refresh=${refresh}`;
  
  // Only add placeholders if on page 1 (first load)
  const blueprintResults = document.getElementById('all-blueprint-results');
  if (page === 1) {
    addPlaceholders(blueprintResults, 9, 'blueprint-placeholder-template');
  }
  
  // Submit API request
  $.ajax({
    type: 'GET',
    url: `/api/blueprints/query/all?${query}`,
    /**
     * Query successful, populate page with Blueprint cards.
     * @param {RemoteBlueprintPage} allBlueprints - Page of Blueprints to display.
     */
    success: allBlueprints => {
      const blueprintTemplate = document.getElementById('all-blueprint-template');
      const blueprintCards = allBlueprints.items.map(blueprint => {
        // Clone template, fill out basic info
        const elementId = `blueprint-id${blueprint.id}`;
        const card = populateBlueprintCard(blueprintTemplate.content.cloneNode(true), blueprint, elementId);

        // Assign function to import button
        card.querySelector('[data-action="import"]').onclick = () => importBlueprint(blueprint.id, elementId);
        
        // Assign blacklist function to hide button
        card.querySelector('[data-action="blacklist"]').onclick = () => {
          $.ajax({
            type: 'PUT',
            url: `/api/blueprints/blacklist/${blueprint.id}`,
            success: () => {
              // Remove Blueprint card from display
              $(`#blueprint-id${blueprint.id}`).transition({animation: 'fade', duration: 800});
              setTimeout(() => {
                document.getElementById(elementId).remove();
                showInfoToast('Blueprint Hidden');
              }, 800);
            },
            error: response => showErrorToast({title: 'Error Hiding Blueprint', response}),
          });
        };

        // Toggle Set viewer on button 
        if (card.querySelector('[data-action="view-set"]')) {
          card.querySelector('[data-action="view-set"]').onclick = () => viewBlueprintSets(blueprint.id);
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
      document.getElementById('all-blueprint-results').scrollIntoView({behavior: 'smooth', block: 'start'});
      $('#all-blueprint-results .card').transition({animation: 'scale', interval: 40});
      $('[data-value="file-count"]').popup({inline: true});
      refreshTheme();
    },
    error: response => showErrorToast({title: 'Unable to Query Blueprints', response}),
  });
}

/**
 * Show the modal to add a Series. Launched by clicking a search result.
 * @param {SearchResult} result - Result whose modal is being displayed.
 * @param {string} resultElementId - ID of the element in the DOM to modify.
 */
function showAddSeriesModal(result, resultElementId) {
  // Update the elements of the modal before showing
  // Update title
  $('#add-series-modal [data-value="series-name-header"]')[0].innerText = `Add Series "${result.name} (${result.year})"`;
  // Query for Blueprints when button is pressed
  $('#add-series-modal button[data-action="search-blueprints"]').off('click').on('click', (event) => {
    // Do not refresh page
    event.preventDefault();
    queryBlueprints(result, 'blueprint-results');
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

/**
 * Quick-add the indicated result. This uses the last-selected Templates and 
 * libraries.
 * @param {SearchResult} result - Result being added.
 * @param {string} resultElementId - ID of the element in the DOM to modify.
 */
function quickAddSeries(result, resultElementId) {
  // Mark element as loading
  let resultElement = document.getElementById(resultElementId)
  resultElement.classList.add('loading');
  resultElement.classList.remove('transition');

  // Wait between calls
  const remainingTime = _lastAdded ? _ADD_INTERVAL_MS - (new Date().getTime() - _lastAdded) : 0;
  setTimeout(() => {
    // Submit API request to add this result
    $.ajax({
      type: 'POST',
      url: '/api/series/new',
      data: JSON.stringify(generateNewSeriesObject(result)),
      contentType: 'application/json',
      /**
       * Series successfully added; show toast and disable the result.
       * @param {Series} series - Newly added Series.
       */
      success: series => {
        resultElement.classList.add('disabled');
        showInfoToast(`Added Series "${series.name}"`);
      },
      error: response => showErrorToast({title: 'Error adding Series', response}),
      complete: () => {
        resultElement.classList.remove('loading');
        resultElement.classList.add('transition');
        _lastAdded = new Date().getTime();
      }
    });
  }, remainingTime);
}

/**
 * Load the interface search dropdown.
 */
function initializeSearchSource() {
  $.ajax({
    type: 'GET',
    url: '/api/settings/episode-data-source',
    /**
     * Data sources queried, initialize dropdown.
     * @param {import('./.types.js').EpisodeDataSourceToggle} dataSources - Which data sources are
     * enabled.
     */
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

/**
 * Initialize the library dropdowns.
 */
function initializeLibraryDropdowns() {
  $.ajax({
    type: 'GET',
    url: '/api/connection/all',
    /**
     * Connections queried, store and then query all libraries.
     * @param {Array<import('./.types.js').AnyConnection>} connections - All globally
     * defined and enabled Connections.
     */
    success: connections => {
      $.ajax({
        type: 'GET',
        url: '/api/available/libraries/all',
        /**
         * Libraries queried successfully, populate the library dropdowns.
         * @param {import('./.types.js').MediaServerLibrary} libraries 
         */
        success: libraries => {
          $('.dropdown[data-value="libraries"]').dropdown({
            placeholder: 'None',
            values: libraries.map(({interface, interface_id, name}) => {
              const serverName = connections.filter(connection => connection.id === interface_id)[0].name || interface;
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
        },
        error: response => showErrorToast({title: 'Error Querying Libraries', response}),
      });
    },
    error: response => showErrorToast({title: 'Error Querying Connections', response}),
  }); 
}

/** Initialize the page. */
async function initAll() {
  initializeSearchSource();
  initializeLibraryDropdowns();

  // Initialize search input with query param if provided
  const query = new URLSearchParams(window.location.search).get('q');
  if (query) {
    document.getElementById('search-query').value = query;
    querySeries();
  }

  // Add custom right-click action to Browse Blueprints button
  $('.button[data-action="browse-blueprints"]').on('contextmenu', (event) => {
    queryAllBlueprints(undefined, true);
  });

  const allTemplates = await fetch('/api/available/templates').then(resp => resp.json());
  $('.dropdown[data-value="template_ids"]').dropdown({
    placeholder: 'None',
    values: await getActiveTemplates(undefined, allTemplates),
  });
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
}

/**
 * Query for a series. This reads the input, makes the API call and then
 * displays the results as cards.
 */
function querySeries() {
  const resultTemplate = document.getElementById('search-result-template');
  const resultSegment = document.getElementById('search-results');
  let query = $('#search-query').val();

  // Exit if are no HTML elements or query
  if (resultTemplate === null || resultSegment === null || !query) { return; }

  // Add placeholders while searching
  addPlaceholders(resultSegment, 10);
  const interfaceId = $('input[name="interface_id"]').val() || {{preferences.episode_data_source}};

  // Submit API request
  $.ajax({
    type: 'GET',
    url: `/api/series/lookup?name=${query}&interface_id=${interfaceId}`,
    /**
     * Lookup successful, populate page.
     * @param {import('./.types.js').SearchResultsPage} allResults - Search results for this query.
    */
    success: allResults => {
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

      // Add elements to page, transition them in
      resultSegment.replaceChildren(...results);
      refreshTheme();
      $('#search-results .card').transition({animation: 'fade', interval: 75});
    },
    error: response => {
      showErrorToast({title: 'Error Looking up Series', response});
      $('#search-results .placeholder').transition({animation: 'fade', interval: 25});
    },
  });
}
