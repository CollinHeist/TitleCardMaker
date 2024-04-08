{% if False %}
import {
  Series, SeriesPage, Statistic
} from './.types.js';
{% endif %}

/** @type {number[]} */
let allIds = [];

/**
 * Refresh the Card data (progress and card counts) for the Series with the
 * given ID.
 * @param {number} seriesId: ID of the Series to update the card data of.
 */
function refreshCardData(seriesId) {
  $.ajax({
    type: 'GET',
    url: `/api/series/series/${seriesId}`,
    success: series => {
      $(`#series-id${series.id} span[data-value="card_count"]`).transition('fade out');
      $(`#series-id${series.id} span[data-value="card_count"]`)[0].innerText = `${series.card_count} / ${series.episode_count} Cards`;
      $(`#series-id${series.id} [data-row="card_count"] .progress`)
        .progress({
          percent: [
            series.card_count / series.episode_count * 100,
            (series.episode_count - series.card_count) / series.episode_count * 100
          ],
          duration: 2000,
        });
      $(`#series-id${series.id} span[data-value="card_count"]`).transition('fade in');
    },
    error: response => showErrorToast({title: 'Error Updating Data', response}),
  });
}

/**
 * Submit an API reuest to toggle the monitored status of the Series with the
 * given ID. This also updates the poster class and the monitored icon.
 * @param {number} seriesId - ID of the Series to toggle.
 */
function toggleMonitoredStatus(seriesId) {
  $.ajax({
    type: 'PUT',
    url: `/api/series/series/${seriesId}/toggle-monitor`,
    success: series => {
      // Show toast, toggle text and icon to show new status
      $(`#series-id${series.id} img`).toggleClass('unmonitored', !series.monitored);
      if (series.monitored) {
        showInfoToast(`Started Monitoring ${series.name}`);
        $(`#series-id${series.id} td[data-row="monitored"] a`)[0].innerHTML = '<i class="ui eye outline green icon"></i>';
      } else {
        showInfoToast(`Stopped Monitoring ${series.name}`);
        $(`#series-id${series.id} td[data-row="monitored"] a`)[0].innerHTML = '<i class="ui eye slash outline red icon">';
      }
      refreshTheme();
    }, error: response => showErrorToast({title: 'Error Changing Status', response}),
  });
}

/**
 * Submit an API request to update the config of the Series with the given ID.
 * @param {number} seriesId - ID of the Series to update. 
 * @param {Object} data - An `UpdateSeries` object to pass to the PATCH request.
 */
function _updateSeriesConfig(seriesId, data) {
  $.ajax({
    type: 'PATCH',
    url: `/api/series/series/${seriesId}`,
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: () => showInfoToast('Updated Series'),
    error: response => showErrorToast({title: 'Error Updating Series', response}),
  });
}
const updateSeriesConfig = debounce((...args) => _updateSeriesConfig(...args));

/**
 * Submit an API request to begin Processing the Series with the given ID.
 * @param {number} seriesId - ID of the Series to process.
 */
function processSeries(seriesId) {
  $(`#series-id${seriesId} td[data-row="process"]`).toggleClass('disabled', true);
  $.ajax({
    type: 'POST',
    url: `/api/series/series/${seriesId}/process`,
    success: () => showInfoToast('Started Processing Series'),
    error: response => showErrorToast({title: 'Error Processing Series', response}),
    complete: () => $(`#series-id${seriesId} td[data-row="process"]`).toggleClass('disabled', false),
  });
}

/** @type {number[]} */
let selectedSeries = [];
/** @type {number} */
let lastSelection;

/**
 * Toggle the series with the given ID's selection status. This modifies the
 * row's class, checkbox, and updates the `selectedSeries` list.
 * @param {number} seriesId - ID of the Series to toggle the selection of.
 * @param {boolean} [force] - Selection value to force for the given Series.
 * @param {PointerEvent} [event] - Click Event triggering the toggle.
 */
function toggleSeriesSelection(seriesId, force=undefined, event=undefined) {
  const _select = (id, status) => {
    $(`#series-id${id}`).toggleClass('selected', status);
    $(`#series-id${id} .checkbox[data-value="select"]`).checkbox(status ? 'check' : 'uncheck');
    // Add or remove from selection
    if (status) { selectedSeries.push(id); }
    else        { selectedSeries = selectedSeries.filter(id_ => id_ !== id); }
  }

  // Unselect if forced or Series is selected (and not being forced)
  if (force === false || (!force && selectedSeries.includes(seriesId))) {
    _select(seriesId,false);
  }
  // Select if forced or Series is not selected
  else if (force || !selectedSeries.includes(seriesId)) {
    _select(seriesId, true);

    // If shift was held, select all between this and last selection
    if (event !== undefined && event.shiftKey && lastSelection !== undefined) {
      const startIndex = allIds.indexOf(lastSelection);
      const endIndex = allIds.indexOf(seriesId);
      if (startIndex < endIndex) {
        allIds.slice(startIndex, endIndex+1).forEach(id => _select(id, true));
      } else if (startIndex > endIndex) {
        allIds.slice(endIndex, startIndex+1).forEach(id => _select(id, true));
      }
    }
    lastSelection = seriesId;
  }

  // If any/none series are selected, ensure toolbar is proper state
  if (selectedSeries.length > 0) {
    $('#toolbar .item[data-action="edit"]').toggleClass('disabled', false);
    $('#toolbar .item[data-action="unselect"]').toggleClass('disabled', false);
  } else {
    $('#toolbar .item[data-action="edit"]').toggleClass('disabled', true);
    $('#toolbar .item[data-action="unselect"]').toggleClass('disabled', true);
  }
}

/** Toggle all currently displayed Series selection status. */
function toggleAllSelection() {
  $('#series-table tr')
    .each((index, row) => {
      toggleSeriesSelection(Number.parseInt(row.dataset.id))
    });
}

/** Unselect all currently displayed Series. */
function clearSelection() {
  $('#series-table tr')
    .each((index, row) => {
      toggleSeriesSelection(Number.parseInt(row.dataset.id), false)
    });
}

/**
 * Navigate to the Series page for the Series with the given ID. This only
 * navigates the page if no Series are selected.
 * @param {number} seriesId - ID of the Series to open the page of.
 */
function openSeries(seriesId) {
  if (selectedSeries.length === 0) {
    window.location.href = `/series/${seriesId}`;
  }
}

/**
 * Populate a <tr> element whose base content is provided as `template` with the
 * data defined in the `Series` object `series`.
 * @param {Series} series - Series whose data is used to populate the row.
 * @param {HTMLTemplateElement} template - Template to clone and populate with
 * data.
 * @returns {HTMLElement} The populated HTML <tr> element which can be added to
 * the DOM.
 */
function _populateSeriesRow(series, template) {
  // Clone Template
  const row = template.content.cloneNode(true);

  // Add ID to row dataset (for querying)
  row.querySelector('tr').dataset.id = series.id;
  row.querySelector('tr').id = `series-id${series.id}`;

  // Determine maximum number of Cards based on libraries
  {% if preferences.library_unique_cards %}
    const maxCards = series.episode_count * series.libraries.length;
  {% else %}
    const maxCards = series.episode_count;
  {% endif %}

  // Make row red / yellow depending on Card count
  if (series.card_count === 0 && series.episode_count > 0) {
    row.querySelector('td').classList.add('left', 'red', 'marked');
  } else if (maxCards - series.card_count > 0) {
    row.querySelector('td').classList.add('left', 'orange', 'marked'); 
  }

  // Add "select row" action to select cell
  row.querySelector('a[data-action="select"]').onclick = (event) => toggleSeriesSelection(series.id, undefined, event);

  // Link name cell to Series page
  row.querySelector('td[data-row="name"] a').onclick = () => openSeries(series.id);
  row.querySelector('td[data-row="name"]').dataset.sortValue = `_${series.sort_name}`; // Add _ so numbers are still parsed as text

  // Add Series Name
  row.querySelector('td[data-row="name"] [data-value="name"]').innerText = series.name;

  // Set poster image src
  const poster = row.querySelector('td[data-row="name"] img');
  poster.src = series.small_poster_url;

  // Add unmonitored class if styling
  {% if preferences.stylize_unmonitored_posters %}
  if (!series.monitored) {
    poster.classList.add('unmonitored'); 
  }
  {% endif %}

  // Add year
  row.querySelector('td[data-row="year"').innerText = series.year;

  // Sort libraries on the number of libraries
  row.querySelector('td[data-row="libraries"]').dataset.sortValue = series.libraries.length;

  // Refresh Card data when the card count cell is clicked
  row.querySelector('td[data-row="card_count"] a').onclick = () => refreshCardData(series.id);
  
  // Fill out Card and episode text
  row.querySelector('td[data-row="card_count"] span[data-value="card_count"]').innerText = `${series.card_count} / ${maxCards} Cards`;

  // Populate Card progress bars
  row.querySelector('td[data-row="card_count"] .progress').dataset.value = `${Math.min(series.card_count, maxCards)},${Math.max(0, maxCards - series.card_count)}`;
  row.querySelector('td[data-row="card_count"] .progress').dataset.total = maxCards;
  row.querySelector('td[data-row="card_count"]').dataset.sortValue = Math.max(0, maxCards - series.card_count);

  // Toggle monitored status when cell is clicked
  row.querySelector('td[data-row="monitored"] a').onclick = () => toggleMonitoredStatus(series.id);

  // Sort by monitored boolean status
  row.querySelector('td[data-row="monitored"]').dataset.sortValue = series.monitored;

  // Set icon for monitored cell
  if (series.monitored) {
    row.querySelector('td[data-row="monitored"] a').innerHTML = '<i class="ui eye outline green icon"></i>';
  } else {
    row.querySelector('td[data-row="monitored"] a').innerHTML = '<i class="ui eye slash outline red icon">';
  }

  // Process Series when process cell is clicked
  row.querySelector('td[data-row="process"] a').onclick = () => processSeries(series.id);

  return row;
}

/**
 * 
 * @param {Series} series - Series whose data is used to populate the card.
 * @param {HTMLTemplateElement} template - Template to clone and populate with
 * data.
 * @returns {HTMLElement} The populated HTML <div> element which can be added to
 * the DOM.
 */
function _populateSeriesCard(series, template) {
  // Clone template
  const clone = template.content.cloneNode(true);

  // Set poster image src and alt text
  const img = clone.querySelector('img');
  img.src = `${series.small_poster_url}?${series.name[0]}${series.year}`;
  img.alt = `Poster for ${series.name}`;

  // Grayscale if unmonitored (and enabled)
  {% if preferences.stylize_unmonitored_posters %}
  if (!series.monitored) {
    img.classList.add('unmonitored'); 
  }
  {% endif %}

  // Link name and poster to the Series page
  const as = clone.querySelectorAll('a');
  as[0].href = `/series/${series.id}`;
  as[1].href = `/series/${series.id}`;

  // Go to Series page on Enter event for keyboard navigation
  clone.querySelector('.text.content').addEventListener('keydown', event => {
    // Check if the pressed key is Enter (key code 13)
    if (event.keyCode === 13) { window.location.href = `/series/${series.id}`; }
  });

  // Populate title
  const title = clone.querySelector('.series-name');
  title.setAttribute('title', `${series.name} (${series.year})`);
  title.innerText = series.name;

  // Progress bar
  const progressBar = clone.querySelector('.progress');
  const cardVal = Math.min(series.card_count, series.episode_count);
  if (cardVal > 0) {
    if (series.monitored) {
      progressBar.setAttribute('data-value', `${cardVal},${series.episode_count-cardVal},0,0`);
    } else {
      progressBar.setAttribute('data-value', `0,0,${cardVal},${series.episode_count-cardVal}`);
    }
    progressBar.setAttribute('data-total', series.episode_count);
  }

  return clone;
}

/**
 * Submit an API request to get all the Series at the given page number and add
 * their content to the page.
 * @param {number} [page] - Page number of Series to load 
 * @param {boolean} [keepSelection=false] - Whether to keep the current selection of
 * Series.
 */
async function getAllSeries(page=undefined, keepSelection=false) {
  // Get page from URL param if provided
  page = page || new URLSearchParams(window.location.search).get('page') || 1;

  // Get associated sort query param
  const sortParam = window.localStorage.getItem('sort-by') || 'alphabetical'

  // Fade out existing posters
  {% if not preferences.reduced_animations %}
    {% if preferences.home_page_table_view %}
    $('#series-table tr').transition({animation: 'scale', interval: 10, reverse: true});
    {% else %}
    $('#series-list .card').transition({animation: 'scale', interval: 10, reverse: true});
    {% endif %}
  {% endif %}

  // Get this page of Series data
  /** @type {SeriesPage} */
  let allSeriesData = await fetch(`/api/series/all?order_by=${sortParam}&size={{preferences.home_page_size}}&page=${page}`).then(resp => resp.json());
  await queryLibraries();
  let allSeries = allSeriesData.items;
  allIds = allSeries.map(series => series.id);

  // Hide loader
  $('.loading.container').transition('fade out');

  // Create elements of each Series
  {% if preferences.home_page_table_view %}
    const template = document.getElementById('series-row-template');

    // Clear selected series if indicated
    if (!keepSelection) { selectedSeries = []; }
    
    // Generate table rows
    let rows = allSeries.map(series => _populateSeriesRow(series, template));
  
    // Add rows, transition them in (if enabled)
    document.getElementById('series-table').replaceChildren(...rows);
    {% if not preferences.reduced_animations %}
      $('#series-table tr').transition({animation: 'scale', interval: 15});
    {% endif %}
    $('.progress').progress({duration: 1800});

    // Set selected statuses
    selectedSeries.forEach(seriesId => {
      $(`#series-id${seriesId}`).toggleClass('selected', true);
      $(`#series-id${seriesId} .checkbox[data-value="select"]`).checkbox('check');
    });

    // Prevent the mouse down event from triggering to disable text selection for shift-clicking multiple rows
    $('#series-table').mousedown(function (event) { event.preventDefault(); });

    // Initialize library dropdown for each Series
    allSeries.forEach(async (series) => {
      await initializeLibraryDropdowns({
        selectedLibraries: series.libraries,
        dropdownElements: $(`#series-id${series.id} .dropdown[data-value="libraries"]`),
        clearable: false,
        useLabels: false,
        onChange: function(value, text, $selectedItem) {
          // Current value of the library dropdown
          let libraries = [];
          if (value) {
            libraries = value.split(',').map(libraryStr => {
              const libraryData = libraryStr.split('::');
              return {interface: libraryData[0], interface_id: libraryData[1], name: libraryData[2]};
            });
          }
          // Get series ID
          const seriesId = $selectedItem.closest('tr').data('id');
          updateSeriesConfig(seriesId, {libraries});
        },
      });
    });
  {% else %}
    const template = document.getElementById('series-template');
    let allSeriesCards = allSeries.map(series => _populateSeriesCard(series, template));

    // Add new cards, transition them in (if enabled)
    document.getElementById('series-list').replaceChildren(...allSeriesCards);
    {% if not preferences.reduced_animations %}
      $('#series-list .card').transition({animation: 'scale', interval: 15});
    {% endif %}
    $('.progress').progress({duration: 2000});

    // Dim Series posters on hover
    $('.ui.cards .image').dimmer({on: 'ontouchstart' in document.documentElement ? 'click' : 'hover'});
  {% endif %}

  // Update pagination
  updatePagination({
    paginationElementId: 'pagination',
    navigateFunction: getAllSeries,
    page: allSeriesData.page,
    pages: allSeriesData.pages,
    amountVisible: isSmallScreen() ? 5 : 25,
    hideIfSinglePage: true,
  });

  // Update page search param field for the current page
  const url = new URL(location.href);
  url.searchParams.set('page', page);
  history.pushState(null, '', url);

  // Refresh theme for any newly added HTML
  refreshTheme();
}


const statisticMap = [
  {description: 'Number of Series', dataValue: 'series'},
  {description: 'Number of Monitored Series', dataValue: 'monitored'},
  {description: 'Number of Unmonitored Series', dataValue: 'unmonitored'},
  //
  {description: 'Number of Named Fonts', dataValue: 'fonts'},
  {description: 'Number of Templates', dataValue: 'templates'},
  {description: 'Number of Syncs', dataValue: 'syncs'},
  //
  {description: 'Number of Episodes', dataValue: 'episodes'},
  {description: 'Number of Title Cards', dataValue: 'title-cards'},
  {description: 'Number of loaded Title Cards', dataValue: 'loaded-title-cards'},
  //
  {description: 'File size of all Title Cards', dataValue: 'filesize'},
];

/** Get all statistics and load them into the DOM */
function getAllStatistics() {
  $.ajax({
    type: 'GET',
    url: '/api/statistics',
    /**
     * API call was successful, populate statistic elements.
     * @param {Statistic[]} statistics 
     */
    success: statistics => {
      statistics.forEach(statistic => {
        const map = statisticMap.filter(({description}) => statistic.description === description);
        if (!map || map.length === 0) { return; }

        const element = document.querySelector(`.statistics .statistic[data-value="${map[0].dataValue}"]`);
        if (element) {
          element.querySelector('.value').innerText = statistic.value_text;
          element.querySelector('.label').innerText = statistic.unit;
        }
      });
    },
  });
}

/** Initialize the page by querying for Series and statistics */
function initAll() {
  // Make remote queries
  getAllSeries();
  getAllStatistics();
  // Initialize table sorting and dropdowns
  $('table').tablesort();
  $('.ui.dropdown').dropdown();
}

const sortStates = {
  cards: ['cards',        'reverse-cards'],
  id:    ['reverse-id',   'id',],
  name:  ['alphabetical', 'reverse-alphabetical'],
  sync:  ['sync', 'sync'],
  year:  ['year',         'reverse-year'],
}
/**
 * Adjust how the Series are sorted on the home page. This updates the local
 * storage for the sort parameter, and re-queries the current page.
 * @param {"cards" | "id" | "name" | "sync" | "year"} sortBy - How to sort the
 * Series on the page.
 */
function sortSeries(sortBy) {
  // Get current sort state
  const currentSortState = window.localStorage.getItem('sort-by') || 'alphabetical';

  // Get new sort state, update local storage
  const newSortState = sortStates[sortBy][(sortStates[sortBy].indexOf(currentSortState) + 1) % sortStates[sortBy].length];
  window.localStorage.setItem('sort-by', newSortState);

  // Re-query current page if modified
  if (currentSortState !== newSortState) { getAllSeries(); }
}

/**
 * Submit an API request to mark all the currently selected Series as monitored.
 */
function batchMonitor() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'PUT',
    url: '/api/series/batch/monitor',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: updatedSeries => {
      showInfoToast(`Monitored ${updatedSeries.length} Series`);
      getAllSeries(undefined, true);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Updating Series', response}),
  });
}

/**
 * Submit an API request to mark all the currently selected Series as unmonitored.
 */
function batchUnmonitor() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'PUT',
    url: '/api/series/batch/unmonitor',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: updatedSeries => {
      showInfoToast(`Unmonitored ${updatedSeries.length} Series`);
      getAllSeries(undefined, true);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Updating Series', response}),
  });
}

/**
 * Submit an API request to begin processing all the currently selected Series.
 */
function batchProcess() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'POST',
    url: '/api/series/batch/process',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: () => {
      showInfoToast(`Started Processing ${selectedSeries.length} Series`);
      // getAllSeries(undefined, true);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Processing Series', response}),
  });
}

/**
 * Submit an API request to load the Title Cards all the currently selecte
 * Series.
 * @param {boolean} reload - Whether to force reload the Title Cards.
 */
function batchLoad(reload=false) {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'PUT',
    url: `/api/cards/batch/load?reload=${reload}`,
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: () => showInfoToast(`Loaded Title Cards`),
    error: response => showErrorToast({title: 'Error Loading Title Cards', response}),
  });
}

/**
 * Submit an API request to delete all the Episodes of all the currently
 * selected Series.
 */
function batchDeleteEpisodes() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'DELETE',
    url: '/api/episodes/batch/delete',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: actions => {
      showInfoToast(`Deleted Episodes and Title Cards`);
      // getAllSeries(undefined, true);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Deleting Episodes', response}),
  });
}

/**
 * Submit an API request to delete the Title Cards of all the currently selected
 * Series.
 */
function batchDeleteCards() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'DELETE',
    url: '/api/cards/batch',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: actions => {
      showInfoToast(`Deleted ${actions.deleted} Title Cards`);
      // getAllSeries(undefined, true);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Deleting Title Cards', response}),
  });
}

/**
 * Submit an API request to delete all the currently selected Series.
 */
function batchDeleteSeries() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'DELETE',
    url: '/api/series/batch/delete',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: () => {
      showInfoToast(`Deleted ${selectedSeries.length} Series`);
      // getAllSeries(undefined, false); // Clear selection
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Deleting Series', response}),
  });
}

/**
 * Change the global display style to the poster or tabular view. This submits
 * an API request and, if successful, reloads the page.
 * @param {"poster" | "table"} style 
 */
function toggleDisplayStyle(style) {
  $.ajax({
    type: 'PATCH',
    url: '/api/settings/update',
    data: JSON.stringify({home_page_table_view: style === 'table'}),
    contentType: 'application/json',
    success: () => location.reload(),
    error: response => showErrorToast({title: 'Error Changing View', response}),
  });
}
