function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderStudentCard(student) {
  const studentCard = document.getElementById("student-card");
  if (!studentCard) {
    return;
  }

  const skills = student.structured_facts.skills.length
    ? student.structured_facts.skills.join(", ")
    : "Not specified";

  studentCard.innerHTML = `
    <p class="eyebrow">Student Profile</p>
    <h1>${escapeHtml(student.structured_facts.name)}</h1>
    <p>${escapeHtml(student.research_summary)}</p>
    <p><strong>Skills:</strong> ${escapeHtml(skills)}</p>
  `;
}

function renderMatches(matches) {
  const container = document.getElementById("matches");
  if (!container) {
    return;
  }

  container.innerHTML = matches
    .map((match, index) => {
      const faculty = match.faculty;
      const warning = match.warning
        ? `<p class="warning">${escapeHtml(match.warning)}</p>`
        : "";

      return `
        <article class="panel faculty-card" data-card-index="${index}">
          <p class="score">${escapeHtml(match.match_strength.toUpperCase())} MATCH - ${escapeHtml(match.score)}</p>
          <h3>${escapeHtml(faculty.name)}</h3>
          <p class="meta">${escapeHtml(faculty.department)}</p>
          <p>${escapeHtml(match.rationale)}</p>
          ${warning}
          <div class="email-tabs" role="tablist" aria-label="Email draft modes">
            <button class="tab is-active" data-mode="coffee_chat">Coffee chat</button>
            <button class="tab" data-mode="lab_inquiry">Lab inquiry</button>
            <button class="tab" data-mode="paper_response">Paper response</button>
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
  });
}

async function loadResults() {
  const cached = window.sessionStorage.getItem("latestResults");
  const data = cached
    ? JSON.parse(cached)
    : await fetch("/data/demo_results.json").then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      });
  renderStudentCard(data.student);
  renderMatches(data.matches);
}

loadResults().catch((error) => {
  const container = document.getElementById("matches");
  if (container) {
    container.innerHTML = `<p>Unable to load demo results: ${escapeHtml(error.message)}</p>`;
  }
});
