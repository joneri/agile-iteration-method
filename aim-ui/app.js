"use strict";

const state = { board: null, timer: null };
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

function addFact(list, label, value) {
  const group = el("div");
  group.append(el("dt", "", label), el("dd", "", value || "—"));
  list.append(group);
}

function setConnection(kind, label) {
  const connection = $("connection-label").parentElement;
  connection.classList.toggle("is-live", kind === "live");
  connection.classList.toggle("is-error", kind === "error");
  $("connection-label").textContent = label;
}

function renderRoles(epic) {
  const lane = $("role-lane");
  lane.replaceChildren();
  epic.canonicalRoles.forEach((role) => {
    const chip = $("role-template").content.firstElementChild.cloneNode(true);
    chip.classList.toggle("is-active", role.active);
    chip.querySelector(".role-name").textContent = role.name;
    if (role.active) chip.setAttribute("aria-current", "true");
    lane.append(chip);
  });
}

function renderHelpers(epic) {
  const lane = $("helper-lane");
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

function renderCard(increment) {
  const card = $("card-template").content.firstElementChild.cloneNode(true);
  card.classList.toggle("is-active", increment.active);
  card.querySelector(".increment-id").textContent = increment.id;
  card.querySelector(".owner-badge").textContent = increment.canonicalOwner;
  card.querySelector(".increment-title").textContent = increment.title;
  card.querySelector(".epic-link").textContent = `From ${increment.epicId}`;
  const facts = card.querySelector(".card-facts");
  addFact(facts, "Gate", increment.gate);
  addFact(facts, "Mode", increment.mode);
  addFact(facts, "Cost", increment.costProfile);
  addFact(facts, "State", increment.runtimeStatus.replaceAll("_", " "));
  const attention = card.querySelector(".attention");
  if (increment.attention) {
    attention.hidden = false;
    attention.textContent = increment.attention;
  }
  const links = card.querySelector(".evidence-links");
  increment.evidence.forEach((item) => {
    const link = el("a", "", item.label);
    link.href = `/api/evidence?path=${encodeURIComponent(item.path)}`;
    link.target = "_blank";
    link.rel = "noopener";
    links.append(link);
  });
  if (increment.evidence.length === 0) links.append(el("span", "", "No evidence linked"));
  return card;
}

function renderKanban(board, epic) {
  const kanban = $("kanban");
  kanban.replaceChildren();
  board.columns.forEach((column) => {
    const section = $("column-template").content.firstElementChild.cloneNode(true);
    section.dataset.column = column.id;
    section.querySelector("h3").textContent = column.label;
    const items = epic.increments.filter((item) => item.column === column.id);
    const count = section.querySelector(".column-count");
    count.textContent = items.length;
    count.setAttribute("aria-label", `${items.length} increment${items.length === 1 ? "" : "s"}`);
    const stack = section.querySelector(".card-stack");
    items.forEach((item) => stack.append(renderCard(item)));
    kanban.append(section);
  });
}

function render(board) {
  state.board = board;
  if (!board.epics || board.epics.length === 0) {
    $("control-room").hidden = true;
    $("empty-state").hidden = false;
    $("empty-message").textContent = board.warnings?.[0] || "No active Epic is available.";
    setConnection("error", "Runtime needs attention");
    return;
  }
  const epic = board.epics[0];
  $("empty-state").hidden = true;
  $("control-room").hidden = false;
  $("epic-title").textContent = epic.title;
  $("epic-id").textContent = epic.id;
  const facts = $("runtime-facts");
  facts.replaceChildren();
  addFact(facts, "Current role", epic.currentRole);
  addFact(facts, "Last gate", epic.lastGatePassed || "Not passed");
  addFact(facts, "Mode", epic.mode);
  addFact(facts, "Cost profile", epic.costProfile);
  renderRoles(epic);
  renderHelpers(epic);
  renderKanban(board, epic);
  $("last-refresh").textContent = `Updated ${formatTime(board.generatedAt)}`;
  setConnection("live", `Live · ${epic.runtimeStatus.replaceAll("_", " ")}`);
}

async function refresh() {
  try {
    const response = await fetch("/api/board", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    render(await response.json());
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
