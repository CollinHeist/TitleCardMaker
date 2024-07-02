document$.subscribe(function() {
  // Exit if not on home page
  if (window.location.pathname !== '/') { return; }

  // Update scroller marquees
  const scrollers = document.querySelectorAll('.scroller');
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    // Scrolling disabled, delete all but the first image (first two for theme-specific imaging)
    scrollers.forEach(scroller => {
      const images = Array.from(scroller.querySelectorAll('.scroller__inner > *'));
      for (let i = 2; i < images.length; i++) {
        images[i].remove();
      }
    });
  } else {
    scrollers.forEach(scroller => {
      // If clones are present, skip (this function can be triggered >1 times as SPA)
      if (scroller.querySelector('[aria-hidden=true]')) { return; }

      // Enable animation attribute
      scroller.setAttribute('data-animated', true);

      const scrollerInner = scroller.querySelector('.scroller__inner');

      // Randomize order of images if it is randomized
      if (scroller.classList.contains('randomized')) {
        for (let i = scrollerInner.children.length; i >= 0; i--) {
          scrollerInner.appendChild(scrollerInner.children[Math.random() * i | 0]);
        }
      }

      const scrollerContent = Array.from(scrollerInner.children); // Do not use live children

      scrollerContent.forEach(item => {
        const newItem = item.cloneNode(true);
        newItem.setAttribute('aria-hidden', true);
        scrollerInner.appendChild(newItem);
      });
    });
  }
});