let allCardTypes;
async function getAllCardTypes(showExcluded=false) {
  if (allCardTypes === undefined) {
    allCardTypes = await fetch(`/api/available/card-types?show_excluded=${showExcluded}`).then(resp => resp.json());
  }
}

async function loadCardTypes(args) {
  let {element, isSelected, showExcluded=false, dropdownArgs} = args;
  if (allCardTypes === undefined) {
    // Make API request for all types if not provided
    await getAllCardTypes(showExcluded);
  }

  // Generate lists of local/remote types
  let localTypes = [];
  let remoteTypes = [];
  allCardTypes.forEach(({name, identifier, source, creators}) => {
    const selected = isSelected(identifier);
    if (source === 'local') {
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

  // Initialze dropdown with values
  $(element).dropdown({
    values: [
      {name: 'Built-in Cards', type: 'header'},
      ...localTypes,
      {name: 'Remote Cards', type: 'header'},
      ...remoteTypes,
    ], ...dropdownArgs,
  });

  return allCardTypes;
}
