/** @type {Date} When the server was booted */
const bootTime = new Date('{{ preferences.server_boot_time }}');

/**
 * Update the uptime text on the page.
 */
function updateUptimeText() {
  const diff = timeDiffString(bootTime, false);
  document.querySelector('[data-value="uptime"]').innerText = diff;
}

function initAll() {
  updateUptimeText();
  setInterval(updateUptimeText, 1000);
}
