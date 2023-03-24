// // Load sidebar
// let xhr = new XMLHttpRequest();
// xhr.open('GET', '/templates/sidebar.html', true);
// xhr.onreadystatechange = function() {
//   if (this.readyState !== 4) return;
//   if (this.status !== 200) return;
//   document.getElementById('nav-menu').innerHTML = this.responseText;
// };
// xhr.send();

// // Load header
// let xhr2 = new XMLHttpRequest();
// xhr2.open('GET', '/templates/header.html', true);
// xhr2.onreadystatechange = function() {
//   if (this.readyState !== 4){return;}
//   if (this.status !== 200) {return;}
//   document.getElementById('page-header').innerHTML = this.responseText;
// };
// xhr2.send();

// Initialize header search bar
// $(document).ready(() => {
//   $.fn.search.settings.templates = {
//     standard: function(response) {
//       let elements = response.results.map(({id, name, poster_url}) => {
//         return `<a class="search result" href="/series/${id}"><div class="search content"><img src="${poster_url}" style="width: 35px; height: 50px; line-height: 50px">${name}</div></a>`;
//       });
//       return elements.join('');
//     }
//   }
//   $('#search-bar').search({
//     apiSettings: {
//       url: '/api/series/search?query={query}',
//     },
//     // minCharacters: 3
//   });
// });

// When the document is loaded...
$(document).ready(function() {
  // Load the header.html file
  $.get('/templates/header.html')
    .done(data => {
      // Inject the header HTML into the page-header element
      $('#page-header').html(data)
      // Search bar uses the search API 
      $('#search-bar').search({
        apiSettings: {
          url: '/api/series/search?query={query}&max_results=8',
        },
      });
    })
    .fail(($xhr, errorMsg) => $content.text(`Error: ${errorMsg}`));

  // Load the sidebar.html file
  $.get('/templates/sidebar.html')
    .done(data => {
      // Inject the sidebar HTML into the nev-menu element
      $('#nav-menu').html(data)
    })
    .fail(($xhr, errorMsg) => $content.text(`Error: ${errorMsg}`));

  // Search results should show a poster preview
  $.fn.search.settings.templates = {
    standard: (response) => {
      let elements = response.results.map(({id, name, poster_url}) => {
        return `<a class="search result" href="/series/${id}"><div class="search content"><img src="${poster_url}">${name}</div></a>`;
      });
      return elements.join('');
    }, message: (message, type) => {
      if (message === 'Your search returned no results') {
        return '<div class="search result">No Series found..</div>';
      } else {
        return `<div class="search result">${message}</div>`;
      }
     },
  }
  // $('.ui').toggleClass('inverted', true);
})