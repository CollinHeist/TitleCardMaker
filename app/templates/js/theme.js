function refreshTheme() {
  const siteTheme = window.localStorage.getItem('site-theme') || 'dark';
  const inverted = (siteTheme === 'dark');
  $('#main-content .ui:not(.uninvertible)').toggleClass('inverted', inverted);
  $('.modal:not(.basic):not(.uninvertible), .modal:not(.basic):not(.uninvertible) .ui, .accordion, .accordion .ui').toggleClass('inverted', inverted);
}

function toggleTheme() {
  const currentIcons = $('#theme-toggle i');
  if (currentIcons.length === 0 ) { return; }
  // Toggle inverted class modifier, update button sun <-> moon, and set background color
  // Light -> Dark
  if (currentIcons[0].classList.contains('sun')) {
    currentIcons[0].className = 'moon outline icon';
    currentIcons[1].className = 'sun outline icon';
    $('body')[0].style.setProperty('background-image', 'linear-gradient(to bottom right, var(--background-color-dark), #313131)');
    window.localStorage.setItem('site-theme', 'dark');
  // Dark -> light
  } else {
    currentIcons[1].className = 'moon outline icon';
    currentIcons[0].className = 'sun outline icon';
    $('body')[0].style.setProperty('background-image', 'linear-gradient(to bottom right, var(--background-color-light), #d9d9d9)');
    window.localStorage.setItem('site-theme', 'light');
  }
  refreshTheme();
}

// Default theme is LIGHT, so if dark is indicated, toggle
$(document).ready(() => {
  const siteTheme = window.localStorage.getItem('site-theme') || 'dark';
  if (siteTheme === 'dark') { toggleTheme(); }
});