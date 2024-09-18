/** @type {CardTypeDescription[]} */
let allCardTypes;

/**
 * 
 * @param {boolean} showExcluded Whether to include excluded card types.
 */
async function getAllCardTypes(showExcluded=false) {
  if (allCardTypes === undefined) {
    allCardTypes = await fetch(`/api/available/card-types?show_excluded=${showExcluded}`)
      .then(resp => resp.json());
  }
}

/**
 * Loads and initializes a dropdown menu with card types.
 * @async
 * @function
 * @param {Object} args - The arguments for the function.
 * @param {HTMLElement} args.element - The DOM dropdown element to initialize.
 * @param {Function} args.isSelected - A function that determines if a card type
 * is selected, based on its identifier.
 * @param {boolean} [args.showExcluded=false] - Whether to include excluded card
 * types in the dropdown.
 * @param {Object} args.dropdownArgs - Additional arguments to pass to the
 * dropdown initialization function.
 * @returns {Promise<CardTypeDescription[]>} A promise that resolves to an array
 * of the card type descriptions.
 */
async function loadCardTypes(args) {
  let {element, isSelected, showExcluded=false, dropdownArgs} = args;
  if (allCardTypes === undefined) {
    // Make API request for all types if not provided
    await getAllCardTypes(showExcluded);
  }

  // Generate lists of local/remote types
  let builtinTypes = [],
      localTypes = [],
      remoteTypes = [];
  allCardTypes.forEach(({name, identifier, source, creators}) => {
    const selected = isSelected(identifier);
    if (source === 'builtin') {
      builtinTypes.push({name: name, value: identifier, selected: selected});
    }
    else if (source === 'local') {
      localTypes.push({name: name, value: identifier, selected: selected});
    } else {
      remoteTypes.push({
        name: name,
        value: identifier,
        text: identifier,
        selected: selected,
        description: creators[0],
        descriptionVertical: true,
      });
    }
  });

  // Initialize dropdown with values
  $(element).dropdown({
    values: [
      {name: 'Built-in Cards', type: 'header'},
      ...builtinTypes,
      {name: 'Local Cards', type: 'header'},
      ...localTypes,
      {name: 'Remote Cards', type: 'header'},
      ...remoteTypes,
    ], ...dropdownArgs,
  });

  return allCardTypes;
}
