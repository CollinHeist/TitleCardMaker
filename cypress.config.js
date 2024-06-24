const { defineConfig } = require('cypress')

module.exports = defineConfig({
  projectId: "sod537",
  e2e: {
    baseUrl: 'http://localhost:4242',
  },
});
