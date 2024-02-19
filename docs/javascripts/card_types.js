document$.subscribe(function() {
  // Only run on card type pages
  if (!window.location.pathname.startsWith('/card_types/')) { return; }
  console.log('Loading ImageCompares..');

  const options = {
    hoverStart: false,
    controlShadow: false,
    addCircle: true,
    addCircleBlur: true,
    showLabels: true,
  };
  const labelOptions = {onHover: true};

  document.querySelectorAll('.image-compare').forEach((element) => {
    console.log(element);
    new ImageCompare(
      element,
      {
        startingPoint: element.dataset?.startingPoint,
        verticalMode: element.dataset?.verticalMode === "true",
        labelOptions: {
          before: element.dataset?.leftLabel,
          after: element.dataset?.rightLabel,
          ...labelOptions,
        },
        ...options,
      }
    ).mount();
  });
});