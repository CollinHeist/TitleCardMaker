$(document).ready(function() {
  // Trigger events on keypresses
  $(document).keypress((event) => {
    if (event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA' && !event.target.isContentEditable) {
      // 'f' sets focus to search bar - e.g. "find"
      if (event.key === 'f' || event.key === 's' || event.key === '/') { $('#search-bar input').focus(); }
      // Shift + 'h' takes to home page
      else if (event.key === 'H' && event.shiftKey) { window.location.href = '/'; }
    }
  });

  // Search results should show a poster preview
  $.fn.search.settings.templates = {
    standard: response => {
      const query = $('#search-bar input').val();
      let elements = response.results.map(({id, name, poster_url}) => {
        return `<a class="search result" href="/series/${id}"><div class="search content"><img src="${poster_url}">${name}</div></a>`;
      });
      elements.push(`<a class="search result" href="/add?q=${query}">Search for "${query}"..</a>`);
      return elements.join('');
    },
    message: (message, type) => {
      if (message === 'Your search returned no results') {
        const query = $('#search-bar input').val();
        return `<a class="search result" href="/add?q=${query}">Search for "${query}"..</a>`;
      } else {
        return `<div class="search result">${message}</div>`;
      }
    },
  }

  // Search bar uses the search API
  $('#search-bar').search({
    apiSettings: {
      url: '/api/series/search?name={query}&size=10&page=1',
      onResponse: serverResponse => { return serverResponse.items; },
    },
  });
})