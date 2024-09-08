{% if False %}
import {
  Episode, EpisodePage, Series
} from './.types.js';
{% endif %}


/**
 * Query all Episodes which are missing a Card and display them all on the page.
 */
function queryMissingCards() {
  $.ajax({
    type: 'GET',
    url: '/api/missing/cards',
    /**
     * Missing Episodes queried, populate table.
     * @param {EpisodePage} episodeData - Episodes missing Cards.
     */
    success: episodeData => {
      /** @type {Object.<number, Episode>} Group Episodes by Series*/
      const groupedEpisodes = {};
      episodeData.items.forEach(episode => {
        if (!groupedEpisodes[episode.series_id]) {
          groupedEpisodes[episode.series_id] = [];
        }
        groupedEpisodes[episode.series_id].push(episode);
      });

      // Templates
      const template = document.getElementById('missing-card-template');
      const table = document.getElementById('missing-cards');
      const rowTemplate = document.getElementById('missing-card-row-template');

      // Add rows to the table
      for (const [series_id, episodes] of Object.entries(groupedEpisodes)) {
        // Link name cell to Series page
        const row = template.content.cloneNode(true);
        row.querySelector('td[data-row="series"]').onclick = () => window.location.href = `/series/${series_id}#files`;
        row.querySelector('td[data-row="series"] [data-value="name"]').innerText = episodes[0].series.name;
        row.querySelector('td[data-row="series"] img').src = episodes[0].series.small_poster_url;
        row.querySelector('td[data-row="series"]').rowSpan = episodes.length;
        row.querySelector('td[data-row="season"]').innerText = `Season ${episodes[0].season_number}`;
        row.querySelector('td[data-row="episode"]').innerText = `Episode ${episodes[0].episode_number}`;
        row.querySelector('td[data-row="title"]').innerText = episodes[0].title;
        table.appendChild(row);

        // Add each subsequent row
        for (let i = 1; i < episodes.length; i++) {
          const row = rowTemplate.content.cloneNode(true);
          row.querySelector('td[data-row="season"]').innerText = `Season ${episodes[i].season_number}`
          row.querySelector('td[data-row="episode"]').innerText = `Episode ${episodes[i].episode_number}`
          row.querySelector('td[data-row="title"]').innerText = episodes[i].title;
          table.appendChild(row);
        }
      }

      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Querying Missing Cards', response}),
  });
}

/**
 * Query all Series which are missing logos and display them on the page.
 */
function queryMissingLogos() {
  $.ajax({
    url: '/api/missing/logos',
    /**
     * Missing logos queried, populate the table.
     * @param {Series[]} allSeries - List of Series which are missing logos.
     */
    success: allSeries => {
      // Templates
      const template = document.getElementById('missing-logo-template');
      const table = document.getElementById('missing-logos');

      allSeries.forEach(series => {
        const row = template.content.cloneNode(true);

        row.querySelector('td[data-row="series"]').onclick = () => window.location.href = `/series/${series.id}#files`;
        row.querySelector('td[data-row="series"] [data-value="name"]').innerText = series.name;
        row.querySelector('td[data-row="series"] img').src = series.small_poster_url;

        row.querySelector('td[data-row="filename"]').innerText = 'logo.png';

        table.appendChild(row);
      });

      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Querying Missing Logos', response}),
  });
}


function initAll() {
  queryMissingCards();
  queryMissingLogos();
}
