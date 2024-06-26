// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

Cypress.Commands.add('createObjectAndGetId', (url, body) => {
  cy.request('POST', url, body).then((resp) => {
    // Reload page
    cy.reload();

    return cy.wrap(resp.body.id);
  });
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
