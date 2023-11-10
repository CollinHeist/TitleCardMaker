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

function isSmallScreen() {
  return window.screen.availWidth < 768;
}

function formatBytes(bytes, decimals = 2) {
  if (!+bytes) return '0 B'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

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

function showErrorToast(args) {
  const {title, message, response, displayTime=10000} = args;
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

function showInfoToast(args) {
  if (typeof args === 'string') {
    $.toast({class: 'blue info', title: args});
  } else {
    const {title, message, displayTime} = args;
    $.toast({
      class: 'blue info',
      title: title,
      message: message,
      displayTime: displayTime,
    });
  }
}

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

function createPageElement(pageNumber, pageText, active = false, navigateFunction) {
  let element = document.createElement('a');
  element.className = active ? 'active disabled item' : 'item';
  element.innerText = pageText;
  if (pageNumber !== undefined) { element.onclick = () => navigateFunction(pageNumber); }
  return element;
}

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

/*
 *
 */
let allExtras, cardTypeSet, cardTypes;
async function queryAvailableExtras() {
  if (allExtras === undefined) {
    allExtras = await fetch('/api/available/extras').then(resp => resp.json());
    // Get list of all unique card types
    cardTypeSet = new Set();
    allExtras.forEach(extra => cardTypeSet.add(extra.card_type));
    cardTypes = Array.from(cardTypeSet);
  }
}

/*
 * Initialize the extra key dropdowns with all available options.
 */
let popups = {};
async function initializeExtraDropdowns(
    value,
    dropdownElements,
    popupHeaderElement,
    popupDescriptionElement) {
  // Only re-query for extras if not initialized
  if (allExtras === undefined) {
    await queryAvailableExtras();
  }

  // Create list of values for the dropdown
  let dropdownValues = [],
      found = false;
  cardTypes.forEach(card_type => {
    // Add dividing header for each card type
    dropdownValues.push({name: card_type, type: 'header', divider: true});

    // Add each extra
    allExtras.forEach(extra => {
      // Store the popup data for this identifier
      popups[extra.identifier] = (extra.tooltip || extra.description)
        .replaceAll('<v>', '<span class="ui blue text">')
        .replaceAll('</v>', '</span>');

      if (extra.card_type === card_type) {
        found ||= extra.identifier === value;
        dropdownValues.push({
          name: extra.name,
          text: extra.name,
          value: extra.identifier,
          description: extra.description,
          descriptionVertical: true,
          selected: extra.identifier === value,
        });
        // Initialize popup
        if (extra.identifier === value && popupHeaderElement && popupDescriptionElement) {
          popupHeaderElement[0].innerText = extra.name;
          popupDescriptionElement[0].innerHTML = popups[extra.identifier];
        }
      }
    });
  });

  // If not found, must be manually specified - add
  if (!found) {
    dropdownValues.push({name: 'Variable Overrides', type: 'header', divider: true});
    dropdownValues.push({
      name: value,
      value: value,
      selected: true,
    });
    popupHeaderElement[0].innerText = value;
    popupDescriptionElement[0].innerHTML = 'Manually specified variable override.';
  }

  // Initialize dropdown
  dropdownElements.dropdown({
    placeholder: 'Extra',
    values: dropdownValues,
    clearable: true,
    allowAdditions: true,
    onChange: function(value, text, $selectedItem) {
      if ($selectedItem === null) { return; }
      // Update the popup to the newly selected field
      $selectedItem.closest('.field').find('.popup .header').text(text);
      $selectedItem.closest('.field').find('.popup .description').html(popups[value]);
    }
  });
}

/*
 * Fill out the given Blueprint card element with the details - i.e. the
 * creator, title, image, description, etc.
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
  return card;
}