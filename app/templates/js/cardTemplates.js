async function reloadPreview(watchStatus, formElement, cardElement, imgElement) {
  let form = new FormData(formElement);
  let listData = {extra_keys: [], extra_values: []};
  if (watchStatus === 'watched' && form.get('watched_style') === '') {
    form.set('style', '{{preferences.default_watched_style}}');
  } else if (watchStatus === 'unwatched' && form.get('unwatched_style') === '') {
    form.set('style', '{{preferences.default_unwatched_style}}');
  } else if (form.get(`${watchStatus}_style`).includes('blur')) {
    form.set('blur', true);
  } else if (form.get(`${watchStatus}_style`).includes('grayscale')) {
    form.set('grayscale', true);
  }
  
  for (let [key, value] of [...form.entries()]) {
    if (key === 'extra_keys') { listData.extra_keys.push(value); }
    if (key === 'extra_values') { listData.extra_values.push(value); }
    if (value === '') { form.delete(key); }
  }

  const previewCard = {
    card_type: "{{preferences.default_card_type.lower()}}",
    style: form.get(`${watchStatus}_style`),
    ...Object.fromEntries(form.entries()),
    extra_keys: listData.extra_keys,
    extra_values: listData.extra_values,
  };
  cardElement.classList.add('loading');
  $.ajax({
    type: 'POST',
    url: '/api/cards/preview',
    data: JSON.stringify(previewCard),
    contentType: 'application/json',
    success: response => {
      imgElement.src = `${response}?${new Date().getTime()}`;
    },
    error: response => {
      $.toast({
        class: 'error',
        title: 'Error Creating Preview Card',
        message: response,
      });
    }, complete: () => {
      cardElement.classList.remove('loading');
    }
  });
}

async function showDeleteModal(templateId) {
  // Get list of Series associated with this Template
  const allSeriesResponse = await fetch(`/api/series/search?template_id=${templateId}&size=25`).then(resp => resp.json());
  const seriesElements = allSeriesResponse.items.map(({name, year}) => {
    return `<li>${name} (${year})</li>`
  });
  // More than 25 Series, add indicator of total amount being deleted
  if (allSeriesResponse.total > 25) {
    seriesElements.push(`<li><span class="ui red text">${allSeriesResponse.total-25} more Series...</span></li>`)
  }
  $('#delete-template-modal [data-value="series-list"]')[0].innerHTML = seriesElements.join('');
  // Attach functions to delete buttons
  $('#delete-template-modal .button[data-action="delete-template"]').off('click').on('click', () => {
    $.ajax({
      type: 'DELETE',
      url: `/api/templates/${templateId}`,
      success: response => {
        $.toast({class: 'blue info', title: 'Deleted Template'});
        getAllTemplates();
      },
      error: response => {
        $.toast({class: 'error', title: 'Error Deleting Template'});
      }, complete: () => {}
    });
  });

  $('#delete-template-modal').modal('show');
}

async function getAllTemplates() {
  const allFilterOptions = await fetch('/api/available/template-filters').then(resp => resp.json());
  const allCardTypes = await fetch('/api/available/card-types').then(resp => resp.json());
  const allFonts = await fetch('/api/fonts/all').then(resp => resp.json());
  const allStyles = await fetch('/api/available/styles').then(resp => resp.json());
  const allTemplates = await fetch('/api/templates/all').then(resp => resp.json());
  const allEpisodeDataSources = await fetch('/api/available/episode-data-sources').then(resp => resp.json());
  const allTranslations = await fetch('/api/available/translations').then(resp => resp.json());
  const elements = allTemplates.items.map(templateObj => {
    // Clone template
    const base = document.querySelector('#template').content.cloneNode(true);
    base.querySelector('.accordion').id = `template-id${templateObj.id}`;
    // Set accordion title and title input
    base.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${templateObj.name}`;
    const nameElem = base.querySelector('input[name="name"]');
    nameElem.placeholder = templateObj.name; nameElem.value = templateObj.name;
    // Filters added later
    // Card type set later
    // Font set later
    // Unwatched and Watched style set later
    // Hide season text set later
    // Season titles
    if (Object.entries(templateObj.season_titles).length > 0) {
      const rangeDiv = base.querySelector('.field[data-value="season-title-range"]');
      const valueDiv = base.querySelector('.field[data-value="season-title-value"]');
      for (const [range, value] of Object.entries(templateObj.season_titles)) {
        const rangeElem = document.createElement('input');
        rangeElem.name = 'season_title_ranges'; rangeElem.setAttribute('data-value', 'season-titles');
        rangeElem.type = 'text'; rangeElem.value = range;
        rangeDiv.appendChild(rangeElem);
        const valueElem = document.createElement('input');
        valueElem.name = 'season_title_values'; valueElem.type = 'text'; valueElem.value = value;
        valueDiv.appendChild(valueElem);
      }
    }
    // Hide episode text set later
    // if (templateObj.hide_episode_text) {
    //   base.querySelector('input[name="hide_episode_text"]').setAttribute('checked', '');
    //   base.querySelector('.field[data-value="episode-text-format"]').className = 'ui disabled field';
    // }
    // Episode text format
    base.querySelector('input[name="episode_text_format"]').value = templateObj.episode_text_format;
    // Ignore localized
    if (templateObj.skip_localized_images) {
      base.querySelector('input[name="skip_localized_images"]').setAttribute('checked', '');
    }
    // Episode data source set later
    // Sync specials set later
    // Image source priority set later
    // Translations added later
    // Extras
    if (Object.entries(templateObj.extras).length > 0) {
      const labelDiv = base.querySelector('.field[data-value="extra-key"]');
      const inputDiv = base.querySelector('.field[data-value="extra-value"]');
      for (const [key, value] of Object.entries(templateObj.extras)) {
        const label = document.createElement('input');
        label.name = 'extra_keys'; label.type = 'text'; label.value = key;
        labelDiv.appendChild(label);
        const valueElem = document.createElement('input');
        valueElem.name = 'extra_values'; valueElem.type = 'text'; valueElem.value = value;
        inputDiv.appendChild(valueElem)
      }
    }
    // Update card preview(s)
    const form = base.querySelector('form');
    const watchedCard = base.querySelector('.card[content-type="watched"]'),
        unwatchedCard = base.querySelector('.card[content-type="unwatched"]');
    const watchedImg = base.querySelector('img[content-type="watched"]'),
        unwatchedImg = base.querySelector('img[content-type="unwatched"]');
    base.querySelector('.button[data-action="refresh"]').onclick = () => {
      reloadPreview('watched', form, watchedCard, watchedImg);
      reloadPreview('unwatched', form, unwatchedCard, unwatchedImg);
    }
    return base;
  });
  document.getElementById('templates').replaceChildren(...elements);
  $('.ui.accordion').accordion();
  $('.ui.checkbox').checkbox();

  // Fill in fancy values
  allTemplates.items.forEach(templateObj => {
    // Filters
    if (templateObj.filters.length > 0) {
      const conditionsDiv = $(`#template-id${templateObj.id} [data-value="conditions"]`);
      for (const condition of templateObj.filters) {
        // Create new filter, add to div
        const newCondition = document.getElementById('filter-template').content.cloneNode(true);
        conditionsDiv.append(newCondition);
        // Initialize dropdowns
        $(`#template-id${templateObj.id} .dropdown[data-value="filter-arguments"]`).last().dropdown({
          placeholder: 'Select Argument',
          values: allFilterOptions.arguments.map(argument => {
            return {name: argument, value: argument, selected: argument === condition.argument};
          })
        });
        $(`#template-id${templateObj.id} .dropdown[data-value="filter-operators"]`).last().dropdown({
          placeholder: 'Select Operation',
          values: allFilterOptions.operations.map(operation => {
            return {name: operation, value: operation, selected: operation === condition.operation};
          })
        });
        if (condition.reference !== null) {
          $(`#template-id${templateObj.id} input[data-value="filter-reference"]`).last()[0].value = condition.reference;
        }
      }
    }
    // Add new fields with add condition button
    $(`#template-id${templateObj.id} .button[data-add-field="condition"]`).on('click', () => {
      const newCondition = document.getElementById('filter-template').content.cloneNode(true);
      $(`#template-id${templateObj.id} [data-value="conditions"]`).append(newCondition);
      $(`#template-id${templateObj.id} [data-value="conditions"] .dropdown[data-value="filter-arguments"]`).last().dropdown({
        placeholder: 'Select Argument',
        values: allFilterOptions.arguments.map(argument => {
          return {name: argument, value: argument, selected: false};
        }),
      });
      $(`#template-id${templateObj.id} [data-value="conditions"] .dropdown[data-value="filter-operators"]`).last().dropdown({
        placeholder: 'Select Operation',
        values: allFilterOptions.operations.map(operation => {
          return {name: operation, value: operation, selected: false};
        }),
      });
    });
    // Card type
    loadCardTypes({
      element: `#template-id${templateObj.id} >* .dropdown[data-value="card-types"]`,
      isSelected: (identifier) => identifier === templateObj.card_type,
      dropdownArgs: {
        placeholder: 'Global Default',
      }
    });
    // Font
    $(`#template-id${templateObj.id} >* .dropdown[data-value="font-dropdown"]`).dropdown({
      values: allFonts.map(({id, name}) => {
        return {name: name, value: id, selected: id === templateObj.font_id};
      }), placeholder: 'Card Default',
    });
    // Watched style
    $(`#template-id${templateObj.id} >* .dropdown[data-value="watched-style"]`).dropdown({
      values: [
        {name: 'Art Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'art').map(({name, value}) => {
          return {name: name, value: value, selected: value === templateObj.watched_style};
        }),
        {name: 'Unique Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'unique').map(({name, value}) => {
          return {name: name, value: value, selected: value === templateObj.watched_style};
        }),
      ], placeholder: 'Global Default',
    });
    // Unwatched style
    $(`#template-id${templateObj.id} >* .dropdown[data-value="unwatched-style"]`).dropdown({
      values: [
        {name: 'Art Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'art').map(({name, value}) => {
          return {name: name, value: value, selected: value === templateObj.unwatched_style};
        }),
        {name: 'Unique Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'unique').map(({name, value}) => {
          return {name: name, value: value, selected: value === templateObj.unwatched_style};
        }),
      ], placeholder: 'Global Default',
    });
    // Hide season text
    initializeNullableBoolean({
      dropdownElement: $(`#template-id${templateObj.id} .dropdown[data-value="hide_season_text"]`),
      value: templateObj.hide_season_text,
    });
    // Add new fields to add title button
    $(`#template-id${templateObj.id} .button[data-value="add-title"]`).on('click', () => {
      const newRange = document.createElement('input');
      newRange.name = 'season_title_ranges'; newRange.type = 'text';
      newRange.setAttribute('data-value', 'season-titles');
      const newTitle = document.createElement('input');
      newTitle.name = 'season_title_values'; newTitle.type = 'text';
      $(`#template-id${templateObj.id} >* .field[data-value="season-title-range"]`).append(newRange);
      $(`#template-id${templateObj.id} >* .field[data-value="season-title-value"]`).append(newTitle);
      $('.field[data-value="season-titles"] label i').popup({
        popup: '#season-title-popup',
        position: 'right center',
      });
    });
    // Hide episode text
    initializeNullableBoolean({
      dropdownElement: $(`#template-id${templateObj.id} .dropdown[data-value="hide_episode_text"]`),
      value: templateObj.hide_episode_text,
    });
    // Episode data source
    $(`#template-id${templateObj.id} >* .dropdown[data-value="episode-data-source"]`).dropdown({
      values: allEpisodeDataSources.map(({name, value}) => {
        return {name: name, value: value, selected: value === templateObj.episode_data_source};
      }), placeholder: 'Global Default',
    });
    // Skip localized images
    initializeNullableBoolean({
      dropdownElement: $(`#template-id${templateObj.id} .dropdown[data-value="skip_localized_images"]`),
      value: templateObj.skip_localized_images,
    });
    // Translations
    if (templateObj.translations !== null && templateObj.translations.length > 0) {
      const translationSegment = $(`#template-id${templateObj.id} [data-value="translations"]`);
      for (const translation of templateObj.translations) {
        // Create new translation entry, add to translation segment
        const newTranslation = document.querySelector('#translation-template').content.cloneNode(true);
        translationSegment.append(newTranslation);
        // Initialize dropdowns
        $(`#template-id${templateObj.id} .dropdown[data-value="language_code"]`).last().dropdown({
          values: [
            {name: 'Language', type: 'header'},
            ...allTranslations.map(({language_code, language}) => {
              return {name: language, value: language_code, selected: translation.language_code === language_code};
            })
          ],
        });
        let extraValue = [];
        if (translation.data_key !== 'preferred_title' && translation.data_key !== 'kanji') {
          extraValue.push({name: translation.data_key, value: translation.data_key, selected: true});
        }
        $(`#template-id${templateObj.id} .dropdown[data-value="data_key"]`).last().dropdown({
          allowAdditions: true,
          values: [
            {name: 'Key', type: 'header'},
            {name: 'Preferred title', text: 'the preferred title', value: 'preferred_title', selected: translation.data_key === 'preferred_title'},
            {name: 'Kanji', text: 'kanji', value: 'kanji', selected: translation.data_key === 'kanji'},
            ...extraValue,
          ]
        });
      }
    }
    // Add new field with add translation button
    $(`#template-id${templateObj.id} .button[data-add-field="translation"]`).on('click', () => {
      const newTranslation = document.querySelector('#translation-template').content.cloneNode(true);
      $(`#template-id${templateObj.id} [data-value="translations"]`).append(newTranslation);
      // Language code dropdown
      $(`#template-id${templateObj.id} .dropdown[data-value="language_code"]`).last().dropdown({
        values: [
          {name: 'Language', type: 'header'},
          ...allTranslations.map(({language_code, language}) => {
            return {name: language, value: language_code};
          })
        ],
      });
      // Translation data key dropdown
      $(`#template-id${templateObj.id} .dropdown[data-value="data_key"]`).last().dropdown({
        allowAdditions: true,
        values: [
          {name: 'Key', type: 'header'},
          {name: 'Preferred title', text: 'the preferred title', value: 'preferred_title'},
          {name: 'Kanji', text: 'kanji', value: 'kanji'},
        ]
      });
    });
    // Add new fields with add extra button
    $(`#template-id${templateObj.id} .button[data-value="add-extra"]`).on('click', () => {
      const newKey = document.createElement('input');
      newKey.name = 'extra_keys'; newKey.type = 'text';
      const newValue = document.createElement('input');
      newValue.name = 'extra_values'; newValue.type = 'text';
      $(`#template-id${templateObj.id} >* .field[data-value="extra-key"]`).append(newKey);
      $(`#template-id${templateObj.id} >* .field[data-value="extra-value"]`).append(newValue);
    });
    
    // Update via API
    $(`#template-id${templateObj.id} >* form`).on('submit', (event) => {
      event.preventDefault();
      // Parse form
      let form = new FormData(event.target);
      let listData = {
        argument: [], operation: [], reference: [],
        extra_keys: [], extra_values: [],
        season_title_ranges: [], season_title_values: [],
        language_code: [], data_key: [],
      };
      for (const [key, value] of [...form.entries()]) {
        if (Object.keys(listData).includes(key)) { listData[key].push(value); }
        // if (value === '') { form.delete(key); }
      }
      // Parse array of Filters
      let filters = [];
      listData.argument.forEach((value, index) => {
        if (value !== '') {
          filters.push({argument: value, operation: listData.operation[index], reference: listData.reference[index]});
        }
      });
      // Parse array of Translations
      let translations = [];
      listData.language_code.forEach((value, index) => {
        if (value !== '') {
          translations.push({language_code: value, data_key: listData.data_key[index]});
        }
      });

      $.ajax({
        type: 'PATCH',
        url: `/api/templates/${templateObj.id}`,
        data: JSON.stringify({
          ...Object.fromEntries(form.entries()),
          ...listData,
          translations: translations,
          filters: filters,
        }),
        contentType: 'application/json',
        success: updatedTemplate => {
          $.toast({
            class: 'blue info',
            title: `Updated Template "${updatedTemplate.name}"`,
          });
        }, error: response => {
          $.toast({
            class: 'error',
            title: 'Error Updating Template',
            message: response.responseJSON.detail,
          });
        }, complete: () => {}
      });
    });
    // Delete via API
    $(`#template-id${templateObj.id} >* button[button-type="delete"]`).on('click', (event) => {
      event.preventDefault();
      showDeleteModal(templateObj.id);
    });
  });

  // Enable accordion/dropdown/checkbox elements
  $('.ui.accordion').accordion();
  $('.field[data-value="season-titles"] label i').popup({
    popup: '#season-title-popup',
    position: 'right center',
  });

  // Refresh theme for any newly added HTML
  refreshTheme();
}

async function initAll() {
  getAllTemplates();

  // Create new (blank) template on button click
  $('#new-template').on('click', () => {
    $.ajax({
      type: 'POST',
      url: '/api/templates/new',
      data: JSON.stringify({name: 'Blank Template'}),
      contentType: 'application/json',
      success: (response) => {
        $.toast({
          class: 'blue info',
          title: `Created Template #${response.id}`,
        });
        getAllTemplates();
      }, error: (response) => {
        $.toast({
          class: 'error',
          title: 'Error Creating Template',
          message: response.responseJSON.detail,
        });
      }
    });
  });
}