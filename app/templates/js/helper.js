/**
 * @typedef {Object} DropdownValue
 * @property {string} name - Name of the value as it appears in the dropdown.
 * @property {string} value - Value which will be listed in the dropdown's
 * input.
 * @property {bool} selected - Whether this value is selected within the
 * dropdown.
 */

/**
 * @typedef {Object} Extra
 * @property {string} name
 * @property {DictKey} identifier
 * @property {string} description
 * @property {?string} tooltip
 * @property {?string} card_type
 */

/**
 * Toggle the side navigation menu. If on mobile, then the menu is toggled,
 * if on desktop, then this redirects to the home page.
 */
function toggleNavMenu() {
  // On mobile toggle the nav menu; on desktop go home
  if (isSmallScreen()) {
    const navMenu = document.getElementById('nav-menu');
    const mainContent = document.getElementById('main-content');
    if (navMenu.style.display === 'none') {
      // Currently hidden, show
      navMenu.style.display = 'block';
      mainContent.style.removeProperty('padding-left');
    } else {
      navMenu.style.display = 'none';
      mainContent.style.paddingLeft = '15px';
    }
  } else {
    // Not on mobile, go to home page
    window.location.href = '/';
  }
}

/**
 * Debounce the given function with the given timeout. The minimum interval
 * between calls to the return of this function will be `timeout` ms.
 * @arg {function} func - Function to debounce.
 * @arg {Number} [timeout] - Minimum interval between calls to `func`.
 * @returns {function} Debounced version of `func`.
 */ 
function debounce(func, timeout = 850){
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => { func.apply(this, args); }, timeout);
  };
}

/**
 * Determine whether this device is technically a small screen.
 * @returns {bool} Whether this device screen is small, and mobile
 * formatting should apply.
 */
const isSmallScreen = () => window.innerWidth < 768;

/**
 * Format the given number of bytes into a human-readable string.
 * @example
 * formatBytes(1.25e6, 2); // '1.19 MiB'
 * @param {number} bytes - Byte amount to forma.
 * @param {number} [decimals] - Number of decimal places to display.
 * @returns {string} Formatted string.
 */
function formatBytes(bytes, decimals = 2) {
  if (!+bytes) return '0 B'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

/**
 * Format the given FastAPI response object into a single string.
 * @param {Object} errorResponse - AJAX response from to format.
 * @param {string|Object} errorResponse.detail - Details of the FastAPI error to
 * add to the return.
 * @returns {string} Formatted string representation of the given response.
 */
function formatFastAPIError(errorResponse) {
  // No response or details
  if (!errorResponse || !errorResponse.detail) {
    return undefined;
  }

  // If detail is string, likely an explicit error
  if (typeof errorResponse.detail === 'string') {
    return errorResponse.detail;
  }

  const formattedErrors = errorResponse.detail.map(detail => {
    let errorMessage = "An error occurred.";

    if (typeof detail === 'string') {
      errorMessage = detail;
    } else if (detail.msg) {
      errorMessage = detail.msg;
    }

    if (detail.loc && Array.isArray(detail.loc)) {
      errorMessage = `${detail.loc[1]}: ${errorMessage}`;
    }

    return errorMessage;
  });

  return formattedErrors.join('\n');
}

/**
 * Show an error toast. Equivalent to `$.toast({class: 'error', ...args})`
 * @param {Object} args - Arguments for the toast creation.
 * @param {string} args.title - Title of the toast.
 * @param {string} args.message - Message of the toast - only displayed if
 * args.response is undefined.
 * @param {*} args.response - Response object to format in the message text.
 * @param {number} [args.displayTime=7500] - How long (in ms) to display the toast.
 */
function showErrorToast({title, message, response, displayTime=7500}) {
  console.log(response);
  if (response === undefined) {
    $.toast({
      class: 'error',
      title,
      message,
      displayTime: displayTime,
    });
  } else {
    $.toast({
      class: 'error',
      title,
      message: formatFastAPIError(response.responseJSON),
      displayTime: displayTime,
    });
  }
}

/**
 * Show an error toast. Equivalent to `$.toast({class: 'blue info', ...args})`
 * @param {string | Object} args - Toast title or arguments
 * @param {string} [args.title] - Title of the toast.
 * @param {string} [args.message] - Message of the toast - only displayed if
 * args.response is undefined.
 * @param {number} [args.displayTime=1000] - How long (in ms) to display the toast.
 */
function showInfoToast(args) {
  if (typeof args === 'string') {
    $.toast({class: 'blue info', title: args});
  } else {
    const {title, message, displayTime=1000} = args;
    $.toast({
      class: 'blue info',
      title: title,
      message: message,
      displayTime: displayTime,
    });
  }
}

/**
 * Get the list of template values (for a $.dropdown) based on the given
 * IDs.
 * @param {int[]} activeIds - Template IDs which are active and to include
 * in the return.
 * @param {Object[]} availableTemplates - List of all the available
 * Template objects which should be filtered.
 * @returns {DropdownValue[]} List of values which can be used in the 
 * dropdown initialization for the given Template IDs.
 */
function getActiveTemplates(activeIds, availableTemplates) {
  let values = [];
  // Add all active Template values
  if (activeIds !== undefined && activeIds !== null) {
    activeIds.forEach(activeId => {
      for (let {id, name} of availableTemplates) {
        // Found matching Template, add to values array
        if (activeId === id) {
          values.push({name: name, value: id, selected: true});
          break;
        }
      }
    });
  }
  // Add all inactive Template values
  availableTemplates.forEach(({id, name}) => {
    // Skip Templates already included
    if (activeIds === undefined || activeIds === null) {
      values.push({name: name, value: id, selected: false});
    } else if (!activeIds.includes(id)) {
      values.push({name: name, value: id, selected: false});
    }
  });

  return values;
}

/**
 * 
 * @param {int} pageNumber - Page number of the element to create.
 * @param {string} pageText - Text to display within the element.
 * @param {bool} active - Whether this element should be created as active
 * and disabled.
 * @param {function} navigateFunction - Function to call when this element
 * is clicked.
 * @returns {HTMLElement} Created element for use in a pagination menu.
 */
function createPageElement(pageNumber, pageText, active = false, navigateFunction) {
  let element = document.createElement('a');
  element.className = active ? 'active disabled item' : 'item';
  element.innerText = pageText;
  if (pageNumber !== undefined) {
    element.onclick = () => {
      // Add a looping animation to show element has been clicked
      element.classList.add('transition', 'looping', 'pulsating', 'blue');
      // Call navigate function on this page number
      navigateFunction(pageNumber);
    }
  }
  return element;
}

/**
 * 
 * @param {string} [args.paginationElementId] - DOM Element ID of the pagination
 * menu to update.
 * @param {function} [args.navigateFunction] - Function to call when a
 * page button is clicked.
 * @param {number} [args.page=1] - Current page number. Defaults to 1.
 * @param {number} [args.pages=1] - Total number of pages. Defaults to 1.
 * @param {?number} [args.amountVisible] - Total number of page buttons to make
 * visible. If undefined, then the amount is determined by the element width.
 * @param {boolean} [args.hideIfSinglePage=false] - Whether to hide the
 * pagination menu if there is only a single page.
 * @returns 
 */
function updatePagination(args) {
  let {
    paginationElementId = () => {},
    navigateFunction = () => {},
    page = 1,
    pages = 1,
    amountVisible = undefined,
    hideIfSinglePage = false,
  } = args;

  // Remove existing pagination links
  $(`#${paginationElementId} a`).remove();

  // If amount visible is not fixed, then determine via width
  if (amountVisible === undefined) {
    let totalWidth = document.getElementById(paginationElementId).offsetWidth;
    let pageWidth = page + 10 > 100 ? 56.25 : 48.25;
    amountVisible = Math.floor(totalWidth / pageWidth);
  }

  // Add no links if only one page
  if (pages === 1) {
    if (hideIfSinglePage) {
      $(`#${paginationElementId}`).remove();
    } else {
      $(`#${paginationElementId}`).append([
        createPageElement(1, 1, true, navigateFunction)
      ]);
    }
    return;
  }

  // Determine how many links to show on the left and right of the active page
  let links = [],
      leftLinksBounds = Math.min(page-1, (amountVisible - 1) / 2),
      rightLinksBounds = Math.min(pages-page, (amountVisible - 1) / 2);
  let leftLinks = Math.floor(Math.min(page-1, leftLinksBounds + ((amountVisible-1) / 2) - rightLinksBounds)),
      rightLinks = Math.floor(Math.min(pages, rightLinksBounds + ((amountVisible-1) / 2) - leftLinksBounds));

  // Create previous pages
  for (let pageNum = page - leftLinks; pageNum < page; pageNum++) {
    // Skip invalid pages
    if (pageNum <= 0) { continue; }
    // First nav
    if (pageNum > 1 && links.length === 0) {
      links.push(createPageElement(1, '«', false, navigateFunction));
    } else {
      links.push(createPageElement(pageNum, pageNum, false, navigateFunction));
    }
  }
  // Add active page
  links.push(createPageElement(page, page, true, navigateFunction));
  // Add next pages
  for (let pageNum = page + 1; pageNum <= page + rightLinks && pageNum <= pages; pageNum++) {
    // Last nav
    if (pageNum !== pages && pageNum === page + rightLinks) {
      links.push(createPageElement(pages, '»', false, navigateFunction));
    } else {
      links.push(createPageElement(pageNum, pageNum, false, navigateFunction));
    }
  }

  $(`#${paginationElementId}`).append(links);
}

function initializeNullableBoolean(args) {
  const {dropdownElement, value} = args;
  const isTrue = (value === true) || (value === 'True');
  const isFalse = (value === false) || (value === 'False');
  dropdownElement.dropdown({
    placeholder: 'Default',
    values: [
      {name: 'True', value: 'True', selected: isTrue},
      {name: 'False', value: 'False', selected: isFalse},
    ],
  });
}

/**
 * Download a text file of the given data to the browser.
 * @param {string} filename - Name of the file to download as.
 * @param {string} text - Text to download.
 */
function downloadTextFile(filename, text) {
  // Create download element, add to document
  var element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);
  element.style.display = 'none';
  document.body.appendChild(element);

  // "Click" element to initiate download, remove from document
  element.click();
  document.body.removeChild(element);
}

async function downloadFile(filename, url) {
  // Fetch contents from URL
  const response = await fetch(url);
  if (response.status !== 200 ) {
    showErrorToast({title: 'Error Downloading File'});
    return;
  }

  // Get file contents
  const blob = await response.blob();

  // Create download element, add to document
  const downloadLink = document.createElement('a');
  downloadLink.setAttribute('href', URL.createObjectURL(blob));
  downloadLink.setAttribute('download', filename);
  downloadLink.style.display = 'none';
  document.body.appendChild(downloadLink);

  // "Click" element to initiate download, remove from document
  downloadLink.click();
  document.body.removeChild(downloadLink);
}

async function downloadFileBlob(filename, blob) {
  // Create download element, add to document
  const downloadLink = document.createElement('a');
  downloadLink.setAttribute('href', URL.createObjectURL(blob));
  downloadLink.setAttribute('download', filename);
  downloadLink.style.display = 'none';
  document.body.appendChild(downloadLink);

  // "Click" element to initiate download, remove from document
  downloadLink.click();
  document.body.removeChild(downloadLink);
}

/** @type {Extra[]} */
let allExtras;

let cardTypeSet, cardTypes;
/**
 * Submit an API request to get all the available extras and populate the
 * allExtras, cardTypeSet, and cardTypes variables.
 */
async function queryAvailableExtras() {
  if (allExtras === undefined) {
    allExtras = await fetch('/api/available/extras').then(resp => resp.json());
    // Get list of all unique card types
    cardTypeSet = new Set();
    allExtras.forEach(extra => cardTypeSet.add(extra.card_type));
    cardTypes = Array.from(cardTypeSet);
  }
}

let popups = {};
let _allLibraries, _allConnections;
/**
 * Query for all the globally available Connections and Libraries. This updates
 * the global variables. Only re-queries if not initialized.
 */
async function queryLibraries() {
  if (_allConnections === undefined) {
    _allConnections = await fetch('/api/connection/all')
      .then(resp => resp.json());
  }
  if (_allLibraries === undefined) {
    _allLibraries = await fetch('/api/available/libraries/all')
      .then(resp => resp.json());
  }
}

/**
 *
 */
async function initializeLibraryDropdowns({
    selectedLibraries,
    dropdownElements,
    clearable=true,
    useLabels=true,
    onChange=() => {}}) {
  // Only re-query for libraries if not initialized
  if (_allLibraries === undefined || _allConnections === undefined) {
    await queryLibraries();
  }

  // Start library value list with those selected by the Series
  const dropdownValues = selectedLibraries.map(library => {
    return {
      interface: library.interface,
      interface_id: library.interface_id,
      name: library.name,
      selected: true
    };
  });

  // Add each library not already selected
  _allLibraries.forEach(({interface, interface_id, name}) => {
    if (!(dropdownValues.some(library => library.interface_id === interface_id && library.name === name))) {
      dropdownValues.push({interface, interface_id, name, selected: false});
    }
  });

  // Initialize dropdown
  dropdownElements.dropdown({
    placeholder: 'None',
    clearable,
    useLabels,
    onChange,
    values: dropdownValues.map(({interface, interface_id, name, selected}) => {
      const serverName = _allConnections.filter(connection => connection.id === interface_id)[0].name || interface;
      return {
        name: name,
        text: `${name} (${serverName})`,
        value: `${interface}::${interface_id}::${name}`,
        description: serverName,
        descriptionVertical: true,
        selected: selected,
      };
    }),
  });
}

/**
 * Fill out the given Blueprint card element with the details - i.e. the
 * creator, title, image, description, etc.
 * @param {HTMLTemplateElement} card - Template element being populated.
 * @param {import("./.types").RemoteBlueprint} blueprint - Blueprint used to
 * populate the given card.
 * @param {string} blueprintId - DOM Element ID of the card.
 */
function populateBlueprintCard(card, blueprint, blueprintId) {
  // Fill out card
  card.querySelector('.card').id = blueprintId;
  let preview = card.querySelector('img');
  preview.src = blueprint.json.previews[0];
  // More than one preview, mark image as multi (for CSS formatting), and cycle through images on click
  if (blueprint.json.previews.length > 1) {
    card.querySelector('.image').classList.add('multi');
    card.querySelector('.image').style.backgroundImage = `url("${blueprint.json.previews[1]}")`;
    preview.dataset.imageIndex = 0;
    preview.onclick = () => {
      let newImageIndex = ($(`#${blueprintId} img`).data('imageIndex') + 1) % blueprint.json.previews.length;
      let nextImageIndex = (newImageIndex + 1) % blueprint.json.previews.length;
      $(`#${blueprintId} .image`).css('background-image', `url("${blueprint.json.previews[nextImageIndex]}")`);
      $(`#${blueprintId} img`).attr('src', blueprint.json.previews[newImageIndex]);
      $(`#${blueprintId} img`).data('imageIndex', newImageIndex);
    };
  }

  card.querySelector('[data-value="creator"]').innerText = blueprint.creator;

  // If there is a Series name element, fill out
  if (card.querySelector('[data-value="name"]')) {
    card.querySelector('[data-value="name"]').innerText = blueprint.series.name;
  }
  if (card.querySelector('[data-value="year"]')) {
    card.querySelector('[data-value="year"]').innerText = `(${blueprint.series.year})`;
  }
  if (card.querySelector('[data-value="series_full_name"')) {
    card.querySelector('[data-value="series_full_name"').innerText = `${blueprint.series.name} (${blueprint.series.year})`;
  }

  // Font count
  if (blueprint.json.fonts.length === 0) {
    card.querySelector('[data-value="font-count"]').remove();
  } else {
    let text = `<b>${blueprint.json.fonts.length}</b> Font` + (blueprint.json.fonts.length > 1 ? 's' : '');
    card.querySelector('[data-value="font-count"]').innerHTML = text;
  }

  // Templates count
  if (blueprint.json.templates.length === 0) {
    card.querySelector('[data-value="template-count"]').remove();
  } else {
    let text = `<b>${blueprint.json.templates.length}</b> Template` + (blueprint.json.templates.length > 1 ? 's' : '');
    card.querySelector('[data-value="template-count"]').innerHTML = text;
  }

  // Episodes count
  const episodeOverrideCount = Object.keys(blueprint.json.episodes).length;
  if (episodeOverrideCount === 0) {
    card.querySelector('[data-value="episode-count"]').remove();
  } else {
    let text = `<b>${episodeOverrideCount}</b> Episode Override` + (episodeOverrideCount > 1 ? 's' : '');
    card.querySelector('[data-value="episode-count"]').innerHTML = text;
  }

  // Source files count
  const sourceFileCount = blueprint.json.series.source_files.length;
  if (sourceFileCount === 0) {
    card.querySelector('[data-value="file-count"]').remove();
    card.querySelector('.popup').remove();
  } else {
    const text = `<b>${sourceFileCount}</b> Source File` + (sourceFileCount > 1 ? 's' : '');
    card.querySelector('[data-value="file-count"]').innerHTML = text;
    card.querySelector('.popup .content').innerHTML = blueprint.json.series.source_files.join(', ');
  }

  card.querySelector('[data-value="description"]').innerHTML = '<p>' + blueprint.json.description.join('</p><p>') + '</p>';

  // Sets
  if (blueprint.set_ids.length > 0) {
    card.querySelector('[data-value="set-count"]').innerText = blueprint.set_ids.length > 1
      ? `${blueprint.set_ids.length} Associated Sets`
      : `1 Associated Set`;
  } else if (card.querySelector('.extra.content')) {
    card.querySelector('.extra.content').remove();
  }

  return card;
}


function timeDiffString(previousRun) {
  const previous = new Date(previousRun);

  // Get current time
  const diffSeconds = Math.floor((new Date() - previous) / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Create string for next run time, only show up to two time units
  const timeUnits = [];
  if (diffDays > 1) { timeUnits.push(`${diffDays} days`); }
  else if (diffDays > 0) { timeUnits.push(`diffDays day`); }
  if (diffHours % 24 > 1) { timeUnits.push(`${diffHours%24} hours`); }
  else if (diffHours % 24 > 0) { timeUnits.push(`${diffHours%24} hour`); }
  if (diffMinutes % 60 > 1) { timeUnits.push(`${diffMinutes%60} minutes`); }
  else if (diffMinutes % 60 > 0) { timeUnits.push(`${diffMinutes%60} minute`); }
  if (diffSeconds % 60 > 1) { timeUnits.push(`${diffSeconds%60} seconds`); }
  else if (diffSeconds % 60 > 0) { timeUnits.push(`<${diffSeconds%60} second`); }

  return timeUnits.slice(0, 2).join(', ') + ' ago';
}

/**
 * Convert a string to title case.
 * @param {string} str - The input string to convert to title case.
 * @returns {string} The input string converted to title case.
 * @example
 * // returns "I Love JavaScript"
 * toTitleCase("i love JavaScript");
 */
function toTitleCase(str) {
  return str.replace(/(?:^|\s)\w/g, function(match) {
    return match.toUpperCase();
  });
}

/**
 * 
 * @param {?Object.<string, string>} activeExtras - Object of active extras to
 * initialize the extra input fields with.
 * @param {string} activeTab - Name of the tab to mark as active.
 * @param {string} sectionQuerySelector - Query selector to find the section
 * being populated.
 * @param {HTMLTemplateElement} inputTemplateElement - ID of the extra input
 * element to clone and populate.
 * @param {isGlobal} - Whether the extras being initialized are for global
 * extras, or not. Global extras are formatted under {card_type: {}}, while
 * normal extras are not. If global, variable overrides are excluded, and inputs
 * of the same name are not linked.
 * @param {number} groupAmount - How many extras to combine in a single group
 * field. Default 2.
 */
async function initializeExtras(
  activeExtras,
  activeTab,
  sectionQuerySelector,
  inputTemplateElement,
  isGlobal = false,
  groupAmount = 2,
) {
  if (allExtras === undefined) {
    await queryAvailableExtras();
  }

  /** @type {Object.<string, Extra[]>} */
  const types = {};

  // Create object of card type identifiers to array of extras
  allExtras.forEach(extra => {
    // If skipping overrides, skip if no assigned card type
    if (isGlobal && !extra.card_type) { return; }

    extra.card_type = extra.card_type || 'Variable Overrides';
    if (types[extra.card_type] === undefined) {
      types[extra.card_type] = [];
    }
    types[extra.card_type].push(extra);
  });

  // Create tabs for each card type
  const extraMenu = document.querySelector(`${sectionQuerySelector} .menu`);
  for (const [card_type, extras] of Object.entries(types)) {
    // Create tab menu item
    const newMenuItem = document.createElement('a');
    newMenuItem.className = card_type === activeTab ? 'active item' : 'item';
    newMenuItem.dataset.tab = card_type.replace('/', '_');
    newMenuItem.innerText = toTitleCase(card_type);
    extraMenu.appendChild(newMenuItem);

    // Create tab itself
    const newTab = document.createElement('div');
    newTab.className = 'ui bottom attached tab segment' + (card_type === activeTab ? ' active' : '');
    newTab.dataset.tab = card_type.replace('/', '_'); // Cannot use / in tab identifiers
    extraMenu.insertAdjacentElement('afterend', newTab);

    // Add input field for each extra
    extras.forEach((extra, index) => {
      const newInput = inputTemplateElement.content.cloneNode(true);
      newInput.querySelector('label').innerText = extra.name;
      newInput.querySelector('input').name = extra.identifier;
      newInput.querySelector('.help').innerHTML = `<b>${extra.description}</b><br>`
        + (extra.tooltip
            ? extra.tooltip
                .replaceAll('<v>', '<span class="ui blue text inverted">')
                .replaceAll('</v>', '</span>')
                .replaceAll(
                  /<c>(.*?)<\/c>/g,
                  '<code class="color">$1<span style="--color: $1" class="color circle"></span></code>'
                )
            : ''
          );

      // Fill out input if part of active extras
      if ((isGlobal && activeExtras.hasOwnProperty(card_type)
            && activeExtras[card_type][extra.identifier]) ||
          (!isGlobal && activeExtras[extra.identifier])) {
            newInput.querySelector('input').value = isGlobal
              ? activeExtras[card_type][extra.identifier]
              : activeExtras[extra.identifier];
      }

      // Group every two fields into a field group
      if (index % groupAmount === 0) {
        const newFields = document.createElement('div');
        newFields.className = 'ui equal width fields';
        newTab.appendChild(newFields);
      }
      newTab.lastChild.appendChild(newInput);
    });
  }

  // Change all inputs with the same name when any input is changed
  if (!isGlobal) {
    $(`${sectionQuerySelector}`).on('change', 'input', function() {
      $(`${sectionQuerySelector} input[name="${$(this).attr('name')}"]`).val($(this).val());
    });
  }

  // Initialize tabs
  $(`${sectionQuerySelector} .item`).tab();
}

/**
 * Determine whether the given color definition is "light".
 * @param {number} r - Red value of the color.
 * @param {number} g - Green value of the color.
 * @param {number} b - Blue value of the color.
 * @returns {boolean} `true` if the color is light, `false` otherwise.
 */
const isLightColor = (r, g, b) => (r * 0.299) + (g * 0.587) + (b * 0.114) < 186;

/** @type {set[string]} */
const _analyzedImages = new Set();

/**
 * Analyze the palette of the given image, populating the palette object with
 * color swatches from the analysis.
 * @param {string} imageElementSelector - Selector of the image element to
 * analyze.
 * @param {string} paletteSelector - Selector of the palette in the DOM to
 * populate with colors.
 */
function analyzePalette(imageElementSelector, paletteSelector) {
  const image = document.querySelector(imageElementSelector);
  const palette = document.querySelector(paletteSelector);
  // Early exit if there is no image or image
  if (!image || !image.src || !palette || _analyzedImages.has(image.src)) { return; }

  function hasDuplicatesWithinRange(subArray, seenArrays) {
    const tooClose = (v0, v1) => Math.abs(v0 - v1) <= 10;
    for (const seenArray of seenArrays) {
      if (tooClose(seenArray[0], subArray[0])
          && tooClose(seenArray[1], subArray[1])
          && tooClose(seenArray[2], subArray[2])) {
        return true;
      }
    }
    return false;
  }

  /** @type {set[number, number, number]} */
  const seen = new Set();

  // Analyze image, filter out colors that are too similiar to another
  new ColorThief().getPalette(image, 8, 12)?.filter(subArray => {
    // return true;
    if (hasDuplicatesWithinRange(subArray, seen)) {
      return false;
    } else {
      seen.add(subArray);
      return true;
    }
  }).forEach(([r, g, b]) => { // Create swatches for each indicated color
    const bubble = document.createElement('span');
    bubble.className = 'color';
    bubble.style.setProperty('--color', `rgb(${r}, ${g}, ${b})`);
    bubble.dataset.clipboardText = `rgb(${r}, ${g}, ${b})`;
    palette.appendChild(bubble);
  });

  // Add to list of analyzed images
  _analyzedImages.add(image.src);

  // Copy to clipboard when clicked
  new ClipboardJS(`${paletteSelector} span.color`)
    .on('success', function (event) {
      showInfoToast(`Copied ${event.text} to clipboard`);
    });
}
