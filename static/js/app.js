document.addEventListener('DOMContentLoaded', () => {
  const MOBILE_MAX = 767;
  const isMobile = () => window.matchMedia(`(max-width: ${MOBILE_MAX}px)`).matches;

  const syncMobileThemeColor = () => {
    const metaThemeColor = document.querySelector('#theme-color-meta');
    if (!metaThemeColor) return;

    const bottomNav = document.querySelector('.bottom-nav');
    if (bottomNav && isMobile()) {
      const navBg = window.getComputedStyle(bottomNav).backgroundColor;
      if (navBg) metaThemeColor.setAttribute('content', navBg);
      return;
    }

    const rootColor = window.getComputedStyle(document.documentElement).getPropertyValue('--system-nav-color').trim();
    if (rootColor) metaThemeColor.setAttribute('content', rootColor);
  };

  /**
   * PWA cold-start often reports wrong dvh/svh and safe-area until resume/resize.
   * Drive layout height from visualViewport and measure the real nav height.
   */
  const syncViewportLayout = () => {
    const root = document.documentElement;
    const vv = window.visualViewport;
    const height = Math.round((vv && vv.height) || window.innerHeight || 0);
    if (height > 0) {
      root.style.setProperty('--app-height', `${height}px`);
    }

    const nav = document.querySelector('.bottom-nav');
    const onAgenda = Boolean(document.querySelector('.gcal-page'));
    if (onAgenda && nav && isMobile()) {
      const gapRaw = getComputedStyle(root).getPropertyValue('--gcal-nav-gap').trim();
      const gap = Number.parseFloat(gapRaw) || 12;
      root.style.setProperty('--nav-clearance', `${Math.round(nav.getBoundingClientRect().height + gap)}px`);
    } else {
      root.style.removeProperty('--nav-clearance');
    }
  };

  const scheduleViewportSync = () => {
    syncViewportLayout();
    requestAnimationFrame(() => {
      syncViewportLayout();
      requestAnimationFrame(syncViewportLayout);
    });
  };

  syncMobileThemeColor();
  scheduleViewportSync();
  // iOS standalone often corrects insets only after a short delay on cold launch.
  [50, 150, 400, 1000].forEach((ms) => setTimeout(scheduleViewportSync, ms));

  window.addEventListener('resize', () => {
    syncMobileThemeColor();
    scheduleViewportSync();
  });
  window.addEventListener('orientationchange', scheduleViewportSync);
  window.addEventListener('pageshow', scheduleViewportSync);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) scheduleViewportSync();
  });
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', scheduleViewportSync);
    window.visualViewport.addEventListener('scroll', scheduleViewportSync);
  }

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
