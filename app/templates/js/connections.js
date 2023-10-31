/*
* Get all the defined non-Sonarr Connections and update the allConnections
* list.
*/
let allConnections = [];
async function getAllConnections() {
  let allC = await fetch('/api/connection/all').then(resp => resp.json());
  allConnections = allC.filter(connection => connection.interface_type !== 'Sonarr');
}

/*
 * Get the global logo language priority, and initialize the dropdown
 * with those values.
 */
let availableLanguages = [];
async function getAvailableLanguages() {
  availableLanguages = await fetch('/api/available/logo-languages').then(resp => resp.json());
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
    },
  });
  $('form[form-type="tmdb"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['empty'],
      api_key: ['empty', 'regExp[/^[a-f0-9]+$/gi]'],
      minimum_dimensions: ['empty', 'regExp[/^\d+x\d+$/gi]'],
      logo_language_priority: ['empty', 'minLength[1]'],
    },
  });
}

/*
 * Add form validation to the Tautulli integration form, and assign the
 * API request to the form submission.
 */
function initializeTautulliForm(plexInterfaceId) {
  // Add form validation
  $('#tautulli-agent-form').form({
    on: 'blur',
    inline: true,
    fields: {
      url: ['empty'],
      api_key: ['empty'],
      agent_name: {
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
      url: `/api/connection/tautulli/integrate?plex_interface_id=${plexInterfaceId}`,
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: () => {
        // Show toast, disable 
        $.toast({
          class: 'blue info',
          title: `Created "${data.agent_name}" Notification Agent`,
          displayTime: 5000,
        });
        $('#tautulli-agent-modal button').toggleClass('disabled', true);
        $(`#connection${plexInterfaceId} .button[data-action="tautulli"]`).toggleClass('disabled', true);
      }, error: response => showErrorToast({title: 'Error Creating Notification Agent', response}),
      complete: () => $('#tautulli-agent-modal button').toggleClass('loading', false),
    });
  });
}

/*
 * Add the required HTML elements for a new Sonarr library field to the Form
 * of the Connection with the given ID.
 */
function addSonarrLibraryField(connectionId) {
  // Add interface_id dropdown
  const interfaceDropdownTemplate = document.getElementById('interface-dropdown-template');
  const dropdown = interfaceDropdownTemplate.content.cloneNode(true);
  $(`#connection${connectionId} .field[data-value="media_server"]`).append(dropdown);
  $(`#connection${connectionId} .dropdown[data-value="interface_id"]`).last().dropdown({
    placeholder: 'Media Server',
    values: allConnections.map(({id, name}) => {
      return {value: id, name: name, selected: false};
    }),
  });
  // Add library name and path inputs
  const name = document.createElement('input');
  $(`#connection${connectionId} .field[data-value="library_name"]`).append(name);
  const path = document.createElement('input');
  $(`#connection${connectionId} .field[data-value="library_path"]`).append(path);
  refreshTheme();
}

/*
 * Submit an API request to update the given Connection. This parses the given
 * form, and adds any checkboxes or given jsonData to the submitted JSON object.
 */
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

/*
 * Display a temporary modal which asks the user to confirm the Connection
 * deletion. If confirmed, then submit an API request to delete the Connection
 * with the given ID. If that is successful, then the HTML element(s) for this
 * Connection are removed from the page and the Sonarr connections are
 * re-initialized (so they may display the correct library dropdowns).
 */
function deleteConnection(connectionId) {
  $.modal({
    classTitle: 'ui icon header',
    title: '<i class="trash icon"></i>Delete Connection?',
    class: 'basic',
    classContent: 'center aligned',
    content: '<span class="ui text">This action cannot be undone.</span><br><span class="ui text">This will delete any associated Syncs, libraries, Episode and Image sources.</span>',
    classActions: 'center aligned',
    actions: [
      {text: 'No', icon: 'remove', class: 'green ok basic inverted'},
      {
        text: 'Yes, delete this Connection',
        icon: 'trash alternate outline',
        class: 'red inverted',
        click: () => {
          $.ajax({
            type: 'DELETE',
            url: `/api/connection/${connectionId}`,
            success: () => {
              showInfoToast('Deleted Connection');
              // Delete this connection from the page, refresh Sonarr so server dropdowns update
              document.getElementById(`connection${connectionId}-title`).remove();
              document.getElementById(`connection${connectionId}`).remove();
              getAllConnections().then(initializeSonarr);
            },
            error: response => showErrorToast({title: 'Error Deleting Connection', response}),
          });
        }
      },
    ]
  }).modal('show');
}

/*
 * Initialize the Emby portion of the page with all Emby Connections.
 */
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
                  return {
                    name: username,
                    value: username,
                    selected: username === connection.username
                  };
                }),
              });
            }, error: response => showErrorToast({title: `Error Querying ${connection.name} Usernames`, response}),
          });
        } else if (connection.username) {
          const dropdown = $(`#connection${connection.id} .dropdown[data-value="username"]`);
          dropdown.toggleClass('disabled', true);
          dropdown.dropdown({
            values: [{name: connection.username, value: connection.username, selected: true}],
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
      addFormValidation();
      refreshTheme();
    },
  });
}

/*
 * Initialize the Jellyfin portion of the page with all Jellyfin Connections.
 */
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
                  return {
                    name: username,
                    value: username,
                    selected: username === connection.username
                  };
                }),
              });
            }, error: response => showErrorToast({title: `Error Querying ${connection.name} Usernames`, response}),
          });
        } else if (connection.username) {
          const dropdown = $(`#connection${connection.id} .dropdown[data-value="username"]`);
          dropdown.toggleClass('disabled', true);
          dropdown.dropdown({
            values: [{name: connection.username, value: connection.username, selected: true}],
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

/*
 * Initialize the Plex portion of the page with all Plex Connections.
 */
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
        // Assign appropriate Tautulli modal form launch to button
        $(`#connection${connection.id} .button[data-action="tautulli"]`).on('click', () => {
          initializeTautulliForm(connection.id);
          $('#tautulli-agent-modal')
            .modal({blurring: true})
            .modal('show');
        });
        // Assign save function to button
        $(`#connection${connection.id} form`).on('submit', (event) => {
          event.preventDefault();
          if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
          updateConnection(new FormData(event.target), connection.id, 'Plex');
        });
        // Assign delete function to button
        $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
          event.preventDefault();
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

/*
 * Initialize the Sonarr portion of the page with all Sonarr Connections.
 */
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
        // Remove warning
        sonarrForm.querySelector('.warning.message').remove();
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
        $(`#connection${connection.id} .button[data-action="add-library"]`).on('click', () => addSonarrLibraryField(connection.id));
        // Query libraries on click
        $(`#connection${connection.id} .button[data-action="query-libraries"]`).on('click', () => {
          $.ajax({
            type: 'GET',
            url: `/api/connection/sonarr/${connection.id}/libraries`,
            success: libraries => {
              // Add new library fields if needed
              const inputCount = $(`#connection${connection.id} .field[data-value="library_name"] input`).length;
              if (inputCount < libraries.length) {
                [...Array(libraries.length - inputCount)].map(() => addSonarrLibraryField(connection.id));
              }
              libraries.forEach(({name, path}, index) => {
                $(`#connection${connection.id} .field[data-value="library_name"] input`).eq(index).val(name);
                $(`#connection${connection.id} .field[data-value="library_path"] input`).eq(index).val(path);
              });
            }, error: response => showErrorToast({title: 'Error Querying Libraries', response}),
          });
        });
        // Assign save function to button
        $(`#connection${connection.id} form`).on('submit', (event) => {
          event.preventDefault();
          if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
          const form = new FormData(event.target);
          // Add library list data
          const libraryData = [];
          $(`#connection${connection.id} .field[data-value="library_name"] input`).each((index, element) => {
            const path = $(`#connection${connection.id} .field[data-value="library_path"] input`).eq(index).val();
            if (path !== "") {
              libraryData.push({
                name: element.value,
                path: path,
                interface_id: $(`#connection${connection.id} .dropdown[data-value="interface_id"] input`).eq(index).val(),
              });
            }
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

/*
 * Initialize the TMDb portion of the page with all TMDb Connections.
 */
function initializeTMDb() {
  $.ajax({
    type: 'GET',
    url: '/api/connection/tmdb/all',
    success: connections => {
      const tmdbTemplate = document.getElementById('tmdb-connection-template');
      const tmdbSection = document.getElementById('tmdb-connections');

      // Add accordions for each Connection
      const tmdbForms = connections.map(connection => {
        const tmdbForm = tmdbTemplate.content.cloneNode(true);
        tmdbForm.querySelector('.title').id = `connection${connection.id}-title`;
        tmdbForm.querySelector('.content').id = `connection${connection.id}`;
        // Enable later
        tmdbForm.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${connection.name}`;
        tmdbForm.querySelector('input[name="name"]').value = connection.name;
        tmdbForm.querySelector('input[name="api_key"]').value = connection.api_key;
        tmdbForm.querySelector('input[name="minimum_dimensions"]').value = connection.minimum_dimensions;
        // Language priority later
        return tmdbForm;
      });
      tmdbSection.replaceChildren(...tmdbForms);

      // Initialize elements of Form
      connections.forEach(connection => {
        // Enabled
        $(`#connection${connection.id} .checkbox[data-value="enabled"]`).checkbox(
          connection.enabled ? 'check' : 'uncheck'
        );
        // Ignore localized images
        $(`#connection${connection.id} .checkbox[data-value="ignore_localized"]`).checkbox(
          connection.ignore_localized ? 'check' : 'uncheck'
        );
        // Initialize logo language priority dropdown
        $(`#connection${connection.id} .dropdown[data-value="logo_language_priority"]`).dropdown({
          values: availableLanguages.map(language => {
            return {
              name: language.name,
              value: language.value,
              selected: connection.logo_language_priority.includes(language.value),
            };
          }),
        });
        // Assign save function to button
        $(`#connection${connection.id} form`).on('submit', (event) => {
          event.preventDefault();
          if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
          updateConnection(new FormData(event.target), connection.id, 'TMDb');
        });
        // Assign delete function to button
        $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
          event.preventDefault();
          deleteConnection(connection.id);
        });
      });
    }, error: response => showErrorToast({title: 'Error Querying TMDb Connections', response}),
    complete: () => {
      addFormValidation();
      refreshTheme();
    },
  });
}

/*
 * Add a new (blank) Connection of the given type to the UI. This adjusts the
 * save button to submit a POST request instead of PATCH. 
 */
let tempFormId = 0;
function addConnection(connectionType) {
  // Get the template for this connection - Jellyfin uses Emby template
  let template;
  if (connectionType === 'jellyfin') {
    template = document.getElementById('emby-connection-template').content.cloneNode(true);
  } else {
    template = document.getElementById(`${connectionType}-connection-template`).content.cloneNode(true);
  }
  // Add ID to form
  let formId = `new-connection${tempFormId}`
  template.querySelector('form').id = formId;
  tempFormId++;

  // Make minor adjustments
  if (connectionType === 'sonarr') {
    // Disable library fields
    template.querySelector('.button[data-action="add-library"]').classList.add('disabled');
    template.querySelector('.button[data-action="query-libraries"]').classList.add('disabled');
  } else if (connectionType === 'tmdb') {
    // Disable dropdown until added
    template.querySelector('.field[data-value="logo_language_priority"]').classList.add('disabled');
  } else if (connectionType === 'emby' || connectionType === 'jellyfin') {
    // Remove username dropdown until added
    template.querySelector('.field[data-value="username"]').remove();
  }
  // Turn save button into create
  template.querySelector('button[data-action="save"] > .visible.content').innerText = 'Create';
  template.querySelector('form').onsubmit = (event) => {
    event.preventDefault();
    // Parse form and submit API request
    let form = new FormData(event.target);
    $.each($(`#${formId}`).find('input[type=checkbox]'), (key, val) => {
      form.append($(val).attr('name'), $(val).is(':checked'));
    });
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
  addFormValidation();
  $('.ui.checkbox').checkbox();
}

async function initAll() {
  initializeEmby();
  initializeJellyfin();
  initializePlex();
  await getAllConnections();
  initializeSonarr();
  await getAvailableLanguages();
  initializeTMDb();

  // Enable elements
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
  $('.ui.accordion').accordion();

  initializeAuthForm();
}
