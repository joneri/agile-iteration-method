"use strict";

const installTabs = Array.from(document.querySelectorAll('.install-tabs [role="tab"]'));
const feedback = document.getElementById("copy-feedback");
// New copy requests supersede older ones; install tab changes affect only install feedback.
let copyRevision = 0;
let installTabRevision = 0;

function selectInstallTab(selected) {
  installTabRevision += 1;
  installTabs.forEach((tab) => {
    const active = tab === selected;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    document.getElementById(tab.getAttribute("aria-controls")).hidden = !active;
  });
  feedback.textContent = "";
}

installTabs.forEach((tab, index) => {
  const panel = document.getElementById(tab.getAttribute("aria-controls"));
  panel.setAttribute("role", "tabpanel");
  panel.tabIndex = 0;
  tab.addEventListener("click", () => selectInstallTab(tab));
  tab.addEventListener("keydown", (event) => {
    const targets = {
      ArrowRight: (index + 1) % installTabs.length,
      ArrowLeft: (index + installTabs.length - 1) % installTabs.length,
      Home: 0,
      End: installTabs.length - 1,
    };
    if (!(event.key in targets)) return;
    event.preventDefault();
    const target = installTabs[targets[event.key]];
    selectInstallTab(target);
    target.focus();
  });
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.hidden = false;
  button.addEventListener("click", async () => {
    const revision = ++copyRevision;
    const command = document.getElementById(button.dataset.copy);
    const currentFeedback = document.getElementById(button.dataset.feedback || "copy-feedback");
    const tabRevision = installTabRevision;
    const isCurrent = () => revision === copyRevision
      && (currentFeedback !== feedback || tabRevision === installTabRevision);
    const destination = button.dataset.destination === "agent"
      ? "your coding agent’s chat" : "your project’s terminal";
    currentFeedback.textContent = "";
    try {
      await navigator.clipboard.writeText(command.textContent);
      if (isCurrent()) {
        currentFeedback.textContent = `Copied. Paste into ${destination}.`;
      }
    } catch (_error) {
      if (!isCurrent()) return;
      const range = document.createRange();
      range.selectNodeContents(command);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      currentFeedback.textContent = "Text selected. Use your keyboard or browser menu to copy it.";
    }
  });
});

document.querySelector(".install-panel").classList.add("is-enhanced");
document.querySelector(".install-tabs").hidden = false;
selectInstallTab(installTabs[0]);
