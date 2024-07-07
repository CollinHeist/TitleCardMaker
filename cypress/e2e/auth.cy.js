describe('Authentication', () => {
  it('Visits the login page with authentication disabled', () => {
    cy.visit('/login')
    cy.url().should('eq', Cypress.config('baseUrl') + '/')
  });

  it('Enables authentication', () => {
    // Visit Connections page, click checkbox
    cy.visit('/connections')

    cy.get('.checkbox[data-value="require_auth"] label')
      .should('exist')
      .click('left')

    // Should be redirected to the login page
    cy.url().should('eq', Cypress.config('baseUrl') + '/login?redirect=/connections')
  });

  it('Visits a page without authentication', () => {
    const pages = [
      '/', '/add', '/missing', '/card-templates', '/fonts', '/sync', '/settings',
      '/connections', '/scheduler', '/import', '/logs', '/graphs', '/series/1',
    ];

    pages.forEach((url) => {
      cy.visit(url)
      cy.url().should('eq', Cypress.config('baseUrl') + `/login?redirect=${url}`)
    });
  });

  it('Makes an API request without authentication', () => {
    cy.request({
      method: 'GET',
      url: '/api/available/series',
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.eq(401)
      expect(resp.body).to.have.property('detail', 'Invalid credentials')
    });
  });

  it('Makes an API request that does not require authentication without authentication', () => {
    cy.request({
      method: 'POST',
      url: '/api/cards/key?interface_id=0',
      body: '999',
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.be.greaterThan(401);
      expect(resp.body).to.have.property('detail', 'No Plex Connection with ID 0')
    });

    cy.fixture('fake_webhook.json').then((data) => {
      cy.request({
        method: 'POST',
        url: '/api/cards/sonarr',
        body: data,
      }).then((resp) => {
        expect(resp.body).to.be.null
      })
    });
  });

  it('Attemps to log in with the incorrect username or password', () => {
    // Intercept the authentication request
    cy.intercept('POST', '/api/auth/authenticate').as('authenticate')

    const badCredentials = [
      { username: 'ADMIN', password: 'password' },
      { username: 'admin', password: 'PASSWORD' },
    ];

    cy.visit('/login')
    badCredentials.forEach(({username, password}) => {
      // Type credentials
      cy.get("#username")
        .clear()
        .type(username)
      cy.get('#password')
        .clear()
        .type(password)
  
      // Click log in button
      cy.contains('Login')
        .should('exist')
        .click()
  
      // Verify authentication returned unauthorized; did not redirect
      cy.wait('@authenticate').its('response.statusCode').should('eq', 401)
      cy.url().should('eq', Cypress.config('baseUrl') + '/login')
    });
  });

  it('Sees the forgot password link on the login page', () => {
    // Forgot password link should be visible on the page
    cy.visit('/login')
    cy.contains('Forgot Password')
      .should('exist')
      .should('have.attr', 'href')
      .and('include', 'titlecardmaker.com')
  });

  it('Logs in with the auto-generated username and password', () => {
    cy.login('/login?redirect=/settings')
    cy.url().should('eq', Cypress.config('baseUrl') + '/settings')
  });

  it('Changes the username', () => {
    // cy.intercept('POST', '/api/auth/authenticate').as('authenticate')

    // Go to Connections page
    cy.login('/login?redirect=/connections')

    // Change username from default
    cy.get('#auth-settings input[name="username"]')
      .clear()
      .type('new username')
    cy.get('#auth-settings input[name="password"]')
      .clear()
      .type('password')
    cy.get('#auth-settings .button').click()

    // Should be redirected to login page
    cy.url().should('eq', Cypress.config('baseUrl') + '/login?redirect=/connections')

    // Attempt login with default credentials - should fail
    cy.login()
    // Verify authentication returned unauthorized; did not redirect
    cy.wait(500)
    cy.url().should('eq', Cypress.config('baseUrl') + '/login')

    // Attempt login with new credentials - should work
    cy.login('/login?redirect=/connections', 'new username', 'password')
    cy.wait(500)
    cy.url().should('eq', Cypress.config('baseUrl') + '/connections')
  });

  it('Changes the password', () => {
    cy.intercept('POST', '/api/auth/authenticate').as('authenticate')

    // Login and go to the Connections page
    cy.login('/login?redirect=/connections', 'new username', 'password')

    // Change password
    cy.get('#auth-settings input[name="password"]')
      .clear()
      .type('new password')
    cy.get('#auth-settings .button').click()

    // Should be redirected to login page
    cy.url().should('eq', Cypress.config('baseUrl') + '/login?redirect=/connections')

    // Attempt login with old credentials - should fail
    cy.login('/login', 'new username', 'password')
    // Verify authentication returned unauthorized; did not redirect
    cy.wait(500)
    cy.url().should('eq', Cypress.config('baseUrl') + '/login')

    // Attempt login with new credentials - should work
    cy.login('/login?redirect=/connections', 'new username', 'new password')
    cy.wait(500)
    cy.url().should('eq', Cypress.config('baseUrl') + '/connections')
  });

  it('Disables authentication', () => {
    cy.login('/login?redirect=/connections', 'new username', 'new password')

    cy.wait(500)
    cy.get('.checkbox[data-value="require_auth"] label')
      .should('exist')
      .click('left')

    cy.visit('/login')
    cy.url().should('eq', Cypress.config('baseUrl') + '/')
  });
});
