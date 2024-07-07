describe('Page Navigation', () => {
  // Navigate directly via URLs
  const pages = [
    { path: '/',               name: 'Home'                           },
    { path: '/add',            name: 'Add Series'                     },
    { path: '/missing',        name: 'Missing'                        },
    { path: '/card-templates', name: 'Templates'                      },
    { path: '/fonts',          name: 'Fonts'                          },
    { path: '/sync',           name: 'Sync'                           },
    { path: '/settings',       name: 'Settings'                       },
    { path: '/connections',    name: 'Connections'                    },
    { path: '/scheduler',      name: 'Scheduler'                      },
    { path: '/import',         name: 'Importer'                       },
    { path: '/logs',           name: 'Logs'                           },
    { path: '/graphs',         name: 'Graphs'                         },
    { path: '/changelog',      name: 'Changelog'                      },
    { path: '/non-existent',   name: 'Non-existent', expectRoot: true },
  ];

  pages.forEach(({ path, name, expectRoot }) => {
    it(`Visits the ${name} page`, () => {
      cy.visit(path)
      cy.url().should('contain', Cypress.config('baseUrl') + (expectRoot ? '/' : path))
    });
  });

  // Visit the series page
  it('Visits the Series page', () => {
    // Create new Series so the page can be visited
    cy.createObjectAndGetId('/api/series/new', {'name': '_', 'year': 2024}).then((seriesId) => {
      cy.visit(`/series/${seriesId}`)
      cy.url().should('contain', Cypress.config('baseUrl') + `/series/${seriesId}`)
    });
  });

  it('Visits a non-existent Series page', () => {
    cy.visit('/series/999')
    cy.url().should('contain', Cypress.config('baseUrl') + '/')
  });

  // Navigate via the sidebar to all possible pages
  const sidebarNavigation = [
    {
      fromUrl: '/',
      fromName: 'home',
      navs: [
        { selector: '#nav-menu [href="/add"]',            name: 'add series',    expectedUrl: '/add'            },
        { selector: '#nav-menu [href="/missing"]',        name: 'missing cards', expectedUrl: '/missing'        },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates',     expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',         expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/sync"]',           name: 'sync',          expectedUrl: '/sync'           },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',      expectedUrl: '/settings'       },
        { selector: '#page-header [href="/logs"]',        name: 'logs',          expectedUrl: '/logs'           },
        { selector: '#main-content [href="/graphs"]',     name: 'graph',         expectedUrl: '/graphs'         },
      ]
    },
    {
      fromUrl: '/add',
      fromName: 'add series',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',          expectedUrl: '/'               },
        { selector: '#nav-menu [href="/missing"]',        name: 'missing cards', expectedUrl: '/missing'        },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates',     expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',         expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/sync"]',           name: 'sync',          expectedUrl: '/sync'           },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',      expectedUrl: '/settings'       },
        { selector: '#page-header [href="/logs"]',        name: 'logs',          expectedUrl: '/logs'           },
      ]
    },
    {
      fromUrl: '/missing',
      fromName: 'missing cards',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',       expectedUrl: '/'               },
        { selector: '#nav-menu [href="/add"]',            name: 'add series', expectedUrl: '/add'            },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates',  expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',      expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/sync"]',           name: 'sync',       expectedUrl: '/sync'           },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',   expectedUrl: '/settings'       },
        { selector: '#page-header [href="/logs"]',        name: 'logs',       expectedUrl: '/logs'           },
      ]
    },
    {
      fromUrl: '/card-templates',
      fromName: 'templates',
      navs: [
        { selector: '#nav-menu [href="/"]',         name: 'home',     expectedUrl: '/'         },
        { selector: '#nav-menu [href="/fonts"]',    name: 'fonts',    expectedUrl: '/fonts'    },
        { selector: '#nav-menu [href="/sync"]',     name: 'sync',     expectedUrl: '/sync'     },
        { selector: '#nav-menu [href="/settings"]', name: 'settings', expectedUrl: '/settings' },
        { selector: '#page-header [href="/logs"]',  name: 'logs',     expectedUrl: '/logs'     },
      ]
    },
    {
      fromUrl: '/fonts',
      fromName: 'fonts',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',      expectedUrl: '/'               },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates', expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/sync"]',           name: 'sync',      expectedUrl: '/sync'           },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',  expectedUrl: '/settings'       },
        { selector: '#page-header [href="/logs"]',        name: 'logs',      expectedUrl: '/logs'           },
      ]
    },
    {
      fromUrl: '/sync',
      fromName: 'sync',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',      expectedUrl: '/'               },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates', expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',     expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',  expectedUrl: '/settings'       },
        { selector: '#page-header [href="/logs"]',        name: 'logs',      expectedUrl: '/logs'           },
      ]
    },
    {
      fromUrl: '/settings',
      fromName: 'settings',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',        expectedUrl: '/'               },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates',   expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',       expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/connections"]',    name: 'connections', expectedUrl: '/connections'    },
        { selector: '#nav-menu [href="/scheduler"]',      name: 'scheduler',   expectedUrl: '/scheduler'      },
        { selector: '#nav-menu [href="/import"]',         name: 'import',      expectedUrl: '/import'         },
        { selector: '#nav-menu [href="/changelog"]',      name: 'changelog',   expectedUrl: '/changelog'      },
        { selector: '#page-header [href="/logs"]',        name: 'logs',        expectedUrl: '/logs'           },
        { selector: '#main-content .label [href="/changelog"]', name: 'changelog', expectedUrl: '/changelog', }
      ]
    },
    {
      fromUrl: '/connections',
      fromName: 'connections',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',      expectedUrl: '/'               },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates', expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',     expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',  expectedUrl: '/settings'       },
        { selector: '#nav-menu [href="/scheduler"]',      name: 'scheduler', expectedUrl: '/scheduler'      },
        { selector: '#nav-menu [href="/import"]',         name: 'import',    expectedUrl: '/import'         },
        { selector: '#nav-menu [href="/changelog"]',      name: 'changelog',   expectedUrl: '/changelog'      },
        { selector: '#page-header [href="/logs"]',        name: 'logs',      expectedUrl: '/logs'           },
      ]
    },
    {
      fromUrl: '/scheduler',
      fromName: 'scheduler',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',        expectedUrl: '/'               },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates',   expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',       expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',    expectedUrl: '/settings'       },
        { selector: '#nav-menu [href="/connections"]',    name: 'connections', expectedUrl: '/connections'    },
        { selector: '#nav-menu [href="/import"]',         name: 'import',      expectedUrl: '/import'         },
        { selector: '#nav-menu [href="/changelog"]',      name: 'changelog',   expectedUrl: '/changelog'      },
        { selector: '#page-header [href="/logs"]',        name: 'logs',        expectedUrl: '/logs'           },
      ]
    },
    {
      fromUrl: '/import',
      fromName: 'import',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',        expectedUrl: '/'               },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates',   expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',       expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',    expectedUrl: '/settings'       },
        { selector: '#nav-menu [href="/connections"]',    name: 'connections', expectedUrl: '/connections'    },
        { selector: '#nav-menu [href="/scheduler"]',      name: 'scheduler',   expectedUrl: '/scheduler'      },
        { selector: '#nav-menu [href="/changelog"]',      name: 'changelog',   expectedUrl: '/changelog'      },
        { selector: '#page-header [href="/logs"]',        name: 'logs',        expectedUrl: '/logs'           },
      ],
    },
    {
      fromUrl: '/changelog',
      fromName: 'Changelog',
      navs: [
        { selector: '#nav-menu [href="/"]',               name: 'home',        expectedUrl: '/'               },
        { selector: '#nav-menu [href="/card-templates"]', name: 'templates',   expectedUrl: '/card-templates' },
        { selector: '#nav-menu [href="/fonts"]',          name: 'fonts',       expectedUrl: '/fonts'          },
        { selector: '#nav-menu [href="/settings"]',       name: 'settings',    expectedUrl: '/settings'       },
        { selector: '#nav-menu [href="/connections"]',    name: 'connections', expectedUrl: '/connections'    },
        { selector: '#nav-menu [href="/scheduler"]',      name: 'scheduler',   expectedUrl: '/scheduler'      },
        { selector: '#nav-menu [href="/import"]',         name: 'import',      expectedUrl: '/import'         },
        { selector: '#page-header [href="/logs"]',        name: 'logs',        expectedUrl: '/logs'           },
      ],
    }
  ];

  sidebarNavigation.forEach(({fromUrl, fromName, navs}) => {
    navs.forEach(({selector, name, expectedUrl}) => {
      it(`Visits the ${name} page while on the ${fromName} page`, () => {
        cy.visit(fromUrl);
        cy.get(selector).should('exist').click();
        cy.url().should('contain', Cypress.config('baseUrl') + expectedUrl);
      });
    });
  })
});
