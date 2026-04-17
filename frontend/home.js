import {
  escapeHtml,
  facultyProfileLink,
  formatRelativeDate,
  isFacultySaved,
  loadDraft,
  loadLastResults,
  loadSavedFaculty,
  toggleSavedFaculty,
} from "/frontend/shared.js";

let browserRecords = [];

function renderDraftState() {
  const container = document.getElementById("draft-state");
  const draft = loadDraft();
  if (!draft) {
    container.innerHTML = `
      <p>No unfinished draft yet. Start the form and your progress will be saved in this browser.</p>
    `;
    return;
  }

  const interest = escapeHtml(draft.primary_interest_text || "Research interests not started");
  container.innerHTML = `
    <div class="dashboard-info">
      <p><strong>Last edited:</strong> ${escapeHtml(formatRelativeDate(draft.updatedAt))}</p>
      <p><strong>Major:</strong> ${escapeHtml(draft.major || "Not specified")}</p>
      <p><strong>Current topic:</strong> ${interest}</p>
    </div>
  `;
}

function renderPossibleConnections() {
  const container = document.getElementById("possible-connections");
  const latestResults = loadLastResults();
  const matches = latestResults?.matches || [];
  document.getElementById("latest-match-count").textContent = String(matches.length);

  if (!matches.length) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No matches yet. Submit the form to see your top faculty recommendations here.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = matches.slice(0, 3).map(renderFacultyConnectionCard).join("");
  bindSavedToggles(container);
}

function renderFacultyConnectionCard(match) {
  const faculty = match.faculty;
  const saved = isFacultySaved(faculty.id);
  const tags = (faculty.research_keywords || []).slice(0, 4);
  return `
    <article class="mini-card">
      <div class="card-header-inline">
        <div>
          <p class="score">${escapeHtml(match.match_strength.toUpperCase())} MATCH</p>
          <h3>${escapeHtml(faculty.name)}</h3>
          <p class="meta">${escapeHtml(faculty.department)}</p>
        </div>
        <button class="save-toggle ${saved ? "is-saved" : ""}" data-faculty-id="${escapeHtml(faculty.id)}" type="button">
          ${saved ? "Saved" : "Save"}
        </button>
      </div>
      <p>${escapeHtml(match.rationale)}</p>
      <div class="keyword-row">
        ${tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}
      </div>
      <div class="card-actions">
        <a class="text-link" href="/results">Open full result</a>
        <a class="text-link" href="${escapeHtml(facultyProfileLink(faculty))}" target="_blank" rel="noreferrer">Faculty profile</a>
      </div>
    </article>
  `;
}

function renderBrowserControls() {
  const departments = [...new Set(browserRecords.map((record) => record.department).filter(Boolean))].sort();
  const keywords = [...new Set(browserRecords.flatMap((record) => record.research_keywords || []))].sort();

  const departmentSelect = document.getElementById("browse-department");
  const keywordSelect = document.getElementById("browse-keyword");

  departmentSelect.innerHTML = `<option value="">All departments</option>${departments
    .map((department) => `<option value="${escapeHtml(department)}">${escapeHtml(department)}</option>`)
    .join("")}`;
  keywordSelect.innerHTML = `<option value="">All research areas</option>${keywords
    .map((keyword) => `<option value="${escapeHtml(keyword)}">${escapeHtml(keyword)}</option>`)
    .join("")}`;
}

function renderFacultyBrowser() {
  const container = document.getElementById("browse-results");
  const search = document.getElementById("browse-search").value.trim().toLowerCase();
  const department = document.getElementById("browse-department").value;
  const keyword = document.getElementById("browse-keyword").value;
  const minYear = Number(document.getElementById("browse-activity").value || 0);

  const filtered = browserRecords.filter((record) => {
    const haystack = [
      record.name,
      record.department,
      record.browser_snippet,
      ...(record.research_keywords || []),
    ]
      .join(" ")
      .toLowerCase();

    const matchesSearch = !search || haystack.includes(search);
    const matchesDepartment = !department || record.department === department;
    const matchesKeyword = !keyword || (record.research_keywords || []).includes(keyword);
    const matchesYear = !minYear || Number(record.last_active_year || 0) >= minYear;
    return matchesSearch && matchesDepartment && matchesKeyword && matchesYear;
  });

  document.getElementById("browser-record-count").textContent = String(browserRecords.length);

  if (!filtered.length) {
    container.innerHTML = `
      <div class="empty-state panel">
        <p>No faculty records match these filters.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(renderBrowserCard).join("");
  bindSavedToggles(container);
}

function renderBrowserCard(record) {
  const saved = isFacultySaved(record.id);
  const eligibleBadge = record.eligible_for_matching ? "Match-eligible" : "Browse-only";
  return `
    <article class="panel faculty-card">
      <div class="card-header-inline">
        <div>
          <p class="score">${escapeHtml(eligibleBadge)}</p>
          <h3>${escapeHtml(record.name)}</h3>
          <p class="meta">${escapeHtml(record.title)} · ${escapeHtml(record.department)}</p>
        </div>
        <button class="save-toggle ${saved ? "is-saved" : ""}" data-faculty-id="${escapeHtml(record.id)}" type="button">
          ${saved ? "Saved" : "Save"}
        </button>
      </div>
      <p>${escapeHtml(record.browser_snippet)}</p>
      <p class="meta">Recent activity: ${escapeHtml(record.last_active_year || "Unknown")}</p>
      <div class="keyword-row">
        ${(record.research_keywords || []).slice(0, 6).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}
      </div>
      <div class="card-actions">
        <a class="text-link" href="${escapeHtml(record.profile_url || "#")}" target="_blank" rel="noreferrer">Faculty profile</a>
      </div>
    </article>
  `;
}

function bindSavedToggles(scope) {
  scope.querySelectorAll(".save-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      toggleSavedFaculty(button.dataset.facultyId);
      document.getElementById("saved-faculty-count").textContent = String(loadSavedFaculty().length);
      renderPossibleConnections();
      renderFacultyBrowser();
    });
  });
}

async function loadFacultyBrowser() {
  const response = await fetch("/data/faculty_browser.json");
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  browserRecords = await response.json();
}

async function init() {
  document.getElementById("saved-faculty-count").textContent = String(loadSavedFaculty().length);
  renderDraftState();
  renderPossibleConnections();
  await loadFacultyBrowser();
  renderBrowserControls();
  renderFacultyBrowser();

  ["browse-search", "browse-department", "browse-keyword", "browse-activity"].forEach((id) => {
    document.getElementById(id).addEventListener("input", renderFacultyBrowser);
    document.getElementById(id).addEventListener("change", renderFacultyBrowser);
  });
}

init().catch((error) => {
  document.getElementById("browse-results").innerHTML = `
    <div class="panel empty-state">
      <p>Unable to load the faculty browser: ${escapeHtml(error.message)}</p>
    </div>
  `;
});
