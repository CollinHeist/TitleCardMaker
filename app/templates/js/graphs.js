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
  $.ajax({
    type: 'GET',
    url: '/api/statistics/snapshots',
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
          data: snapshots.map(snapshot => snapshot.filesize),
          yAxisID: 'yFilesize'
        }
      ];

      const ctx = document.getElementById('graph');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          fill: true,
          stepped: true,
          datasets: datasets
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
                text: 'Bytes',
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