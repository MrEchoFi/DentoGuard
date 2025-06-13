
document.addEventListener('DOMContentLoaded', () => {
  const box = document.querySelector('.result-box');
  if (box) {
    box.style.opacity = 0;
    setTimeout(() => {
      box.style.transition = 'opacity 1s';
      box.style.opacity = 1;
    }, 100);
  }
});

