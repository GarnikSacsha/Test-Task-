const $ = (selector) => document.querySelector(selector);

const state = {
  email: null,
  messages: [],
};

function log(message, ok = true) {
  const item = document.createElement("li");
  item.textContent = `${new Date().toLocaleTimeString()} ${ok ? "OK" : "ERR"} ${message}`;
  $("#log").prepend(item);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with ${response.status}`);
  }
  return payload;
}

async function checkHealth() {
  try {
    const data = await api("/health");
    $("#health-dot").className = `dot ${data.status === "ok" ? "ok" : "bad"}`;
    $("#health-text").textContent = `${data.status} / ${data.browser}`;
    $("#hero-browser").textContent = data.demo_mode ? "demo mode" : data.browser;
    $("#hero-count").textContent = data.inbox_count;
    if (data.current_email) {
      state.email = data.current_email;
      $("#email-value").textContent = data.current_email;
      $("#hero-email-value").textContent = data.current_email;
    }
  } catch (error) {
    $("#health-dot").className = "dot bad";
    $("#health-text").textContent = "API unavailable";
    $("#hero-browser").textContent = "offline";
  }
}

async function loadEmail() {
  try {
    const data = await api("/api/email");
    state.email = data.email;
    $("#email-value").textContent = data.email;
    $("#hero-email-value").textContent = data.email;
    log(`Loaded email ${data.email}`);
    await checkHealth();
  } catch (error) {
    log(error.message, false);
  }
}

async function loadInbox() {
  try {
    const data = await api("/api/inbox");
    state.messages = data.messages;
    $("#inbox-count").textContent = data.count;
    $("#hero-count").textContent = data.count;
    renderInbox(data.messages);
    log(`Loaded ${data.count} inbox message(s)`);
    await checkHealth();
  } catch (error) {
    log(error.message, false);
  }
}

function renderInbox(messages) {
  const list = $("#inbox-list");
  list.innerHTML = "";
  list.className = messages.length ? "inbox" : "inbox empty";
  if (!messages.length) {
    list.textContent = "Inbox is empty";
    return;
  }

  for (const message of messages) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "message";
    button.innerHTML = `<strong>${escapeHtml(message.subject || "No subject")}</strong><span>${escapeHtml(message.sender || "unknown sender")} / ${escapeHtml(message.time || "unknown time")}</span>`;
    button.addEventListener("click", () => loadMessage(message.id));
    list.append(button);
  }
}

async function loadMessage(id) {
  try {
    const data = await api(`/api/email/${encodeURIComponent(id)}`);
    $("#message-id").textContent = data.id;
    $("#message-content").textContent = JSON.stringify(data, null, 2);
    log(`Loaded message ${id}`);
  } catch (error) {
    log(error.message, false);
  }
}

async function refreshEmail() {
  try {
    const data = await api("/api/email/refresh", { method: "POST" });
    state.email = data.email;
    state.messages = [];
    $("#email-value").textContent = data.email;
    $("#hero-email-value").textContent = data.email;
    $("#message-id").textContent = "select a message";
    $("#message-content").textContent = "Waiting for a message selection.";
    renderInbox([]);
    $("#inbox-count").textContent = "0";
    $("#hero-count").textContent = "0";
    log(`Generated new address ${data.email}`);
    await checkHealth();
  } catch (error) {
    log(error.message, false);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

$("#load-email").addEventListener("click", loadEmail);
$("#hero-email").addEventListener("click", loadEmail);
$("#load-inbox").addEventListener("click", loadInbox);
$("#new-email").addEventListener("click", refreshEmail);
$("#copy-email").addEventListener("click", async () => {
  if (!state.email) return;
  await navigator.clipboard.writeText(state.email);
  log("Copied current email");
});
$("#clear-log").addEventListener("click", () => {
  $("#log").innerHTML = "";
});

checkHealth();
