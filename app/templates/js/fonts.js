// Function to create a new empty font
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

function deleteFont(font) {
  $.ajax({
    type: 'DELETE',
    url: `/api/fonts/${font.id}`,
    success: () => {
      $.toast({class: 'blue info', title: `Deleted Font "${font.name}"`});
      $('.ui.accordion').accordion('close');
      getAllFonts();
    },
    error: response => showErrorToast({title: 'Error Deleting Font', response}),
  });
}

function reloadPreview(fontId, fontForm, previewForm, cardElement, imageElement) {
  const fontFormObj = new FormData(fontForm);
  const previewFormObj = new FormData(previewForm);
  // Don't bother if no preview card type is selected
  if (previewFormObj.get('card_type') === '') { return; }
  const previewCardObj = {
    card_type: previewFormObj.get('card_type'),
    title_text: previewFormObj.get('title_text'),
    season_text: 'Season 1',
    episode_text: 'Episode 1',
    font_id: fontId,
    font_title_case: fontFormObj.get('title_case'),
    font_color: fontFormObj.get('color'),
    font_interline_spacing: fontFormObj.get('interline_spacing'),
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
    success: (response) => {
      // Update source, use current time to force reload
      imageElement.src = `${response}?${new Date().getTime()}`;
    },
    error: response => showErrorToast({title: 'Error Creating Preview Card', response}),
    complete: () => {cardElement.classList.remove('loading'); }
  });
}

// Function to get all fonts and add their elements to the page
async function getAllFonts() {
  // Query for all Fonts
  const fonts = await fetch('/api/fonts/all').then(resp => resp.json());
  const hasManyFonts = fonts.length > 20; // Add headers if >10 Fonts

  // Create array of elements
  const fontElements = [];
  let currentHeader = null;

  fonts.forEach((fontObj) => {
    // Add header element for this letter if needed
    const letter = fontObj.sort_name[0].toUpperCase();
    if (hasManyFonts && letter != currentHeader) {
      currentHeader = letter;
      const header = document.createElement('h2');
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
    template.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${fontObj.name}`;
    const name = template.querySelector('input[name="name"]');
    name.placeholder = fontObj.name; name.value = fontObj.name;
    const file = template.querySelector('label[data-value="file"]');
    file.innerText = fontObj.file_name === null ? 'Font' : `Font (${fontObj.file_name})`;
    if (fontObj.color !== null) {
      const color = template.querySelector('input[name="color"]');
      color.placeholder = fontObj.color; color.value = fontObj.color;
    }
    if (fontObj.title_case !== null) {
      template.querySelector('input[name="title_case"]').value = fontObj.title_case;
    }
    const size = template.querySelector('input[name="size"]');
    size.placeholder = fontObj.size*100; size.value = fontObj.size*100;
    const kerning = template.querySelector('input[name="kerning"]');
    kerning.placeholder = fontObj.kerning*100; kerning.value = fontObj.kerning*100;
    const stokeWidth = template.querySelector('input[name="stroke_width"]');
    stokeWidth.placeholder = fontObj.stroke_width*100; stokeWidth.value = fontObj.stroke_width*100;
    const interlineSpacing = template.querySelector('input[name="interline_spacing"]');
    interlineSpacing.placeholder = fontObj.interline_spacing; interlineSpacing.value = fontObj.interline_spacing;
    const verticalShift = template.querySelector('input[name="vertical_shift"]');
    verticalShift.placeholder = fontObj.vertical_shift; verticalShift.value = fontObj.vertical_shift;
    if (fontObj.delete_missing) {
      template.querySelector('input[name="delete_missing"]').checked = true;
    }
    const inElement = template.querySelector('.field[data-value="in-replacements"]');
    const outElement = template.querySelector('.field[data-value="out-replacements"]');
    if (fontObj.replacements) {
      Object.entries(fontObj.replacements).forEach(([in_, out_]) => {
        const newInput = document.createElement('input');
        newInput.name = 'replacements_in'; newInput.type='text';
        newInput.placeholder = in_; newInput.value = in_;
        inElement.appendChild(newInput);
        const newOutput = document.createElement('input');
        newOutput.name = 'replacements_out'; newOutput.type='text';
        newOutput.placeholder = out_; newOutput.value = out_;
        outElement.appendChild(newOutput);
      });
    }
    // Add new input fields on click of addReplacement button
    template.querySelector('.button[data-value="addReplacement"]').onclick = () => {
      const blankInput = document.createElement('input');
      blankInput.name = 'replacements_in'; blankInput.type='text';
      inElement.appendChild(blankInput);
      const blankOutput = document.createElement('input');
      blankOutput.name = 'replacements_out'; blankOutput.type='text';
      outElement.appendChild(blankOutput);
    };

    // Set submit form event to submit PATCH API request
    template.querySelector('form[data-value="font-form"]').id = `font-id${fontObj.id}`;
    template.querySelector('form[data-value="font-form"]').onsubmit = (event) => {
      event.preventDefault();
      // Validate form, if invalid, exit
      if (!$(`#font-id${fontObj.id}`).form('is valid')) { return; }
      let form = new FormData(event.target);
      let listData = {replacements_in: [], replacements_out: []};
      for (let [key, value] of [...form.entries()]) {
        if (key === 'size' || key === 'kerning' || key === 'stroke_width') {
          form.set(key, value/100.0);
        }
        if (key === 'replacements_in') { listData.replacements_in.push(value); }
        if (key === 'replacements_out') { listData.replacements_out.push(value); }
      }
      $.ajax({
        type: 'PATCH',
        url: `/api/fonts/${fontObj.id}`,
        data: JSON.stringify({...Object.fromEntries(form.entries()), ...listData}),
        contentType: 'application/json',
        success: font => $.toast({class: 'blue info', title: `Updated Font "${font.name}"`}),
        error: response => showErrorToast({title: 'Error Updating Font', response}),
      });

      // Submit separate API request to upload font file
      if (form.get('font_file').size === 0) { return; }
      let fileForm = new FormData();
      fileForm.append('file', form.get('font_file'));
      $.ajax({
        type: 'PUT',
        url: `/api/fonts/${fontObj.id}/file`,
        data: fileForm,
        processData: false,
        contentType: false,
        success: () => $.toast({class: 'blue info', title: 'Uploaded Font File'}),
        error: response => showErrorToast({title: 'Error Uploading Font File', response}),
      });
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

    fontElements.push(template);
    // return template;
  });
  // Put new font elements on the page
  const fontsElement = document.getElementById('fonts');
  fontsElement.replaceChildren(...fontElements);

  // Enable accordion/dropdown/checkbox elements
  $('.ui.accordion').accordion();
  $('.ui.dropdown').dropdown();
  $('.ui.checkbox').checkbox();
  // Apply form validations
  $('.form[data-value="font-form"]').form({
    on: 'blur',
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

// Function to add dropdown card types
async function initCardTypeDropdowns() {
  loadCardTypes({
    element: '.ui.card-type.dropdown',
    isSelected: (identifier) => identifier === '{{preferences.default_card_type}}',
    showExcluded: false,
    dropdownArgs: {},
  });
}
