function downloadPage() {
  // Get arrays of each value
  const levels = $('#log-data [data-value="level"]').map(function() { return $(this).text(); }).get();
  const times = $('#log-data [data-value="time"]').map(function() { return $(this).text(); }).get();
  const context_ids = $('#log-data [data-value="context_id"]').map(function() { return $(this).text(); }).get();
  const messages = $('#log-data [data-value="message"]').map(function() { return $(this).text(); }).get();
  // Create combined string of all rows
  let logStr = '';
  for (let i = 0; i < levels.length; i++) {
    logStr += `[${levels[i]}] [${times[i]}] [${context_ids[i]}] ${messages[i]}\n`;
  }
  // Download text 
  downloadTextFile('tcm_log.txt', logStr);
}

function updateMessageLevel(level) {
  // Uppercase first letter of level
  const newLevel = level.charAt(0).toUpperCase() + level.slice(1)
  $('.dropdown[data-value="level"]').dropdown('set text', newLevel);
  $('.dropdown[data-value="level"]').dropdown('set selected', newLevel);
  $('.dropdown[data-value="level"]').dropdown('set value', newLevel.toLowerCase());
}

function updateTimestamp(timestamp) {
  // Get current values of before/after
  const currentAfter = $('input[name="after"]').val();
  const currentBefore = $('input[name="before"]').val();
  // Populate after if blank, else before
  if (currentAfter === '') {
    $('input[name="after"]')[0].value = timestamp;
  } else if (currentBefore === '') {
    $('input[name="before"]')[0].value = timestamp;
  } else {
    //
  }
}

function appendContextID(id) {
  // Get current value
  const currentVal = $('input[name="context_id"]').val();
  // Only append if ID is not already listed
  if (!currentVal.includes(id)) {
    $('input[name="context_id"]')[0].value = currentVal === '' ? id : `${currentVal},${id}`;
  }
}

function resetForm() {
  $('#log-filters').form('clear');
}

async function queryForLogs(page=1) {
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
  const messageData = await fetch(`/api/logs/query?page=${page}&shallow=false&${queryString}`).then(resp => resp.json());
  const allMessages = messageData.items;
  
  // Update table
  const rows = allMessages.map(message => {
    // Clone row template
    const base = document.querySelector(`#${message.level}-message-template`).content.cloneNode(true);
    // Update rows
    const shortTime = message.time.match(/^(.[^\.]+\.\d{3}?)\d*$/m);
    if (shortTime) {
      base.querySelector('[data-value="time"]').innerText = shortTime[1];
    } else {
      base.querySelector('[data-value="time"]').innerText = message.time;
    }
    base.querySelector('[data-value="context_id"]').innerText = message.context_id;
    base.querySelector('[data-value="message"]').innerText = message.message;

    // On click of log level, update filter level
    base.querySelector('[data-value="level"]').onclick = () => updateMessageLevel(message.level);
    // On click of timestamp, update before/after fields
    base.querySelector('[data-value="time"]').onclick = () => updateTimestamp(message.time);
    // On click of context ID, append current ID to input
    base.querySelector('[data-value="context_id"]').onclick = () => appendContextID(message.context_id);

    return base;
  });
  document.getElementById('log-data').replaceChildren(...rows);

  // Update pagination
  updatePagination({
    paginationElementId: 'pagination',
    navigateFunction: queryForLogs,
    page: messageData.page,
    pages: messageData.pages,
    amountVisible: 10,
  });
}


function initAll() {
  queryForLogs();

  $('.ui.dropdown').dropdown();
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