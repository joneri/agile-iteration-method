"use strict";

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
