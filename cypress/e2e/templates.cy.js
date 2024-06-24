describe('Card Templates', () => {
  beforeEach(() => cy.visit('/card-templates'));

  it('Creates a new Blank Template', () => {
    // Create template via API so there is at least one subelement
    cy.request('POST', '/api/templates/new', {'name': '_'});
    cy.reload();

    // Create new Template
    cy.get('#templates > .accordion').its('length').then(initialCount => {
      // Click create button
      cy.get('#main-content button')
        .should('exist')
        .contains('Create New Template')
        .click()
      ;
  
      // New template should have been added to DOM
      cy.get('#templates > .accordion').should('have.length', initialCount + 1);

      // Get last accordion (newly added template)
      cy.get('#templates > .accordion').last()
        // Click to expand
        .click()
        .then(() => {
          // After it has rendered
          cy.get("#templates > .accordion > .content").last()
            // Content should be marked active
            .should('be.visible')
            .within(() => {
              cy.get('input:not([name="name"])').each($input => {
                cy.wrap($input).should('have.value', '');
              });
            })
        })
      ;
    });
  });
  
  it('Changes a template name and verify it persists after save and reload', () => {
    cy.createObjectAndGetId('/api/templates/new', {'name': ' Blank Template'}).then((templateId) => {
      // Create random name
      const newValue = Math.random().toString(36).substring(2, 10);
      // Get newly created Template
      cy.get(`#template-id${templateId}`)
        .should('exist')
        .click()
        .then(($template) => {
          // Put new randomized name in the name field
          cy.wrap($template).find('.content')
            .should('have.class', 'active')
            .find('input[name="name"]').first()
              .clear()
              .type(newValue)
              .should('have.value', newValue)
            ;
  
          // Save changes
          cy.wrap($template).contains('button', 'Save Changes').click();
        })

      // Reload page
      cy.reload();

      // Check name
      cy.get(`#template-id${templateId}`)
        // Expand template
        .click()
        // Verify name matches
        .find('.content input[name="name"]')
        .should('have.value', newValue);
    });
  });

  it('Adds a new filter condition', () => {
    // Create new blank Template with no conditions
    cy.createObjectAndGetId('/api/templates/new', {'name': ' Blank Template'}).then((templateId) => {
      cy.get(`#template-id${templateId}`)
        // Template should be on page, expand
        .should('exist')
        .click()
        .then(($template) => {
          cy.wait(150);
          // Click add-template button
          cy.wrap($template).find('.button[data-add-field="condition"]')
            .should('exist')
            .click()

          // Verify a new field was added
          cy.wrap($template).find('[data-value="conditions"]').children().should('have.length', 1)

          // New conditions should have argument, operation, and reference inputs
          cy.wrap($template).find('[data-value="conditions"]').first().find('input[name="argument"]').should('exist');
          cy.wrap($template).find('[data-value="conditions"]').first().find('input[name="operation"]').should('exist');
          cy.wrap($template).find('[data-value="conditions"]').first().find('input[name="reference"]').should('exist');
        })
    });
  });

  it('Refreshes the template previews', () => {
    // Intercept refresh preview so it can be waited on
    cy.intercept('POST', '/api/cards/preview').as('refreshPreview');
    // Create new Template to manipulate
    cy.createObjectAndGetId('/api/templates/new', {'name': ' Blank Template'}).then((templateId) => {
      cy.get(`#template-id${templateId}`)
        // Template should be on page, expand
        .should('exist')
        .click()
        .then(($template) => {
          // Click refresh previews button
          cy.wrap($template).find('.button[data-action="refresh"]')
            .should('exist')
            .click()
          cy.wait('@refreshPreview');
            
          // Watched and unwatched images should be populated
          cy.wrap($template).find('img[content-type="watched"]')
            .should('be.visible')
            .should('have.attr', 'src')
            .should('include', '/internal_assets/preview/')
          cy.wrap($template).find('img[content-type="unwatched"]')
            .should('be.visible')
            .should('have.attr', 'src')
            .should('include', '/internal_assets/preview/')
        })
      
      // Refresh watched preview by clicking the image individually
      cy.reload()
      cy.get(`#template-id${templateId}`)
        // Template should be on page, expand
        .should('exist')
        .click()
        .then(($template) => {
          // Click watched card to refresh
          cy.wrap($template).find('.card[content-type="watched"]')
            .should('exist')
            .click()
          cy.wait('@refreshPreview');

          cy.wrap($template).find('img[content-type="watched"]')
            .should('have.attr', 'src')
            .and('match', /^\/internal_assets\/preview\//)
          cy.wrap($template).find('img[content-type="unwatched"]')
            .should('have.attr', 'src')
            .should('eq', '/internal_assets/blank.png')
        })

        // Refresh unwatched preview by clicking the image individually
        cy.reload()
        cy.get(`#template-id${templateId}`)
          // Template should be on page, expand
          .should('exist')
          .click()
          .then(($template) => {
            // Click unwatched card to refresh
            cy.wrap($template).find('.card[content-type="unwatched"]')
              .should('exist')
              .click()
            cy.wait('@refreshPreview');

            cy.wrap($template).find('img[content-type="unwatched"]')
              .should('have.attr', 'src')
              .and('match', /^\/internal_assets\/preview\//)
            cy.wrap($template).find('img[content-type="watched"]')
              .should('have.attr', 'src')
              .should('eq', '/internal_assets/blank.png')
          })
    });
  });

  it('Does not delete a Template if confirmation is rejected', () => {
    // Get existing number of templates
    cy.get('#templates > .accordion').its('length').then((templateCount) => {
      // Allow time for content to load
      cy.wait(400);
      // Delete first template
      cy.get('#templates > .accordion').last()
        // Expand template
        .click()
        // Click delete button
        .find('button[button-type="delete"]')
          .should('exist')
          .click()
      ;
      // Click confirmation modal
      // cy.get('#delete-template-modal [data-action="reject-deletion"]')
      cy.get('#delete-template-modal .green.button')
        .should('be.visible')
        .click()
      ;

      // Check length again
      cy.get('#templates > .accordion').should('have.length', templateCount);
    });
  });

  it('Deletes a Template', () => {
    // Get existing number of templates
    cy.get('#templates > .accordion').its('length').then((templateCount) => {
      // Allow time for content to load
      cy.wait(350);
      // Delete first template
      cy.get('#templates > .accordion').last()
        // Expand template
        .click()
        // Click delete button
        .find('button[button-type="delete"]')
          .should('exist')
          .click()
      ;
      // Click confirmation modal
      // cy.get('#delete-template-modal [data-action="reject-deletion"]')
      cy.get('#delete-template-modal [data-action="delete-template"]')
        .should('be.visible')
        .click()
      ;

      // Check length again
      cy.get('#templates > .accordion').should('have.length', templateCount - 1);
    });
  });

});
