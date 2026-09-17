document.addEventListener('DOMContentLoaded', () => {
  // Auto-hide flash messages
  document.querySelectorAll('.message').forEach((el) => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity .4s';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // Register service worker (PWA)
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }
});
