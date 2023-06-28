$(document).ready(() => {
  // List of logs to display
  var logs = [];
  async function getRecentLogs() {
    // Get last 30sec of logs
    const last30s = encodeURIComponent(dateToISO8601(new Date(Date.now() - 1  * 1000 * 30)));
    const allMessages = await fetch(`/api/logs/query?page=1&after=${last30s}&level=info`).then(resp => resp.json());
    // Add to list of logs to display
    logs = logs.concat(allMessages.items);
  }

  // Display the oldest pending log
  function displayLogs() {
    if (logs.length > 0) {
      const message = logs.shift();
      const isError = ['warning', 'error', 'critical'].includes(message.level);
      $.toast({
        class: isError ? 'right aligned red error' : 'right aligned blue info',
        message: message.message,
        displayTime: 5000,
        position: 'bottom right',
        showIcon: isError ? 'exclamation circle' : 'info circle',
        showProgress: 'top',
      })
    }
  }

  // Query for new logs every 30 seconds
  setInterval(getRecentLogs, 1 * 1000 * 30);
  // Display any pending logs every 5 seconds
  setInterval(displayLogs, 1 * 1000 * 5);
});