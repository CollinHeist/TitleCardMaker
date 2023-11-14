/*
 * Refresh the Card data (progress and card counts) for the Series with the
 * given ID.
 * 
 * @args {int} serieId: ID of the Series to update the card data of.
 */
function refreshCardData(seriesId) {
  $.ajax({
    type: 'GET',
    url: `/api/series/${seriesId}`,
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

/*
 * Submit an API reuest to toggle the monitored status of the Series with the
 * given ID. This also updates the poster class and the monitored icon.
 * 
 * @param {int} seriesId: ID of the Series to toggle.
 */
function toggleMonitoredStatus(seriesId) {
  $.ajax({
    type: 'POST',
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

function processSeries(seriesId) {
  $(`#series-id${seriesId} td[data-row="process"]`).toggleClass('disabled', true);
  $(`#series-id${seriesId} td[data-row="process"] i`).toggleClass('loading disabled', true);
  $.ajax({
    type: 'POST',
    url: `/api/series/${seriesId}/process`,
    success: () => {
      showInfoToast('Started Processing Series');
    },
    error: response => showErrorToast({title: 'Error Processing Series', response}),
    complete: () => {
      $(`#series-id${seriesId} td[data-row="process"]`).toggleClass('disabled', false);
      $(`#series-id${seriesId} td[data-row="process"] i`).toggleClass('loading disabled', false);
    },
  });
}

/*
 * Function to toggle the series with the given ID's selection. This modifies
 * the row's class, checkbox, and updates the `selectedSeries` list.
 */
let selectedSeries = [];
function toggleSeriesSelection(seriesId) {
  // Unselect
  if (selectedSeries.includes(seriesId)) {
    $(`#series-id${seriesId}`).toggleClass('selected', false);
    $(`#series-id${seriesId} .checkbox[data-value="select"]`).checkbox('uncheck');
    selectedSeries = selectedSeries.filter(id => id !== seriesId);
  }
  // Select
  else {
    $(`#series-id${seriesId}`).toggleClass('selected', true);
    $(`#series-id${seriesId} .checkbox[data-value="select"]`).checkbox('check');
    selectedSeries.push(seriesId);
  }

  // If any series are selected, ensure "actions" button is displayed
  if (selectedSeries.length > 0) {
    $('#toolbar .item[data-action="edit"]').toggleClass('disabled', false);
  } else {
    $('#toolbar .item[data-action="edit"]').toggleClass('disabled', true);
  }
}

/*
 * Navigate to the Series page for the Series with the given ID. This only
 * navigates the page if no Series are selected.
 */
function openSeries(seriesId) {
  if (selectedSeries.length === 0) {
    window.location.href = `/series/${seriesId}`;
  }
}

// Get all series and load their cards into HTML
async function getAllSeries(page=undefined) {
  // Get page from URL param if provided
  page = page || new URLSearchParams(window.location.search).get('page') || 1;

  // Get associated sort query param
  const sortState = window.localStorage.getItem('series-sort-order') || 'a-z';
  const sortParam = {
    'id-asc': 'id',
    'id-desc': 'reverse-id',
    'a-z': 'alphabetical',
    'z-a': 'reverse-alphabetical',
    'year-asc': 'year',
    'year-desc': 'reverse-year',
  }[sortState];

  // Fade out existing posters
  $('#series-list .card').transition({animation: 'scale', interval: 15, reverse: true});

  // Get this page of Series data
  let allSeriesData = await fetch(`/api/series/all?order_by=${sortParam}&size={{preferences.home_page_size}}&page=${page}`).then(resp => resp.json());
  let allSeries = allSeriesData.items;

  // Create Series cards
  if (true) {
    const template = document.getElementById('series-row-template');
    // Clear selected series
    selectedSeries = [];
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
    $('#series-table tr').transition({animation: 'scale', interval: 25});
    $('.progress').progress({duration: 2000});
    // Initialize library dropdowns
    allSeries.forEach(async (series) => {
      await initializeLibraryDropdowns(
        series.libraries,
        $(`#series-id${series.id} .dropdown[data-value="libraries"]`),
        false,
        false,
      );
    })
  } else {
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
    $('.loading.container').transition('fade out');
    document.getElementById('series-list').replaceChildren(...allSeriesCards);
    $('#series-list .card').transition({animation: 'scale', interval: 15});
    $('.progress').progress({duration: 2000});
  }

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
  // Dim Series posters on hover
  $('.ui.cards .image').dimmer({
    on: 'ontouchstart' in document.documentElement ? 'click' : 'hover'
  });
}

// Get all statistics and load them into HTML
function getAllStatistics() {
  $.ajax({
    type: 'GET',
    url: '/api/statistics',
    success: statistics => {
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

async function initAll() {
  getAllStatistics();
  getAllSeries();

  // WIP
  $('.ui.dropdown').dropdown();
  // $('.modal').modal('show');
  $('.ui.checkbox').checkbox();
  $('.ui.progress').progress();
  $('table').tablesort();
  // WIP

  // Dim Series posters on hover
  $('.ui.cards .image').dimmer({
    on: 'ontouchstart' in document.documentElement ? 'click' : 'hover'
  });
}

// Sort series different ways
let sortStates = {
  'id': {state: 0, allStates: [{icon: 'sort icon', sortState: 'id-desc'}, {icon: 'sort icon', sortState: 'id-asc'}]},
  'title': {state: 0, allStates: [{icon: 'sort alphabet down icon', sortState: 'a-z'}, {icon: 'sort alphabet down alternate icon', sortState: 'z-a'}]},
  'year': {state: 0, allStates: [{icon: 'sort numeric down icon', sortState: 'year-asc'}, {icon: 'sort numeric down alternate icon', sortState: 'year-desc'}]},
}

function sortSeries(elem, sortBy) {
  // Update sort state property
  let {state, allStates} = sortStates[sortBy];
  let {sortState} = allStates[state];
  window.localStorage.setItem('series-sort-order', sortState);

  // Re-query current page
  getAllSeries();

  // Wait for rotation to finish, then change icon state
  document.getElementById(elem.firstElementChild.id).classList.toggle('rotate');
  setTimeout(() => {
    sortStates[sortBy].state = (sortStates[sortBy].state + 1) % 2;
    let {icon} = sortStates[sortBy].allStates[sortStates[sortBy].state];
    elem.firstElementChild.className = icon;
    // Update local storage for sort setting
    window.localStorage.setItem('series-sort-order', sortState);
  }, 500); // Timeout set to match the transition duration
}
