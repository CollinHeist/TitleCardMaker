const createLogMessage = () => {
  const elem = document.createElement('div');
  elem.id = '__current_log';
  elem.onclick = () => elem.remove();
  document.querySelector('body').appendChild(elem);
  return elem;
}

const addMessage = (message) => {
  // Either replace currently displayed message or create a new one
  document.getElementById('__current_log')?.remove();
  const info = createLogMessage();
  info.innerHTML = message;

  // Remove message after 5 seconds
  setTimeout(() => {
    info.innerHTML = '<i class="exclamation circle icon"></i>';
    info.addEventListener('mouseover', () => {
      info.innerHTML = message;
    })
    info.addEventListener('mouseout', () => {
      info.innerHTML = '<i class="exclamation circle icon"></i>';
    });
  }, 5000);
};