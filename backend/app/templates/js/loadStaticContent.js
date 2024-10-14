const _thisScript = document.currentScript;

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

  // Enable webhook if passed as true in the script tag
  if (Object.fromEntries(new URL(_thisScript.src).searchParams).websocket.toLowerCase() === 'true') {
    const createLogMessage = () => {
      const elem = document.createElement('div');
      elem.id = '__current_log';
      elem.onclick = () => elem.remove();
      document.querySelector('body').appendChild(elem);
      return elem;
    }
  
    const addMessage = (message) => {
      // Either replace currently displayed message or create a new one
      document.getElementById('__current_log')?.remove();
      const info = createLogMessage();
      info.innerText = message;
  
      // Remove message after 5 seconds
      setTimeout(() => {
        info.innerHTML = '<i class="exclamation circle icon"></i>';
        info.addEventListener('mouseover', () => {
          info.innerHTML = message;
        })
        info.addEventListener('mouseout', () => {
          info.innerHTML = '<i class="exclamation circle icon"></i>';
        });
      }, 5000);
    };

    // Open logging WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
    const websocket = new WebSocket(wsUrl);

    websocket.onclose = () => addMessage('Connection Closed');
    websocket.onmessage = (event) => addMessage(event.data);
    websocket.onerror = (error) => {
      console.log(error);
      addMessage('Error ocurred - see Console');
    }
  
    window.onbeforeunload = function() {
      websocket.onclose = () => {};
      websocket.close();
    };
  } else {
    console.log('Websockets have been globally disabled')
  }
});
