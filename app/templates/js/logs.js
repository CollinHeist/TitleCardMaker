{% if False %}
import {LogEntry, LogEntryPage, LogLevel} from './.types.js';
{% endif %}

/** @type {Array<string>} */
let currentPage = [];

/**
 * Download the current page of logs. This reads the value of `currentPage`.
 */
function downloadPage() {
  // Skip if no logs to download
  if (!currentPage || currentPage.length === 0) { return; }

  // Create combined string of all messages
  const logStr = currentPage.join('\n');

  // Download text 
  downloadTextFile('tcm_log.txt', logStr);
}

/**
 * Set the given level as the currently selected value in the dropdown.
 * @param {LogLevel} level - The log
 * level to set as the current selection in the dropdown.
 */
function updateMessageLevel(level) {
  // Uppercase first letter of level
  const newLevel = level.toUpperCase();
  $('.dropdown[data-value="level"]').dropdown('set text', newLevel);
  $('.dropdown[data-value="level"]').dropdown('set selected', newLevel);
  $('.dropdown[data-value="level"]').dropdown('set value', newLevel);
}

/**
 * Set the timestamp filter field to the given value. This updates the "after"
 * field if blank, then the before field. If neither are blank nothing happens.
 * @param {string} timestamp - Timestamp to set as the current value.
 */
function updateTimestamp(timestamp) {
  // Get current values of before/after
  const currentAfter = $('input[name="after"]').val();
  const currentBefore = $('input[name="before"]').val();

  // Populate after if blank, else before
  if (currentAfter === '') {
    $('input[name="after"]')[0].value = timestamp;
  } else if (currentBefore === '') {
    $('input[name="before"]')[0].value = timestamp;
  }
}

/**
 * Add the given context ID to the current log filter input field.
 * @param {string} id - Unique context ID to add to the current log filters.
 */
function appendContextID(id) {
  // Get current value
  const currentVal = $('input[name="context_id"]').val();
  // Only append if ID is not already listed
  if (!currentVal.includes(id)) {
    $('input[name="context_id"]')[0].value = currentVal === '' ? id : `${currentVal},${id}`;
  }
}

/**
 * Reset the filter form.
 */
function resetForm() {
  $('#log-filters').form('clear');
}

/**
 * Submit an API request to query for the given page of logs. If successful,
 * then add those logs to the DOM.
 * @param {number} [page=1] - Page number of logs to query.
 */
function queryForLogs(page=1) {
  // Prepare Form
  const form = new FormData(document.getElementById('log-filters'));

  // Remove blank values
  for (let [key, value] of [...form.entries()]) {
    if (value === '') { form.delete(key); }
  }

  // Create query param string
  const queryString = [...form.entries()]
    .map(x => `${encodeURIComponent(x[0])}=${encodeURIComponent(x[1])}`)
    .join('&');

  // Submit API request
  $.ajax({
    type: 'GET',
    url: `/api/logs/query?page=${page}&shallow=false&${queryString}`,
    /**
     * Logs queries successfully, add rows for each log message to the DOM.
     * @param {LogEntryPage} messages - Log messages to update the table with.
     */
    success: messages => {
      currentPage = [];
      const rows = messages.items.map(message => {
        // Clone template
        const row = document.querySelector(`#${message.level.toLowerCase()}-message-template`).content.cloneNode(true);

        const shortTime = message.time.match(/^(.[^\.]+\.\d{3}?)\d*$/m);
        if (shortTime) {
          row.querySelector('[data-value="time"]').innerText = shortTime[1];
        } else {
          row.querySelector('[data-value="time"]').innerText = message.time;
        }
        row.querySelector('[data-value="context_id"]').innerText = message.context_id;
        row.querySelector('[data-value="message"]').innerText = message.message;

        // On click of log level, update filter level
        row.querySelector('[data-value="level"]').onclick = () => updateMessageLevel(message.level);
        
        // On click of timestamp, update before/after fields
        row.querySelector('[data-value="time"]').onclick = () => updateTimestamp(message.time);
        
        // On click of context ID, append current ID to input
        row.querySelector('[data-value="context_id"]').onclick = () => appendContextID(message.context_id);

        // Add message to current page array
        currentPage.push(`[${message.level.toUpperCase()}] [${message.time}] [${message.context_id}] ${message.message}`);

        return row;
      });

      // Add rows to page
      document.getElementById('log-data').replaceChildren(...rows);

      // Update pagination
      updatePagination({
        paginationElementId: 'pagination',
        navigateFunction: queryForLogs,
        page: messages.page,
        pages: messages.pages,
        amountVisible: isSmallScreen() ? 5 : 15,
      });

      $('.ui.dropdown').dropdown();
    },
    error: response => showErrorToast({type: 'Error Querying Logs', response}),
  });
}

/**
 * Initialize the page. This queries for logs, initializes dropdowns, and
 * initializes the after/before calendar inputs.
 */
function initAll() {
  queryForLogs();
  
  $('#date-after').calendar({
    type: 'datetime',
    endCalendar: $('#date-before'),
    maxDate: new Date(), // Cannot select dates after today
    formatter: {
      datetime: 'YYYY-MM-DDTHH:mm:ss', // ISO 8601
    }
  });
  $('#date-before').calendar({
    type: 'datetime',
    startCalendar: $('#date-after'),
    maxDate: new Date(), // Cannot select dates after today
    formatter: {
      datetime: 'YYYY-MM-DDTHH:mm:ss', // ISO 8601
    }
  });
}