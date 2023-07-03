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
  async function getRecentLogs() {
    // Get last 30sec of logs
    const last30s = encodeURIComponent(dateToISO8601(new Date(Date.now() - 1  * 1000 * 30)));
    const allMessages = await fetch(`/api/logs/query?page=1&after=${last30s}&level=info`).then(resp => resp.json());
    // Add to list of logs to display, limit to 60 messages
    logs = logs.concat(allMessages.items).slice(undefined, 60);
  }

  // Display the oldest pending log
  function displayLogs() {
    if (logs.length > 0) {
      for (let i = 0; i < 3 && logs.length > 0; i++) {
        setTimeout(() => {
          // Get latest message, exit if none left
          const message = logs.shift();
          if (message === undefined) { return; }

          // Display toast of this message
          const isError = ['warning', 'error', 'critical'].includes(message.level);
          $.toast({
            class: isError ? 'right aligned red error' : 'right aligned blue info',
            message: message.message,
            displayTime: isError ? 10000 : 5000,
            position: 'bottom right',
            showIcon: isError ? 'exclamation circle' : 'info circle',
            showProgress: 'top',
          });
        }, 500 * i);
      }
    }
  }

  // Query for new logs every 30 seconds
  setInterval(getRecentLogs, 1 * 1000 * 30);
  // Display any pending logs every 5 seconds
  setInterval(displayLogs, 1 * 1000 * 5);
});