const { defineConfig } = require('cypress')

module.exports = defineConfig({
  projectId: "sod537",
  reporter: 'mochawesome',
  reporterOptions: {
    reportDir: 'cypress/results',
    charts: true,
    overwrite: false,
    html: false,
    json: true,
  },
  e2e: {
    baseUrl: 'http://localhost:4242',
  },
});
