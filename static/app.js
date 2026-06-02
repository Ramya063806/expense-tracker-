const API = "/api";

function formatMoney(amount) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

function formatDate(iso) {
  return new Date(iso + "T12:00:00").toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function showToast(message, type = "success") {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = `toast ${type}`;
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => el.classList.add("hidden"), 3500);
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return null;
  return res.json();
}

async function checkHealth() {
  const badge = document.getElementById("chroma-status");
  try {
    const data = await api("/health");
    if (data.chroma_connected) {
      badge.textContent = "Chroma connected";
      badge.className = "status-badge connected";
    } else {
      badge.textContent = "Chroma offline";
      badge.className = "status-badge disconnected";
    }
  } catch {
    badge.textContent = "API offline";
    badge.className = "status-badge disconnected";
  }
}

async function loadStats() {
  const stats = await api("/stats");
  document.getElementById("stat-total").textContent = formatMoney(stats.total);
  document.getElementById("stat-count").textContent = String(stats.count);

  const container = document.getElementById("stat-categories");
  const entries = Object.entries(stats.by_category);
  if (!entries.length) {
    container.innerHTML = '<span class="pill">No data yet</span>';
    return;
  }
  container.innerHTML = entries
    .map(
      ([cat, total]) =>
        `<span class="pill">${cat}: <strong>${formatMoney(total)}</strong></span>`
    )
    .join("");

  const filter = document.getElementById("filter-category");
  const current = filter.value;
  filter.innerHTML =
    '<option value="">All categories</option>' +
    entries
      .map(([cat]) => `<option value="${cat}">${cat}</option>`)
      .join("");
  filter.value = current;
}

function renderExpenseItem(expense, highlight = false) {
  const div = document.createElement("article");
  div.className = `expense-item${highlight ? " search-hit" : ""}`;
  div.dataset.id = expense.id;
  div.innerHTML = `
    <div class="expense-main">
      <strong>${escapeHtml(expense.description)}</strong>
      <div class="expense-meta">${formatDate(expense.expense_date)}</div>
    </div>
    <span class="expense-amount">${formatMoney(expense.amount)}</span>
    <div style="display:flex;align-items:center;gap:0.5rem">
      <span class="expense-category">${escapeHtml(expense.category)}</span>
      <button type="button" class="btn btn-danger" data-delete="${expense.id}">Delete</button>
    </div>
  `;
  div.querySelector("[data-delete]").addEventListener("click", () =>
    deleteExpense(expense.id)
  );
  return div;
}

function escapeHtml(text) {
  const d = document.createElement("div");
  d.textContent = text;
  return d.innerHTML;
}

async function loadExpenses(category = "") {
  const path = category
    ? `/expenses?category=${encodeURIComponent(category)}`
    : "/expenses";
  const expenses = await api(path);
  const list = document.getElementById("expense-list");

  if (!expenses.length) {
    list.innerHTML =
      '<p class="empty-state">No expenses yet. Add your first one above.</p>';
    return;
  }

  list.innerHTML = "";
  expenses.forEach((e) => list.appendChild(renderExpenseItem(e)));
}

async function deleteExpense(id) {
  if (!confirm("Delete this expense?")) return;
  try {
    await api(`/expenses/${id}`, { method: "DELETE" });
    showToast("Expense deleted");
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function refresh() {
  await Promise.all([
    loadStats(),
    loadExpenses(document.getElementById("filter-category").value),
  ]);
}

document.getElementById("expense-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const data = new FormData(form);
  try {
    await api("/expenses", {
      method: "POST",
      body: JSON.stringify({
        description: data.get("description"),
        amount: parseFloat(data.get("amount")),
        category: data.get("category"),
        expense_date: data.get("expense_date"),
      }),
    });
    form.reset();
    document.querySelector('[name="expense_date"]').valueAsDate = new Date();
    showToast("Expense added");
    document.getElementById("search-results").classList.add("hidden");
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = new FormData(e.target).get("query");
  const container = document.getElementById("search-results");
  try {
    const result = await api(`/search?q=${encodeURIComponent(query)}`);
    container.classList.remove("hidden");
    if (!result.expenses.length) {
      container.innerHTML =
        "<h3>No matches</h3><p class=\"empty-state\">Try different wording.</p>";
      return;
    }
    container.innerHTML = `<h3>Results for “${escapeHtml(result.query)}”</h3>`;
    result.expenses.forEach((exp) => {
      container.appendChild(renderExpenseItem(exp, true));
    });
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("filter-category").addEventListener("change", (e) => {
  loadExpenses(e.target.value).catch((err) => showToast(err.message, "error"));
});

document.querySelector('[name="expense_date"]').valueAsDate = new Date();

checkHealth();
refresh().catch((err) => showToast(err.message, "error"));
