/*
 * Get a string of the difference between the given datetime string and
 * the current time. Only up to the two highest intervals are returned.
 */
function timeDiffString(next_run) {
  const nextRun = new Date(next_run);

  // Get current time, 
  const now = new Date();
  const diffSeconds = Math.floor((nextRun - now) / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Create string for next run time, only show up to two time units
  const timeUnits = [];
  if (diffDays > 1) { timeUnits.push(`<span class="ui red text">${diffDays}</span> days`); }
  else if (diffDays > 0) { timeUnits.push(`<span class="ui red text">${diffDays}</span> day`); }
  if (diffHours % 24 > 1) { timeUnits.push(`<span class="ui green text">${diffHours%24}</span> hours`); }
  else if (diffHours % 24 > 0) { timeUnits.push(`<span class="ui green text">${diffHours%24}</span> hour`); }
  if (diffMinutes % 60 > 1) { timeUnits.push(`<span class="ui blue text">${diffMinutes%60}</span> minutes`); }
  else if (diffMinutes % 60 > 0) { timeUnits.push(`<span class="ui blue text">${diffMinutes%60}</span> minute`); }
  if (diffSeconds % 60 > 1) { timeUnits.push(`<span class="ui teal text">${diffSeconds%60}</span> seconds`); }
  else if (diffSeconds % 60 > 0) { timeUnits.push(`<span class="ui teal text">${diffSeconds%60}</span> second`); }

  return inStr = timeUnits.slice(0, 2).join(', ');
}

/*
 * Get a string representation of the given frequency.
 */
function timeFreqString(freq, top=-1) {
  const seconds = Math.floor(freq);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const timeUnits = [];
  if (days > 0) { timeUnits.push(`${days} days`); }
  if (hours % 24 > 0) { timeUnits.push(`${hours%24} hours`); }
  if (minutes % 60 > 0) { timeUnits.push(`${minutes%60} minutes`); }
  if (seconds % 60 > 0 || timeUnits.length === 0) { timeUnits.push(`${seconds%60} seconds`); }
  
  if (top > 0) { return timeUnits.slice(0, top).join(', '); }
  else { return timeUnits.join(', '); }
}

/*
 * Reschedule all tasks on this page. This reads the text contents of
 * each row of the table for the API request. A separate request is
 * submitted for each row.
 */
function updateScheduledTasks() {
  $('#task-table tr').each((index, row) => {
    const taskId = row.dataset.id;
    // Updating Cron schedule or frequency
    let updateObject = {};
    if ($(`tr[data-id="${taskId}"] > td[data-column="frequency"]`).length > 0) {
      const frequencyText = $(`tr[data-id="${taskId}"] > td[data-column="frequency"]`)[0].innerText;

      const intervalRegex = /(\d+) (week|day|hour|minute|second)s?/g;
      const allMatches = [...frequencyText.matchAll(intervalRegex)];

      // Create object based on this frequency text
      allMatches.forEach(([_, interval, unit]) => updateObject[`${unit}s`] = interval);
    } else {
      updateObject.crontab = $(`tr[data-id="${taskId}"] > td[data-column="schedule"]`)[0].innerText;
    }

    // Submit API request to reschedule this task
    $.ajax({
      type: 'PUT',
      url: `/api/schedule/update/${taskId}`,
      data: JSON.stringify(updateObject),
      contentType: 'application/json',
      success: () => showInfoToast(`Rescheduled Task ${taskId}`),
      error: response => showErrorToast({title: 'Error Recheduling Task', response}),
      complete: () => initAll(),
    });
  });
}

/*
 * Submit the API request to toggle the Scheduler type. If successful,
 * this reloads the page.
 */
function toggleScheduleType() {
  document.getElementById('toggle-button').classList.add('loading');
  $.ajax({
    type: 'POST',
    url: '/api/schedule/type/toggle',
    success: () => {
      showInfoToast({title: 'Updated Scheduler', message: 'Reloading page..'});
      setTimeout(() => location.reload(), 2000);
    }, error: response => {
      document.getElementById('toggle-button').classList.remove('loading');
      showErrorToast({title: 'Error Changing Scheduler', response});
    },
  });
}

/*
 * Submit the API request to run the Task with the given ID.
 */
function runTask(taskId) {
  // If task is already running, do not re-run
  if ($(`tr[data-id="${taskId}"] td[data-column="runTask"] i`)[0].classList.contains('loading')) {
    showInfoToast(`Task ${taskId} is already running`);
    return; 
  }
  $(`tr[data-id="${taskId}"] td[data-column="runTask"] i`).toggleClass('blue loading', true);
  showInfoToast(`Running Task ${taskId}`);
  $.ajax({
    type: 'POST',
    url: `/api/schedule/${taskId}`,
    success: response => {
      showInfoToast(`Task ${taskId} Completed`);
      $(`tr[data-id="${taskId}"] td[data-column="previous_duration"]`)[0].innerHTML = timeFreqString(response.previous_duration, 2);
    }, error: response => showErrorToast({title: 'Error Running Task', response}),
    complete: () => $(`tr[data-id="${taskId}"] td[data-column="runTask"] i`).toggleClass('blue loading', false),
  });
}

/**
 * Decode the given crontab expression into a human-readable string.
 * @param {string} crontab - Crontab to decode
 * @returns {string} Decoded cron expression HTML.
 */
function decodeCrontab(crontab) {
  try {
    return `<span class="ui text">${cronstrue.toString(crontab)}</span>`;
  } catch (error) {
    return '<span class="ui red text">Invalid Expression</span>';
  }
}

/**
 * Initialize all elements on the page. This creates the Scheduled Task
 * table.
 */
async function initAll() {
  const taskTable = document.getElementById('task-table');
  const rowTemplate = document.getElementById('task-template');
  if (taskTable === null || rowTemplate === null) { return; }

  const allTasks = await fetch('/api/schedule/scheduled').then(resp => resp.json());
  const rows = allTasks.map(task => {
    const row = rowTemplate.content.cloneNode(true);
    row.querySelector('tr').dataset.id = task.id;
    if (task.running) {
      // Do not make this column selectable
      row.querySelector('td[data-column="runTask"]').className = 'center aligned';
      // Put icon in loading state
      row.querySelector('td[data-column="runTask"] i').className = 'blue loading sync icon';
    } else {
      // Task is not currently running, allow it to be run via click
      row.querySelector('td[data-column="runTask"] a').onclick = () => runTask(task.id);
    }
    row.querySelector('td[data-column="description"]').innerHTML = task.description;
    // Fill out schedule row
    if (row.querySelector('td[data-column="schedule"]')) {
      // Add human-readable time
      const span = row.querySelector('td[data-column="schedule"] span');
      const scheduleStringRow = row.querySelector('td[data-column="schedule-string"]');
      scheduleStringRow.innerHTML = decodeCrontab(task.crontab);
      span.innerText = task.crontab;

      // Update tooltip on edit
      span.addEventListener('keyup', function() {
        scheduleStringRow.innerHTML = decodeCrontab(span.innerText);
      });
    // Fill out frequency row
    } else {
      row.querySelector('td[data-column="frequency"]').innerHTML = `<span contenteditable="true">${timeFreqString(task.frequency)}</span>`;
    }
    if (task.previous_duration === null || task.previous_duration < 0) {
      row.querySelector('td[data-column="previous_duration"]').innerHTML = '-';
    } else {
      row.querySelector('td[data-column="previous_duration"]').innerHTML = timeFreqString(task.previous_duration, 2);
    }
    row.querySelector('td[data-column="next_run"]').innerHTML = `in ${timeDiffString(task.next_run)}`;

    return row;
  });
  taskTable.replaceChildren(...rows);
}