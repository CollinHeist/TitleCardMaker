/*
 * Submit the API request to get any available Emby usernames. If
 * successful, the Emby usernames dropdown is populated.
 */
function getEmbyUsernames() {
  $.ajax({
    type: 'GET',
    url: '/api/available/usernames/emby',
    success: usernames => {
      $('.dropdown[data-value="emby_username"]').dropdown({
        values: usernames.map(username => {
          return {
            name: username,
            value: username,
            selected: username === '{{preferences.emby_username}}'
          };
        }),
      });
    }, error: response => showErrorToast({title: 'Error Querying emby Usernames', response}),
  });
}

/*
 * Submit the API request to get any available Jellyfin usernames. If
 * successful, the Jellyfin usernames dropdown is populated.
 */
function getJellyfinUsernames() {
  $.ajax({
    type: 'GET',
    url: '/api/available/usernames/jellyfin',
    success: usernames => {
      $('.dropdown[data-value="jellyfin_username"]').dropdown({
        values: usernames.map(username => {
          return {
            name: username,
            value: username,
            selected: username === '{{preferences.jellyfin_username}}'
          };
        }),
      });
    }, error: response => showErrorToast({title: 'Error Querying Jellyfin Usernames', response}),
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

/*
 * Get the global logo language priority, and initialize the dropdown
 * with those values.
 */
async function getLanguagePriorities() {
  $.ajax({
    type: 'GET',
    url: '/api/settings/logo-language-priority',
    success: languages => {
      $('.dropdown[data-value="tmdb_logo_language_priority"]').dropdown({
        values: languages,
        clearable: true,
      });
    }, error: response => showErrorToast({title: 'Error Querying Language Priority', response}),
  });
}

/*
 * Initialize all the media server filesize limit dropdowns.
 */
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

/*
 * Submit the API request to enable authentication. If successful the page
 * is redirected to the login page with a callback to redirect back here
 * if the subsequent login is successful.
 */
function enableAuthentication() {
  $.ajax({
    type: 'POST',
    url: '/api/auth/enable',
    success: () => {
      // Show toast, redirect to login page
      $.toast({
        class: 'blue info',
        title: 'Enabled Authentication',
        message: 'You will be redirected to the login page..'
      });
      // After 2.5s, redirect to login with redirect back here
      setTimeout(() => {
        window.location.href = '/login?redirect=/connections';
      }, 2500);
    }, error: response => {
      showErrorToast({title: 'Error Enabling Authentication', response});
    },
  });
}

/*
 * Submit the API request to disable authentication. If successful the
 * authentication section is disabled.
 */
function disableAuthentication() {
  $.ajax({
    type: 'POST',
    url: '/api/auth/disable',
    success: () => {
      // Uncheck checkbox, disable fields
      $('.checkbox[data-value="require_auth"]').checkbox('uncheck');
      $('#auth-settings .field').toggleClass('disabled', true);
      // Clear username input
      $('#auth-settings input[name="username"]')[0].value = '';
      // Show toast
      $.toast({class: 'warning', title: 'Disabled Authentication'});
    }, error: response => {
      showErrorToast({title: 'Error Disabling Authentication', response});
    },
  });
}

/*
 * Submit the API request to edit the current active User's credentials.
 * If successful, the TCM token cookie is cleared, and the page is
 * redirected to the login page with a callback to redirect back here.
 */
function editUserAuth() {
  // Submit API request to update user credentials
  $.ajax({
    type: 'POST',
    url: '/api/auth/edit',
    data: JSON.stringify({
      username: $('#auth-settings input[name="username"]')[0].value,
      password: $('#auth-settings input[name="password"]')[0].value,
    }), contentType: 'application/json',
    success: () => {
      $.toast({
        class: 'blue info',
        title: 'Credentials Updated',
        message: 'You will be redirected to the login page..',
      });

      // Clear cookie
      document.cookie = `tcm_token=;Max-Age=0;path=/;SameSite=Lax`;

      // Redirect back here
      setTimeout(() => {
        window.location.href = '/login?redirect=/connections';
      }, 1000);
    }, error: response => {
      showErrorToast({title: 'Unable to Update Credentials', response});
    },
  });
}

/*
 * Initialize the Authorization form/section. This populates the current
 * User's username (if applicable), enabled/disables fields, and assigns
 * functions to all events/presses.
 */
function initializeAuthForm() {
  // Initialize username field with current user
  $.ajax({
    type: 'GET',
    url: '/api/auth/active',
    success: username => {
      if (username !== null) {
        $('#auth-settings input[name="username"]')[0].value = username;
      }
    }, error: response => {
      showErrorToast({title: 'Error Querying Authorized Users', response});
    },
  })

  // Enable/disable auth fields based on initial state
  {% if preferences.require_auth %}
  $('.checkbox[data-value="require_auth"]').checkbox('check');
  $('#auth-settings .field').toggleClass('disabled', false);
  {% else %}
  $('#auth-settings .field').toggleClass('disabled', true);
  $('.checkbox[data-value="require_auth"]').checkbox('uncheck');
  {% endif %}

  // Assign checked/unchecked functions
  $('.checkbox[data-value="require_auth"]').checkbox({
    onChecked: enableAuthentication,
    onUnchecked: disableAuthentication,
  });

  // Assign edit API request to button press
  $('#auth-settings button').on('click', event => {
    event.preventDefault();
    editUserAuth();
  });
}

/*
 * Initialize the enable/disable connection toggles for all the non-auth
 * forms. This assigns the /enable API request to the checkbox checking,
 * and /disable to the unchecking. It then initializes the form enabled/
 * disabled statuses themselves.
 */
function initializeFormToggles() {
  // Fields to enable/disable on button presses
  const toggleFields = [
    {title: 'Emby',     toggleAPI: '/api/connection/emby',     buttonId: '#enable-emby'},
    {title: 'Jellyfin', toggleAPI: '/api/connection/jellyfin', buttonId: '#enable-jellyfin'},
    {title: 'Plex',     toggleAPI: '/api/connection/plex',     buttonId: '#enable-plex'},
    {title: 'Sonarr',   toggleAPI: '/api/connection/sonarr',   buttonId: '#enable-sonarr'},
    {title: 'TMDb',     toggleAPI: '/api/connection/tmdb',     buttonId: '#enable-tmdb'},
  ];
  toggleFields.forEach(({title, buttonId, toggleAPI}) => {
    $(buttonId).checkbox({
      onChecked: () => {
        // Enable connection
        $(`#${title.toLowerCase()}-settings .field`).toggleClass('disabled', false);
        $.ajax({
          type: 'PUT',
          url: `${toggleAPI}/enable`,
          success: () => $.toast({class: 'blue info', title: `Enabled ${title} Connection`}),
          error: response => showErrorToast({title: `Error Enabling ${title} Connection`, response})
        });
      }, onUnchecked: () => {
        // Disable connection
        $(`#${title.toLowerCase()}-settings .field`).toggleClass('disabled', true);
        $.ajax({
          type: 'PUT',
          url: `${toggleAPI}/disable`,
          success: () => $.toast({class: 'warning', title: `Disabled ${title} Connection`}),
          error: response => showErrorToast({title: `Error Disabling ${title} Connection`, response}),
        });
      },
    })
  });

  // Initialize enabled/disabled states of form fields
  toggleFields.forEach(({title, buttonId}) => {
    $(`#${title.toLowerCase()}-settings .field`).toggleClass('disabled', !$(buttonId)[0].classList.contains('checked'));
  });
}

/*
 * Add form validation for all the non-Auth and Tautulli connection
 * forms.
 */
function addFormValidation() {
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
}

/*
 * Add form validation to the Tautulli integration form, and assign the
 * API request to the form submission.
 */
function initializeTautulliForm() {
  // Add form validation
  $('#tautulli-agent-form').form({
    on: 'blur',
    inline: true,
    fields: {
      tautulli_url: ['empty'],
      tautulli_api_key: ['empty'],
      tautulli_agent_name: {
        optional: true,
        value: ['minLength[1]'],
      },
    },
  }).on('submit', event => {
    // Prevent default event form handler
    event.preventDefault();
    // If the form is not valid, exit
    if (!$('#tautulli-agent-form').form('is valid')) { return; }

    // Submit API request
    const data = Object.fromEntries(new FormData(event.target));
    $('#tautulli-agent-modal button').toggleClass('loading', true);
    $.ajax({
      type: 'POST',
      url: '/api/connection/tautulli/integrate',
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: () => {
        // Show toast, disable 
        $.toast({
          class: 'blue info',
          title: `Created "${data.tautulli_agent_name}" Notification Agent`,
          displayTime: 5000,
        });
        $('#tautulli-agent-modal button').toggleClass('disabled', true);
      }, error: response => showErrorToast({title: 'Error Creating Notification Agent', response}),
      complete: () => $('#tautulli-agent-modal button').toggleClass('loading', false)
    });
  });
}

/*
 * Add an onChange event to the Plex filesize limit field that displays
 * the filesize limit warning if a size >10 MB is entered.
 */
function enablePlexFilesizeWarning() {
  $('.field[data-value="plex_filesize_limit"]').on('change', () => {
    const number = $('.field[data-value="plex_filesize_limit"] input[name="filesize_limit_number"]').val() * 1;
    const unit = $('.field[data-value="plex_filesize_limit"] input[name="filesize_limit_unit"]').val();
    const unitValues = {
      'Bytes': 1, 'Kilobytes':  2**10, 'Megabytes':  2**20, 'Gigabytes':  2**30, 'Terabytes':  2**40
    };
    let current = unitValues[unit] * number,
        limit   = 10 * unitValues['Megabytes'];
    $('#plex-filesize-warning').toggleClass('visible', current > limit);
  });
}

async function initAll() {
  {% if preferences.use_emby %}
  getEmbyUsernames();
  {% endif %}
  {% if preferences.use_jellyfin %}
  getJellyfinUsernames();
  {% endif %}
  {% if preferences.use_sonarr %}
  getSonarrLibraries();
  {% endif %}
  addFormValidation();
  getLanguagePriorities();
  initializeFilesizeDropdown();
  initializeAuthForm();
  initializeFormToggles();
  enablePlexFilesizeWarning();
  initializeTautulliForm();

  // Enable dropdowns, checkboxes
  $('.ui.dropdown').dropdown();

  // Attach Tautlli modal to button
  $('#tautulli-agent-modal')
    .modal({blurring: true})
    .modal('attach events', '#tautulli-agent-button', 'show')
    .modal('setting', 'transition', 'fade up')

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
      let libraryNames = [],
          libraryPaths = [];
      for (const [key, value] of [...form.entries()]) {
        if (connection === 'sonarr') {
          if (key === 'library_names') { libraryNames.push(value); }
          if (key === 'library_paths') { libraryPaths.push(value); }
        }
        if (value === '') { form.delete(key); }
      }
      let sonarr_libraries = libraryNames.map((name, index) => ({ name, path: libraryPaths[index] }));
      // Add checkbox status as true/false
      $.each($(formId).find('input[type=checkbox]'), (key, val) => {
        form.append($(val).attr('name'), $(val).is(':checked'))
      });

      // Submit API request
      $(submitButtonId).toggleClass('disabled loading', true);
      $.ajax({
        type: 'PATCH',
        url: `/api/connection/${connection}`,
        data: JSON.stringify({...Object.fromEntries(form.entries()), libraries: sonarr_libraries}),
        contentType: 'application/json',
        success: () => {
          if (successCallback !== undefined ) { successCallback(); }
          $.toast({
            class: 'blue info',
            title: `Updated Connection to ${title}`,
          });
          getEmbyUsernames();
          getJellyfinUsernames();
          $(formId).toggleClass('error', false);
        }, error: response => {
          showErrorToast({title: `Invalid ${title} Connection`, response});
          $(formId).toggleClass('error', true);
          $(`${formId} .error.message`)[0].innerHTML = `<div class="header">${response.statusText}</div><p>${response.responseText}</p>`;
        }, complete: () => {
          $(submitButtonId).toggleClass('disabled loading', false);
        }
      });
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
