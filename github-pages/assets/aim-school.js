"use strict";

const preparation = document.querySelector("[data-preparation]");
if (preparation) {
  const tabList = preparation.querySelector("[data-preparation-tabs]");
  const tabs = [...preparation.querySelectorAll("[data-preparation-tab]")];
  const panels = [...preparation.querySelectorAll("[data-preparation-panel]")];
  const activate = (id, { focus = false, remember = false } = {}) => {
    const selected = tabs.find((tab) => tab.dataset.preparationTab === id);
    if (!selected) return;
    for (const tab of tabs) {
      const active = tab === selected;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
    }
    for (const panel of panels) panel.hidden = panel.id !== id;
    if (focus) selected.focus();
    if (remember) history.replaceState(null, "", `#${id}`);
  };
  const followHash = () => {
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
    catch (_error) { return; }
    const panel = target?.closest("[data-preparation-panel]");
    if (!panel) return;
    activate(panel.id);
    // Hash links can point into a panel that was hidden when navigation began.
    requestAnimationFrame(() => target.scrollIntoView({ block: "start" }));
  };

  tabList.setAttribute("role", "tablist");
  for (const tab of tabs) {
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-controls", tab.dataset.preparationTab);
    tab.addEventListener("click", () => activate(tab.dataset.preparationTab, { remember: true }));
    tab.addEventListener("keydown", (event) => {
      const index = tabs.indexOf(tab);
      const next = { ArrowRight: (index + 1) % tabs.length,
        ArrowLeft: (index + tabs.length - 1) % tabs.length,
        Home: 0, End: tabs.length - 1 }[event.key];
      if (next === undefined) return;
      event.preventDefault();
      activate(tabs[next].dataset.preparationTab, { focus: true, remember: true });
    });
  }
  for (const panel of panels) {
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", `${panel.id}-tab`);
    panel.tabIndex = 0;
  }
  preparation.dataset.preparationReady = "true";
  tabList.hidden = false;
  preparation.querySelector("[data-preparation-scroll-hint]").hidden = false;
  activate("new-project");
  followHash();
  window.addEventListener("hashchange", followHash);
}

document.querySelectorAll("[data-school-copy]").forEach((button) => {
  const source = document.getElementById(button.dataset.schoolCopy);
  const status = button.parentElement.querySelector(".school-copy-status");
  if (!source || !status) return;
  let revision = 0;
  button.hidden = false;
  button.addEventListener("click", async () => {
    const current = ++revision;
    status.textContent = "";
    try {
      await navigator.clipboard.writeText(source.textContent);
      if (current !== revision) return;
      const destination = button.dataset.copyTarget === "terminal"
        ? "your project’s terminal" : "your coding agent’s chat";
      status.textContent = `Copied. Paste into ${destination}.`;
    } catch (_error) {
      if (current !== revision) return;
      const range = document.createRange();
      range.selectNodeContents(source);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = "Text selected. Use your keyboard or browser menu to copy it.";
    }
  });
});
