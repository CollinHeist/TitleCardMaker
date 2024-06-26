{% if False %}
import {
  AvailableFont, PreviewTitleCard, SeriesPage, Style, Template, TemplateFilter,
  TemplatePage, Translation
} from './.types.js';
{% endif %}

const allStyles = [
  {name: 'Art', value: 'art', style_type: 'art'},
  {name: 'Blurred Art', value: 'art blur', style_type: 'art'},
  {name: 'Grayscale Art', value: 'art grayscale', style_type: 'art'},
  {name: 'Blurred Grayscale Art', value: 'art blur grayscale', style_type: 'art'},
  {name: 'Unique', value: 'unique', style_type: 'unique'},
  {name: 'Blurred Unique', value: 'blur unique', style_type: 'unique'},
  {name: 'Grayscale Unique', value: 'grayscale unique', style_type: 'unique'},
  {name: 'Blurred Grayscale Unique', value: 'blur grayscale unique', style_type: 'unique'},
];

/**
 * Parse some list value, converting empty lists to the fallback
 * @param {Array} value - List being parsed.
 * @param {*} fallback - Fallback object to return in case `value` is empty.
 * @returns 
 */
const parseList = (value, fallback=[]) => value.length ? value : fallback;

/**
 * Submit an API request to create a new Template. If successful, then all 
 * Templates are reloaded.
 */
function addTemplate() {
  $.ajax({
    type: 'POST',
    url: '/api/templates/new',
    data: JSON.stringify({name: ' Blank Template'}),
    contentType: 'application/json',
    /**
     * Template successfully created, show a Toast and re-query all Templates.
     * @param {Template} template - Newly created Template.
     */
    success: template => {
      showInfoToast(`Created Template #${template.id}`);
      getAllTemplates();
    },
    error: response => showErrorToast({title: 'Error Creating Template', response}),
  });
}

/**
 * Reload the preview image.
 * @param {"watched" | "unwatched"} watchStatus - The type of preview being
 * generated.
 * @param {string} templateElementId - Element ID of the template whose preview
 * is being generated.
 * @param {HTMLElement} cardElement 
 * @param {HTMLElement} imgElement 
 */
function reloadPreview(watchStatus, templateElementId, cardElement, imgElement) {
  /** @type {Style} Effective style */
  const style = watchStatus === 'watched'
    ? $(`#${templateElementId} input[name="watched_style"]`).val() || '{{preferences.default_watched_style}}'
    : $(`#${templateElementId} input[name="unwatched_style"]`).val() || '{{preferences.default_unwatched_style}}'
  ;

  // Generate preview card data
  /** @type {PreviewTitleCard} */
  const previewCard = {
    card_type: $(`#${templateElementId} input[name="card_type"]`).val() || "{{preferences.default_card_type.lower()}}",
    // title_text:
    // season_text: 
    hide_season_text: $(`#${templateElementId} input[name="hide_season_text"]`).val() || false,
    // episode_text: 
    hide_episode_text: $(`#${templateElementId} input[name="hide_episode_text"]`).val() || false,
    episode_text_format: $(`#${templateElementId} input[name="episode_text_format"]`).val() || null,
    blur: style.includes('blur'),
    grayscale: style.includes('grayscale'),
    watched: watchStatus === 'wached',
    style: style,
    font_id: $(`#${templateElementId} input[name="font_id"]`).val() || null,
    extra_keys: parseList(
        $(`#${templateElementId} section[aria-label="extras"] input`).map(function() {
          if ($(this).val() !== '') { 
            return $(this).attr('name'); 
          }
        }).get()
      ),
    extra_values: parseList(
      $(`#${templateElementId} section[aria-label="extras"] input`).map(function() {
          if ($(this).val() !== '') {
            return $(this).val(); 
          }
        }).get(),
      ),
  };

  // Submit API request
  cardElement.classList.add('loading');
  $.ajax({
    type: 'POST',
    url: '/api/cards/preview',
    data: JSON.stringify(previewCard),
    contentType: 'application/json',
    success: imageUrl => imgElement.src = `${imageUrl}?${new Date().getTime()}`,
    error: response =>  showErrorToast({title: 'Error Creating Preview Card', response}),
    complete: () => cardElement.classList.remove('loading'),
  });
}

/**
 * Submit the API requests to delete the Template with the given ID. This also
 * queries and displays a list of the Series associated with this Template.
 * A confirmation modal is shown.
 * @param {number} templateId - ID of the Template being deleted.
 */
function showDeleteModal(templateId) {
  /** @type {string[]} */
  let seriesElements = ['<li><span class="ui text">No associated Series</span></li>'];

  // Get list of Series associated with this Template
  $.ajax({
    type: 'GET',
    url: `/api/series/search?template_id=${templateId}&size=25`,
    /**
     * Series queried successfully, populate list to display in modal.
     * @param {SeriesPage} allSeries - Page of Series associated with the
     * Template being deleted.
     */
    success: allSeries => {
      seriesElements = allSeries.items.map(({name, year}) => `<li>${name} (${year})</li>`);
      if (allSeries.total > 25) {
        seriesElements.push(`<li><span class="ui red text">${allSeries.total-25} more Series...</span></li>`);
      }
    },
    error: response => showErrorToast({title: 'Error Querying Associated Series', response}),
    /** Fill out and display modal to confirm deletion */
    complete: () => {
      // Populate modal with list of Series (or nothing)
      $('#delete-template-modal [data-value="series-list"]')[0].innerHTML = seriesElements.join('');

      // Assign delete API request to button press
      $('#delete-template-modal .button[data-action="delete-template"]').off('click').on('click', () => {
        $.ajax({
          type: 'DELETE',
          url: `/api/templates/${templateId}`,
          success: () => {
            showInfoToast('Deleted Template');
            getAllTemplates(); // TODO delete just this one template element
          },
          error: response => showErrorToast({title: 'Error Deleting Template', response}),
        });
      });
    
      $('#delete-template-modal').modal('show');
    },
  });
}

/**
 * Parse the given Form and submit an API request to patch this Template.
 * @param {number} templateId - ID of the Template being updated.
 */
function updateTemplate(templateId) {
  const data = {
    name: $(`#template-id${templateId} input[name="name"]`).val(),
    filters: parseList(
        Array.from(document.querySelectorAll(`#template-id${templateId} input[name="operation"]`)).map((input, index) => {
          return {
            argument: document.querySelectorAll(`#template-id${templateId} input[name="argument"]`)[index].value,
            operation: input.value,
            reference: document.querySelectorAll(`#template-id${templateId} input[name="reference"]`)[index].value,
          };
        }).filter(({operation}) => operation !== '')
      ),
    card_type: $(`#template-id${templateId} input[name="card_type"]`).val() || null,
    font_id: $(`#template-id${templateId} input[name="font_id"]`).val() || null,
    watched_style: $(`#template-id${templateId} input[name="watched_style"]`).val() || null,
    unwatched_style: $(`#template-id${templateId} input[name="unwatched_style"]`).val() || null,
    hide_season_text: $(`#template-id${templateId} input[name="hide_season_text"]`).val() || null,
    season_title_ranges: parseList(
        Array.from(document.querySelectorAll(`#template-id${templateId} input[name="season_title_ranges"]`)).map(input => input.value),
      ),
    season_title_values: parseList(
        Array.from(document.querySelectorAll(`#template-id${templateId} input[name="season_title_values"]`)).map(input => input.value),
      ),
    hide_episode_text: $(`#template-id${templateId} input[name="hide_episode_text"]`).val() || null,
    episode_text_format: $(`#template-id${templateId} input[name="episode_text_format"]`).val() || null,
    skip_localized_images: $(`#template-id${templateId} input[name="skip_localized_images"]`).val() || null,
    data_source_id: $(`#template-id${templateId} input[name="data_source_id"]`).val() || null,
    sync_specials: $(`#template-id${templateId} input[name="sync_specials"]`).val() || null,
    translations: parseList(
        Array.from(document.querySelectorAll(`#template-id${templateId} input[name="language_code"]`)).map((input, index) => {
          return {
            language_code: input.value,
            data_key: document.querySelectorAll(`#template-id${templateId} input[name="data_key"]`)[index].value,
          };
        }).filter(({data_key}) => data_key !== '')
      ),
    extra_keys: parseList(
        $(`#template-id${templateId} section[aria-label="extras"] input`).map(function() {
          if ($(this).val() !== '') { 
            return $(this).attr('name'); 
          }
        }).get()
      ),
    extra_values: parseList(
        $(`#template-id${templateId} section[aria-label="extras"] input`).map(function() {
          if ($(this).val() !== '') {
            return $(this).val(); 
          }
        }).get(),
      ),
  }

  $.ajax({
    type: 'PATCH',
    url: `/api/templates/${templateId}`,
    data: JSON.stringify(data),
    contentType: 'application/json',
    /**
     * Template updated, display toast.
     * @param {Template} updatedTemplate - New Template
     */
    success: updatedTemplate => showInfoToast(`Updated Template "${updatedTemplate.name}"`),
    error: response => showErrorToast({title: 'Error Updating Template', response}),
  });
}

/**
 * Query all templates, adding their content to the page.
 */
async function getAllTemplates() {
  /** @type {TemplatePage} Query all Templates */
  const allTemplates = await fetch('/api/templates/all').then(resp => resp.json());

  // Create elements to add to the page
  const elements = [],
        hasManyTemplates = allTemplates.items.length > 10;
  let currentHeader = '';
  allTemplates.items.forEach(templateObj => {
    // Add letter header for this Font if necessary
    const letter = templateObj.sort_name[0].toUpperCase();
    if (hasManyTemplates && letter !== currentHeader) {
      const header = document.createElement('h3');
      header.className = 'ui dividing header';
      header.innerText = letter === ' ' ? 'Blank Templates' : letter;
      elements.push(header);
      currentHeader = letter;
    }

    // Clone template
    const base = document.querySelector('#template').content.cloneNode(true);
    const templateElementId = `template-id${templateObj.id}`
    base.querySelector('.accordion').id = templateElementId;
    // Set accordion title and title input
    base.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${templateObj.name}`;
    const nameElem = base.querySelector('input[name="name"]');
    nameElem.placeholder = templateObj.name;
    nameElem.value = templateObj.name;
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
    // Extras later
    // Update card preview(s)
    const watchedCard = base.querySelector('.card[content-type="watched"]'),
        unwatchedCard = base.querySelector('.card[content-type="unwatched"]');
    const watchedImg = base.querySelector('img[content-type="watched"]'),
        unwatchedImg = base.querySelector('img[content-type="unwatched"]');
    base.querySelector('.button[data-action="refresh"]').onclick = () => {
      reloadPreview('watched', templateElementId, watchedCard, watchedImg);
      reloadPreview('unwatched', templateElementId, unwatchedCard, unwatchedImg);
    };
    watchedCard.onclick = () => reloadPreview('watched', templateElementId, watchedCard, watchedImg);
    unwatchedCard.onclick = () => reloadPreview('unwatched', templateElementId, unwatchedCard, unwatchedImg);
    elements.push(base);
  });

  // Add elements to the page, refresh theme, and then initialize accordions
  document.getElementById('templates').replaceChildren(...elements);
  refreshTheme();
  $('.ui.accordion').accordion();

  // Query all "extra" content necessary for dropdowns and such
  /** @type {TemplateFilter} */
  const allFilterOptions = await fetch('/api/available/template-filters').then(resp => resp.json());
  /** @type {AvailableFont[]} */
  const allFonts = await fetch('/api/available/fonts').then(resp => resp.json());
  const allEpisodeDataSources = await fetch('/api/settings/episode-data-source').then(resp => resp.json());
  /** @type {Translation[]} */
  const allTranslations = await fetch('/api/available/translations').then(resp => resp.json());
  await queryAvailableExtras();
  await getAllCardTypes();

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
          $(`#template-id${templateObj.id} input[data-value="filter-reference"]`).last().val(condition.reference);
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
      refreshTheme();
    });
    // Card type
    loadCardTypes({
      element: `#template-id${templateObj.id} .dropdown[data-value="card-types"]`,
      isSelected: (identifier) => identifier === templateObj.card_type,
      dropdownArgs: {
        placeholder: 'Global Default',
      }
    });
    // Font
    $(`#template-id${templateObj.id} .dropdown[data-value="font_id"]`).dropdown({
      placeholder: 'Card Default',
      values: allFonts.map(({id, name}) => {
        return {name: name, value: id, selected: id === templateObj.font_id};
      }),
    });
    // Update/remove link to Font
    if (templateObj.font_id === null) {
      $(`#template-id${templateObj.id} a[data-value="font-link"]`).remove();
    } else {
      $(`#template-id${templateObj.id} a[data-value="font-link"]`)[0].href = `/fonts#font-id${templateObj.font_id}`;
    }
    // Watched style
    $(`#template-id${templateObj.id} .dropdown[data-value="watched_style"]`).dropdown({
      placeholder: 'Global Default',
      values: [
        {name: 'Art Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'art').map(({name, value}) => {
          return {name: name, value: value, selected: value === templateObj.watched_style};
        }),
        {name: 'Unique Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'unique').map(({name, value}) => {
          return {name: name, value: value, selected: value === templateObj.watched_style};
        }),
      ],
    });
    // Unwatched style
    $(`#template-id${templateObj.id} .dropdown[data-value="unwatched_style"]`).dropdown({
      placeholder: 'Global Default',
      values: [
        {name: 'Art Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'art').map(({name, value}) => {
          return {name: name, value: value, selected: value === templateObj.unwatched_style};
        }),
        {name: 'Unique Variations', type: 'header'},
        ...allStyles.filter(({style_type}) => style_type === 'unique').map(({name, value}) => {
          return {name: name, value: value, selected: value === templateObj.unwatched_style};
        }),
      ],
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
    $(`#template-id${templateObj.id} .dropdown[data-value="data_source_id"]`).dropdown({
      placeholder: 'Global Default',
      values: allEpisodeDataSources.map(({name, interface_id}) => {
        return {name, value: interface_id, selected: interface_id === templateObj.data_source_id};
      }),
    });
    // Skip localized images
    initializeNullableBoolean({
      dropdownElement: $(`#template-id${templateObj.id} .dropdown[data-value="skip_localized_images"]`),
      value: templateObj.skip_localized_images,
    });
    // Special syncing
    initializeNullableBoolean({
      dropdownElement: $(`#template-id${templateObj.id} .dropdown[data-value="sync_specials"]`),
      value: templateObj.sync_specials,
    })
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
    // Extras
    initializeExtras(
      templateObj.extras,
      templateObj.card_type || '{{preferences.default_card_type}}',
      `#template-id${templateObj.id} section[aria-label="extras"]`,
      document.getElementById('extra-template'),
    );
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
    
    // Update via API
    $(`#template-id${templateObj.id} form`).on('submit', (event) => {
      event.preventDefault();
      updateTemplate(templateObj.id);
    });
    // Delete via API
    $(`#template-id${templateObj.id} button[button-type="delete"]`).on('click', (event) => {
      event.preventDefault();
      showDeleteModal(templateObj.id);
    });
  });

  // Enable accordion/dropdown/checkbox elements
  $('.ui.accordion').accordion();
  $('.ui.checkbox').checkbox();
  $('.field[data-value="season-titles"] label i').popup({
    popup: '#season-title-popup',
    position: 'right center',
  });

  // Refresh theme for any newly added HTML
  refreshTheme();
}

function initAll() {
  getAllTemplates();
}
