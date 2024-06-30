{% if False %}
import {
  AnyConnection, EpisodeDataSourceToggle, MediaServerLibrary,
  RemoteBlueprintPage, RemoteBlueprintSet, SearchResult, SearchResultsPage,
  Series, 
} from './.types.js';
{% endif %}

/** @type {EpisodeDataSourceToggle} Which data sources are enabled*/
const episodeDataSources = {{episode_data_sources|tojson}};
/** @type {AnyConnection[]} All globally defined and enabled Connections */
const allConnections = {{all_connections|tojson}};
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
  const template_string = $('#new-series .dropdown[data-value="template_ids"]').dropdown('get value');
  const template_ids = template_string === '' ? [] : template_string.split(',');
  
  // Parse libraries
  const library_vals = $('#new-series .dropdown[data-value="libraries"]').dropdown('get value');
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
  const resultElement = document.getElementById(resultElementId);
  resultElement.classList.add('loading');
  resultElement.classList.remove('transition');

  // Wait between calls
  const remainingTime = _lastAdded ? _ADD_INTERVAL_MS - (new Date().getTime() - _lastAdded) : 0;
  setTimeout(() => {
    $.ajax({
      type: 'POST',
      url: '/api/series/new',
      data: JSON.stringify(generateNewSeriesObject(result)),
      contentType: 'application/json',
      /**
       * Series added successfully, disable element in DOM and show sucess.
       * @param {Series} series - Newly added Series.
       */
      success: series => {
        resultElement.classList.add('disabled');
        showInfoToast(`Added Series "${series.name}"`);
      },
      error: response => showErrorToast({title: 'Error Adding Series', response}),
      complete: () => {
        resultElement.classList.remove('loading');
        _lastAdded = new Date().getTime();
      },
    });
  }, remainingTime);
}

/**
 * Submit an API request to import the given global Blueprint - creating the
 * associated Series if it does not exist.
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
      $('#add-series-modal').modal('close');
    },
    error: response => showErrorToast({title: 'Error Importing Blueprint', response}),
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
        // Add header for this Set
        const header = document.createElement('h4');
        header.innerText = set.name; header.className = 'ui header';
        setSection.appendChild(header);

        // Create section of cards for Blueprints of this Set
        const bpCards = document.createElement('div');
        bpCards.className = 'ui three stackable raised cards';
        setSection.appendChild(bpCards);

        // Add all BPs in the set
        for (let blueprint of set.blueprints.sort((a, b) => a.series.name.localeCompare(b.series.name))) {
          const elementId = `blueprint-set-id${blueprint.id}`;
          blueprint.set_ids = [];
          const card = populateBlueprintCard(
            blueprintTemplate.content.cloneNode(true), blueprint, elementId
          );
          // Remove blacklist button
          card.querySelector('[data-action="blacklist"]').remove();

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
 * Parse the Blueprint search input for a creator name.
 * @returns Object of the filter name and creator.
 */
function parseBlueprintSearchName() {
  let name = $('input[name="blueprint_series_name"]').val();
  let creator = null;

  let colonIndex = name.indexOf('creator:');
  if (colonIndex !== -1) {
    creator = name.substring(colonIndex + 8).trim();
    name = name.substring(0, colonIndex).trim();
  } else if (name.indexOf('by:') !== -1) {
    colonIndex = name.indexOf('by:');
    creator = name.substring(colonIndex + 3).trim();
    name = name.substring(0, colonIndex).trim();
  }

  return {filterName: name || null, filterCreator: creator || null};
}

/**
 * Query for all Blueprints defined for all Series and load the given page of
 * results.
 * @param {number} [page=1] - Page number of Blueprints to query and display.
 * @param {boolean} [refresh=false] - Whether to force refresh the database.
 */
function queryAllBlueprints(page=1, refresh=false) {
  // Generate endpoint query parameters
  const {filterName, filterCreator} = parseBlueprintSearchName();
  const orderBy = $('[data-value="order_by"]').val();
  const includeMissing = $('.checkbox[data-value="include_missing_series"]').checkbox('is unchecked');
  const includeImported = $('.checkbox[data-value="included_imported"]').checkbox('is checked');
  const query = new URLSearchParams({
    page: page,
    size: 15,
    order_by: orderBy,
    include_missing_series: includeMissing,
    include_imported: includeImported,
    force_refresh: refresh,
    name: filterName,
    creator: filterCreator,
  });
  if (filterName === null) { query.delete('name'); }
  if (filterCreator === null) { query.delete('creator'); }
  
  // Only add placeholders if on page 1 (first load)
  const blueprintResults = document.getElementById('all-blueprint-results');
  if (page === 1) {
    addPlaceholders(blueprintResults, 9, 'blueprint-placeholder-template');
  }

  // Query by series name if provided, otherwise query all
  const endpointUrl = filterName ? '/api/blueprints/query/series' : '/api/blueprints/query/all';

  // Submit API request
  $.ajax({
    type: 'GET',
    url: `${endpointUrl}?${query.toString()}`,
    /**
     * Query successful, populate page with Blueprint cards.
     * @param {RemoteBlueprintPage} allBlueprints - Page of Blueprints to display.
     */
    success: allBlueprints => {
      const blueprintTemplate = document.getElementById('all-blueprint-template');
      // If filtered by name, return is just list of BPs; otherwise a Page
      const items = filterName ? allBlueprints : allBlueprints.items;
      const blueprintCards = items.map(blueprint => {
        // Clone template, fill out basic info
        const elementId = `blueprint-id${blueprint.id}`;
        const card = populateBlueprintCard(blueprintTemplate.content.cloneNode(true), blueprint, elementId);

        // When name is clicked, populate and focus to series search bar
        card.querySelector('[data-action="search-series"]').onclick = () => {
          $('#search-bar input').val(blueprint.series.name).focus();
        }

        // When creator is clicked, populate input and click
        card.querySelector('[data-value="creator"]').onclick = () => {
          $('input[name="blueprint_series_name"]').val(`by:${blueprint.creator}`).focus();
          queryAllBlueprints();
        }

        // If multiple Blueprints for this Series, add count and assign click
        // interaction - otherwise remove the count altogether
        if (blueprint.series.blueprint_count > 1) {
          card.querySelector('[data-value="count"]').innerText = blueprint.series.blueprint_count;

          // When count icon is clicked, filter blueprints by this name
          card.querySelector('[data-value="count"]').onclick = () => {
            $('input[name="blueprint_series_name"]').val(blueprint.series.name);
            queryAllBlueprints();
          }
        } else {
          card.querySelector('[data-value="count"]').remove();
        }

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
        hideIfSinglePage: false,
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
 * Load the interface search dropdown.
 */
function initializeSearchSource() {
  $('.dropdown[data-value="interface_id"]').dropdown({
    placeholder: 'Default',
    values: episodeDataSources.map(({name, interface_id, selected}) => {
      return {name, value: interface_id, selected};
    }),
  });
}

/**
 * Initialize the library dropdowns.
 */
function initializeLibraryDropdowns() {
  $.ajax({
    type: 'GET',
    url: '/api/available/libraries/all',
    /**
     * Libraries queried successfully, populate the library dropdowns.
     * @param {MediaServerLibrary} libraries 
     */
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
    },
    error: response => showErrorToast({title: 'Error Querying Libraries', response}),
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
     * @param {SearchResultsPage} allResults - Search results for this query.
    */
    success: allResults => {
      const results = allResults.items.map((result, index) => {
        // Clone template
        const card = resultTemplate.content.cloneNode(true);

        // Assign ID
        const resultId = `result${index}`
        card.querySelector('.card').id = resultId;

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
          card.querySelector('.card').onclick = () => addSeries(result, resultId);
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
