// ***********************************************
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

/**
 * Create a new object and return the `id` attribute of the return.
 * @example
 * cy.createObjectAndGetId(('/api/fonts/new', {'name': 'New Font'})).then((fontId) => {})
 */
Cypress.Commands.add(
  'createObjectAndGetId',
  /**
   * Submit an API request to the given URL with the given body, returning a
   * wrapped instance of the returned object ID.
   * @param {string} url API URL to submit the POST request to.
   * @param {Object} body Object to send in the API request body.
   */
  (url, body) => {
    cy.request('POST', url, body).then((resp) => {
      // Reload page
      cy.reload();

      return cy.wrap(resp.body.id);
    });
  }
);

/**
 * Submit an API request to completely reset TCM.
 */
Cypress.Commands.add(
  'resetDatabase',
  () => cy.request('POST', '/api/reset')
);

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
   * @param {boolean} enabled Whether to enable the Connection to TMDb.
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
 * Enter the extra value for a given card type and label.
 */
Cypress.Commands.add(
  'selectExtra',
  /**
   * Enter the value of the given extra.
   * @param {Element} parentSelector Selector of the parent object containing
   * the extras to interact with.
   * @param {string} cardType Name of the card type to select. This should not
   * be the identifier, but the actual name - e.g. `Anime`.
   * @param {string} label Label of the extra to populate - e.g.
   * `Episode Text Font Size`.
   * @param {string} value Value to put into the extra input.
   */
  (parentObject, cardType, label, value) => {
    // Click tab for this card type
    parentObject.within(section => {
      cy.wrap(section)
        .find('.menu .item')
        .contains(cardType)
        .click()
    });

    // Fill out this input
    parentObject.within(section => {
      cy.wrap(section)
        // Find active tab for currently selected card type
        .find('.active.tab')
        // Find indicated extra label
        .contains('label', label)
        // Get input associated with this extra
        .parent()
        .find('input')
        // Type value
        .clear()
        .type(value)
        .should('have.value', value)
    })
  }
);

/**
 * Validate the extra value of the given card type / label.
 */
Cypress.Commands.add(
  'validateExtra',
  /**
   * Validate the value of the given extra.
   * @param {Element} parentSelector Selector of the parent object containing
   * the extras to interact with.
   * @param {string} cardType Name of the card type to select. This should not
   * be the identifier, but the actual name - e.g. `Anime`.
   * @param {string} label Label of the extra to validate - e.g.
   * `Episode Text Font Size`.
   * @param {string} value Value to validate is present in the extra input.
   */
  (parentObject, cardType, label, value) => {
    // Click tab for this card type
    parentObject.within(section => {
      cy.wrap(section)
        .find('.menu .item')
        .contains(cardType)
        .click()
    });

    // Fill out this input
    parentObject.within(section => {
      cy.wrap(section)
        // Find active tab for currently selected card type
        .find('.active.tab')
        // Find indicated extra label
        .contains('label', label)
        // Get input associated with this extra
        .parent()
        .find('input')
        // Validate value
        .should('have.value', value)
    })
  }
);

/**
 * Custom command to select an option from a dropdown.
 * @example
 * cy.selectDropdown(
 *   '@templateContent',
 *   '.dropdown[data-value="card_type"]',
 *   'Anime'
 *  )
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
