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
      const scrollerContent = Array.from(scrollerInner.children); // Do not use live children

      scrollerContent.forEach(item => {
        const newItem = item.cloneNode(true);
        newItem.setAttribute('aria-hidden', true);
        scrollerInner.appendChild(newItem);
      });
    });
  }

  // Get elements whose src attributes are being changed
  let previewElements = [
    document.getElementById('preview0'),
    document.getElementById('preview1'),
  ]
  if (previewElements.some(element => element === undefined)) { return; }
  // Link of previews to choose from
  let previewLinks = [
    'https://user-images.githubusercontent.com/17693271/185820454-4e3dca1c-c0df-4fa0-a7a7-81e070aa9e69.jpg',
    'https://user-images.githubusercontent.com/17693271/275364823-473521f4-e2e3-4236-a514-49eb186f2872.jpg',
    'https://user-images.githubusercontent.com/17693271/243572310-c5f34e46-ec3b-44a9-a563-b9a24db8cd1a.jpg',
    'https://user-images.githubusercontent.com/17693271/212500535-e88daff6-ecc0-4cc8-8627-82069114c7e0.jpg',
    'https://user-images.githubusercontent.com/17693271/232378485-a9a737dc-9faf-47c2-b639-7df3d3ffb194.jpg',
    'https://user-images.githubusercontent.com/17693271/214648223-b4f68553-e982-4efa-a16b-9662018b5d40.jpg',
    'https://user-images.githubusercontent.com/17693271/202352614-155a176a-fdb0-4476-9f11-6a3a20533a54.jpg',
    'https://user-images.githubusercontent.com/17693271/212500009-067f14ff-4f48-4f75-bacd-7311a9aba716.jpg',
    'https://user-images.githubusercontent.com/17693271/277546845-a8de2b70-5d62-4a14-97cd-3ed365054795.jpg',
    'https://user-images.githubusercontent.com/17693271/180627387-f72bb58e-e001-4608-b4be-82a26263c628.jpg',
    'https://user-images.githubusercontent.com/17693271/203910966-4dde1466-6c7e-4422-923b-1f9222ad49e9.jpg',
    'https://user-images.githubusercontent.com/17693271/212500240-ae946f2c-a5c8-4881-85f2-83ccb45bf46e.jpg',
    'https://user-images.githubusercontent.com/17693271/170836059-136fa6eb-40ef-4cd7-9aca-8ad8e0537239.jpg',
    'https://user-images.githubusercontent.com/17693271/233257029-8b17ce2e-01ea-4ae3-bc73-54e152be4d31.jpg',
    'https://user-images.githubusercontent.com/17693271/213939482-6018b2be-28c5-42dd-988d-d7b9733fe0e8.jpg',
    'https://user-images.githubusercontent.com/17693271/260020601-14f25d6a-4be7-4078-97c2-7730ed070508.jpg',
  ];

  // Choose random preview URLs, update each elements src attribute
  function randomizePreviews() {
    // Get random preview images
    const randomPreviews = [];
    while (randomPreviews.length < previewElements.length) {
      const randomIndex = Math.floor(Math.random() * previewLinks.length);
      if (!randomPreviews.includes(previewLinks[randomIndex])) {
        randomPreviews.push(previewLinks[randomIndex]);
      }
    }

    // Update URLs of preview images
    previewElements.forEach((element, index) => element.src = randomPreviews[index]);
  }

  // Update images on interval
  setInterval(randomizePreviews, 3500);
});