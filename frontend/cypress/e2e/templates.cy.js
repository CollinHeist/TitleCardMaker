const getRandomText = () => Math.random().toString(36).substring(2, 10);

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

  it('Changes all settings', () => {
    const originalName = getRandomText();
    const newSettings = {
      name: getRandomText(),
      card_type: 'White Border',
      font_id: getRandomText(),
      watched_style: 'Blurred Grayscale Art',
      unwatched_style: 'Grayscale Unique',
      hide_season_text: 'True',
      hide_episode_text: 'False',
      episode_text_format: getRandomText(),
      skip_localized_images: 'True',
      data_source_id: 'TMDb',
      sync_specials: 'False',
      extras: [
        { cardType: 'Anime',              name: 'Episode Text Font Size', value: '2.0'     },
        { cardType: 'Banner',             name: 'Banner Color',           value: 'black'   },
        { cardType: 'Graph',              name: 'Text Position',          value: 'left'    },
        { cardType: 'Music',              name: 'Player Style',           value: 'poster'  },
        { cardType: 'Tinted Frame',       name: 'Frame Color',            value: 'crimson' },
        { cardType: 'Variable Overrides', name: 'Season Text Format',     value: 'S1'      },
      ],
    };

    // Create Font so it can be assigned to the Template
    cy.createObjectAndGetId('/api/fonts/new', {'name': newSettings.font_id}).as('fontId')
    // Create dummy TMDb Connection so it can be selected
    cy.createTMDbConnection()
    cy.reload()

    cy.createObjectAndGetId('/api/templates/new', {'name': originalName}).then((templateId) => {
      // Expand template
      cy.get('#templates').contains(originalName)
        .click()
        .parent()
        .then(($template) => {
          cy.wrap($template).find('.content').as('templateContent')
          cy.get('@templateContent').should('have.class', 'active')

          // Name
          cy.get('@templateContent')
            .find('input[name="name"]').first()
              .clear()
              .type(newSettings.name)
              .should('have.value', newSettings.name)

          // Card type
          cy.selectDropdown('@templateContent', '.dropdown[data-value="card_type"]', newSettings.card_type)

          // Font ID
          cy.selectDropdown('@templateContent', '.dropdown[data-value="font_id"]', newSettings.font_id)

          // Watched style
          cy.selectDropdown('@templateContent', '.dropdown[data-value="watched_style"]', newSettings.watched_style)

          // Unwatched style
          cy.selectDropdown('@templateContent', '.dropdown[data-value="unwatched_style"]', newSettings.unwatched_style)

          // Hide Season Text
          cy.selectDropdown('@templateContent', '.dropdown[data-value="hide_season_text"]', newSettings.hide_season_text)

          // Hide Episode Text
          cy.selectDropdown('@templateContent', '.dropdown[data-value="hide_episode_text"]', newSettings.hide_episode_text)
  
          // Episode Text Format
          cy.get('@templateContent')
            .find('input[name="episode_text_format"]').first()
              .clear()
              .type(newSettings.episode_text_format)
              .should('have.value', newSettings.episode_text_format)

          // Ignored Localized Images
          cy.selectDropdown('@templateContent', '.dropdown[data-value="skip_localized_images"]', newSettings.skip_localized_images)

          // Episode Data Source
          cy.selectDropdown('@templateContent', '.dropdown[data-value="data_source_id"]', newSettings.data_source_id)

          // Enable Specials
          cy.selectDropdown('@templateContent', '.dropdown[data-value="sync_specials"]', newSettings.sync_specials)

          // Extras
          newSettings.extras.forEach((extra) => {
            cy.selectExtra(
              cy.get('@templateContent').find('section[aria-label="extras"]'),
              extra.cardType, extra.name, extra.value
            )
          })

          // Save changes
          cy.get('@templateContent').contains('button', 'Save Changes').click()
        })

      // Reload page, find Template object
      cy.reload()
      cy.get('#templates').contains(newSettings.name)
        .click()
        .parent()
        .then(($template) => {
          // Verify all settings carried over
          cy.wrap($template).find('.content').as('templateContent')

          // Name
          cy.get('@templateContent').find('input[name="name"]')
            .should('have.value', newSettings.name)

          // Card type
          cy.get('@templateContent').find('.dropdown[data-value="card_type"] .menu .selected')
            .should('contain', newSettings.card_type)

          // Font ID
          cy.get('@templateContent').find('.dropdown[data-value="font_id"] .menu .selected')
            .should('contain', newSettings.font_id)

          // Watched style
          cy.get('@templateContent').find('.dropdown[data-value="watched_style"] .menu .selected')
            .should('contain', newSettings.watched_style)

          // Unwatched style
          cy.get('@templateContent').find('.dropdown[data-value="unwatched_style"] .menu .selected')
            .should('contain', newSettings.unwatched_style)

          // Hide Season Text
          cy.get('@templateContent').find('.dropdown[data-value="hide_season_text"] .menu .selected')
            .should('contain', newSettings.hide_season_text)

          // Hide Episode Text
          cy.get('@templateContent').find('.dropdown[data-value="hide_episode_text"] .menu .selected')
            .should('contain', newSettings.hide_episode_text)
  
          // Episode Text Format
          cy.get('@templateContent').find('input[name="episode_text_format"]')
            .should('have.value', newSettings.episode_text_format)

          // Ignored Localized Images
          cy.get('@templateContent').find('.dropdown[data-value="skip_localized_images"] .menu .selected')
            .should('contain', newSettings.skip_localized_images)

          // Episode Data Source
          cy.get('@templateContent').find('.dropdown[data-value="data_source_id"] .menu .selected')
            .should('contain', newSettings.data_source_id)

          // Enable Specials
          cy.get('@templateContent').find('.dropdown[data-value="sync_specials"] .menu .selected')
            .should('contain', newSettings.sync_specials)

          // Extras
          newSettings.extras.forEach((extra) => {
            cy.validateExtra(
              cy.get('@templateContent').find('section[aria-label="extras"]'),
              extra.cardType, extra.name, extra.value
            )
          })
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

  // TODO
  it('Assigns a global default Template', () => {

  });

});
