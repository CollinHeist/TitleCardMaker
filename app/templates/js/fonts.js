/*
 * Submit an API request to create a new Font. If successful, then all Fonts
 * are reloaded.
 */
function addFont() {
  const data = {name: ' Blank Custom Font'};
  $.ajax({
    type: 'POST',
    url: '/api/fonts/new',
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: font => {
      showInfoToast(`Created Font #${font.id}`);
      getAllFonts();
    },
    error: response => showErrorToast({title: 'Error Creating Font', response}),
  });
}

/*
 * Submit an API request to delete the given Font from the database. If
 * successful, the HTML element for this Font is removed from the page.
 */
function deleteFont(font) {
  $.ajax({
    type: 'DELETE',
    url: `/api/fonts/${font.id}`,
    success: () => {
      showInfoToast(`Deleted Font "${font.name}"`);
      $(`#font-id${font.id}`).remove();
    },
    error: response => showErrorToast({title: 'Error Deleting Font', response}),
  });
}

function reloadPreview(fontId, fontForm, previewForm, cardElement, imageElement) {
  const fontFormObj = new FormData(fontForm);
  const previewFormObj = new FormData(previewForm);
  const previewCardObj = {
    card_type: previewFormObj.get('card_type') || '{{preferences.default_card_type}}',
    title_text: previewFormObj.get('title_text'),
    season_text: 'Season 1',
    episode_text: 'Episode 1',
    font_id: fontId,
    font_title_case: fontFormObj.get('title_case'),
    font_color: fontFormObj.get('color'),
    font_interline_spacing: fontFormObj.get('interline_spacing'),
    font_interword_spacing: fontFormObj.get('interword_spacing'),
    font_kerning: fontFormObj.get('kerning') / 100.0,
    font_size: fontFormObj.get('size') / 100.0,
    font_stroke_width: fontFormObj.get('stroke_width') / 100.0,
    font_vertical_shift: fontFormObj.get('vertical_shift'),
  };

  // Submit API request
  cardElement.classList.add('loading');
  $.ajax({
    type: 'POST',
    url: '/api/cards/preview',
    data: JSON.stringify(previewCardObj),
    contentType: 'application/json',
    success: imageUrl => imageElement.src = `${imageUrl}?${new Date().getTime()}`,
    error: response => showErrorToast({title: 'Error Creating Preview Card', response}),
    complete: () => cardElement.classList.remove('loading'),
  });
}

function saveFontForm(fontId, event) {
  // Validate form, exit if invalid
  if (!$(`#font-id${fontId}`).form('is valid')) {
    return;
  }

  // Construct form
  let form = new FormData(event.target);
  let listData = {replacements_in: [], replacements_out: []};
  for (let [key, value] of [...form.entries()]) {
    if (key === 'size' || key === 'kerning' || key === 'stroke_width') {
      form.set(key, value/100.0);
    }
    if (key === 'replacements_in') { listData.replacements_in.push(value); }
    if (key === 'replacements_out') { listData.replacements_out.push(value); }
  }
  // Add boolean toggle(s)
  $.each($(`#font-id${fontId}`).find('input[type=checkbox]'), (key, val) => {
    form.append($(val).attr('name'), $(val).is(':checked'));
  });

  // Submit API request
  $.ajax({
    type: 'PATCH',
    url: `/api/fonts/${fontId}`,
    data: JSON.stringify({...Object.fromEntries(form.entries()), ...listData}),
    contentType: 'application/json',
    success: font => showInfoToast(`Updated Font "${font.name}"`),
    error: response => showErrorToast({title: 'Error Updating Font', response}),
  });

  // Submit separate API request to upload font file
  if (form.get('font_file').size === 0) { return; }
  let fileForm = new FormData();
  fileForm.append('file', form.get('font_file'));
  $.ajax({
    type: 'PUT',
    url: `/api/fonts/${fontId}/file`,
    data: fileForm,
    processData: false,
    contentType: false,
    success: () => showInfoToast('Uploaded Font File'),
    error: response => showErrorToast({title: 'Error Uploading Font File', response}),
    complete: () => $(`#font-id${fontId} .button[data-action="populateReplacements"]`).toggleClass('disabled', false),
  });
}

// Function to add dropdown card types
async function initCardTypeDropdowns() {
  loadCardTypes({
    element: '.ui.card-type.dropdown',
    isSelected: (identifier) => identifier === '{{preferences.default_card_type}}',
    showExcluded: false,
    dropdownArgs: {},
  });
}

function querySuggestedFontReplacements(fontId, elementId) {
  $.ajax({
    type: 'GET',
    url: `/api/fonts/${fontId}/analysis`,
    success: analysis => {
      // Disable button now that Font has been analyzed
      $(`#${elementId} .button[data-action="populateReplacements"]`).toggleClass('disabled', true);
      // Show toast for irreplacable characters
      if (analysis.missing.length > 0) {
        showErrorToast({
          title: 'Irreplaceable Characters Identified',
          message: 'No Suitable replacements found for: ' + analysis.missing.join(' '),
          displayTime: 10000,
        });
      }
      // No replacements, show toast and exit
      if (Object.keys(analysis.replacements).length === 0) {
        showInfoToast('No Suggested Replacements');
        return;
      }
      // There are replacements, add to page
      const inElement = document.querySelector(`#${elementId} .field[data-value="in-replacements"]`);
      const outElement = document.querySelector(`#${elementId} .field[data-value="out-replacements"]`);
      for (const [repl_in, repl_out] of Object.entries(replacements)) {
        // Skip if this replacement already exists
        let found = false;
        $(`#${elementId} input[name="replacements_in"]`).each(function() {
          if ($(this).val() === repl_in) { found = true; return; }
        });
        if (!found) {
          const newInput = document.createElement('input');
          newInput.value = repl_in; newInput.name = 'replacements_in'; newInput.type='text';
          inElement.appendChild(newInput);
          const newOutput = document.createElement('input');
          newOutput.value = repl_out; newOutput.name = 'replacements_out'; newOutput.type='text';
          outElement.appendChild(newOutput);
        }
      }
      showInfoToast({title: 'Added Suggested Replacements', message: 'Blank replacements indicate a deleted character'});
    }, error: response => showErrorToast({title: 'Error Analyzing Font', response}),
  });
}

// Function to get all fonts and add their elements to the page
async function getAllFonts() {
  // Query for all Fonts
  const fonts = await fetch('/api/fonts/all').then(resp => resp.json());
  const hasManyFonts = fonts.length > 20; // Add headers if >10 Fonts
  const activeFont = window.location.hash.substring(1);
  let previewData;

  // Create array of elements
  const fontElements = [];
  let currentHeader = null;

  fonts.forEach((fontObj) => {
    // Add header element for this letter if needed
    const letter = fontObj.sort_name[0].toUpperCase();
    if (hasManyFonts && letter != currentHeader) {
      currentHeader = letter;
      const header = document.createElement('h2');
      // header.id = letter;
      header.className = 'ui dividing header';
      if (letter === ' ') {
        header.innerText = 'Blank Fonts';
      } else {
        header.innerText = letter;
      }
      fontElements.push(header);
    }

    // Add Font accordion
    const template = document.querySelector('#font-template').content.cloneNode(true);
    template.querySelector('.accordion').id = `font-id${fontObj.id}`;
    // Make accordion active if this was indicated in the URL has
    if (`font-id${fontObj.id}` === activeFont) {
      template.querySelector('.title').classList.add('active');
      template.querySelector('.content').classList.add('active');
    }
    template.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${fontObj.name}`;
    template.querySelector('input[name="name"]').value = fontObj.name;
    const file = template.querySelector('label[data-value="file"]');
    file.innerText = fontObj.file_name === null ? 'Font' : `Font (${fontObj.file_name})`;
    if (fontObj.color !== null) {
      template.querySelector('input[name="color"]').value = fontObj.color;
    }
    if (fontObj.title_case !== null) {
      template.querySelector('input[name="title_case"]').value = fontObj.title_case;
    }
    template.querySelector('input[name="size"]').value = Math.floor(fontObj.size*100);
    template.querySelector('input[name="kerning"]').value = Math.floor(fontObj.kerning*100);
    template.querySelector('input[name="stroke_width"]').value = Math.floor(fontObj.stroke_width*100);
    template.querySelector('input[name="interline_spacing"]').value = fontObj.interline_spacing;
    template.querySelector('input[name="interword_spacing"]').value = fontObj.interword_spacing;
    template.querySelector('input[name="vertical_shift"]').value = fontObj.vertical_shift;
    if (fontObj.delete_missing) {
      template.querySelector('input[name="delete_missing"]').checked = true;
    }
    const inElement = template.querySelector('.field[data-value="in-replacements"]');
    const outElement = template.querySelector('.field[data-value="out-replacements"]');
    if (fontObj.replacements) {
      Object.entries(fontObj.replacements).forEach(([in_, out_]) => {
        const newInput = document.createElement('input');
        newInput.name = 'replacements_in'; newInput.type='text';
        newInput.value = in_;
        inElement.appendChild(newInput);
        const newOutput = document.createElement('input');
        newOutput.name = 'replacements_out'; newOutput.type='text';
        newOutput.value = out_;
        outElement.appendChild(newOutput);
      });
    }
    // Query suggested font replacements on button click
    template.querySelector('.button[data-action="populateReplacements"]').onclick = () => querySuggestedFontReplacements(fontObj.id, `font-id${fontObj.id}`);
    // Add new input fields on click of addReplacement button
    template.querySelector('.button[data-action="addReplacement"]').onclick = () => {
      const blankInput = document.createElement('input');
      blankInput.name = 'replacements_in'; blankInput.type='text';
      inElement.appendChild(blankInput);
      const blankOutput = document.createElement('input');
      blankOutput.name = 'replacements_out'; blankOutput.type='text';
      outElement.appendChild(blankOutput);
    };

    // Set submit form event to submit PATCH API request
    template.querySelector('form[data-value="font-form"]').id = `font-id${fontObj.id}`;
    template.querySelector('form[data-value="font-form"]').onsubmit = event => {
      event.preventDefault();
      saveFontForm(fontObj.id, event);
    };

    // Set delete button to submit DELETE API request
    template.querySelector('.negative.button').onclick = event => {
      event.preventDefault();
      deleteFont(fontObj);
    };

    // Reload preview when button is pressed
    const previewCard = template.querySelector('.ui.card');
    const previewImage = template.querySelector('img');
    const fontForm = template.querySelector('form[data-value="font-form"]');
    const previewForm =  template.querySelector('form[data-value="preview-form"]');
    template.querySelector('.button[data-action="refresh"]').onclick = () => reloadPreview(fontObj.id, fontForm, previewForm, previewCard, previewImage);
    // If this font was indicated in URL, initiate preview load
    if (`font-id${fontObj.id}` === activeFont) {
      previewData = [fontObj.id, fontForm, previewForm, previewCard, previewImage];
    }
    // Update title text + preview when a-z icon is clicked
    const titleInput = template.querySelector('form[data-value="preview-form"] input[name="title_text"]');
    template.querySelector('form[data-value="preview-form"] .field label a').onclick = () => {
      titleInput.value = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ\\nabcdefghijklmnopqrstuvwxyz';
      reloadPreview(fontObj.id, fontForm, previewForm, previewCard, previewImage);
    }

    fontElements.push(template);
  });
  // Put new font elements on the page
  document.getElementById('fonts').replaceChildren(...fontElements);

  // Scroll to active Font if indicated
  if (activeFont) {
    document.getElementById(activeFont).scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
    // Start loading preview
    reloadPreview(...previewData);
  }

  // Enable accordion/dropdown/checkbox elements
  $('.ui.accordion').accordion();
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
  // Apply form validations
  $('.form[data-value="font-form"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['minLength[1]'],
      size: ['integer[1..]'],
    },
  });

  // Fill in card type dropdowns
  initCardTypeDropdowns();

  // Refresh theme for any newly added HTML
  refreshTheme();
}
