{% if False %}
import {Episode, EpisodePage} from './.types.js';
{% endif %}


function initAll() {
  $.ajax({
    type: 'GET',
    url: '/api/cards/missing',
    /** @param {EpisodePage} episodeData */
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
      const rowTemplate = document.getElementById('row-template');

      // Add rows to the table
      for (const [series_id, episodes] of Object.entries(groupedEpisodes)) {
        // Link name cell to Series page
        const row = template.content.cloneNode(true);
        row.querySelector('td[data-row="series"]').onclick = () => window.location.href = `/series/${series_id}`;
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
  });
}
