document.addEventListener("DOMContentLoaded", () => {
  const words = document.querySelectorAll(".word");
  const plane = document.querySelector(".plane");

  window.addEventListener("scroll", () => {
    const scrollY = window.scrollY;

    const textTriggerStart = window.innerHeight * 0.5;
    const textTriggerEnd = window.innerHeight * 2;

    const textScrollProgress = Math.min(
      Math.max(
        (scrollY - textTriggerStart) / (textTriggerEnd - textTriggerStart),
        0
      ),
      1
    );

    const wordsToShow = Math.floor(textScrollProgress * words.length);
    words.forEach((word, index) => {
      word.style.color = index < wordsToShow ? "white" : "#666";
    });

    const planeTriggerStart = window.innerHeight * 0;
    const planeTriggerEnd = window.innerHeight * 0.5;

    const planeScrollProgress = Math.min(
      Math.max(
        (scrollY - planeTriggerStart) / (planeTriggerEnd - planeTriggerStart),
        0
      ),
      1
    );

    if (plane) {
      const translateY = -planeScrollProgress * 100;
      const translateX = planeScrollProgress * window.innerWidth;
      plane.style.transform = `translate(${translateX}px, ${translateY}px) rotate(-10deg)`;
    }
  });
});
