// Function to grab list of usernames from Emby
async function getEmbyUsernames() {
  const usernames = await fetch('/api/available/usernames/emby').then(resp => resp.json());
  $('.dropdown[data-value="emby_username"]').dropdown({
    values: usernames.map(username => {
      return {name: username, value: username, selected: username === '{{preferences.emby_username}}'};
    }),
  });
}

// Function to grab list of usernames from Jellyfin
async function getJellyfinUsernames() {
  const usernames = await fetch('/api/available/usernames/jellyfin').then(resp => resp.json());
  $('.dropdown[data-value="jellyfin_username"]').dropdown({
    values: usernames.map(username => {
      return {name: username, value: username, selected: username === '{{preferences.jellyfin_username}}'};
    }),
  });
}

// Function to get the Sonarr library mappings
async function getSonarrLibraries() {
  const libraries = await fetch('/api/settings/sonarr-libraries').then(resp => resp.json());
  libraries.forEach(({name, path}) => {
    // Append library inputs
    const libName = document.createElement('input');
    libName.type = 'text'; libName.placeholder = 'Library Name';
    libName.name = 'library_names'; libName.value = name;
    $('#sonarr-libraries-library-names').append(libName);
    // Append library paths
    const libPath = document.createElement('input');
    libPath.type = 'text'; libPath.placeholder = 'Library Path';
    libPath.name = 'library_paths'; libPath.value = path;
    $('#sonarr-libraries-library-paths').append(libPath);
  });
}

async function getLanguagePriorities() {
  const languages = await fetch('/api/settings/logo-language-priority').then(resp => resp.json());
  $('.dropdown[data-value="tmdb_logo_language_priority"]').dropdown({
    values: languages,
    clearable: true,
  });
}

function initializeFilesizeDropdown() {
  // Emby
  $('.dropdown[data-value="emby_filesize_limit_unit"]').dropdown({
    placeholder: '{{preferences.emby_filesize_limit_unit}}',
    values: ['Bytes', 'Kilobytes', 'Megabytes', 'Gigabytes', 'Terabytes'].map(unit => {
      return {name: unit, value: unit, selected: unit === '{{preferences.emby_filesize_limit_unit}}'};
    }),
  });
  // Jellyfin
  $('.dropdown[data-value="jellyfin_filesize_limit_unit"]').dropdown({
    placeholder: '{{preferences.jellyfin_filesize_limit_unit}}',
    values: ['Bytes', 'Kilobytes', 'Megabytes', 'Gigabytes', 'Terabytes'].map(unit => {
      return {name: unit, value: unit, selected: unit === '{{preferences.jellyfin_filesize_limit_unit}}'};
    }),
  });
  // Plex
  $('.dropdown[data-value="plex_filesize_limit_unit"]').dropdown({
    placeholder: '{{preferences.plex_filesize_limit_unit}}',
    values: ['Bytes', 'Kilobytes', 'Megabytes', 'Gigabytes', 'Terabytes'].map(unit => {
      return {name: unit, value: unit, selected: unit === '{{preferences.plex_filesize_limit_unit}}'};
    }),
  });
}

async function initAll() {
  getEmbyUsernames();
  getJellyfinUsernames();
  getSonarrLibraries();
  getLanguagePriorities();
  initializeFilesizeDropdown();

  // Enable dropdowns, checkboxes
  $('.ui.dropdown').dropdown();

  // Attach Tautlli modal to button
  $('#tautulli-agent-modal')
    .modal({blurring: true})
    .modal('attach events', '#tautulli-agent-button', 'show')
    .modal('setting', 'transition', 'fade up')

  // Fields to enable/disable on button presses
  const toggleFields = [
    {title: 'Emby',     toggleAPI: '/api/connection/emby',     buttonId: '#enable-emby'},
    {title: 'Jellyfin', toggleAPI: '/api/connection/jellyfin', buttonId: '#enable-jellyfin'},
    {title: 'Plex',     toggleAPI: '/api/connection/plex',     buttonId: '#enable-plex'},
    {title: 'Sonarr',   toggleAPI: '/api/connection/sonarr',   buttonId: '#enable-sonarr'},
    {title: 'TMDb',     toggleAPI: '/api/connection/tmdb',     buttonId: '#enable-tmdb'},
  ];
  toggleFields.forEach(({title, buttonId, fields, toggleAPI}) => {
    $(buttonId).checkbox({
      onChecked: () => {
        $(`#${title.toLowerCase()}-settings .field`).toggleClass('disabled', false);
        $.ajax({
          type: 'PUT',
          url: `${toggleAPI}/enable`,
          success: () => {
            $.toast({
              class: 'blue info',
              title: `Enabled Connection to ${title}`,
            });
          }, error: response => {
            $.toast({
              class: 'error',
              title: `Error Enabling Connection to ${title}`,
              message: response.responseJSON.detail,
              displayTime: 0,
            });
          }, complete: () => {}
        });
      }, onUnchecked: () => {
        $(`#${title.toLowerCase()}-settings .field`).toggleClass('disabled', true);
        $.ajax({
          type: 'PUT',
          url: `${toggleAPI}/disable`,
          success: () => {
            $.toast({
              class: 'warning',
              title: `Disabled Connection to ${title}`,
            });
          }, error: response => {
            $.toast({
              class: 'error',
              title: `Error Disabling Connection to ${title}`,
              message: response.responseJSON.detail,
              displayTime: 0,
            });
          },
        });
      },
    })
  });

  // Initialize enabled/disabled states of form fields
  toggleFields.forEach(({title, buttonId}) => {
    $(`#${title.toLowerCase()}-settings .field`).toggleClass('disabled', !$(buttonId)[0].classList.contains('checked'));
  });

  // Show filesize warning in Plex if >10 MB
  $('.field[data-value="plex_filesize_limit"]').on('change', event => {
    const number = $('.field[data-value="plex_filesize_limit"] input[name="filesize_limit_number"]').val() * 1;
    const unit = $('.field[data-value="plex_filesize_limit"] input[name="filesize_limit_unit"]').val();
    const unitValues = {
      'Bytes': 1, 'Kilobytes':  2**10, 'Megabytes':  2**20, 'Gigabytes':  2**30, 'Terabytes':  2**40
    };
    let current = unitValues[unit] * number,
        limit   = 10 * unitValues['Megabytes'];
    $('#plex-filesize-warning').toggleClass('visible', current > limit);
  })

  // Add form validation
  $('#emby-settings').form({
    on: 'blur',
    inline: true,
    fields: {
      url: ['empty'],
      api_key: ['empty', 'regExp[/^[a-f0-9]+$/gi]'],
      filesize_limit_number: {
        optional: true,
        rules: [{type: 'integer[0..]'}], 
      },
    },
  });
  $('#jellyfin-settings').form({
    on: 'blur',
    inline: true,
    fields: {
      url: ['empty'],
      api_key: ['empty', 'regExp[/^[a-f0-9]+$/gi]'],
      filesize_limit_number: {
        optional: true,
        rules: [{type: 'integer[0..]'}], 
      },
    },
  });
  $('#plex-settings').form({
    on: 'blur',
    inline: true,
    fields: {
      url: ['empty'],
      filesize_limit_number: ['integer[0..]'],
    },
  });
  $('#sonarr-settings').form({
    on: 'blur',
    inline: true,
    fields: {
      url: ['empty'],
      api_key: ['empty', 'regExp[/^[a-f0-9]+$/gi]'],
    },
  });
  $('#tmdb-settings').form({
    on: 'blur',
    inline: true,
    fields: {
      api_key: ['empty', 'regExp[/^[a-f0-9]+$/gi]'],
      minimum_width: ['integer[0..]'],
      minimum_height: ['integer[0..]'],
      logo_language_priority: ['empty', 'minLength[1]'],
    },
  });

  // Connection submit button handling
  const connections = [
    {connection: 'emby', title: 'Emby', formId: '#emby-settings', submitButtonId: '#submit-emby', successCallback: getEmbyUsernames},
    {connection: 'jellyfin', title: 'Jellyfin', formId: '#jellyfin-settings', submitButtonId: '#submit-jellyfin', successCallback: getJellyfinUsernames},
    {connection: 'plex', title: 'Plex', formId: '#plex-settings', submitButtonId: '#submit-plex'},
    {connection: 'sonarr', title: 'Sonarr', formId: '#sonarr-settings', submitButtonId: '#submit-sonarr'},
    {connection: 'tmdb', title: 'TMDb', formId: '#tmdb-settings', submitButtonId: '#submit-tmdb'},
  ]
  connections.forEach(({connection, title, formId, submitButtonId, successCallback}) => {
    $(formId).on('submit', (event) => {
      // Prevent default event form handler
      event.preventDefault();
      if (!$(formId).form('is valid')) { return; }

      // Merge multiple form inputs into list values
      let form = new FormData(event.target);
      let listData = {library_names: [], library_paths: []};
      for (const [key, value] of [...form.entries()]) {
        if (connection === 'sonarr') {
          if (key === 'library_names') { listData.library_names.push(value); }
          if (key === 'library_paths') { listData.library_paths.push(value); }
        }
        if (value === '') { form.delete(key); }
      }
      // Add checkbox status as true/false
      $.each($(formId).find('input[type=checkbox]'), (key, val) => {
        form.append($(val).attr('name'), $(val).is(':checked'))
      });

      // Submit API request
      $(submitButtonId).toggleClass('disabled loading', true);
      $.ajax({
        type: 'PATCH',
        url: `/api/connection/${connection}`,
        data: JSON.stringify({...Object.fromEntries(form.entries()), ...listData}),
        contentType: 'application/json',
        success: response => {
          if (successCallback !== undefined ) { successCallback(); }
          $.toast({
            class: 'blue info',
            title: `Updated Connection to ${title}`,
          });
          getEmbyUsernames();
          getJellyfinUsernames();
          $(formId).toggleClass('error', false);
        }, error: response => {
          $.toast({
            class: 'error',
            title: `Invalid ${title} Connection`,
            message: response.responseJSON.detail,
            displayTime: 0,
          });
          $(formId).toggleClass('error', true);
          $(`${formId} .error.message`)[0].innerHTML = `<div class="header">${response.statusText}</div><p>${response.responseText}</p>`;
        }, complete: () => {
          $(submitButtonId).toggleClass('disabled loading', false);
        }
      });
    });
  });

  // Tautulli agent form validation and submission
  $('#tautulli-agent-form').form({
    on: 'blur',
    inline: true,
    fields: {
      tautulli_url: ['empty'],
      tautulli_api_key: ['empty'],
      tautulli_agent_name: {
        optional: true,
        value: ['minLength[1]']
      },
    },
  }).on('submit', event => {
    // Prevent default event form handler, validate form
    event.preventDefault();
    if (!$('#tautulli-agent-form').form('is valid')) { return; }

    // Create JSON from form
    const data = Object.fromEntries(new FormData(event.target));

    // Submit API request
    $('#tautulli-agent-modal button').toggleClass('loading', true);
    $.ajax({
      type: 'POST',
      url: '/api/connection/tautulli/integrate',
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: response => {
        // Show toast, disable 
        $.toast({
          class: 'blue info',
          title: `Created "${data.tautulli_agent_name}" Notification Agent`,
          displayTime: 5000,
        });
        $('#tautulli-agent-modal button').toggleClass('disabled', true);
      }, error: response => {
        $.toast({
          class: 'error',
          title: 'Error Creating Notification Agent',
          message: response.responseJSON.detail,
          displayTime: 0,
        });
      }, complete: () => {
        $('#tautulli-agent-modal button').toggleClass('loading', false);
      }
    });
  });
}

// Add new library path
function addSonarrLibrary() {
  // Add library name input
  const nameInput = document.createElement('input');
  nameInput.type = 'text'; nameInput.placeholder = 'Library Name';
  nameInput.name = 'library_names';
  $('#sonarr-libraries-library-names').append(nameInput);
  // Add library path input
  const pathInput = document.createElement('input');
  pathInput.type = 'text'; pathInput.placeholder = 'Library Path';
  pathInput.name = 'library_paths';
  $('#sonarr-libraries-library-paths').append(pathInput);
}

// Query for Sonarr libraries
async function querySonarrLibraries() {
  // Get all the potential Sonarr libraries
  $('#submit-sonarr').toggleClass('loading', true);
  const libraries = await fetch('/api/connection/sonarr/libraries').then(resp => resp.json());
  if (libraries === undefined) {
    $.toast({class: 'error', message: 'Unable to query Sonarr Libraries'});
    $('#submit-sonarr').toggleClass('loading', false);
    return;
  }

  // Get the existing input elements
  let libraryNames = $('input[name="library_names"]');
  let libraryPaths = $('input[name="library_paths"]');
  for (let [index, {name, path}] of libraries.entries()) {
    // If there is no existing input for this library, add a new one
    if (libraryNames[index] === undefined) {
      addSonarrLibrary();
      libraryNames = $('input[name="library_names"]');
      libraryPaths = $('input[name="library_paths"]');
    }

    // Fill in text input fields
    libraryNames[index].value = name;
    libraryPaths[index].value = path;
  }

  // Add warning that these libraries will need to be checked
  $('#sonarr-settings').toggleClass('warning', true);
  $('#submit-sonarr').toggleClass('loading', false);
}
