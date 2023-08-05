$(document).ready(() => {
  function dateToISO8601(date) {
    const year = 1900 + date.getYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    const milliseconds = String(date.getMilliseconds()).padStart(3, '0');
  
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}.${milliseconds}`;
  }

  // List of logs to display
  var logs = [];
  let getLogId, displayLogId;
  async function getRecentLogs() {
    // Get last 30sec of logs
    const last30s = encodeURIComponent(dateToISO8601(new Date(Date.now() - 1  * 1000 * 30)));
    const now = encodeURIComponent(dateToISO8601(new Date()));
    $.ajax({
      type: 'GET',
      url: `/api/logs/query?page=1&after=${last30s}&before=${now}&level=info&shallow=true`,
      success: allMessages => logs = logs.concat(allMessages.items).slice(undefined, 60),
      error: response => {
        // If unauthorized, cancel recurrent requests
        if (response.status === 401) {
          clearInterval(getLogId);
          clearInterval(displayLogId);
        }
      },
    });
  }

  // Display the oldest pending log
  function displayLogs() {
    if (logs.length > 0 || document.getElementsByClassName('toast').length > 3) {
      // Get latest message, exit if none left
      const message = logs.shift();
      if (message === undefined) { return; }

      // Display toast of this message
      const isError = ['warning', 'error', 'critical'].includes(message.level);
      $.toast({
        class: isError ? 'right aligned red error' : 'right aligned blue info',
        message: message.message,
        displayTime: 5000,
        position: 'bottom right',
        showIcon: isError ? 'exclamation circle' : 'info circle',
        showProgress: 'top',
      });
    }
  }

  // Query for new logs every 30 seconds
  getLogId = setInterval(getRecentLogs, 1 * 1000 * 30);
  // Display any pending logs every 5 seconds
  displayLogId = setInterval(displayLogs, 1 * 1000 * 5);
});