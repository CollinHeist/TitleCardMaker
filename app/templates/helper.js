function sortStandardizeStr(text) {
  return text.toString().replace(/^(a|an|the)(\s)/i, '').toLowercase();
}

function formatBytes(bytes, decimals = 2) {
  if (!+bytes) return '0 B'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

function getActiveTemplates(activeIds, allTemplates) {
  let values = [];
  // Add all active Template values
  if (activeIds !== undefined && activeIds !== null) {
    activeIds.forEach(activeId => {
      for (let {id, name} of allTemplates) {
        // Found matching Template, add to values array
        if (activeId === id) {
          values.push({name: name, value: id, selected: true});
          break;
        }
      }
    });
  }
  // Add all inactive Template values
  allTemplates.forEach(({id, name}) => {
    // Skip Templates already included
    if (activeIds === undefined || activeIds === null) {
      values.push({name: name, value: id, selected: false});
    } else if (!activeIds.includes(id)) {
      values.push({name: name, value: id, selected: false});
    }
  });

  return values;
}

function formatValidationError(response) {
  const detail = response.responseJSON.detail;
  let message = '';
  detail.forEach(obj => message += `<li>${obj.loc[1]} : ${obj.msg}</li>`)
  return `<ul class="ui list">${message}</ul>`;
}

function createPageElement(pageNumber, pageText, active = false, navigateFunction) {
  let element = document.createElement('a');
  element.className = active ? 'active disabled item' : 'item';
  element.innerText = pageText;
  if (pageNumber !== undefined) { element.onclick = () => navigateFunction(pageNumber); }
  return element;
}

function updatePagination(args) {
  const {
    paginationElementId = () => {},
    navigateFunction = () => {},
    page = 1,
    pages = 1,
    amountVisible = 5,
    hideIfSinglePage = false,
  } = args;

  // Remove existing pagination links
  $(`#${paginationElementId} a`).remove();

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
    $.toast({class: 'error', title: 'Error Downloading File'});
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