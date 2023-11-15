/**
 * Refresh the Card data (progress and card counts) for the Series with the
 * given ID.
 * @param {int} seriesId: ID of the Series to update the card data of.
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
 * @param {int} seriesId - ID of the Series to toggle.
 */
function toggleMonitoredStatus(seriesId) {
  $.ajax({
    type: 'PUT',
    url: `/api/series/${seriesId}/toggle-monitor`,
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
 * @param {int} seriesId - ID of the Series to update. 
 * @param {Object} data - An `UpdateSeries` object to pass to the PATCH request.
 */
function _updateSeriesConfig(seriesId, data) {
  $.ajax({
    type: 'PATCH',
    url: `/api/series/${seriesId}`,
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: () => showInfoToast('Updated Series'),
    error: response => showErrorToast({title: 'Error Updating Series', response}),
  });
}
const updateSeriesConfig = debounce((...args) => _updateSeriesConfig(...args));

/**
 * Submit an API request to begin Processing the Series with the given ID.
 * @param {int} seriesId - ID of the Series to process.
 */
function processSeries(seriesId) {
  $(`#series-id${seriesId} td[data-row="process"]`).toggleClass('disabled', true);
  $(`#series-id${seriesId} td[data-row="process"] i`).toggleClass('loading disabled', true);
  $.ajax({
    type: 'POST',
    url: `/api/series/series/${seriesId}/process`,
    success: () => showInfoToast('Started Processing Series'),
    error: response => showErrorToast({title: 'Error Processing Series', response}),
    complete: () => {
      $(`#series-id${seriesId} td[data-row="process"]`).toggleClass('disabled', false);
      $(`#series-id${seriesId} td[data-row="process"] i`).toggleClass('loading disabled', false);
    },
  });
}

/** @type {Array<int>} */
let selectedSeries = [];

/**
 * Toggle the series with the given ID's selection status. This modifies the
 * row's class, checkbox, and updates the `selectedSeries` list.
 * @param {int} seriesId - ID of the Series to toggle the selection of.
 * @param {boolean} [force] - Selection value to force for the given Series.
 */
function toggleSeriesSelection(seriesId, force=undefined) {
  // Unselect if forced or Series is selected (and not being forced)
  if (force === false || (!force && selectedSeries.includes(seriesId))) {
    $(`#series-id${seriesId}`).toggleClass('selected', false);
    $(`#series-id${seriesId} .checkbox[data-value="select"]`).checkbox('uncheck');
    // Remove from selected ID list
    selectedSeries = selectedSeries.filter(id => id !== seriesId);
  }
  // Select if forced or Series is not selected
  else if (force || !selectedSeries.includes(seriesId)) {
    $(`#series-id${seriesId}`).toggleClass('selected', true);
    $(`#series-id${seriesId} .checkbox[data-value="select"]`).checkbox('check');
    selectedSeries.push(seriesId);
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
 * @param {int} seriesId - ID of the Series to open the page of.
 */
function openSeries(seriesId) {
  if (selectedSeries.length === 0) {
    window.location.href = `/series/${seriesId}`;
  }
}

/**
 * Submit an API request to get all the Series at the given page number and add
 * their content to the page.
 * @param {int} [page] - Page number of Series to load 
 * @param {boolean} [keepSelection] - Whether to keep the current selection of
 * Series.
 */
async function getAllSeries(page=undefined, keepSelection=false) {
  // Get page from URL param if provided
  page = page || new URLSearchParams(window.location.search).get('page') || 1;

  // Get associated sort query param
  const sortParam = window.localStorage.getItem('sort-by') || 'alphabetical'

  // Fade out existing posters
  $('#series-list .card').transition({animation: 'scale', interval: 15, reverse: true});

  // Get this page of Series data
  let allSeriesData = await fetch(`/api/series/all?order_by=${sortParam}&size={{preferences.home_page_size}}&page=${page}`).then(resp => resp.json());
  let allSeries = allSeriesData.items;

  // Create Series cards
  {% if preferences.home_page_table_view %}
  const template = document.getElementById('series-row-template');
  // Clear selected series if indicated
  if (!keepSelection) { selectedSeries = []; }
  
  // Generate table rows
  let rows = allSeries.map(series => {
    // Get row template
    const row = template.content.cloneNode(true);
    row.querySelector('tr').dataset.id = series.id;
    row.querySelector('tr').id = `series-id${series.id}`;
    // Make row red / yellow depending on Card count
    if (series.card_count === 0) { row.querySelector('td').classList.add('left', 'red', 'marked'); }
    else if (series.episode_count - series.card_count > 0) { row.querySelector('td').classList.add('left', 'orange', 'marked'); }
    // Add "select row" action to select cell
    row.querySelector('a[data-action="select"]').onclick = () => toggleSeriesSelection(series.id);
    // Link name cell
    row.querySelector('td[data-row="name"] a').onclick = () => openSeries(series.id);
    row.querySelector('td[data-row="name"]').dataset.sortValue = `_${series.sort_name}`; // Add _ so numbers are still parsed as text
    // Fill out data
    row.querySelector('td[data-row="name"] [data-value="name"]').innerText = series.name;
    const poster = row.querySelector('td[data-row="name"] img');
    poster.src = `${series.small_poster_url}?${series.year}`;
    {% if preferences.stylize_unmonitored_posters %}
    if (!series.monitored) { poster.classList.add('unmonitored'); }
    {% endif %}
    row.querySelector('td[data-row="year"').innerText = series.year;
    row.querySelector('td[data-row="libraries"]').dataset.sortValue = series.libraries.length;
    // libraries later
    row.querySelector('td[data-row="card_count"] a').onclick = () => refreshCardData(series.id);
    row.querySelector('td[data-row="card_count"] span[data-value="card_count"]').innerText = `${series.card_count} / ${series.episode_count} Cards`;
    row.querySelector('td[data-row="card_count"] .progress').dataset.value = `${series.card_count},${Math.max(0, series.episode_count-series.card_count)}`;
    row.querySelector('td[data-row="card_count"] .progress').dataset.total = series.episode_count;
    row.querySelector('td[data-row="card_count"]').dataset.sortValue = Math.max(0, series.episode_count-series.card_count);
    row.querySelector('td[data-row="monitored"] a').onclick = () => toggleMonitoredStatus(series.id);
    row.querySelector('td[data-row="monitored"]').dataset.sortValue = series.monitored;
    if (series.monitored) {
      row.querySelector('td[data-row="monitored"] a').innerHTML = '<i class="ui eye outline green icon"></i>';
    } else {
      row.querySelector('td[data-row="monitored"] a').innerHTML = '<i class="ui eye slash outline red icon">';
    }
    row.querySelector('td[data-row="process"] a').onclick = () => processSeries(series.id);

    return row;
  });
  // Hide loader
  $('.loading.container').transition('fade out');

  // Add rows
  document.getElementById('series-table').replaceChildren(...rows);
  $('#series-table tr').transition({animation: 'scale', interval: 20});
  $('.progress').progress({duration: 1800});

  // Set selected statuses
  selectedSeries.forEach(seriesId => {
    $(`#series-id${seriesId}`).toggleClass('selected', true);
    $(`#series-id${seriesId} .checkbox[data-value="select"]`).checkbox('check');
  });

  // Initialize library dropdowns
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
  let allSeriesCards = allSeries.map(series => {
    const clone = template.content.cloneNode(true);
    const topDiv = clone.querySelector('div');
    // Set sorting attributes
    topDiv.setAttribute('data-series-id', series.id);
    topDiv.setAttribute('data-series-sort-name', series.sort_name);
    topDiv.setAttribute('data-series-year', series.year);
    // Poster
    const img = clone.querySelector('img');
    img.src = `${series.small_poster_url}?${series.name[0]}${series.year}`;
    img.alt = `Poster for ${series.name}`;
    // Grayscale if unmonitored (and enabled)
    {% if preferences.stylize_unmonitored_posters %}
    if (!series.monitored) { img.classList.add('unmonitored'); }
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
  });
  // Fade out loader
  $('.loading.container').transition('fade out');
  // Add new cards, transition them in
  document.getElementById('series-list').replaceChildren(...allSeriesCards);
  $('#series-list .card').transition({animation: 'scale', interval: 15});
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

// Get all statistics and load them into HTML
function getAllStatistics() {
  $.ajax({
    type: 'GET',
    url: '/api/statistics',
    success: statistics => {
      $('#statistics .statistic').remove();
      const statisticsElement = document.getElementById('statistics');
      const template = document.getElementById('statistic-template');
      statistics.forEach(({value_text, unit, description}) => {
        const clone = template.content.cloneNode(true);
        clone.querySelector('.statistic').title = description;
        clone.querySelector('.value').innerText = value_text;
        clone.querySelector('.label').innerText = unit;
        statisticsElement.appendChild(clone);
      });
    },
    // error: response => showErrorToast({title: 'Error Querying Statistics', response}),
  });
}

function initAll() {
  getAllStatistics();
  getAllSeries();

  // WIP
  $('.ui.dropdown').dropdown();
  // $('.modal').modal('show');
  $('.ui.checkbox').checkbox();
  $('.ui.progress').progress();
  $('table').tablesort();
  // WIP
}

const sortStates = {
  name:  ['alphabetical', 'reverse-alphabetical'],
  id:    ['id',           'reverse-id'],
  cards: ['cards',        'reverse-cards'],
  year:  ['year',         'reverse-year'],
}
/**
 * Adjust how the Series are sorted on the home page. This updates the
 * local storage for the sort parameter, and re-queries the current page.
 * @param {string} sortBy - How to sort the Series on the page.
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
    },
    error: response => showErrorToast({title: 'Error Updating Series', response}),
  });
}

/**
 * Submit an API request to mark all the currently selected Series as  unmonitored.
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
      getAllSeries(undefined, true);
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
      getAllSeries(undefined, true);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Deleting Title Cards', response}),
  });
}
