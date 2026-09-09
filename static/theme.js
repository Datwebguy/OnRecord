(() => {
  const root = document.documentElement;
  const stored = localStorage.getItem("onrecord-theme");
  root.dataset.theme = stored || "light";

  function syncThemeControls() {
    const isDark = root.dataset.theme === "dark";
    document.querySelectorAll("[data-theme-logo]").forEach((logo) => {
      logo.src = isDark ? logo.dataset.darkLogo : logo.dataset.lightLogo;
    });
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.setAttribute("aria-pressed", String(isDark));
      button.innerHTML = isDark
        ? '<span class="theme-dot theme-dot-dark"></span> Light mode'
        : '<span class="theme-dot theme-dot-light"></span> Dark mode';
    });
  }

  window.toggleOnRecordTheme = () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("onrecord-theme", root.dataset.theme);
    syncThemeControls();
    window.dispatchEvent(new CustomEvent("onrecord:theme", { detail: root.dataset.theme }));
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", window.toggleOnRecordTheme);
    });
    syncThemeControls();
  });
})();
