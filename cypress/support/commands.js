// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

Cypress.Commands.add('createObjectAndGetId', (url, body) => {
  cy.request('POST', url, body).then((resp) => {
    // Reload page
    cy.reload();

    return cy.wrap(resp.body.id);
  });
});

Cypress.Commands.add('resetDatabase', () => {
  cy.request('POST', '/api/reset');
});

Cypress.Commands.add('login', (url, username, password) => {
  cy.visit(url || '/login')

  // Type credentials
  cy.get("#username")
    .clear()
    .type(username || 'admin')
  cy.get('#password')
    .clear()
    .type(password || 'password')

  // Click log in button
  cy.contains('Login')
    .click()
});

/**
 * Create a new Connection to TMDb. This uses the `TMDB_API_KEY` environment
 * variable as the API key.
 */
Cypress.Commands.add(
  'createTMDbConnection',
  /**
   * Create a new Connection to TMDb.
   * @param {?boolean} enabled Whether to enable the Connection to TMDb.
   */
  (enabled=false) => {
    cy.request(
      'POST',
      '/api/connection/tmdb/new',
      {
        'name': 'TMDb',
        'interface_type': 'TMDb',
        'enabled': enabled,
        'api_key': Cypress.env('TMDB_API_KEY') || 'abcdef',
      }
    );
  }
);

/**
 * Custom command to select an option from a dropdown.
 * @example
 * cy.selectDropdown('@templateContent', '.dropdown[data-value="card_type"]', 'Anime')
 */
Cypress.Commands.add(
  'selectDropdown',
  /**
   * Select an option from a dropdown.
   * @param {string} parentSelector - Parent selector which contains the dropdown
   * to interact with.
   * @param {string} dropdownSelector - Selector of the dropdown element to
   * click and query the text of.
   * @param {string} optionText - The display text of the dropdown option to
   * select.
   */
  (parentSelector, dropdownSelector, optionText) => {
    // Find parent
    cy.get(parentSelector)
      // Click dropdown
      .find(dropdownSelector)
      .click()
      // Find and click option
      .contains(optionText)
      .click()

    // Find parent
    cy.get(parentSelector)
      // Verify dropdown shows option text
      .find(dropdownSelector)
      .should('contain', optionText)
  }
);
