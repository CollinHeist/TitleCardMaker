{% if False %}
import {
  SystemBackup
} from './.types.js';
{% endif %}

/** @type {Date} When the server was booted */
const bootTime = new Date('{{ preferences.server_boot_time }}');

/**
 * Update the uptime text on the page.
 */
function updateUptimeText() {
  const diff = timeDiffString(bootTime, false);
  document.querySelector('[data-value="uptime"]').innerText = diff;
}

/**
 * Formats a date string into a more readable format.
 *
 * @param {string} dateString - The date string in ISO 8601 format.
 * @returns {string} The formatted date and time string.
 * @example
 * formatDate(new Date()) // "July 23, 2024 at 00:00"
 */
function formatDate(dateString) {
  const date = new Date(dateString);

  const options = { 
      year: 'numeric', 
      month: 'long', 
      day: '2-digit',
      hour: '2-digit', 
      minute: '2-digit', 
      // second: '2-digit',
      hour12: false // Use 24-hour time format
  };

  return date.toLocaleDateString('en-US', options);
}

/**
 * 
 */
function querySystemBackups() {
  $.ajax({
    type: 'GET',
    url: '/api/settings/backups',
    /**
     * List of available backups queried. Populate page.
     * @param {SystemBackup[]} backups - List of system backups.
     */
    success: (backups) => {
      // Table to populate
      const table = document.querySelector('#system-backups tbody');
      const template = document.getElementById('backup-row-template');

      // Add row for each backup
      backups.forEach(backup => {
        const row = template.content.cloneNode(true);

        // Add timestamp, sort by timestamp
        row.querySelector('[data-value="timestamp"]').innerText = formatDate(backup.timestamp);
        row.querySelector('[data-value="timestamp"]').dataset.sortValue = new Date(backup.timestamp).getTime();
        row.querySelector('[data-value="version"]').innerText = backup.version;
        row.querySelector('[data-value="schema"]').innerText = backup.database.schema_version;
        row.querySelector('[data-value="database-filesize"]').innerText = formatBytes(backup.database.filesize, 1);
        row.querySelector('[data-value="database-filesize"]').dataset.sortValue = backup.database.filesize;
        row.querySelector('[data-value="settings-filesize"]').innerText = formatBytes(backup.settings.filesize, 1);
        row.querySelector('[data-value="settings-filesize"]').dataset.sortValue = backup.settings.filesize;
        table.appendChild(row);
      });
      $('.sortable.table').tablesort();

      // Add filesize totals to each column header as tooltips
      document.querySelector('#system-backups [data-row-label="database-filesize"] span')
        .dataset.tooltip = `Total Size: ${formatBytes(backups.reduce((n, {database}) => n + database.filesize, 0), 1)}`;
      document.querySelector('#system-backups [data-row-label="settings-filesize"] span')
        .dataset.tooltip = `Total Size: ${formatBytes(backups.reduce((n, {settings}) => n + settings.filesize, 0), 1)}`;
    },
  });
}

function initAll() {
  updateUptimeText();
  setInterval(updateUptimeText, 1000);
  querySystemBackups();
}
