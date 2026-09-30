document.addEventListener('DOMContentLoaded', () => {
  const syncMobileThemeColor = () => {
    const metaThemeColor = document.querySelector('#theme-color-meta');
    if (!metaThemeColor) return;

    const bottomNav = document.querySelector('.bottom-nav');
    if (bottomNav && window.matchMedia('(max-width: 767px)').matches) {
      const navBg = window.getComputedStyle(bottomNav).backgroundColor;
      if (navBg) metaThemeColor.setAttribute('content', navBg);
      return;
    }

    const rootColor = window.getComputedStyle(document.documentElement).getPropertyValue('--system-nav-color').trim();
    if (rootColor) metaThemeColor.setAttribute('content', rootColor);
  };

  syncMobileThemeColor();
  window.addEventListener('resize', syncMobileThemeColor);

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
