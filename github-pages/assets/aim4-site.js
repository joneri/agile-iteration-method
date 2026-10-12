"use strict";

// This standalone example explains the lifecycle. It has no project connection.
const exampleStories = {
  retry: {
    id: "US-01", epic: "Customer recovery", title: "Try a failed payment again",
    need: "As a customer, I need to retry a failed payment so that I can complete my purchase without starting over.",
    criteria: ["A retry keeps the existing order and its items.", "A successful retry creates one payment, without a duplicate charge."],
  },
  support: {
    id: "US-02", epic: "Support clarity", title: "Find the payment failure",
    need: "As a support agent, I need to find the failed payment and its outcome so that I can help the customer take the right next step.",
    criteria: ["The agent can find a failure using the order reference.", "The recorded result distinguishes a failed payment from a successful retry."],
  },
  report: {
    id: "US-03", epic: "Support clarity", title: "See the weekly picture",
    need: "As an operator, I need a weekly view of payment failures so that I can spot recurring problems and prioritize improvements.",
    criteria: ["The report groups failures by week and reason.", "Successful retries are shown separately from unresolved failures."],
  },
};

function scenarioForStep(step) {
  const steps = [
    { phase: "backlog", label: "Intent → Stories", next: "Select a delivery →", explanation: "PO identifies the needs and their priority. Choose a Story to inspect its perspective and criteria, then walk through a delivery." },
    { phase: "backlog", label: "Delivery selection", next: "Simulate approved scope →", explanation: "PO and TDO select the customer and support Stories across two Epics. The reporting Story stays in the backlog. Selection alone does not authorize implementation." },
    { phase: "in_progress", label: "Approved scope → implementation", next: "Simulate verified evidence →", explanation: "In this example, Gate A and Gate B approve the scope and plan. Dev builds the selected improvement. Each Story keeps its own criteria." },
    { phase: "acceptance", label: "Verified → awaiting acceptance", next: "Simulate user acceptance →", explanation: "Independent review and TDO validation have checked current evidence for every selected criterion. The delivery is ready for your acceptance; it is not Done yet." },
    { phase: "done", label: "Accepted Stories · open Epics", next: "Example complete", explanation: "You accept the verified delivery. Two Stories are Done; both Epics remain open until their outcomes are proven. The weekly report remains a separate need in the backlog." },
  ];
  const selectedStep = Math.max(0, Math.min(steps.length - 1, step));
  return { ...steps[selectedStep], step: selectedStep, selected: selectedStep > 0 ? ["retry", "support"] : [], complete: selectedStep === steps.length - 1 };
}

function scrollExampleBoard(board, destination, reducedMotion) {
  // Scroll this board only: page position and keyboard focus stay with the user.
  const inset = Number.parseFloat(window.getComputedStyle(board).paddingLeft) || 0;
  const left = board.scrollLeft + destination.getBoundingClientRect().left
    - board.getBoundingClientRect().left - inset;
  board.scrollTo({ left: Math.max(0, left), behavior: reducedMotion ? "instant" : "smooth" });
}

let exampleStep = 0;
let selectedStory = "retry";
const demoCards = Array.from(document.querySelectorAll("[data-story]"));

function renderStoryDetail() {
  const story = exampleStories[selectedStory];
  const scenario = scenarioForStep(exampleStep);
  document.getElementById("detail-id").textContent = `${story.id} · ${story.epic}`;
  document.getElementById("detail-title").textContent = story.title;
  document.getElementById("detail-need").textContent = story.need;
  const criteria = document.getElementById("detail-criteria");
  criteria.replaceChildren();
  story.criteria.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    criteria.append(item);
  });
  document.getElementById("detail-evidence").textContent = !scenario.selected.includes(selectedStory)
    ? "This need remains in the backlog. It has no accepted delivery evidence."
    : exampleStep >= 3
      ? "Illustrative evidence: each criterion passed review and validation. These are example outcomes, not real test results."
      : "Evidence comes from the delivery. A plan alone proves nothing.";
  demoCards.forEach((card) => card.setAttribute("aria-pressed", String(card.dataset.story === selectedStory)));
}

function renderExample() {
  const scenario = scenarioForStep(exampleStep);
  const focused = document.activeElement;
  const previous = new Map(demoCards.map((card) => [card, card.getBoundingClientRect()]));
  demoCards.forEach((card) => {
    const selected = scenario.selected.includes(card.dataset.story);
    const phase = selected ? scenario.phase : "backlog";
    document.getElementById(`demo-${phase}`).append(card);
    card.classList.toggle("is-selected", selected);
    card.classList.toggle("is-accepted", selected && scenario.complete);
    card.querySelector(".card-status").textContent = selected
      ? ["", "Selected · awaiting approval", "Scope approved", "Evidence verified", "Accepted by you"][scenario.step]
      : "View need & criteria ↗";
  });
  document.querySelectorAll("[data-count]").forEach((badge) => {
    badge.textContent = document.getElementById(`demo-${badge.dataset.count}`).children.length;
  });
  document.getElementById("demo-step").textContent = scenario.label;
  document.getElementById("demo-explanation").textContent = scenario.explanation;
  const next = document.getElementById("demo-next");
  next.textContent = scenario.next;
  next.disabled = scenario.complete;
  document.getElementById("demo-reset").disabled = exampleStep === 0;
  renderStoryDetail();
  if (demoCards.includes(focused)) focused.focus({ preventScroll: true });
  if (scenario.complete && focused === next) document.getElementById("demo-reset").focus({ preventScroll: true });
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  scrollExampleBoard(document.querySelector(".demo-board"),
    document.querySelector(`.demo-column[data-column="${scenario.phase}"]`), reducedMotion);
  if (reducedMotion) return;
  window.requestAnimationFrame(() => {
    demoCards.forEach((card) => {
      const before = previous.get(card);
      const after = card.getBoundingClientRect();
      const x = before.left - after.left;
      const y = before.top - after.top;
      if ((x || y) && card.animate) card.animate([{ transform: `translate(${x}px, ${y}px)` }, { transform: "translate(0, 0)" }], { duration: 420, easing: "cubic-bezier(.22,1,.36,1)" });
    });
  });
}

demoCards.forEach((card) => card.addEventListener("click", () => {
  selectedStory = card.dataset.story;
  renderStoryDetail();
}));
document.getElementById("demo-next").addEventListener("click", () => {
  exampleStep = Math.min(4, exampleStep + 1);
  renderExample();
});
document.getElementById("demo-reset").addEventListener("click", () => {
  exampleStep = 0;
  selectedStory = "retry";
  renderExample();
  document.getElementById("demo-next").focus({ preventScroll: true });
});

const installTabs = Array.from(document.querySelectorAll('.install-tabs [role="tab"]'));
function selectInstallTab(selected) {
  installTabs.forEach((tab) => {
    const active = tab === selected;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    document.getElementById(tab.getAttribute("aria-controls")).hidden = !active;
  });
  document.getElementById("hero-copy-feedback").textContent = "";
}
installTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectInstallTab(tab));
  tab.addEventListener("keydown", (event) => {
    const targets = { ArrowRight: (index + 1) % installTabs.length,
      ArrowLeft: (index + installTabs.length - 1) % installTabs.length,
      Home: 0, End: installTabs.length - 1 };
    if (!(event.key in targets)) return;
    event.preventDefault();
    const target = installTabs[targets[event.key]];
    selectInstallTab(target);
    target.focus();
  });
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  let copyAttempt = 0;
  button.addEventListener("click", async () => {
    const attempt = ++copyAttempt;
    const command = document.getElementById(button.dataset.copy);
    const feedback = document.getElementById(button.dataset.feedback || "copy-feedback");
    const destination = button.dataset.destination === "agent" ? "your coding agent’s chat" : "your project’s terminal";
    const stillRelevant = () => attempt === copyAttempt && !button.closest('[role="tabpanel"]')?.hidden;
    try {
      await navigator.clipboard.writeText(command.textContent);
      if (stillRelevant()) feedback.textContent = `Copied. Paste into ${destination}.`;
    } catch (_error) {
      if (!stillRelevant()) return;
      const range = document.createRange();
      range.selectNodeContents(command);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      feedback.textContent = "Text selected. Use your keyboard or browser menu to copy it.";
    }
  });
});
