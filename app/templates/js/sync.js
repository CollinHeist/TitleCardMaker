/*
 * Submit an API request to get all defined Connections. The dropdowns for each
 * connection type are initialized with the servers for that connection. Any
 * types without connections are removed from the page.
 */
function initConnectionDropdowns() {
  $.ajax({
    type: 'GET',
    url: '/api/connection/all',
    success: connections => {
      const emby = connections.filter(({interface_type}) => interface_type === 'Emby');
      const jellyfin = connections.filter(({interface_type}) => interface_type === 'Jellyfin');
      const plex = connections.filter(({interface_type}) => interface_type === 'Plex');
      const sonarr = connections.filter(({interface_type}) => interface_type === 'Sonarr');

      $('.dropdown[data-type="emby_connections"]').dropdown({
        placeholder: 'Connection',
        values: emby.map(({id, name}) => {
          return {name, value: id};
        }),
      });
      $('.dropdown[data-type="jellyfin_connections"]').dropdown({
        placeholder: 'Connection',
        values: jellyfin.map(({id, name}) => {
          return {name, value: id};
        }),
      });
      $('.dropdown[data-type="plex_connections"]').dropdown({
        placeholder: 'Connection',
        values: plex.map(({id, name}) => {
          return {name, value: id};
        }),
      });
      $('.dropdown[data-type="sonarr_connections"]').dropdown({
        placeholder: 'Connection',
        values: sonarr.map(({id, name}) => {
          return {name, value: id};
        }),
      });

      // Remove sections with no connections
      if (emby.length === 0) { $('section[data-connection="emby"]').remove(); }
      if (jellyfin.length === 0) { $('section[data-connection="jellyfin"]').remove(); }
      if (plex.length === 0) { $('section[data-connection="plex"]').remove(); }
      if (sonarr.length === 0) { $('section[data-connection="sonarr"]').remove(); }
    }, error: response => showErrorToast({title: 'Error Querying Connections', response}),
  });
}

/*
 * Get all libraries on all defined interfaces and initialize the dropdowns for
 * Emby, Jellyfin, and Plex.
 */
function getLibraries() {
  $.ajax({
    type: 'GET',
    url: '/api/available/libraries/all',
    success: libraries => {
      const emby = libraries.filter(({media_server}) => media_server === 'Emby').map(({name}) => {
        return {name, selected: false};
      });
      const jellyfin = libraries.filter(({media_server}) => media_server === 'Jellyfin').map(({name}) => {
        return {name, selected: false};
      });
      const plex = libraries.filter(({media_server}) => media_server === 'Plex').map(({name}) => {
        return {name, selected: false};
      });

      $('#emby-sync-form .dropdown[data-value="required_libraries"]').dropdown({
        placeholder: 'None',
        values: emby,
      });
      $('#emby-sync-form .dropdown[data-value="excluded_libraries"]').dropdown({
        placeholder: 'None',
        values: emby,
      });

      $('#jellyfin-sync-form .dropdown[data-value="required_libraries"]').dropdown({
        placeholder: 'None',
        values: jellyfin,
      });
      $('#jellyfin-sync-form .dropdown[data-value="excluded_libraries"]').dropdown({
        placeholder: 'None',
        values: emby,
      });

      $('#plex-sync-form .dropdown[data-value="required_libraries"]').dropdown({
        placeholder: 'None',
        values: plex,
      });
      $('#plex-sync-form .dropdown[data-value="excluded_libraries"]').dropdown({
        placeholder: 'None',
        values: plex,
      });
    }, error: response => showErrorToast({title: 'Error Querying Libraries', response}),
  });
}

/*
 * Get all tags on all defined Sonarr interfaces and initialize the dropdowns.
 */
function getTags() {
  $.ajax({
    type: 'GET',
    url: '/api/available/tags/sonarr',
    success: tags => {
      $('.dropdown[dropdown-type="sonarr-tags"]').dropdown({
        allowAdditions: true,
        placeholder: 'None',
        values: tags.map(({label}) => {
          return {name: label, value: label, selected: false};
        })
      })
    }, error: response => showErrorToast({title: 'Error Querying Tags', response}),
  });
}

function getTemplates() {
  $.ajax({
    type: 'GET',
    url: '/api/available/templates',
    success: availableTemplates => {
      $('.dropdown[data-value="template_ids"]').dropdown({
        placeholder: 'None',
        values: getActiveTemplates(null, availableTemplates),
      });
    }, error: response => showErrorToast({'title': 'Error Getting Template List', response}),
  })
}

function showEditModel(sync) {
  // Get reference New Sync modal to edit
  const refModalId = `add-${sync.interface}-sync-modal`.toLowerCase();
  const editModal = document.getElementById(refModalId).cloneNode(true);
  editModal.id = `edit-sync${sync.id}`;
  editModal.querySelector('form').id =  `edit-sync${sync.id}-form`;
  document.querySelector('body').append(editModal);
  $('.ui.dropdown[dropdown-type="server-tags"]').dropdown({allowAdditions: true});
  $('.ui.checkbox').checkbox();
  // Fill out existing data
  $(`#edit-sync${sync.id} .header`)[0].innerText = `Editing Sync "${sync.name}"`;
  $(`#edit-sync${sync.id} .dropdown[data-value="interface_id"]`).dropdown('set selected', sync.interface_id);
  $(`#edit-sync${sync.id} input[name="name"]`)[0].value = sync.name;
  $(`#edit-sync${sync.id} .dropdown[data-value="template_ids"]`).dropdown('set selected', sync.template_ids);
  $(`#edit-sync${sync.id} .dropdown[data-value="required_tags"]`).dropdown('set selected', sync.required_tags);
  $(`#edit-sync${sync.id} .dropdown[data-value="required_libraries"]`).dropdown('set selected', sync.required_libraries);
  $(`#edit-sync${sync.id} .dropdown[data-value="required_series_type"]`).dropdown('set selected', sync.required_series_type);
  $(`#edit-sync${sync.id} .dropdown[data-value="excluded_tags"]`).dropdown('set selected', sync.excluded_tags);
  $(`#edit-sync${sync.id} .dropdown[data-value="excluded_libraries"]`).dropdown('set selected', sync.excluded_libraries);
  $(`#edit-sync${sync.id} .dropdown[data-value="excluded_series_type"]`).dropdown('set selected', sync.excluded_series_type);
  const downloadedCheckbox = $(`#edit-sync${sync.id} input[name="downloaded_only"]`);
  if (downloadedCheckbox.length) { downloadedCheckbox[0].checked = sync.downloaded_only; }
  const monitoredCheckbox = $(`#edit-sync${sync.id} input[name="monitored_only"]`);
  if (monitoredCheckbox.length) { monitoredCheckbox[0].checked = sync.monitored_only; }
  // Query tags/libraries when connection field is changed
  $(`#edit-sync${sync.id} .dropdown[data-value="interface_id"] input`).change(async () => {
    if (sync.interface === 'Sonarr') {
      const tags = await fetch(`/api/available/tags/sonarr?interface_id=${sync.interface_id}`).then(resp => resp.json());
      $(`#edit-sync${sync.id} .dropdown[data-value="required_tags"]`)
    }
  });
  // Change "save" button text
  $(`#edit-sync${sync.id} [data-value="primary-button"]`)[0].innerText = 'Save Changes';
  // Delete form assignment
  $(`#edit-sync${sync.id} button`)[0].setAttribute('form', `edit-sync${sync.id}-form`);
  // Submit API request on button press
  $(`#edit-sync${sync.id} button`).on('click', (event) => {
    event.preventDefault();
    // Turn form into object, turning multi selects into arrays
    let form = new FormData(document.getElementById(`edit-sync${sync.id}-form`));
    let dataObj = {downloaded_only: false, monitored_only: false};
    for (let [name, value] of [...form.entries()]) {
      if (name.includes('_tags') || name.includes('_libraries') || name === 'template_ids') {
        if (value !== '') { dataObj[name] = value.split(',');
        } else { dataObj[name] = []; }
      } else if (value !== '') { dataObj[name] = value; }
    }

    $.ajax({
      type: 'PATCH',
      url: `/api/sync/${sync.id}`,
      data: JSON.stringify(dataObj),
      contentType: 'application/json',
      success: updatedSync => {
        showInfoToast(`Updated Sync "${updatedSync.name}"`);
        getAllSyncs();
      }, error: response => showErrorToast({title: 'Error Editing Sync', response}),
      complete: () => {
        $(`#edit-sync${sync.id}`).modal('hide');
        $(`#edit-sync${sync.id}`).remove();
      }
    });
  });

  $(`#edit-sync${sync.id}`).modal('show');
}

async function showDeleteSyncModal(syncId) {
  // Get list of Series associated with this Sync
  const allSeriesResponse = await fetch(`/api/series/search?sync_id=${syncId}&size=25`).then(resp => resp.json());
  const seriesElements = allSeriesResponse.items.map(({name, year}) => {
    return `<li>${name} (${year})</li>`
  });
  // More than 25 Series, add indicator of total amount being deleted
  if (allSeriesResponse.total > 25) {
    seriesElements.push(`<li><span class="ui red text">${allSeriesResponse.total-25} more Series...</span></li>`)
  }
  $('#delete-sync-modal [data-value="series-list"]')[0].innerHTML = seriesElements.join('');
  // Attach functions to delete buttons
  $('#delete-sync-modal .button[data-action="delete-sync-only"]')
    .off('click')
    .on('click', () => {
      $(`#sync${syncId}`).toggleClass('red double loading', true);
      $.ajax({
        type: 'DELETE',
        url: `/api/sync/delete/${syncId}?delete_series=false`,
        success: () => {
          showInfoToast('Deleted Sync');
          getAllSyncs();
        }, error: response => {
          showErrorToast({title: 'Error Deleting Sync', response});
          $(`#sync${syncId}`).toggleClass('red double loading', false);
        },
      });
    });
  $('#delete-sync-modal .button[data-action="delete-sync-and-series"]')
    .off('click')
    .on('click', () => {
      $(`#sync${syncId}`).toggleClass('red double loading', true);
      $.ajax({
        type: 'DELETE',
        url: `/api/sync/delete/${syncId}?delete_series=true`,
        success: () => {
          showInfoToast('Deleted Sync and associated Series');
          getAllSyncs();
        },
        error: response => {
          showErrorToast({title: 'Error Deleting Sync', response});
          $(`#sync${syncId}`).toggleClass('red double loading', false);
        },
      });
    });

  $('#delete-sync-modal').modal('show');
}

async function getAllSyncs() {
  const syncElements = [
    {source: 'emby', elementID: 'emby-syncs'},
    {source: 'jellyfin', elementID: 'jellyfin-syncs'},
    {source: 'plex', elementID: 'plex-syncs'},
    {source: 'sonarr', elementID: 'sonarr-syncs'},
  ];

  syncElements.forEach(async ({source, elementID}) => {
    // Skip if this element is not present, e.g. interface is disabled
    const syncElement = document.getElementById(elementID);
    if (!syncElement) { return; }

    const syncs = await fetch(`/api/sync/${source}/all`).then(resp => resp.json());
    const templateElement = document.querySelector('#sync-card-template');
    const newChildren = syncs.map(syncObject => {
      const {id, name} = syncObject;
      // Clone the card template, adjust header and meta text
      const clone = templateElement.content.cloneNode(true);
      clone.querySelector('.card').id = `sync${id}`;
      clone.querySelector('.header').innerText = name;
      clone.querySelector('.sync-meta').innerText = `Sync ID ${id}`;

      // Edit sync if clicked
      clone.querySelector('i.edit').onclick = () => showEditModel(syncObject);

      // Launch delete sync modal on click of the delete icon
      clone.querySelector('i.trash').onclick = () => showDeleteSyncModal(id);

      // Add sync API request to sync icon
      clone.querySelector('i.sync').onclick = () => {
        // Add loading indicator, create toast
        $(`#sync${id} >* i.sync`).toggleClass('loading blue', true);
        showInfoToast(`Started Syncing "${name}"`);
        // Submit API request, show toast of results
        $.ajax({
          type: 'POST',
          url: `/api/sync/${id}`,
          success: response => {
            let message = '';
            for (let {id, name} of response) {
              message += `<a class="item" href="/series/${id}">${name}</a>`;
            }
            $.toast({
              title: `Synced ${response.length} Series`,
              message: `<ul class="ui ordered animated list">${message}</ul>`,
              displayTime: 0,
              showProgress: 'bottom',
              classProgress: 'black',
            });
          },
          error: response => showErrorToast({title: 'Error encountered while Syncing', response}),
          complete: () => $(`#sync${id} >* i.sync`).toggleClass('loading blue', false),
        });
      }

      return clone;
    });
    syncElement.replaceChildren(syncElement.firstElementChild, ...newChildren);
    refreshTheme();
  });
}

async function getSyncSchedule() {
  const {next_run} = await fetch('/api/schedule/SyncInterfaces').then(resp => resp.json());
  const nextRun = new Date(next_run);
  const nextRunStr = nextRun.toLocaleString();

  // Get current time
  const updatePreview = () => {
    const now = new Date();
    const timeDifferenceSeconds = Math.floor((nextRun - now) / 1000);
    const timeDifferenceMinutes = Math.floor(timeDifferenceSeconds / 60);
    const timeDifferenceHours = Math.floor(timeDifferenceMinutes / 60);
    const timeDifferenceDays = Math.floor(timeDifferenceHours / 24);

    // Create string for next run time, only show up to two time units
    const timeUnits = [];
    if (timeDifferenceDays > 0) { timeUnits.push(`${timeDifferenceDays} days`); }
    if (timeDifferenceHours % 24 > 0) { timeUnits.push(`${timeDifferenceHours%24} hours`); }
    if (timeDifferenceMinutes % 60 > 0) { timeUnits.push(`${timeDifferenceMinutes%60} minutes`); }
    if (timeDifferenceSeconds % 60 > 0) { timeUnits.push(`${timeDifferenceSeconds%60} seconds`); }
    const inStr = timeUnits.slice(0, 2).join(', ');
    $('#next-sync')[0].innerHTML = `<span>All Syncs will run in <span class="ui blue text">${inStr}</span>, at <span class="ui red text">${nextRunStr}</span></span>`;
  }
  setInterval(updatePreview, 1000);
}

async function initAll() {
  initConnectionDropdowns();
  getLibraries();
  getTags();
  getAllSyncs();
  getTemplates();
  getSyncSchedule();

  // Enable elements
  $('.checkbox').checkbox();
  $('.ui.dropdown[dropdown-type="series-type"]').dropdown({
    clearable: true,
    default: 'None',
  });
  $('.ui.dropdown[dropdown-type="server-tags"]').dropdown({allowAdditions: true});

  // Attach button clicks to modal hiding
  $('#add-emby-sync-modal').modal('attach events', '#add-emby-sync', 'show');
  $('#add-jellyfin-sync-modal').modal('attach events', '#add-jellyfin-sync', 'show');
  $('#add-plex-sync-modal').modal('attach events', '#add-plex-sync', 'show');
  $('#add-sonarr-sync-modal').modal('attach events', '#add-sonarr-sync', 'show');
  
  // Submit API request to create a new sync, do so for each source
  const syncData = [
    {interface: 'emby', formID: 'emby-sync-form', modalID: 'add-emby-sync-modal'},
    {interface: 'jellyfin', formID: 'jellyfin-sync-form', modalID: 'add-jellyfin-sync-modal'},
    {interface: 'plex', formID: 'plex-sync-form', modalID: 'add-plex-sync-modal'},
    {interface: 'sonarr', formID: 'sonarr-sync-form', modalID: 'add-sonarr-sync-modal'},
  ];
  syncData.forEach(({interface, formID, modalID}) => {
    $(`#${formID}`).on('submit', (event) => {
      event.preventDefault();
      // Turn form into object, turning multi selects into arrays
      let form = new FormData(event.target);
      let dataObj = {};
      for (let [name, value] of [...form.entries()]) {
        if (name.includes('_tags') || name.includes('_libraries') || name === 'template_ids') {
          if (value !== '') {
            dataObj[name] = value.split(',');
          }
        } else if (value !== '') {
          dataObj[name] = value;
        }
      }
      // Submit API request to add this sync
      $.ajax({
        type: 'POST',
        url: `/api/sync/${interface}/new`,
        data: JSON.stringify(dataObj),
        contentType: 'application/json',
        success: response => {
          showInfoToast(`Created Sync "${response.name}"`);
          getAllSyncs();
          $(`#${modalID}`).modal('hide');
          $(`#${formID}`).form('clear');
        }, error: response => showErrorToast({title: 'Error Creating Sync', response}),
      });
    });
  });
}
