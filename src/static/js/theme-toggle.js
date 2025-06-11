// static/js/theme-toggle.js

document.addEventListener('DOMContentLoaded', function () {
  const toggleButton = document.getElementById('theme-toggle');
  if (!toggleButton) return;  // No toggle button present, nothing to do

  // Helper: update the DOM and localStorage
  function applyTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }
  }

  // Toggle behaviour
  toggleButton.addEventListener('click', function () {
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') {
      applyTheme('light');
    } else {
      applyTheme('dark');
    }
  });
});
