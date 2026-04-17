async function loadResults() {
  const response = await fetch("../data/demo_results.json");
  const data = await response.json();

  const student = data.student;
  const studentCard = document.getElementById("student-card");
  if (studentCard) {
    studentCard.innerHTML = `
      <p class="eyebrow">Student Profile</p>
      <h1>${student.structured_facts.name}</h1>
      <p>${student.research_summary}</p>
      <p><strong>Skills:</strong> ${student.structured_facts.skills.join(", ")}</p>
    `;
  }

  const container = document.getElementById("matches");
  if (!container) {
    return;
  }

  container.innerHTML = data.matches
    .map((match) => {
      const email = match.emails.lab_inquiry;
      return `
        <article class="panel faculty-card">
          <p class="score">${match.match_strength.toUpperCase()} MATCH - ${match.score}</p>
          <h3>${match.faculty.name}</h3>
          <p>${match.faculty.department}</p>
          <p>${match.rationale}</p>
          <div class="email-block">
            <p><strong>Subject:</strong> ${email.subject}</p>
            <pre>${email.body}</pre>
          </div>
        </article>
      `;
    })
    .join("");
}

loadResults().catch((error) => {
  const container = document.getElementById("matches");
  if (container) {
    container.innerHTML = `<p>Unable to load demo results: ${error.message}</p>`;
  }
});
