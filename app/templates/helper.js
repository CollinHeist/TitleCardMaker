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