document$.subscribe(function() {
  if (window.location.pathname !== '/user_guide/fonts/') { return; }
  // Adjust the neighbor paragraph element's letter spacing CSS property
  // with the value of the on-page slider
  const slider = document.getElementById('font-kerning');
  const targetParagraph = document.querySelector('#kerning ~ p');
  if (slider === undefined || targetParagraph === undefined) { return; }

  // Function to update word-spacing based on slider value
  function updateWordSpacing() {
    targetParagraph.style.letterSpacing = slider.value + 'px';
  }

  // Add an event listener to the slider input element
  slider.addEventListener('input', updateWordSpacing);
});