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

let allConnections = [];
async function getAllConnections() {
  let allC = await fetch('/api/connection/all').then(resp => resp.json());
  allC.forEach(connection => {
    if (connection.interface !== 'Sonarr') {
      allConnections.push(connection);
    }
  });
}

/*
 * Get the global logo language priority, and initialize the dropdown
 * with those values.
 */
function getLanguagePriorities() {
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
  $('.checkbox[data-value="require_auth"]').checkbox('uncheck');
  $('#auth-settings .field').toggleClass('disabled', true);
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
          success: () => showInfoToast(`Enabled ${title} Connection`),
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
  $('form[form-type="emby"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['empty'],
      url: ['empty'],
      api_key: ['empty'],
      filesize_limit: {
        rules: [
          {
            type: 'regExp',
            value: /^\d+\s+(Bytes|Kilobytes|Megabytes)$/,
            prompt: 'Filesize limits can be in "Bytes", "Kilobytes", or "Megabytes"',
          }
        ]
      }
    },
  });
  $('form[form-type="plex"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['empty'],
      url: ['empty'],
      api_key: ['empty'],
      filesize_limit: {
        rules: [
          {
            type: 'regExp',
            value: /^\d+\s+(Bytes|Kilobytes|Megabytes)$/,
            prompt: 'Filesize limits can be in "Bytes", "Kilobytes", or "Megabytes"',
          }
        ]
      }
    },
  });
  $('form[form-type="sonarr"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['empty'],
      url: ['empty'],
      api_key: ['empty'],
      library_name: {
        rules: [
          {type: 'empty'},
        ],
      },
    },
  });
  // OLD STUFF 
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
      'Bytes': 1, 'Kilobytes':  2**10, 'Megabytes':  2**20,
      'Gigabytes':  2**30, 'Terabytes':  2**40,
    };
    let current = unitValues[unit] * number,
        limit   = 10 * unitValues['Megabytes'];
    $('#plex-filesize-warning').toggleClass('visible', current > limit);
  });
}

function updateConnection(form, connectionId, connectionType, jsonData) {
  $(`#connection${connectionId} .button[data-action="save"]`).toggleClass('loading', true);
  // Add checkbox status as true/false
  $.each($(`#connection${connectionId}`).find('input[type=checkbox]'), (key, val) => {
    form.append($(val).attr('name'), $(val).is(':checked'))
  });

  $.ajax({
    type: 'PATCH',
    url: `/api/connection/${connectionType.toLowerCase()}/${connectionId}`,
    data: JSON.stringify({
      ...Object.fromEntries(form.entries()),
      ...jsonData,
    }),
    contentType: 'application/json',
    success: updatedConnection => showInfoToast(`Updated Connection "${updatedConnection.name}"`),
    error: response => showErrorToast({title: 'Error Updating Connection', response}),
    complete: () => $(`#connection${connectionId} .button[data-action="save"]`).toggleClass('loading', false),
  });
}

function deleteConnection(connectionId) {
  $.ajax({
    type: 'DELETE',
    url: `/api/connection/${connectionId}`,
    success: () => {
      showInfoToast('Deleted Connection');
      document.getElementById(`connection${connectionId}-title`).remove();
      document.getElementById(`connection${connectionId}`).remove();
    },
    error: response => showErrorToast({title: 'Error Deleting Connection', response}),
  });
}

function initializeEmby() {
  $.ajax({
    type: 'GET',
    url: '/api/connection/emby/all',
    success: connections => {
      const embyTemplate = document.getElementById('emby-connection-template');
      const embySection = document.getElementById('emby-connections');

      // Add accordions for each Connection
      const embyForms = connections.map(connection => {
        const embyForm = embyTemplate.content.cloneNode(true);
        embyForm.querySelector('.title').id = `connection${connection.id}-title`;
        embyForm.querySelector('.content').id = `connection${connection.id}`;
        // Enable later
        embyForm.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${connection.name}`;
        embyForm.querySelector('input[name="name"]').value = connection.name;
        embyForm.querySelector('input[name="url"]').value = connection.url;
        embyForm.querySelector('input[name="api_key"]').value = connection.api_key;
        // Username later
        // SSL later
        embyForm.querySelector('input[name="filesize_limit"]').value = connection.filesize_limit;

        return embyForm;
      });
      embySection.replaceChildren(...embyForms);

      // Initialize elements of Form
      connections.forEach(connection => {
        // Enabled
        $(`#connection${connection.id} .checkbox[data-value="enabled"]`).checkbox(
          connection.enabled ? 'check' : 'uncheck'
        );
        // Query for usernames to initialize Dropdown if Connection is enabled
        if (connection.enabled) {
          $.ajax({
            type: 'GET',
            url: `/api/available/usernames/emby?interface_id=${connection.id}`,
            success: usernames => {
              $(`#connection${connection.id} .dropdown[data-value="username"]`).dropdown({
                values: usernames.map(username => {
                  return {name: username, selected: username === connection.username};
                }),
              });
            }, error: response => showErrorToast({title: `Error Querying ${connection.name} Usernames`, response}),
          });
        }
        // SSL
        $(`#connection${connection.id} .checkbox[data-value="use_ssl"]`).checkbox(
          connection.use_ssl ? 'check' : 'uncheck'
        );
        // Assign save function to button
        $(`#connection${connection.id} form`).on('submit', (event) => {
          event.preventDefault();
          if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
          updateConnection(new FormData(event.target), connection.id, 'Emby');
        });
        // Assign delete function to button
        $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
          event.preventDefault();
          deleteConnection(connection.id);
        });
      });
    }, error: response => showErrorToast({title: 'Error Querying Emby Connections', response}),
    complete: () => {
      addFormValidation;
      refreshTheme();
    },
  });
}

function initializeJellyfin() {
  $.ajax({
    type: 'GET',
    url: '/api/connection/jellyfin/all',
    success: connections => {
      const jellyfinTemplate = document.getElementById('emby-connection-template');
      const jellyfinSection = document.getElementById('jellyfin-connections');

      // Add accordions for each Connection
      const jellyfinForms = connections.map(connection => {
        const jellyfinForm = jellyfinTemplate.content.cloneNode(true);
        jellyfinForm.querySelector('.title').id = `connection${connection.id}-title`;
        jellyfinForm.querySelector('.content').id = `connection${connection.id}`;
        // Enable later
        jellyfinForm.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${connection.name}`;
        jellyfinForm.querySelector('input[name="name"]').value = connection.name;
        jellyfinForm.querySelector('input[name="url"]').value = connection.url;
        jellyfinForm.querySelector('input[name="api_key"]').value = connection.api_key;
        // Username later
        // SSL later
        jellyfinForm.querySelector('input[name="filesize_limit"]').value = connection.filesize_limit;

        return jellyfinForm;
      });
      jellyfinSection.replaceChildren(...jellyfinForms);

      // Initialize elements of Form
      connections.forEach(connection => {
        // Enabled
        $(`#connection${connection.id} .checkbox[data-value="enabled"]`).checkbox(
          connection.enabled ? 'check' : 'uncheck'
        );
        // Query for usernames to initialize Dropdown if Connection is enabled
        if (connection.enabled) {
          $.ajax({
            type: 'GET',
            url: `/api/available/usernames/jellyfin?interface_id=${connection.id}`,
            success: usernames => {
              $(`#connection${connection.id} .dropdown[data-value="username"]`).dropdown({
                values: usernames.map(username => {
                  return {name: username, selected: username === connection.username};
                }),
              });
            }, error: response => showErrorToast({title: `Error Querying ${connection.name} Usernames`, response}),
          });
        }
        // SSL
        $(`#connection${connection.id} .checkbox[data-value="use_ssl"]`).checkbox(
          connection.use_ssl ? 'check' : 'uncheck'
        );
        // Assign save function to button
        $(`#connection${connection.id} form`).on('submit', (event) => {
          event.preventDefault();
          if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
          updateConnection(new FormData(event.target), connection.id, 'Jellyfin');
        });
        // Assign delete function to button
        $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
          event.preventDefault();
          deleteConnection(connection.id);
        });
      });
    }, error: response => showErrorToast({title: 'Error Querying Jellyfin Connections', response}),
    complete: () => {
      addFormValidation();
      refreshTheme();
    },
  });
}

function initializePlex() {
  $.ajax({
    type: 'GET',
    url: '/api/connection/plex/all',
    success: connections => {
      const plexTemplate = document.getElementById('plex-connection-template');
      const plexSection = document.getElementById('plex-connections');

      // Add accordions for each Connection
      const plexForms = connections.map(connection => {
        const plexForm = plexTemplate.content.cloneNode(true);
        plexForm.querySelector('.title').id = `connection${connection.id}-title`;
        plexForm.querySelector('.content').id = `connection${connection.id}`;
        // Enable later
        plexForm.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${connection.name}`;
        plexForm.querySelector('input[name="name"]').value = connection.name;
        plexForm.querySelector('input[name="url"]').value = connection.url;
        plexForm.querySelector('input[name="api_key"]').value = connection.api_key;
        // SSL later
        // PMM integration later
        plexForm.querySelector('input[name="filesize_limit"]').value = connection.filesize_limit;

        return plexForm;
      });
      plexSection.replaceChildren(...plexForms);

      // Initialize elements of Form
      connections.forEach(connection => {
        // Enabled
        $(`#connection${connection.id} .checkbox[data-value="enabled"]`).checkbox(
          connection.enabled ? 'check' : 'uncheck'
        );
        // SSL
        $(`#connection${connection.id} .checkbox[data-value="use_ssl"]`).checkbox(
          connection.use_ssl ? 'check' : 'uncheck'
        );
        // Integrate with PMM
        $(`#connection${connection.id} .checkbox[data-value="integrate_with_pmm"]`).checkbox(
          connection.integrate_with_pmm ? 'check' : 'uncheck'
        );
        // Assign save function to button
        $(`#connection${connection.id} form`).on('submit', (event) => {
          event.preventDefault();
          updateConnection(new FormData(event.target), connection.id, 'Plex');
        });
        // Assign delete function to button
        $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
          event.preventDefault();
          if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
          deleteConnection(connection.id);
        });
      });
    }, error: response => showErrorToast({title: 'Error Querying Plex Connections', response}),
    complete: () => {
      addFormValidation();
      refreshTheme();
    },
  });
}

function initializeSonarr() {
  $.ajax({
    type: 'GET',
    url: '/api/connection/sonarr/all',
    success: connections => {
      const sonarrTemplate = document.getElementById('sonarr-connection-template');
      const sonarrSection = document.getElementById('sonarr-connections');
      const interfaceDropdownTemplate = document.getElementById('interface-dropdown-template');

      // Add accordions for each Connection
      const sonarrForms = connections.map(connection => {
        const sonarrForm = sonarrTemplate.content.cloneNode(true);
        sonarrForm.querySelector('.title').id = `connection${connection.id}-title`;
        sonarrForm.querySelector('.content').id = `connection${connection.id}`;
        // Enable later
        sonarrForm.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${connection.name}`;
        sonarrForm.querySelector('input[name="name"]').value = connection.name;
        sonarrForm.querySelector('input[name="url"]').value = connection.url;
        sonarrForm.querySelector('input[name="api_key"]').value = connection.api_key;
        // SSL later
        // Downloaded only later
        // Libraries
        connection.libraries.forEach(({name, path}) => {
          // media_server later
          const dropdown = interfaceDropdownTemplate.content.cloneNode(true);
          sonarrForm.querySelector('.field[data-value="libraries"] .field[data-value="media_server"]').appendChild(dropdown);
          const nameInput = document.createElement('input'); nameInput.name = 'library_name'; nameInput.value = name;
          sonarrForm.querySelector('.field[data-value="libraries"] .field[data-value="library_name"]').appendChild(nameInput);
          const pathInput = document.createElement('input'); pathInput.name = 'library_path'; pathInput.value = path;
          sonarrForm.querySelector('.field[data-value="libraries"] .field[data-value="library_path"]').appendChild(pathInput);
        });
        // Add/query library buttons later

        return sonarrForm;
      });
      sonarrSection.replaceChildren(...sonarrForms);

      // Initialize elements of Form
      connections.forEach(connection => {
        // Enabled
        $(`#connection${connection.id} .checkbox[data-value="enabled"]`).checkbox(
          connection.enabled ? 'check' : 'uncheck'
        );
        // SSL
        $(`#connection${connection.id} .checkbox[data-value="use_ssl"]`).checkbox(
          connection.use_ssl ? 'check' : 'uncheck'
        );
        // Downloaded only
        $(`#connection${connection.id} .checkbox[data-value="downloaded_only"]`).checkbox(
          connection.downloaded_only ? 'check' : 'uncheck'
        );
        // Library interface dropdowns
        connection.libraries.forEach(({interface_id}, index) => {
          $(`#connection${connection.id} .dropdown[data-value="interface_id"]`).eq(index).dropdown({
            placeholder: 'Media Server',
            values: allConnections.map(({id, name}) => {
              return {value: id, name: name, selected: id === interface_id};
            }),
          })
        });
        // Add new library field on click
        $(`#connection${connection.id} .button[data-action="add-library"]`).on('click', () => {
          // Add interface_id dropdown
          const dropdown = interfaceDropdownTemplate.content.cloneNode(true);
          $(`#connection${connection.id} .field[data-value="media_server"]`).append(dropdown);
          $(`#connection${connection.id} .dropdown[data-value="interface_id"]`).last().dropdown({
            placeholder: 'Media Server',
            values: allConnections.map(({id, name}) => {
              return {value: id, name: name, selected: false};
            }),
          });
          // Add library name and path inputs
          const name = document.createElement('input');
          $(`#connection${connection.id} .field[data-value="library_name"]`).append(name);
          const path = document.createElement('input');
          $(`#connection${connection.id} .field[data-value="library_path"]`).append(path);
          refreshTheme();
        });
        // Assign save function to button
        $(`#connection${connection.id} form`).on('submit', (event) => {
          event.preventDefault();
          if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
          const form = new FormData(event.target);
          // Add library list data
          const libraryData = [];
          $(`#connection${connection.id} .field[data-value="library_name"] input`).each((index, element) => {
            libraryData.push({
              name: element.value,
              path: $(`#connection${connection.id} .field[data-value="library_path"] input`).eq(index).val(),
              interface_id: $(`#connection${connection.id} .dropdown[data-value="interface_id"] input`).eq(index).val(),
            });
          });
          updateConnection(form, connection.id, 'Sonarr', {libraries: libraryData});
        });
        // Assign delete function to button
        $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
          event.preventDefault();
          deleteConnection(connection.id);
        });
      });
    }, error: response => showErrorToast({title: 'Error Querying Sonarr Connections', response}),
    complete: () => {
      addFormValidation();
      refreshTheme();
    },
  });
}

function initializeTMDb() {
  $('#tmdb-settings').on('submit', (event) => {
    // Prevent default event form handler
    event.preventDefault();
    if (!$('#tmdb-settings').form('is valid')) { return; }

    // Merge multiple form inputs into list values
    let form = new FormData(event.target);
    for (const [key, value] of [...form.entries()]) {
      if (value === '') { form.delete(key); }
    }
    // Add checkbox status as true/false
    $.each($('#tmdb-settings').find('input[type=checkbox]'), (key, val) => {
      form.append($(val).attr('name'), $(val).is(':checked'))
    });

    // Submit API request
    $('#submit-tmdb').toggleClass('disabled loading', true);
    $.ajax({
      type: 'PATCH',
      url: '/api/connection/tmdb',
      data: JSON.stringify({...Object.fromEntries(form.entries())}),
      contentType: 'application/json',
      success: () => {
        if (successCallback !== undefined ) { successCallback(); }
        showInfoToast(`Updated Connection to ${title}`);
        $('#tmdb-settings').toggleClass('error', false);
      }, error: response => {
        showErrorToast({title: `Invalid ${title} Connection`, response});
        $('#tmdb-settings').toggleClass('error', true);
        $(`${formId} .error.message`)[0].innerHTML = `<div class="header">${response.statusText}</div><p>${response.responseText}</p>`;
      }, complete: () => $('#submit-tmdb').toggleClass('disabled loading', false),
    });
  });
}

/*
 * Add a new (blank) Connection of the given type to the UI. This adjusts the
 * save button to submit a POST request instead of PATCH. 
 */
function addConnection(connectionType) {
  // Get the template for this connection - Jellyfin uses Emby template
  let template;
  if (connectionType === 'jellyfin') {
    template = document.getElementById('emby-connection-template').content.cloneNode(true);
  } else {
    template = document.getElementById(`${connectionType}-connection-template`).content.cloneNode(true);
  }
  // Disable library fields
  if (connectionType === 'sonarr') {
    template.querySelector('.info.message').classList.remove('visible');
    template.querySelector('.button[data-action="add-library"]').classList.add('disabled');
    template.querySelector('.button[data-action="query-libraries"]').classList.add('disabled');
  }
  // Turn save button into create
  template.querySelector('button[data-action="save"] > .visible.content').innerText = 'Create';
  template.querySelector('form').onsubmit = (event) => {
    event.preventDefault();
    // Parse form and submit API request
    let form = new FormData(event.target);
    $.ajax({
      type: 'POST',
      url: `/api/connection/${connectionType}/new`,
      data: JSON.stringify({...Object.fromEntries(form.entries())}),
      contentType: 'application/json',
      success: newConnection => {
        // Show toast, reload page
        showInfoToast({title:`Created Connection "${newConnection.name}"`, message: 'Reloading page..'});
        setTimeout(() => window.location.reload(), 2000);
      },
      error: response => showErrorToast({title: 'Error Creating Connection', response}),
    });
  };
  const connections = document.getElementById(`${connectionType.toLowerCase()}-connections`);
  connections.appendChild(template);
  refreshTheme();
}

async function initAll() {
  initializeEmby();
  initializeJellyfin();
  initializePlex();
  await getAllConnections();
  initializeSonarr();
  initializeTMDb();

  // Enable dropdowns, checkboxes
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
  $('.ui.accordion').accordion();

  getLanguagePriorities();
  // initializeFilesizeDropdown();
  initializeAuthForm();
  initializeFormToggles();
  // enablePlexFilesizeWarning();
  initializeTautulliForm();

  // Attach Tautlli modal to button
  $('#tautulli-agent-modal')
    .modal({blurring: true})
    .modal('attach events', '#tautulli-agent-button', 'show')
    .modal('setting', 'transition', 'fade up');
}
