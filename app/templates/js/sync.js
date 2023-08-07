function getEmbyLibraries() {
  $.ajax({
    type: 'GET',
    url: '/api/available/libraries/emby',
    success: libraries => {
      const values = libraries.map(name => {
        return {name: name, value: name, selected: false}
      });
      $('#emby-sync-form .dropdown[data-value="required_libraries"]').dropdown({
        placeholder: 'None',
        values: values
      });
      $('#emby-sync-form .dropdown[data-value="excluded_libraries"]').dropdown({
        placeholder: 'None',
        values: values
      });
    }, error: response => showErrorToast({title: 'Error Querying Emby Libraries', response}),
  });
}

function getJellyfinLibraries() {
  $.ajax({
    type: 'GET',
    url: '/api/available/libraries/jellyfin',
    success: libraries => {
      const values = libraries.map(name => {
        return {name: name, value: name, selected: false}
      });
      $('#jellyfin-sync-form .dropdown[data-value="required_libraries"]').dropdown({
        placeholder: 'None',
        values: values
      });
      $('#jellyfin-sync-form .dropdown[data-value="excluded_libraries"]').dropdown({
        placeholder: 'None',
        values: values
      });
    }, error: response => showErrorToast({title: 'Error Querying Jellyfin Libraries', response}),
  });
}

async function getPlexLibraries() {
  $.ajax({
    type: 'GET',
    url: '/api/available/libraries/plex',
    success: libraries => {
      const values = libraries.map(name => {
        return {name: name, value: name, selected: false}
      });
      $('#plex-sync-form .dropdown[data-value="required_libraries"]').dropdown({
        placeholder: 'None',
        values: values
      });
      $('#plex-sync-form .dropdown[data-value="excluded_libraries"]').dropdown({
        placeholder: 'None',
        values: values
      });
    }, error: response => showErrorToast({title: 'Error Querying Plex Libraries', response}),
  });
}

async function getTemplates() {
  const templates = await fetch('/api/templates/all').then(resp => resp.json());
  $('.dropdown[data-value="template_ids"]').dropdown({
    values: getActiveTemplates(null, templates),
  });
}

// Function to add tags to all tag dropdowns
async function getSonarrTags() {
  // Add tag options to add tag dropdowns
  const tags = await fetch('/api/available/tags/sonarr').then(resp => resp.json());
  $('.dropdown[dropdown-type="sonarr-tags"]').dropdown({
    placeholder: 'None',
    allowAdditions: true,
    values: tags.map(({id, label}) => {
      return {name: label, value: label, selected: false};
    }),
  })
}

async function showEditModel(sync) {
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
      success: response => {
        $.toast({class: 'blue info', title: `Updated Sync "${response.name}"`});
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
  $('#delete-sync-modal .button[data-action="delete-sync-only"]').off('click').on('click', () => {
    $(`#card-sync${syncId}`).toggleClass('red double loading', true);
    $.ajax({
      type: 'DELETE',
      url: `/api/sync/delete/${syncId}?delete_series=false`,
      success: () => {
        $.toast({class: 'blue info', title: 'Deleted Sync'});
        getAllSyncs();
      },
      error: response => {
        showErrorToast({title: 'Error Deleting Sync', response});
        $(`#card-sync${syncId}`).toggleClass('red double loading', false);
      }, complete: () => {}
    });
  });
  $('#delete-sync-modal .button[data-action="delete-sync-and-series"]').off('click').on('click', () => {
    $(`#card-sync${syncId}`).toggleClass('red double loading', true);
    $.ajax({
      type: 'DELETE',
      url: `/api/sync/delete/${syncId}?delete_series=true`,
      success: () => {
        $.toast({class: 'blue info', title: 'Deleted Sync and associated Series'});
        getAllSyncs();
      },
      error: response => {
        showErrorToast({title: 'Error Deleting Sync', response});
        $(`#card-sync${syncId}`).toggleClass('red double loading', false);
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
      const card = clone.querySelector('.card');
      card.id = `card-sync${id}`;
      clone.querySelector('.header').innerText = name;
      clone.querySelector('.sync-meta').innerText = `Sync ID ${id}`;

      // Edit sync if clicked
      clone.querySelector('i.edit').onclick = () => showEditModel(syncObject);

      // Launch delete sync modal on click of the delete icon
      clone.querySelector('i.trash').onclick = () => showDeleteSyncModal(id);

      // Add sync API request to sync icon
      clone.querySelector('i.sync').onclick = () => {
        // Add loading indicator, create toast
        $(`#card-sync${id} >* i.sync`).toggleClass('loading blue', true);
        $.toast({
          class: 'blue info',
          title: `Started Syncing "${name}"`,
        });
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
          complete: () => $(`#card-sync${id} >* i.sync`).toggleClass('loading blue', false),
        });
      }

      return clone;
    });
    syncElement.replaceChildren(syncElement.firstElementChild, ...newChildren);
    refreshTheme();
  });
}

async function getScheduledSyncs() {
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
  getAllSyncs();
  {% if preferences.use_emby %}
  getEmbyLibraries();
  {% endif %}
  {% if preferences.use_jellyfin %}
  getJellyfinLibraries();
  {% endif %}
  {% if preferences.use_plex %}
  getPlexLibraries();
  {% endif %}
  getTemplates();
  {% if preferences.use_sonarr %}
  getSonarrTags();
  {% endif %}
  getScheduledSyncs();

  // Enable elements
  $('.checkbox').checkbox();
  $('.ui.dropdown[dropdown-type="series-type"]').dropdown({
    clearable: true,
    default: 'None',
  });
  $('.ui.dropdown[dropdown-type="server-tags"]').dropdown({allowAdditions: true});

  // Attach button clicks to modal hiding
  {% if preferences.use_emby %}
  $('#add-emby-sync-modal').modal('attach events', '#add-emby-sync', 'show');
  {% endif %}
  {% if preferences.use_jellyfin %}
  $('#add-jellyfin-sync-modal').modal('attach events', '#add-jellyfin-sync', 'show');
  {% endif %}
  {% if preferences.use_plex %}
  $('#add-plex-sync-modal').modal('attach events', '#add-plex-sync', 'show');
  {% endif %}
  {% if preferences.use_sonarr %}
  $('#add-sonarr-sync-modal').modal('attach events', '#add-sonarr-sync', 'show');
  {% endif %}

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
          $.toast({
            class: 'blue info',
            title: `Created Sync "${response.name}"`,
          });
          getAllSyncs();
          $(`#${modalID}`).modal('hide');
        }, error: response => showErrorToast({title: 'Error Creating Sync', response}),
      });
    });
  });
}
