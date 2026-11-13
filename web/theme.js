"use strict";
// This small script runs in <head>, before CSS and the first paint.
(() => {
  const key = "secmd_theme";
  const root = document.documentElement;
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  const normalize = (value) =>
    ["light", "dark", "system"].includes(value) ? value : "light";
  let preference = "light";
  try {
    preference = normalize(localStorage.getItem(key));
  } catch {}

  function apply() {
    const theme =
      preference === "system"
        ? system.matches
          ? "dark"
          : "light"
        : preference;
    root.dataset.theme = theme;
    root.dataset.themePreference = preference;
    root.style.colorScheme = theme;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = theme === "dark" ? "#181818" : "#ffffff";
    const control = document.getElementById("theme-select");
    if (control) control.value = preference;
  }

  window.secmdTheme = Object.freeze({
    get preference() {
      return preference;
    },
    get current() {
      return root.dataset.theme;
    },
    setPreference(value) {
      preference = normalize(value);
      try {
        localStorage.setItem(key, preference);
      } catch {}
      apply();
    },
  });
  apply();
  system.addEventListener("change", () => {
    if (preference === "system") apply();
  });
  window.addEventListener("storage", (event) => {
    if (event.key === key || event.key === null) {
      preference = normalize(event.newValue);
      apply();
    }
  });
  document.addEventListener("DOMContentLoaded", () => {
    const control = document.getElementById("theme-select");
    if (control) {
      control.value = preference;
      control.addEventListener("change", (event) =>
        window.secmdTheme.setPreference(event.target.value),
      );
    }
  });
})();
