(() => {
  "use strict";

  const series = Array.isArray(window.CAP_SERIES) ? window.CAP_SERIES : [];
  const resources = Array.isArray(window.CAP_RESOURCES) ? window.CAP_RESOURCES : [];
  const all = [
    ...series.map(item => ({ ...item, catalogType: "series" })),
    ...resources.map(item => ({ ...item, catalogType: "resource" }))
  ];
  const categoryOrder = ["全部", "三年五科", "正式自學", "格鬥遊戲", "主題複習", "讀書計畫", "相關題庫", "資源總覽", "舊版備用", "規劃中"];
  let category = "全部";
  let query = "";

  const search = document.getElementById("catalogSearch");
  const filters = document.getElementById("categoryFilters");
  const summary = document.getElementById("catalogSummary");
  const seriesGrid = document.getElementById("seriesGrid");
  const resourceGrid = document.getElementById("resourceGrid");
  const resourceCount = document.getElementById("resourceCount");

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[char]));
  }

  function safeUrl(value) {
    const url = String(value || "").trim();
    if (!url) return "";
    if (/^https:\/\//i.test(url)) return url;
    if (/^(?:[a-z0-9_-]+\/|\.\.\/|\.\/)/i.test(url) && !url.includes(":")) return url;
    return "";
  }

  function externalAttrs(url) {
    return /^https:\/\//i.test(url) ? ' target="_blank" rel="noopener"' : "";
  }

  function statusMeta(status) {
    return {
      live: ["已上線", "status-live"],
      recommended: ["推薦入口", "status-recommended"],
      legacy: ["舊版備用", "status-legacy"],
      planned: ["規劃中", "status-planned"]
    }[status] || ["已上線", "status-live"];
  }

  function subjectClass(slug) {
    return ["chinese", "english", "math", "social", "science"].includes(slug) ? ` subject-${slug}` : "";
  }

  function actions(item) {
    const items = [];
    const primary = safeUrl(item.studentHref || item.href);
    const teacher = safeUrl(item.teacherHref);
    const repo = safeUrl(item.repoHref);
    if (primary) items.push(`<a class="btn primary sm" href="${esc(primary)}"${externalAttrs(primary)}>開啟網站</a>`);
    if (teacher) items.push(`<a class="btn sm teacher-action" href="${esc(teacher)}"${externalAttrs(teacher)}>教師端</a>`);
    if (repo) items.push(`<a class="btn sm" href="${esc(repo)}"${externalAttrs(repo)}>查看 Repository</a>`);
    if (!items.length) items.push('<span class="unavailable">尚無可開啟網站</span>');
    return items.join("");
  }

  function card(item) {
    const [statusText, statusClass] = statusMeta(item.status);
    const tags = (item.tags || []).slice(0, 6).map(tag => `<span class="tag">${esc(tag)}</span>`).join("");
    const title = item.catalogType === "series" ? `${item.year} 會考${item.name}` : item.title;
    const description = item.catalogType === "series"
      ? `${item.desc}。官方原題截圖、隨手練習、正式測驗與錯題重練。`
      : item.description;
    const icon = item.catalogType === "series" ? item.icon : item.icon || "網";
    const meta = item.catalogType === "series" ? `${item.year} 年・${item.count} 題` : item.meta;
    const searchable = [title, description, item.category, item.kind, meta, ...(item.tags || [])].join(" ").toLowerCase();
    return `<article class="resource-card${item.status === "planned" ? " planned" : ""}" data-category="${esc(item.category)}" data-search="${esc(searchable)}">
      <div class="card-head">
        <div class="resource-icon${subjectClass(item.slug)}">${esc(icon)}</div>
        <div class="card-title"><div class="kind">${esc(item.kind || item.category)}</div><h3>${esc(title)}</h3></div>
        <span class="status-badge ${statusClass}">${esc(statusText)}</span>
      </div>
      <p class="resource-desc">${esc(description)}</p>
      <div class="resource-meta">${esc(meta || "")}</div>
      <div class="tags">${tags}</div>
      <div class="card-actions">${actions(item)}</div>
    </article>`;
  }

  function filterButtons() {
    const present = new Set(all.map(item => item.category));
    const categories = categoryOrder.filter(item => item === "全部" || present.has(item));
    filters.innerHTML = categories.map(item => `<button class="filter ${item === category ? "active" : ""}" type="button" data-category="${esc(item)}" aria-pressed="${item === category}">${esc(item)}</button>`).join("");
    filters.querySelectorAll("button").forEach(button => {
      button.addEventListener("click", () => {
        category = button.dataset.category;
        render();
        if (category !== "全部" && category !== "三年五科") document.getElementById("resources").scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  function matches(item) {
    const title = item.catalogType === "series" ? `${item.year} 會考${item.name}` : item.title;
    const haystack = [title, item.description, item.desc, item.category, item.kind, item.meta, item.year, item.name, ...(item.tags || [])].join(" ").toLowerCase();
    return (category === "全部" || item.category === category) && (!query || haystack.includes(query));
  }

  function render() {
    filterButtons();
    const shownSeries = series.map(item => ({ ...item, catalogType: "series" })).filter(matches);
    const shownResources = resources.map(item => ({ ...item, catalogType: "resource" })).filter(matches);
    seriesGrid.innerHTML = shownSeries.map(card).join("");
    resourceGrid.innerHTML = shownResources.map(card).join("");

    const seriesSection = document.getElementById("series");
    const resourceSection = document.getElementById("resources");
    seriesSection.hidden = shownSeries.length === 0;
    resourceSection.hidden = shownResources.length === 0;
    resourceCount.textContent = `${shownResources.length} 個網站／項目`;
    const shown = shownSeries.length + shownResources.length;
    summary.textContent = shown ? `顯示 ${shown} / ${all.length} 個網站與項目` : "找不到符合條件的網站，請改用其他關鍵字。";
  }

  search.addEventListener("input", () => {
    query = search.value.trim().toLowerCase();
    render();
  });

  document.querySelectorAll("[data-set-category]").forEach(link => {
    link.addEventListener("click", () => {
      category = link.dataset.setCategory;
      query = "";
      search.value = "";
      render();
    });
  });

  render();
})();
