/**
 * Generate a random number `[min, max]`.
 * @param {number} min Minimum random number. Inclusive.
 * @param {number} max Maximum random number. Inclusive.
 * @returns {number} Random integer between min and max.
 */
const randomInt = (min=1, max=59) => Math.floor(Math.random() * (max - min + 1)) + min;

describe('Scheduler', () => {
  beforeEach(() => cy.visit('/scheduler'));

  it('Visits the scheduler page', () => {
    cy.url().should('eq', Cypress.config('baseUrl') + '/scheduler');
  });

  it('Reschedules multiple tasks in basic mode', () => {
    // Make sure scheduler is in basic mode
    // cy.request('POST', '/api/scheduler/type/basic');

    // Iterate through each row in the scheduler body
    const newIntervals = {};
    cy.get("#task-table tr").each(($row, index) => {
      // Get the data-id value of the row
      const rowId = $row.attr('data-id');
      newIntervals[rowId] = `${index+2} hours, ${randomInt()} minutes`;

      // Find the cell with data-column="frequency" and change its text
      cy.wrap($row).find('td[data-column="frequency"] span')
        .clear()
        .type(newIntervals[rowId])
        .should('have.text', newIntervals[rowId])
    });

    // Click the save button
    cy.contains('Save Changes').click();
    cy.wait(250);
    cy.reload();

    // Verify that the new values are saved
    cy.get("#task-table tr").each(($row) => {
      // Check if the cell with data-column="frequency" has the new value
      const rowId = $row.attr('data-id');
      cy.wrap($row).find('td[data-column="frequency"] span').should('have.text', newIntervals[rowId]);
    });
  })

  it('Manually runs a task in basic mode', () => {
    // Intercept run task request
    cy.intercept('POST', '/api/schedule/*').as('runTask');

    // Get existing "previous duration" text
    cy.get('#task-table [data-column="previous_duration"]').last()
      .invoke('text')
      .then((previousDuration) => {
        previousDuration = previousDuration === '0 seconds' ? '-' : previousDuration;
        // Run this task
        cy.get('#task-table [data-column="runTask"]').last().click();
        cy.wait('@runTask');

        // Verify new duration is different
        cy.get('#task-table [data-column="previous_duration"]').last()
          .invoke('text')
          .should((newDuration) => {
            expect(previousDuration).not.to.eq(newDuration);
          });
      });
  });

  it('Attempts to schedule a task faster than 10 minutes', () => {
    cy.get('#task-table tr').first().then(($row) => {
      // Set frequency to some value shorter than 10 minutes
      const rowId = $row.attr('data-id');
      cy.wrap($row).find('td[data-column="frequency"] span')
        .clear()
        .type(`${randomInt(1, 9)} minutes`);
        
      // Click the save button, wait for reschedule to finish
      cy.intercept('PUT', `/api/schedule/update/${rowId}`).as('rescheduleTask');
      cy.contains('Save Changes').click();
      cy.wait('@rescheduleTask');
  
      // Frequency should be limited to 10 minutes
      cy.get(`#task-table tr[data-id="${rowId}"] [data-column="frequency"] span`)
        .should('have.text', '10 minutes');
    });
  });

  // it('Enables the advanced scheduler', () => {
  //   cy.get('#toggle-button').click();
  // });
})
