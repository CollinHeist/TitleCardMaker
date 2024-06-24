describe('Card Templates', () => {
  beforeEach(() => cy.visit('/card-templates'));

  it('Creates a new Blank Template', () => {
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

  it('Changes the name and verify it persists after save and reload', () => {
    // Get first Template ID
    cy.get('#templates > .accordion').first()
      .invoke('attr', 'id')
      .then((id) => cy.wrap(id).as('templateId'))
    ;

    // Change name and save changes
    const newValue = Math.random().toString(36);
    cy.get('#templates > .accordion').first()
      // Expand
      .click()
      .then(($template) => {
        // Put new randomized name in the name field
        cy.wrap($template).get('.content')
          .should('have.class', 'active')
          .find('input[name="name"]').first()
            .clear()
            .type(newValue)
            .should('have.value', newValue)
          ;

        // Save changes
        cy.wrap($template).contains('button', 'Save Changes').click();
      })
    ;

    // Reload page
    cy.reload();

    // Check name
    cy.get('@templateId').then((templateId) => {
      cy.get(`#${templateId}`)
        // Expand template
        .click()
        // Verify name matches
        .find('.content input[name="name"]')
          .should('have.value', newValue)
      ;
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
      cy.get('#delete-template-modal .green.button')
        .should('be.visible')
        .click()
      ;

      // Check length again
      cy.get('#templates > .accordion').should('have.length', templateCount);
    });
  });

  it('Does not delete a Template if confirmation is rejected', () => {
    
  });

});