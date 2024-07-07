// ***********************************************************
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

import './commands'

// Before all test suites, reset the database and global options
before(() => {
  cy.resetDatabase();
});
