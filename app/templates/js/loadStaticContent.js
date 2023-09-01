// When the document is loaded...
$(document).ready(function() {
  // Load the header.html file
  $.get('/templates/header.html')
    .done(data => {
      // Inject the header HTML into the page-header element
      $('#page-header').html(data);
      
      // Search bar uses the search API 
      $('#search-bar').search({
        apiSettings: {
          url: '/api/series/search?name={query}&size=8&page=1',
          onResponse: serverResponse => { return serverResponse.items; },
        },
      });
    })
    .fail(($xhr, errorMsg) => $content.text(`Error: ${errorMsg}`));

  // Trigger events on keypresses
  $(document).keypress((event) => {
    if (event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA' && !event.target.isContentEditable) {
      // 'f' sets focus to search bar - e.g. "find"
      if (event.key === 'f' || event.key === 's') { $('#search-bar input').focus(); }
      // Shift + 'h' takes to home page
      else if (event.key === 'H' && event.shiftKey) { window.location.href = '/'; }
    }
  });

  // Load the sidebar.html file
  $.get('/templates/sidebar.html')
    .done(data => {
      // Inject the sidebar HTML into the nev-menu element
      $('#nav-menu').html(data);
    })
    .fail(($xhr, errorMsg) => $content.text(`Error: ${errorMsg}`));

  // Search results should show a poster preview
  $.fn.search.settings.templates = {
    standard: response => {
      const query = $('#search-bar input').val();
      let elements = response.results.map(({id, name, poster_url}) => {
        return `<a class="search result" href="/series/${id}"><div class="search content"><img src="${poster_url}">${name}</div></a>`;
      });
      elements.push(`<a class="search result" href="/add?q=${query}">Search for "${query}"..</a>`);
      return elements.join('');
    }, message: (message, type) => {
      if (message === 'Your search returned no results') {
        const query = $('#search-bar input').val();
        return `<a class="search result" href="/add?q=${query}">Search for "${query}"..</a>`;
      } else {
        return `<div class="search result">${message}</div>`;
      }
    },
  }
})