function collectStudentPayload(form) {
  const formData = new FormData(form);
  return {
    name: formData.get("name"),
    email: formData.get("email"),
    major: formData.get("major"),
    year: formData.get("year"),
    courses: String(formData.get("courses") || "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean),
    skills: String(formData.get("skills") || "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean),
    interests_freetext: formData.get("interests_freetext"),
    checkbox_areas: formData.getAll("checkbox_areas"),
    goal: formData.get("goal"),
    commitment_hours: Number(formData.get("commitment_hours") || 0),
  };
}

async function submitForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const status = document.getElementById("form-status");
  const button = document.getElementById("submit-button");
  const payload = collectStudentPayload(form);

  status.textContent = "Generating matches...";
  button.disabled = true;
  button.textContent = "Working...";

  try {
    const response = await fetch("/api/match", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: "Request failed" }));
      status.textContent = error.error || "Unable to generate matches.";
      return;
    }

    const results = await response.json();
    window.sessionStorage.setItem("latestResults", JSON.stringify(results));
    window.location.href = "/results";
  } catch (error) {
    status.textContent = "Unable to connect to the matching service.";
  } finally {
    button.disabled = false;
    button.textContent = "Generate Matches";
  }
}

document.getElementById("student-form").addEventListener("submit", submitForm);
