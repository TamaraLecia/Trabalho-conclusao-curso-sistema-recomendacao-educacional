// ---------------- SLIDER ----------------
document.addEventListener('DOMContentLoaded', function () {
  console.log("✅ script.js carregado!");

  const sliders = document.querySelectorAll('.custom-slider');

  sliders.forEach((slider) => {
    const container = slider.closest('.slider-container');
    const bubble = container.querySelector('.slider-bubble');

    const updateBubble = () => {
      const value = slider.value;
      bubble.textContent = value;

      const percent = (value - slider.min) / (slider.max - slider.min);
      const sliderWidth = slider.offsetWidth;
      const thumbOffset = percent * sliderWidth;

      bubble.style.left = `${thumbOffset}px`;
    };

    slider.addEventListener('mousedown', () => container.classList.add('active'));
    slider.addEventListener('mouseup', () => container.classList.remove('active'));
    slider.addEventListener('touchstart', () => container.classList.add('active'));
    slider.addEventListener('touchend', () => container.classList.remove('active'));

    slider.addEventListener('input', updateBubble);
    window.addEventListener('resize', updateBubble);

    updateBubble(); // inicializa
  });
});
