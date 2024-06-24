describe('Visit All Pages', () => {
  it('Visits the home page', () => {
    cy.visit('/')
    cy.url().should('eq', Cypress.config('baseUrl') + '/')
  });

  it('Visits the add Series page', () => {
    cy.visit('/add')
    cy.url().should('eq', Cypress.config('baseUrl') + '/add')
  });

  it('Visits the missing page', () => {
    cy.visit('/missing')
    cy.url().should('eq', Cypress.config('baseUrl') + '/missing')
  });

  it('Visits the Templates page', () => {
    cy.visit('/card-templates')
    cy.url().should('eq', Cypress.config('baseUrl') + '/card-templates')
  });

  it('Visits the Fonts page', () => {
    cy.visit('/fonts')
    cy.url().should('eq', Cypress.config('baseUrl') + '/fonts')
  });

  it('Visits the Sync page', () => {
    cy.visit('/sync')
    cy.url().should('eq', Cypress.config('baseUrl') + '/sync')
  });
  
  it('Visits the Settings page', () => {
    cy.visit('/settings')
    cy.url().should('eq', Cypress.config('baseUrl') + '/settings')
  });

  it('Visits the Connections page', () => {
    cy.visit('/connections')
    cy.url().should('eq', Cypress.config('baseUrl') + '/connections')
  });

  it('Visits the Scheduler page', () => {
    cy.visit('/scheduler')
    cy.url().should('eq', Cypress.config('baseUrl') + '/scheduler')
  });

  it('Visits the Importer page', () => {
    cy.visit('/import')
    cy.url().should('eq', Cypress.config('baseUrl') + '/import')
  });

  it('Visits the Logs page', () => {
    cy.visit('/logs')
    cy.url().should('eq', Cypress.config('baseUrl') + '/logs')
  });

  it('Visits a missing page', () => {
    cy.visit('/non-existent')
    cy.url().should('eq', Cypress.config('baseUrl') + '/')
  });
});
