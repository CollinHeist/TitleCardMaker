// Get all series and load their cards into HTML
async function getAllSeries(page=1) {
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
  const template = document.querySelector('#series-template');
  let allSeriesCards = allSeries.map(series => {
    const clone = template.content.cloneNode(true);
    const topDiv = clone.querySelector('div');
    // Set sorting attributes
    topDiv.setAttribute('data-series-id', series.id);
    topDiv.setAttribute('data-series-sort-name', series.sort_name);
    topDiv.setAttribute('data-series-year', series.year);
    // Poster
    const img = clone.querySelector('img');
    img.src = series.small_poster_url; img.alt = `Poster for ${series.name}`;
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
  document.getElementById('series-list').replaceChildren(...allSeriesCards);
  $('#series-list .card').transition({animation: 'scale', interval: 15});
  $('.progress').progress({duration: 2000});

  // Update pagination
  updatePagination({
    paginationElementId: 'pagination',
    navigateFunction: getAllSeries,
    page: allSeriesData.page,
    pages: allSeriesData.pages,
    amountVisible: isSmallScreen() ? 5 : 25,
    hideIfSinglePage: true,
  });

  // Refresh theme for any newly added HTML
  refreshTheme();
  // Dim Series posters on hover
  $('.ui.cards .image').dimmer({
    on: 'ontouchstart' in document.documentElement ? 'click' : 'hover'
  });
}

// Get all statistics and load them into HTML
async function getAllStatistics() {
  const statistics = await fetch('/api/statistics').then(resp => resp.json());
  const statisticsElement = document.getElementById('statistics');
  const template = document.querySelector('#statistic-template');
  statistics.forEach(({value_text, unit, description}) => {
    const clone = template.content.cloneNode(true);
    clone.querySelector('.statistic').title = description;
    clone.querySelector('.value').innerText = value_text;
    clone.querySelector('.label').innerText = unit;
    statisticsElement.appendChild(clone);
  });
}

async function initAll() {
  getAllStatistics();
  getAllSeries();

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
  // Get all card elements
  let cardList = $(".card");
  let {state, allStates} = sortStates[sortBy];
  let {sortState} = allStates[state];

  cardList.sort((a, b) => {
    switch (sortState) {
      case 'id-asc': return $(a).data('series-id')-$(b).data('series-id');
      case 'id-desc': return $(b).data('series-id')-$(a).data('series-id');
      case 'a-z': return String($(a).data('series-sort-name')).localeCompare(String($(b).data('series-sort-name')));
      case 'z-a': return String($(b).data('series-sort-name')).localeCompare(String($(a).data('series-sort-name')));
      case 'year-asc': return $(a).data('series-year')-$(b).data('series-year');
      case 'year-desc': return $(b).data('series-year')-$(a).data('series-year');
      default: return 0;
    }
  });
  // Return newly sorted list
  $("#series-list").append(cardList);

  // Rotate icon
  document.getElementById(elem.firstElementChild.id).classList.toggle('rotate');

  // Wait for rotation to finish, then change icon state
  setTimeout(() => {
    sortStates[sortBy].state = (sortStates[sortBy].state + 1) % 2;
    let {icon} = sortStates[sortBy].allStates[sortStates[sortBy].state];
    elem.firstElementChild.className = icon;
    // Update local storage for sort setting
    window.localStorage.setItem('series-sort-order', sortState);
  }, 500); // Timeout set to match the transition duration
}
