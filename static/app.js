const form = document.getElementById("searchForm");
const queryInput = document.getElementById("query");
const searchBtn = document.getElementById("searchBtn");
const resultsEl = document.getElementById("results");
const metaEl = document.getElementById("meta");
const summaryEl = document.getElementById("summary");

function money(value) {
  if (typeof value !== "number") return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(value);
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function render(data) {
  if (!data.ok) {
    resultsEl.innerHTML = `<div class="error">${esc(data.error || "Live search failed.")}</div>`;
    metaEl.classList.add("hidden");
    summaryEl.classList.add("hidden");
    return;
  }

  const items = data.results || [];
  metaEl.classList.remove("hidden");
  metaEl.textContent = `${items.length} live offers found • ${data.provider} • checked ${new Date(data.checked_at).toLocaleString()}`;

  if (!items.length) {
    summaryEl.classList.add("hidden");
    resultsEl.innerHTML = `<div class="empty">No priced offers were returned for this search. Try a more specific product name.</div>`;
    return;
  }

  const best = items[0];
  summaryEl.classList.remove("hidden");
  summaryEl.innerHTML = `
    <div><small>LOWEST LIVE PRICE</small><strong>${money(best.price)}</strong></div>
    <div><small>SELLER</small><strong>${esc(best.merchant)}</strong></div>
    <div><small>RESULTS</small><strong>${items.length}</strong></div>
  `;

  resultsEl.innerHTML = items.map((item, index) => `
    <article class="card ${index === 0 ? "best" : ""}">
      <div class="rank">${index + 1}</div>
      <div class="image">
        ${item.thumbnail ? `<img src="${esc(item.thumbnail)}" alt="">` : `<span>SHOP</span>`}
      </div>
      <div class="details">
        <h3>${esc(item.title)}</h3>
        <p class="merchant">${esc(item.merchant)}</p>
        ${item.rating ? `<p class="rating">★ ${esc(item.rating)} ${item.reviews ? `(${esc(item.reviews)})` : ""}</p>` : ""}
        ${item.delivery ? `<p class="delivery">${esc(item.delivery)}</p>` : ""}
      </div>
      <div class="price">
        <strong>${money(item.price)}</strong>
        ${item.old_price ? `<del>${money(item.old_price)}</del>` : ""}
        ${item.link ? `<a href="${esc(item.link)}" target="_blank" rel="noopener">View offer ↗</a>` : ""}
      </div>
    </article>
  `).join("");
}

async function searchLive(q) {
  searchBtn.disabled = true;
  searchBtn.textContent = "Fetching live prices...";
  resultsEl.innerHTML = `<div class="loading">Checking live shopping results…</div>`;

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(q)}`, { cache: "no-store" });
    const data = await response.json();
    render(data);
  } catch (error) {
    resultsEl.innerHTML = `<div class="error">Could not connect to the Smart-Shop server.</div>`;
  } finally {
    searchBtn.disabled = false;
    searchBtn.textContent = "Search Live Prices";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const q = queryInput.value.trim();
  if (q.length >= 2) searchLive(q);
});
