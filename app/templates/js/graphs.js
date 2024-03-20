{% if False %}
import {Snapshot} from './.types.js';
{% endif %}

function initializeCardsGraph(labels, rawData) {
  const chartContext = document.getElementById('titleCardsGraph');
  new Chart(chartContext, {
    type: 'line',
    data: {
      fill: true,
      stepped: true,
      labels: labels,
      datasets: {
        
      },
    },
    options: {
      responsive: true,
      stacked: false,
      interaction: {
        intersect: false,
        axis: 'x'
      },
      plugins: {
        filler: {
          propagate: false
        },
        title: {
          display: true,
          text: (ctx) => 'Title Cards Created',
        }
      },
      scales: {
        x: {
          type: 'time',
          time: {
            // Luxon format string
            tooltipFormat: 'DD T'
          },
          title: {
            display: true,
            text: 'Date'
          }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
        },
      }
    }
  });
}

function getSnapshots() {
  // Get search params from URL
  const params = new URLSearchParams(window.location.search);
  const previousDays = params.get('days') || 14;
  const slice = params.get('slice') || 1;

  // Write params to URL
  params.set('days', previousDays);
  params.set('slice', slice);
  window.history.pushState({}, '', `${window.location.origin}${window.location.pathname}?${params.toString()}`);

  $.ajax({
    type: 'GET',
    url: `/api/statistics/snapshots?previous_days=${previousDays}&slice=${slice}`,
    /**
     * Snapshots queried, populate graph
     * @param {Snapshot} snapshots - Snapshots to populate the graph with.
     */
    success: snapshots => {
      const labels = snapshots.map(snapshot => new Date(snapshot.timestamp));
      const datasets = [
        {
          label: 'Series',
          data: snapshots.map(snapshot => snapshot.series),
        },
        {
          label: 'Episodes',
          data: snapshots.map(snapshot => snapshot.episodes),
          yAxisID: 'yCards',
        },
        // {
        //   label: 'Blueprints',
        //   data: snapshots.map(snapshot => snapshot.blueprints),
        // },
        {
          label: 'Title Cards',
          data: snapshots.map(snapshot => snapshot.cards),
          yAxisID: 'yCards',
        },
        // {
        //   label: 'Fonts',
        //   data: snapshots.map(snapshot => snapshot.fonts),
        // },
        {
          label: 'Loaded Title Cards',
          data: snapshots.map(snapshot => snapshot.loaded),
          yAxisID: 'yCards',
        },
        // {
        //   label: 'Syncs',
        //   data: snapshots.map(snapshot => snapshot.syncs),
        // },
        // {
        //   label: 'Templates',
        //   data: snapshots.map(snapshot => snapshot.templates),
        // },
        {
          label: 'Title Cards Created',
          data: snapshots.map(snapshot => snapshot.cards_created),
          fill: 'origin',
          yAxisID: 'yTotalCards',
        },
        {
          label: 'Title Card Filesize',
          data: snapshots.map(snapshot => snapshot.filesize / 1e6),
          yAxisID: 'yFilesize'
        }
      ];

      const ctx = document.getElementById('graph');
      const TOTAL_DELAY = 2000;
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          fill: true,
          stepped: true,
          datasets: datasets
        },
        options: {
          // animation: {
          //   x: {
          //     type: 'number',
          //     easing: 'linear',
          //     duration: TOTAL_DELAY,
          //     from: NaN,
          //     delay(ctx) {
          //       if (ctx.type !== 'data' || ctx.xStarted) {
          //         return 0;
          //       }
          //       ctx.xStarted = true;
          //       return ctx.index * (TOTAL_DELAY / labels.length);
          //     }
          //   },
          // },
          responsive: true,
          stacked: false,
          interaction: {
            intersect: false,
            axis: 'x'
          },
          plugins: {},
          scales: {
            x: {
              type: 'time',
              time: {
                // Luxon format string
                tooltipFormat: 'DD T'
              },
              grid: {
                drawOnChartArea: false,
              },
              title: {
                display: true,
                text: 'Date'
              },
            },
            y: {
              type: 'linear',
              display: true,
              position: 'left',
            },
            yCards: {
              type: 'linear',
              display: true,
              position: 'left',
              grid: {
                drawOnChartArea: false,
              },
            },
            yTotalCards: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: '# Title Cards',
              },
              grid: {
                drawOnChartArea: false,
              }
            },
            yFilesize: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: 'Megabytes',
              },
              grid: {
                drawOnChartArea: false,
              }
            }
          }
        }
      });

      // -----------------------------------------------------------------------
      const countDatasets = [
        {
          label: 'Blueprints',
          data: snapshots.map(snapshot => snapshot.blueprints),
        },
        {
          label: 'Fonts',
          data: snapshots.map(snapshot => snapshot.fonts),
        },
        {
          label: 'Syncs',
          data: snapshots.map(snapshot => snapshot.syncs),
        },
        {
          label: 'Templates',
          data: snapshots.map(snapshot => snapshot.templates),
        },
      ];

      const countCtx = document.getElementById('dbCountsGraph');
      new Chart(countCtx, {
        type: 'line',
        data: {
          labels: labels,
          fill: true,
          stepped: true,
          datasets: countDatasets,
        },
        options: {
          responsive: true,
          stacked: false,
          interaction: {
            intersect: false,
            axis: 'x'
          },
          plugins: {},
          scales: {
            x: {
              type: 'time',
              time: {
                // Luxon format string
                tooltipFormat: 'DD T'
              },
              title: {
                display: true,
                text: 'Date'
              }
            },
            y: {
              type: 'linear',
              display: true,
              position: 'left',
            },
          }
        }
      });
    },
  });
}

function initAll() {
  getSnapshots();
}