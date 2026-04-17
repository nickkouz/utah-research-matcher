import {
  escapeHtml,
  facultyProfileLink,
  isFacultySaved,
  loadLastResults,
  saveLastResults,
  toggleSavedFaculty,
} from "/frontend/shared.js";

function renderStudentCard(student) {
  const studentCard = document.getElementById("student-card");
  const methods = student.research_methods?.length
    ? student.research_methods.join(", ")
    : "Not specified";
  const domains = student.application_domains?.length
    ? student.application_domains.join(", ")
    : "Not specified";

  studentCard.innerHTML = `
    <p class="eyebrow">Student Profile</p>
    <h1>${escapeHtml(student.structured_facts.name)}</h1>
    <p>${escapeHtml(student.research_summary)}</p>
    <p><strong>Methods:</strong> ${escapeHtml(methods)}</p>
    <p><strong>Application areas:</strong> ${escapeHtml(domains)}</p>
  `;
}

function renderMatches(matches) {
  const container = document.getElementById("matches");
  container.innerHTML = matches
    .map((match, index) => {
      const faculty = match.faculty;
      const warning = match.warning
        ? `<p class="warning">${escapeHtml(match.warning)}</p>`
        : "";
      const saved = isFacultySaved(faculty.id);
      const tags = (faculty.research_keywords || []).slice(0, 5);

      return `
        <article class="panel faculty-card" data-card-index="${index}">
          <div class="card-header-inline">
            <div>
              <p class="score">${escapeHtml(match.match_strength.toUpperCase())} MATCH · ${escapeHtml(match.score)}</p>
              <h3>${escapeHtml(faculty.name)}</h3>
              <p class="meta">${escapeHtml(faculty.title)} · ${escapeHtml(faculty.department)}</p>
            </div>
            <button class="save-toggle ${saved ? "is-saved" : ""}" data-faculty-id="${escapeHtml(faculty.id)}" type="button">
              ${saved ? "Saved" : "Save"}
            </button>
          </div>
          <p>${escapeHtml(match.rationale)}</p>
          ${warning}
          <div class="keyword-row">
            ${tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}
          </div>
          <div class="card-actions">
            <a class="text-link" href="${escapeHtml(facultyProfileLink(faculty))}" target="_blank" rel="noreferrer">Faculty profile</a>
          </div>
          <div class="email-tabs" role="tablist" aria-label="Email draft modes">
            <button class="tab is-active" data-mode="coffee_chat" type="button">Coffee chat</button>
            <button class="tab" data-mode="lab_inquiry" type="button">Lab inquiry</button>
            <button class="tab" data-mode="paper_response" type="button">Paper response</button>
          </div>
          <div class="email-block">
            <p><strong>To:</strong> <span data-field="to">${escapeHtml(match.emails.coffee_chat.faculty_email)}</span></p>
            <p><strong>Subject:</strong> <span data-field="subject">${escapeHtml(match.emails.coffee_chat.subject)}</span></p>
            <pre data-field="body">${escapeHtml(match.emails.coffee_chat.body)}</pre>
          </div>
        </article>
      `;
    })
    .join("");

  container.querySelectorAll(".faculty-card").forEach((card, index) => {
    const match = matches[index];
    const tabs = card.querySelectorAll(".tab");
    const toField = card.querySelector('[data-field="to"]');
    const subjectField = card.querySelector('[data-field="subject"]');
    const bodyField = card.querySelector('[data-field="body"]');
    const saveButton = card.querySelector(".save-toggle");

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const mode = tab.dataset.mode;
        const email = match.emails[mode];

        tabs.forEach((item) => item.classList.toggle("is-active", item === tab));
        toField.textContent = email.faculty_email;
        subjectField.textContent = email.subject;
        bodyField.textContent = email.body;
      });
    });

    saveButton.addEventListener("click", () => {
      toggleSavedFaculty(saveButton.dataset.facultyId);
      saveButton.classList.toggle("is-saved");
      saveButton.textContent = saveButton.classList.contains("is-saved") ? "Saved" : "Save";
    });
  });
}

async function loadResults() {
  const cached = loadLastResults();
  if (cached?.status === "ready" && cached?.matches?.length) {
    return cached;
  }

  const response = await fetch("/data/demo_results.json");
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const data = await response.json();
  if (data?.status === "ready") {
    saveLastResults(data);
  }
  return data;
}

function renderEmptyState() {
  document.getElementById("results-empty").classList.remove("is-hidden");
  document.getElementById("results-section").classList.add("is-hidden");
  document.getElementById("student-card").classList.add("is-hidden");
}

loadResults()
  .then((data) => {
    if (!data || data.status !== "ready" || !data.matches?.length) {
      renderEmptyState();
      return;
    }
    renderStudentCard(data.student);
    renderMatches(data.matches);
  })
  .catch((error) => {
    renderEmptyState();
    document.getElementById("results-empty").innerHTML = `
      <p class="eyebrow">Unable to Load Results</p>
      <h2>Something went wrong while loading match results.</h2>
      <p class="section-copy">${escapeHtml(error.message)}</p>
      <a class="button" href="/form">Return to form</a>
    `;
  });
