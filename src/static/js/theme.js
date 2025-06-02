// static/js/theme.js
(function() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else if (savedTheme === 'light') {
    document.documentElement.removeAttribute('data-theme');
  } else {
    // Use system preference; don't set data-theme, let CSS handle it
  }
})();