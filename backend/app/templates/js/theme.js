/*
 * Refresh the theme of all HTML elements on the page. This sets the inverted
 * CSS class of all elements under the main-content ID; as well as modals.
 * Uninvertible conntent is excluded.
 */
function refreshTheme() {
  const siteTheme = window.localStorage.getItem('site-theme') || 'dark';
  const inverted = (siteTheme === 'dark');
  $('#main-content .ui:not(.uninvertible)').toggleClass('inverted', inverted);
  $('.modal:not(.basic):not(.uninvertible), .modal:not(.basic):not(.uninvertible) >* .ui:not(.uninvertible), .accordion:not(.uninvertible), .accordion:not(.uninvertible) >* .ui:not(.uninvertible)').toggleClass('inverted', inverted);
  if (inverted) {
    // $('body')[0].style.setProperty('background-image', 'linear-gradient(to bottom right, var(--background-color-dark), #313131)');
    $('body')[0].style.setProperty('background-image', 'linear-gradient(to bottom right, rgb(29,29,29), rgb(40,40,40))');
    document.querySelector('body').classList.add('dark');
  } else {
    $('body')[0].style.setProperty('background-image', 'linear-gradient(to bottom right, var(--background-color-light), #d9d9d9)');
    document.querySelector('body').classList.remove('dark');
  }
}

/*
 * Toggle the current theme from light -> dark or dark -> light. This changes 
 * the theme icon, updates the theme local storage variable, and refreshes all
 * HTML.
 */
function toggleTheme() {
  const currentTheme = window.localStorage.getItem('site-theme') || 'dark';
  const currentIcons = $('#theme-toggle i');
  // Light -> Dark
  if (currentTheme === 'light') {
    currentIcons[0].className = 'moon outline icon';
    currentIcons[1].className = 'sun outline icon';
    window.localStorage.setItem('site-theme', 'dark');
  // Dark -> light
  } else {
    currentIcons[1].className = 'moon outline icon';
    currentIcons[0].className = 'sun outline icon';
    window.localStorage.setItem('site-theme', 'light');
  }
  refreshTheme();
}

$(document).ready(() => {
  // Refresh theme
  refreshTheme();
  // Highlight side bar icon of current page
  $(`#nav-menu a[href="${location.pathname}"]`).toggleClass('highlighted', true);
});