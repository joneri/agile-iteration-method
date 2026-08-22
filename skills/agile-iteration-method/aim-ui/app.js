/*
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: aim-ui/app.js
*/
"use strict";

const state = {
  board: null,
  boardSignature: null,
  timer: null,
  filter: "all",
  view: "board",
  pendingAction: null,
};
const epicAccents = ["#20b9ec", "#f6ad22", "#9c7cf4", "#83ca31", "#f17891", "#57c9aa"];
const $ = (id) => document.getElementById(id);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function formatTime(value) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return String(value);
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(date);
}

function statusLabel(value) {
  return String(value || "unknown").replaceAll("_", " ");
}

function addFact(list, label, value) {
  const group = el("div");
  const displayValue = value === undefined || value === null || value === "" ? "—" : value;
  group.append(el("dt", "", label), el("dd", "", displayValue));
  list.append(group);
}

function accentFor(index) {
  return epicAccents[index % epicAccents.length];
}

function semanticBoardSignature(board) {
  const { generatedAt: _generatedAt, ...semanticBoard } = board;
  return JSON.stringify(semanticBoard);
}

function cardKey(epicId, incrementId) {
  return `${epicId}:${incrementId}`;
}

function captureFocus() {
  const active = document.activeElement;
  if (!active || active === document.body) return null;
  if (active.id) return { kind: "id", value: active.id };
  if (active.dataset.view) return { kind: "view", value: active.dataset.view };
  if (active.dataset.epic) return { kind: "epic", value: active.dataset.epic };
  const card = active.closest?.("[data-card-key]");
  if (card && active.dataset.actionKind) {
    return {
      kind: "card-action",
      cardKey: card.dataset.cardKey,
      actionKind: active.dataset.actionKind,
      actionIndex: active.dataset.actionIndex,
    };
  }
  return null;
}

function restoreFocus(token) {
  if (!token || document.activeElement !== document.body) return;
  let target = null;
  if (token.kind === "id") target = $(token.value);
  if (token.kind === "view") {
    target = Array.from(document.querySelectorAll("[data-view]")).find(
      (item) => item.dataset.view === token.value,
    );
  }
  if (token.kind === "epic") {
    target = Array.from(document.querySelectorAll("[data-epic]")).find(
      (item) => item.dataset.epic === token.value,
    );
  }
  if (token.kind === "card-action") {
    target = Array.from(document.querySelectorAll("[data-card-key] .card-action")).find(
      (item) => item.closest("[data-card-key]")?.dataset.cardKey === token.cardKey
        && item.dataset.actionKind === token.actionKind
        && item.dataset.actionIndex === token.actionIndex,
    );
  }
  target?.focus();
}

function setConnection(kind, label) {
  const connection = $("connection-label").parentElement;
  connection.classList.toggle("is-live", kind === "live");
  connection.classList.toggle("is-error", kind === "error");
  $("connection-label").textContent = label;
}

function renderEpicRoster(board) {
  const roster = $("epic-roster");
  roster.replaceChildren();
  board.epics.forEach((epic, index) => {
    const card = $("epic-template").content.firstElementChild.cloneNode(true);
    const accent = accentFor(index);
    card.style.setProperty("--epic-accent", accent);
    card.classList.toggle("is-complete", epic.lifecycle === "closed");
    card.classList.toggle("is-planned", epic.lifecycle === "planned");
    card.classList.toggle("is-focused", epic.focused === true);
    card.querySelector(".epic-index").textContent = String(index + 1).padStart(2, "0");
    card.querySelector(".epic-state").textContent = statusLabel(epic.runtimeStatus);
    card.querySelector(".epic-title").textContent = epic.title;
    card.querySelector(".epic-id").textContent = epic.id;
    const facts = card.querySelector(".epic-facts");
    addFact(facts, "Role", epic.currentRole || "Not active");
    addFact(facts, "Gate", epic.lastGatePassed || "Not passed");
    addFact(facts, "Mode", epic.mode);
    addFact(facts, "Increments", epic.increments.length);
    addFact(facts, "Focus", epic.focused ? "Operator focus" : "—");
    roster.append(card);
  });
}

function renderPortfolioControl(board) {
  const control = board.control || {};
  const maximum = control.maxActiveEpics;
  const running = control.runningEpics || 0;
  const focused = board.epics.find((epic) => epic.id === control.focusedEpicId);
  const summary = $("portfolio-control-summary");
  const facts = $("portfolio-control-facts");
  const status = $("portfolio-control-status");
  const guidance = $("portfolio-control-guidance");
  facts.replaceChildren();

  if (!control.valid) {
    summary.textContent = "Portfolio admission is blocked until the chat-owned control state is repaired.";
  } else if (!control.configured) {
    summary.textContent = "No explicit capacity policy is configured; legacy activation behavior is preserved.";
  } else {
    summary.textContent = `${running} of ${maximum} concurrent Epic slots are in use.`;
  }

  addFact(facts, "Capacity", maximum ?? "Not set");
  addFact(facts, "Running", running);
  addFact(facts, "Available", control.availableSlots ?? "Unbounded");
  addFact(facts, "Focused Epic", focused?.title || control.focusedEpicId || "None");

  status.dataset.status = control.admission || "unbounded";
  status.textContent = statusLabel(control.admission || "unbounded");
  if (control.admission === "blocked") {
    guidance.textContent = "Repair portfolio-control.json from the authoritative AIM chat before activation.";
  } else if (control.admission === "over_capacity") {
    guidance.textContent = "No Epic was paused automatically. Finish or pause one, or explicitly raise capacity in chat.";
  } else if (control.admission === "full") {
    guidance.textContent = "Capacity is full. Finish or pause an Epic, or explicitly raise the limit in chat.";
  } else if (control.admission === "open") {
    guidance.textContent = "Another planned Increment may be activated from the AIM chat.";
  } else {
    guidance.textContent = "Set a capacity in the AIM chat when you want explicit admission control.";
  }
}

function renderPortfolioRun(board) {
  const run = board.portfolioRun || {};
  const panel = $("portfolio-run-panel");
  panel.hidden = !run.configured || state.view !== "portfolio";
  if (!run.configured) return;
  const summary = $("portfolio-run-summary");
  const facts = $("portfolio-run-facts");
  const status = $("portfolio-run-status");
  const guidance = $("portfolio-run-guidance");
  facts.replaceChildren();
  summary.textContent = run.valid
    ? `${run.completed} of ${run.total} Backlog cards completed under ${run.mandateId}.`
    : "Portfolio Auto is paused because its chat-owned run contract is invalid.";
  addFact(facts, "Portfolio", run.runId || "Invalid");
  addFact(facts, "Current card", run.activeCandidateId || "None");
  addFact(facts, "Remaining", run.remaining ?? "Unknown");
  addFact(facts, "Decision", run.decisionAuthority === "portfolio_mandate" ? "Portfolio mandate" : run.decisionAuthority || "None");
  status.dataset.status = run.status || "invalid";
  status.textContent = statusLabel(run.status || "invalid");
  if (!run.valid) guidance.textContent = run.issue || "Repair the run contract in AIM chat.";
  else if (run.status === "paused") guidance.textContent = run.pauseReason;
  else if (run.status === "completed") guidance.textContent = "The approved snapshot is complete.";
  else if (run.status === "stopped") guidance.textContent = run.pauseReason || "The Portfolio was stopped in AIM chat.";
  else guidance.textContent = run.activeCandidateId
    ? `${run.gate || "AIM"} is the durable checkpoint. Auto decisions cite the Portfolio mandate.`
    : "AIM chat may activate the next queued card.";
}

function renderRoles(epic, lane) {
  lane.replaceChildren();
  epic.canonicalRoles.forEach((role) => {
    const chip = $("role-template").content.firstElementChild.cloneNode(true);
    chip.classList.toggle("is-active", role.active);
    chip.querySelector(".role-name").textContent = role.name;
    if (role.active) chip.setAttribute("aria-current", "true");
    lane.append(chip);
  });
}

function renderHelpers(epic, lane) {
  lane.replaceChildren();
  const activity = epic.helperActivity;
  if (!activity.available || activity.items.length === 0) {
    lane.append(el("p", "helper-empty", activity.message || "No helper agents are active."));
    return;
  }
  activity.items.forEach((agent) => {
    const card = $("helper-template").content.firstElementChild.cloneNode(true);
    card.querySelector(".helper-id").textContent = agent.id;
    const status = card.querySelector(".status-pill");
    status.textContent = agent.status;
    status.dataset.status = agent.status;
    card.querySelector(".helper-task").textContent = agent.task;
    const relationship = [agent.canonicalRole, agent.incrementId].filter(Boolean).join(" · ");
    card.querySelector(".helper-link").textContent = relationship || "Scoped helper activity";
    lane.append(card);
  });
  if (activity.message) lane.append(el("p", "helper-empty", activity.message));
}

function renderPeople(epics, board) {
  const grid = $("people-grid");
  grid.replaceChildren();
  epics.forEach((epic) => {
    const index = board.epics.findIndex((item) => item.id === epic.id);
    const panel = $("people-template").content.firstElementChild.cloneNode(true);
    panel.style.setProperty("--epic-accent", accentFor(index));
    panel.querySelector(".people-epic-id").textContent = epic.id;
    panel.querySelector(".people-epic-title").textContent = epic.title;
    renderRoles(epic, panel.querySelector(".role-lane"));
    renderHelpers(epic, panel.querySelector(".helper-lane"));
    grid.append(panel);
  });
}

function actionEnvelope() {
  if (!state.pendingAction) return null;
  const envelope = { ...state.pendingAction.envelope };
  if (envelope.action === "change") {
    envelope.changeRequest = $("change-request").value.trim();
  }
  return envelope;
}

function actionPrompt(envelope) {
  const ordered = Object.fromEntries(Object.keys(envelope).sort().map((key) => [key, envelope[key]]));
  const preamble = state.board?.handoff?.promptPreamble ||
    "Process this user-initiated AIM UI action with $agile-iteration-method. Revalidate every expected field before writing.";
  return `${preamble}\n\nAIM_ACTION_ENVELOPE\n${JSON.stringify(ordered, null, 2)}`;
}

function updateActionPreview() {
  const envelope = actionEnvelope();
  if (!envelope) return;
  $("action-intent").textContent = actionPrompt(envelope);
  const missingChange = envelope.action === "change" && !envelope.changeRequest;
  $("open-action").disabled = missingChange;
  $("copy-action").disabled = missingChange;
}

function openActionDialog(action) {
  state.pendingAction = action;
  $("action-dialog-title").textContent = `${action.label} with AIM`;
  const target = action.envelope.candidateId || action.envelope.incrementId || action.envelope.epicId;
  $("action-target").textContent = `${target} · ${action.envelope.gate || "portfolio admission"}`;
  const needsInput = action.kind === "change";
  $("change-field").hidden = !needsInput;
  $("change-request").value = "";
  $("action-feedback").textContent = "";
  updateActionPreview();
  $("action-dialog").showModal();
  if (needsInput) $("change-request").focus();
  else $("open-action").focus();
}

async function copyActionIntent() {
  const envelope = actionEnvelope();
  if (!envelope) return;
  const prompt = actionPrompt(envelope);
  try {
    await navigator.clipboard.writeText(prompt);
    $("action-feedback").textContent = "Intent copied. Paste it into an AIM chat and send.";
  } catch (_error) {
    $("action-intent").focus();
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents($("action-intent"));
    selection.removeAllRanges();
    selection.addRange(range);
    $("action-feedback").textContent = "Clipboard access is unavailable. The intent is selected for copying.";
  }
}

function openActionInCodex() {
  const envelope = actionEnvelope();
  if (!envelope || (envelope.action === "change" && !envelope.changeRequest)) return;
  const query = new URLSearchParams({
    prompt: actionPrompt(envelope),
    path: state.board.handoff.workspacePath,
  });
  window.location.href = `codex://new?${query.toString()}`;
  $("action-feedback").textContent = "Codex handoff opened. Review the prefilled intent and press Send.";
}

function renderCard(increment, epic, index, existingCard = null) {
  const card = existingCard || $("card-template").content.firstElementChild.cloneNode(true);
  const key = cardKey(epic.id, increment.id);
  const renderSignature = JSON.stringify([increment, epic.id, epic.title, index]);
  card.dataset.cardKey = key;
  if (card.aimRenderSignature === renderSignature) return card;
  card.aimRenderSignature = renderSignature;
  card.style.setProperty("--epic-accent", accentFor(index));
  card.classList.toggle("is-active", increment.active);
  card.classList.toggle("is-planned", increment.planned);
  card.querySelector(".increment-id").textContent = increment.planned
    ? `P${String(increment.priority).padStart(2, "0")} · ${increment.id}`
    : increment.id;
  card.querySelector(".owner-badge").textContent = increment.canonicalOwner;
  card.querySelector(".increment-title").textContent = increment.title;
  card.querySelector(".epic-link").textContent = `Epic ${String(index + 1).padStart(2, "0")} · ${increment.epicId}`;
  const summary = card.querySelector(".increment-summary");
  summary.hidden = true;
  summary.textContent = "";
  if (increment.summary) {
    summary.hidden = false;
    summary.textContent = increment.summary;
  }
  const facts = card.querySelector(".card-facts");
  facts.replaceChildren();
  if (increment.planned) {
    addFact(facts, "Priority", increment.priority);
    addFact(facts, "Status", "Candidate");
  } else {
    addFact(facts, "Gate", increment.gate);
    addFact(facts, "Mode", increment.mode);
    addFact(facts, "Cost", increment.costProfile);
    addFact(facts, "State", statusLabel(increment.runtimeStatus));
  }
  if (increment.portfolioState) {
    addFact(facts, "Portfolio", statusLabel(increment.portfolioState));
  }
  if (increment.decisionAuthority === "portfolio_mandate") {
    addFact(facts, "Approval", "Portfolio mandate");
  }
  const attention = card.querySelector(".attention");
  attention.hidden = true;
  attention.textContent = "";
  if (increment.attention) {
    attention.hidden = false;
    attention.textContent = increment.attention;
  }
  const links = card.querySelector(".evidence-links");
  links.replaceChildren();
  increment.evidence.forEach((item) => {
    const link = el("a", "", item.label);
    link.href = `/api/evidence?path=${encodeURIComponent(item.path)}`;
    link.target = "_blank";
    link.rel = "noopener";
    links.append(link);
  });
  if (increment.evidence.length === 0) {
    links.append(el("span", "", increment.planned ? "Planned in AIM chat" : "No evidence linked"));
  }
  const control = card.querySelector(".card-control");
  const actions = card.querySelector(".card-actions");
  const unavailable = card.querySelector(".action-unavailable");
  actions.replaceChildren();
  unavailable.hidden = true;
  unavailable.textContent = "";
  const reason = (increment.actions || []).find(
    (action) => !action.enabled && action.reason,
  )?.reason;
  const reasonId = `action-reason-${key.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
  unavailable.id = reasonId;
  (increment.actions || []).forEach((action, actionIndex) => {
    const button = el("button", `card-action action-${action.kind}`, action.label);
    button.type = "button";
    button.dataset.actionKind = action.kind;
    button.dataset.actionIndex = String(actionIndex);
    button.disabled = !action.enabled;
    if (action.reason) button.title = action.reason;
    if (!action.enabled && action.reason) button.setAttribute("aria-describedby", reasonId);
    if (action.enabled) button.addEventListener("click", () => openActionDialog(action));
    actions.append(button);
  });
  if (reason) {
    unavailable.hidden = false;
    unavailable.textContent = reason;
  }
  control.hidden = actions.childElementCount === 0 && !reason;
  return card;
}

function visibleEpics(board) {
  if (state.filter === "all") return board.epics;
  return board.epics.filter((epic) => epic.id === state.filter);
}

function renderFilters(board) {
  const filters = $("epic-filters");
  filters.replaceChildren();
  const choices = [{ id: "all", label: "All Epics" }].concat(
    board.epics.map((epic, index) => ({
      id: epic.id,
      label: `${String(index + 1).padStart(2, "0")} · ${epic.title}`,
      accent: accentFor(index),
    })),
  );
  choices.forEach((choice) => {
    const button = el("button", "epic-filter", choice.label);
    button.type = "button";
    button.dataset.epic = choice.id;
    button.setAttribute("aria-pressed", String(state.filter === choice.id));
    if (choice.accent) button.style.setProperty("--epic-accent", choice.accent);
    button.addEventListener("click", () => {
      state.filter = choice.id;
      render(state.board);
    });
    filters.append(button);
  });
}

function renderKanban(board, epics) {
  const kanban = $("kanban");
  const scrollLeft = kanban.scrollLeft;
  const existingCards = new Map(
    Array.from(kanban.querySelectorAll(".increment-card[data-card-key]")).map((card) => [
      card.dataset.cardKey,
      card,
    ]),
  );
  const oldPositions = new Map(
    Array.from(existingCards, ([key, card]) => [
      key,
      {
        column: card.closest(".kanban-column")?.dataset.column,
        rect: card.getBoundingClientRect(),
      },
    ]),
  );
  const existingColumns = new Map(
    Array.from(kanban.querySelectorAll(".kanban-column[data-column]")).map((column) => [
      column.dataset.column,
      column,
    ]),
  );
  const desiredCards = new Set();
  const movedCards = [];
  board.columns.forEach((column) => {
    const section = existingColumns.get(column.id)
      || $("column-template").content.firstElementChild.cloneNode(true);
    section.dataset.column = column.id;
    section.querySelector("h3").textContent = column.label;
    const items = [];
    epics.forEach((epic) => {
      const index = board.epics.findIndex((item) => item.id === epic.id);
      epic.increments
        .filter((item) => item.column === column.id && item.visibleOnBoard !== false)
        .forEach((increment) => items.push({ increment, epic, index }));
    });
    if (column.id === "backlog") {
      items.sort((left, right) => {
        if (left.increment.planned !== right.increment.planned) {
          return left.increment.planned ? 1 : -1;
        }
        return (left.increment.priority || 10 ** 9) - (right.increment.priority || 10 ** 9);
      });
    }
    if (column.id === "done") {
      const rank = new Map(
        (board.history?.closedIncrements || []).map((item, position) => [
          `${item.epicId}:${item.id}`,
          position,
        ]),
      );
      items.sort(
        (left, right) =>
          (rank.get(`${left.increment.epicId}:${left.increment.id}`) ?? 10 ** 9) -
          (rank.get(`${right.increment.epicId}:${right.increment.id}`) ?? 10 ** 9),
      );
    }
    if (column.id === "done") {
      section.querySelector("h3").textContent = `${column.label} · latest ${board.history.doneLimit}`;
    }
    const count = section.querySelector(".column-count");
    count.textContent = items.length;
    count.setAttribute("aria-label", `${items.length} increment${items.length === 1 ? "" : "s"}`);
    const stack = section.querySelector(".card-stack");
    items.forEach(({ increment, epic, index }) => {
      const key = cardKey(epic.id, increment.id);
      desiredCards.add(key);
      const card = renderCard(increment, epic, index, existingCards.get(key));
      card.dataset.column = column.id;
      stack.append(card);
      const previous = oldPositions.get(key);
      if (previous && previous.column !== column.id) {
        movedCards.push({ card, previousRect: previous.rect });
      }
    });
    kanban.append(section);
  });
  existingCards.forEach((card, key) => {
    if (!desiredCards.has(key)) card.remove();
  });
  existingColumns.forEach((column, id) => {
    if (!board.columns.some((item) => item.id === id)) column.remove();
  });
  kanban.scrollLeft = scrollLeft;
  animateCardHandoffs(movedCards);
}

function animateCardHandoffs(movedCards) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  window.requestAnimationFrame(() => {
    movedCards.forEach(({ card, previousRect }) => {
      const nextRect = card.getBoundingClientRect();
      const deltaX = previousRect.left - nextRect.left;
      const deltaY = previousRect.top - nextRect.top;
      if ((!deltaX && !deltaY) || typeof card.animate !== "function") return;
      card.animate(
        [
          { transform: `translate(${deltaX}px, ${deltaY}px)` },
          { transform: "translate(0, 0)" },
        ],
        { duration: 320, easing: "cubic-bezier(0.22, 1, 0.36, 1)" },
      );
    });
  });
}

function renderClosed(board, epics) {
  const groups = $("closed-groups");
  groups.replaceChildren();
  const visibleIds = new Set(epics.map((epic) => epic.id));
  const accepted = (board.history?.closedIncrements || []).filter((item) => visibleIds.has(item.epicId));
  const grouped = new Map();
  accepted.forEach((item) => {
    if (!grouped.has(item.epicId)) grouped.set(item.epicId, []);
    grouped.get(item.epicId).push(item);
  });
  grouped.forEach((items, epicId) => {
    const epic = board.epics.find((candidate) => candidate.id === epicId) || {
      id: epicId,
      title: items[0].epicTitle || epicId,
    };
    const index = Math.max(0, board.epics.findIndex((candidate) => candidate.id === epicId));
    const section = el("section", "closed-group");
    section.style.setProperty("--epic-accent", accentFor(index));
    const header = el("header", "closed-group-heading");
    const titleBlock = el("div");
    titleBlock.append(el("p", "closed-epic-id", epicId), el("h4", "", epic.title));
    header.append(titleBlock, el("span", "closed-group-count", `${items.length} accepted`));
    const list = el("div", "closed-list");
    items.forEach((item) => {
      const row = renderCard(item, epic, index);
      row.classList.add("closed-card");
      const closedTime = el("p", "closed-at", `Accepted ${formatTime(item.acceptedAt)}`);
      row.insertBefore(closedTime, row.querySelector(".card-facts"));
      list.append(row);
    });
    section.append(header, list);
    groups.append(section);
  });
  if (accepted.length === 0) {
    groups.append(el("p", "closed-empty", "No accepted Increments match this Epic filter."));
  }
}

function renderView(board, epics) {
  const showingBoard = state.view === "board";
  const showingPortfolio = state.view === "portfolio";
  const showingPeople = state.view === "people";
  const showingClosed = state.view === "closed";
  $("epic-rail").hidden = !showingPortfolio;
  $("portfolio-run-panel").hidden = !showingPortfolio || !board.portfolioRun?.configured;
  $("portfolio-control-panel").hidden = !showingPortfolio;
  $("people-panel").hidden = !showingPeople;
  $("workflow-panel").hidden = !(showingBoard || showingClosed);
  $("workflow-title-group").hidden = showingClosed;
  $("kanban-panel").hidden = !showingBoard;
  $("closed-panel").hidden = !showingClosed;
  document.querySelectorAll(".section-tab").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.view === state.view));
  });
  if (showingClosed) renderClosed(board, epics);
  if (showingBoard) renderKanban(board, epics);
}

function renderNotices(board) {
  const notices = $("runtime-notices");
  notices.replaceChildren();
  notices.hidden = !board.warnings?.length;
  board.warnings?.forEach((warning) => notices.append(el("p", "", warning)));
}

function updateHeartbeat(board) {
  const activeCount = board.epics?.filter((epic) => epic.active).length || 0;
  $("last-refresh").textContent = `Updated ${formatTime(board.generatedAt)}`;
  setConnection(
    board.health === "degraded" ? "error" : "live",
    `Live · ${activeCount} active Epic${activeCount === 1 ? "" : "s"}`,
  );
}

function render(board) {
  const focusToken = captureFocus();
  state.board = board;
  if (!board.epics || board.epics.length === 0) {
    $("control-room").hidden = true;
    $("empty-state").hidden = false;
    const onboarding = board.onboarding;
    $("empty-eyebrow").textContent = onboarding ? "Ready for AIM" : "Runtime unavailable";
    $("empty-title").textContent = onboarding
      ? "Start from the AIM chat"
      : "No active AIM board can be read";
    $("empty-message").textContent = onboarding
      ? `${onboarding.message} Recommended next action in chat: ${onboarding.nextAction}`
      : board.warnings?.[0] || "No active Epic is available.";
    setConnection(onboarding ? "live" : "error", onboarding ? "UI ready" : "Runtime needs attention");
    return;
  }
  if (state.filter !== "all" && !board.epics.some((epic) => epic.id === state.filter)) {
    state.filter = "all";
  }
  const activeCount = board.epics.filter((epic) => epic.active).length;
  const incrementCount = board.epics.reduce(
    (total, epic) => total + epic.increments.filter((item) => item.visibleOnBoard !== false).length,
    0,
  );
  const plannedCount = board.epics.reduce(
    (total, epic) => total + epic.increments.filter((item) => item.planned).length,
    0,
  );
  const attentionCount = board.epics.reduce(
    (total, epic) => total + epic.increments.filter((item) => item.attention).length,
    0,
  );
  $("empty-state").hidden = true;
  $("control-room").hidden = false;
  $("portfolio-summary").textContent = `${activeCount} running · ${plannedCount} planned · ${incrementCount} cards on the delivery board`;
  const facts = $("runtime-facts");
  facts.replaceChildren();
  addFact(facts, "Active Epics", activeCount);
  addFact(facts, "Workspaces", board.source.workspaceCount || board.epics.length);
  addFact(facts, "Attention", attentionCount);
  addFact(facts, "Accepted history", board.history?.acceptedCount || 0);
  renderPortfolioControl(board);
  renderPortfolioRun(board);
  renderEpicRoster(board);
  renderFilters(board);
  const epics = visibleEpics(board);
  renderPeople(epics, board);
  renderView(board, epics);
  renderNotices(board);
  $("closed-count").textContent = board.history?.acceptedCount || 0;
  updateHeartbeat(board);
  restoreFocus(focusToken);
}

document.querySelectorAll(".section-tab").forEach((button) => {
  button.addEventListener("click", () => {
    state.view = button.dataset.view;
    if (state.board) render(state.board);
  });
});

$("change-request").addEventListener("input", updateActionPreview);
$("copy-action").addEventListener("click", copyActionIntent);
$("open-action").addEventListener("click", openActionInCodex);
$("action-dialog").addEventListener("close", () => {
  state.pendingAction = null;
});

async function refresh() {
  try {
    const response = await fetch("/api/board", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const board = await response.json();
    const signature = semanticBoardSignature(board);
    if (signature === state.boardSignature) {
      state.board = board;
      updateHeartbeat(board);
    } else {
      state.boardSignature = signature;
      render(board);
    }
  } catch (error) {
    setConnection("error", "Connection interrupted · retrying");
    if (!state.board) {
      $("empty-state").hidden = false;
      $("empty-message").textContent = "The local AIM UI server could not be reached.";
    }
  } finally {
    const refreshMs = state.board?.source?.refreshMs || 2000;
    window.clearTimeout(state.timer);
    state.timer = window.setTimeout(refresh, refreshMs);
  }
}

refresh();
