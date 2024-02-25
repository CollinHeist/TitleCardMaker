{% if False %}
import {FontAnalysis, NamedFont} from './.types.js';
{% endif %}

/**
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
    /**
     * Font created; show toast and re-query all Fonts.
     * @param {NamedFont} font - Newly created Font.
     */
    success: font => {
      showInfoToast(`Created Font #${font.id}`);
      window.location.hash = `font-id${font.id}`;
      getAllFonts();
    },
    error: response => showErrorToast({title: 'Error Creating Font', response}),
  });
}

/**
 * Submit an API request to delete the given Font from the database. If
 * successful, the HTML element for this Font is removed from the page.
 * @param {NamedFont} font - Font to delete.
 */
function deleteFont(font) {
  $.ajax({
    type: 'DELETE',
    url: `/api/fonts/${font.id}`,
    /** Font deleted, show toast and remove this Font's element from the DOM. */
    success: () => {
      showInfoToast(`Deleted Font "${font.name}"`);
      $(`#font-id${font.id}`).remove();
    },
    error: response => showErrorToast({title: 'Error Deleting Font', response}),
  });
}

/**
 * Submit an API request to reload the preview image for the Font with the given
 * data.
 * @param {number} fontId - ID of the Font whose preview is being reloaded.
 * @param {HTMLFormElement} fontForm - Form whose data is being previewed.
 * @param {HTMLFormElement} previewForm - Form containing preview images.
 * @param {HTMLElement} cardElement - Element to mark as loading while the
 * preview is being generated.
 * @param {HTMLImageElement} imageElement - Element whose `src` to update.
 */
function reloadPreview(fontId, fontForm, previewForm, cardElement, imageElement) {
  const fontFormObj = new FormData(fontForm);
  const previewFormObj = new FormData(previewForm);
  const previewCardObj = {
    card_type: previewFormObj.get('card_type') || '{{preferences.default_card_type}}',
    title_text: previewFormObj.get('title_text'),
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
    /**
     * Preview created; update `imageElement.src`.
     * @param {string} imageUrl - New URI to the generated preview image.
     */
    success: imageUrl => imageElement.src = `${imageUrl}?${new Date().getTime()}`,
    error: response => showErrorToast({title: 'Error Creating Preview Card', response}),
    complete: () => cardElement.classList.remove('loading'),
  });
}

/**
 * Submit an API request to update the Font with the given ID (if the Font Form
 * is valid). This also uploads the uploaded Font file (if present).
 * @param {number} fontId - ID of the Font whose form is being parsed and
 * updated.
 * @param {EventTarget} eventTarget - Target of the event initializing the save
 * (the Font Form).
 */
function saveFontForm(fontId, eventTarget) {
  // Validate form, exit if invalid
  if (!$(`#font-id${fontId}`).form('is valid')) { return; }

  // Construct form
  let form = new FormData(eventTarget);
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
    /**
     * Font updated, display toast.
     * @param {NamedFont} font - Updated Font.
     */
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

/**
 * Perform an analysis of this Font, adding any suggested Font replacements to
 * the DOM.
 * @param {number} fontId - ID of the Font being analyzed.
 * @param {string} elementId - ID of the form associated with this Font.
 */
function querySuggestedFontReplacements(fontId, elementId) {
  $.ajax({
    type: 'GET',
    url: `/api/fonts/${fontId}/analysis`,
    /**
     * Font analyzed, update DOM with suggested replacements.
     * @param {FontAnalysis} analysis - Analysis to display.
     */
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
      for (const [repl_in, repl_out] of Object.entries(analysis.replacements)) {
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
    },
    error: response => showErrorToast({title: 'Error Analyzing Font', response}),
  });
}

let previewData;
/**
 * 
 * @param {Node} template - Element being populated.
 * @param {NamedFont} font - Font object whose details are used to populate the
 * element.
 * @param {?string} [activeFontId] - ID of the active font. If `font` is this
 * same object, then the accordion is created in an initialized state.
 * @returns {Node} Modified `template`.
 */
function populateFontElement(template, font, activeFontId) {
  // Set Element ID
  template.querySelector('.accordion').id = `font-id${font.id}`;

  // Make accordion active if this was indicated in the URL
  if (activeFontId && `font-id${font.id}` === activeFontId) {
    template.querySelector('.title').classList.add('active');
    template.querySelector('.content').classList.add('active');
  }

  template.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${font.name}`;
  template.querySelector('input[name="name"]').value = font.name;

  template.querySelector('label[data-value="file"]').innerHTML =
    font.file_name === null ? 'File' : `File (<span class="prefix">config/fonts/${font.id}/</span>${font.file_name})`;
  
  if (font.color !== null) {
    template.querySelector('input[name="color"]').value = font.color;
    // Update inline circle
    template.querySelector('.field[data-value="color"] .color.circle').style.setProperty('--color', font.color);
  }
  // Add onchange listener to recolor circle
  template.querySelector('input[name="color"]').oninput = function () {
    document.querySelector(`#font-id${font.id} .field[data-value="color"] .color.circle`).style.setProperty('--color', $(this).val());
  }

  if (font.title_case !== null) {
    template.querySelector('input[name="title_case"]').value = font.title_case;
  }
  template.querySelector('input[name="size"]').value = Math.floor(font.size*100);
  template.querySelector('input[name="kerning"]').value = Math.floor(font.kerning*100);
  template.querySelector('input[name="stroke_width"]').value = Math.floor(font.stroke_width*100);
  template.querySelector('input[name="interline_spacing"]').value = font.interline_spacing;
  template.querySelector('input[name="interword_spacing"]').value = font.interword_spacing;
  template.querySelector('input[name="vertical_shift"]').value = font.vertical_shift;
  if (font.delete_missing) {
    template.querySelector('input[name="delete_missing"]').checked = true;
  }

  // Set font replacements
  const inElement = template.querySelector('.field[data-value="in-replacements"]');
  const outElement = template.querySelector('.field[data-value="out-replacements"]');
  for (let i = 0; i < font.replacements_in.length; i++) {
    const newInput = document.createElement('input');
      newInput.name = 'replacements_in'; newInput.type = 'text';
      newInput.value = font.replacements_in[i];
      inElement.appendChild(newInput);
      
      const newOutput = document.createElement('input');
      newOutput.name = 'replacements_out'; newOutput.type='text';
      newOutput.value = font.replacements_out[i];
      outElement.appendChild(newOutput);
  }

  // Query suggested font replacements on button click
  template.querySelector('.button[data-action="populateReplacements"]').onclick = () => querySuggestedFontReplacements(font.id, `font-id${font.id}`);
  
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
  template.querySelector('form[data-value="font-form"]').id = `font-id${font.id}`;
  template.querySelector('form[data-value="font-form"]').onsubmit = event => {
    event.preventDefault();
    saveFontForm(font.id, event.target);
  };

  // Set delete button to submit DELETE API request
  template.querySelector('.negative.button').onclick = event => {
    event.preventDefault();
    deleteFont(font);
  };

  // Reload preview when button is pressed
  const previewCard = template.querySelector('.ui.card');
  const previewImage = template.querySelector('img');
  const fontForm = template.querySelector('form[data-value="font-form"]');
  const previewForm =  template.querySelector('form[data-value="preview-form"]');
  template.querySelector('.button[data-action="refresh"]').onclick = () => reloadPreview(font.id, fontForm, previewForm, previewCard, previewImage);
  // If this font was indicated in URL, initiate preview load
  if (activeFontId && `font-id${font.id}` === activeFontId) {
    previewData = [font.id, fontForm, previewForm, previewCard, previewImage];
  }

  // Update title text + preview when a-z icon is clicked
  const titleInput = template.querySelector('form[data-value="preview-form"] input[name="title_text"]');
  template.querySelector('form[data-value="preview-form"] .field label a').onclick = () => {
    titleInput.value = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ\\nabcdefghijklmnopqrstuvwxyz';
    reloadPreview(font.id, fontForm, previewForm, previewCard, previewImage);
  }

  return template;
}

/**
 * Submit an API request to query all defined Fonts and add their populated
 * forms to the DOM.
 */
function getAllFonts() {
  $.ajax({
    type: 'GET',
    url: '/api/fonts/all',
    /**
     * Fonts queried, add all Font forms to the DOM.
     * @param {NamedFont[]} fonts 
     */
    success: fonts => {
      // Display head if there are many Fonts
      const hasManyFonts = fonts.length > 20;

      // Get the currently active Font from the URL
      const activeFontId = window.location.hash.substring(1);

      // Create elements to add to DOM
      let currentHeader = null,
          fontElements = [];
      fonts.forEach(font => {
        // Add letter header for this Font if necessary
        let letter = font.sort_name[0].toUpperCase();
        letter = isNaN(parseInt(letter)) ? letter : '#'; // All numbers go under #

        if (hasManyFonts && letter !== currentHeader) {
          const header = document.createElement('h3');
          header.className = 'ui dividing header';
          header.innerText = (letter === ' ') ? 'Blank Fonts' : letter;
          fontElements.push(header);
          currentHeader = letter;
        }

        // Add accordion for this Font
        fontElements.push(populateFontElement(
          document.getElementById('font-template').content.cloneNode(true),
          font,
          activeFontId
        ));
      });

      // Put new font elements on the page
      document.getElementById('fonts').replaceChildren(...fontElements);

      // Scroll to active Font if indicated
      if (activeFontId) {
        document.getElementById(activeFontId).scrollIntoView({
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

      // Fill in card type dropdowns
      loadCardTypes({
        element: '.ui.card-type.dropdown',
        isSelected: (identifier) => identifier === '{{preferences.default_card_type}}',
        showExcluded: false,
        dropdownArgs: {},
      });

      // Refresh theme for any newly added HTML
      refreshTheme();

      // Apply form validations
      $('.form[data-value="font-form"]').form({
        on: 'blur',
        inline: true,
        fields: {
          name: ['minLength[1]'],
          size: ['integer[1..]'],
        },
      });
    },
    error: response => showErrorToast({title: 'Error Loading Fonts', response}),
  });
}

function initAll() {
  getAllFonts();
}