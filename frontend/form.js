import {
  clearDraft,
  loadDraft,
  saveDraft,
  saveLastResults,
} from "/frontend/shared.js";

const form = document.getElementById("student-form");
const statusEl = document.getElementById("form-status");
const buttonEl = document.getElementById("submit-button");
const followupShell = document.getElementById("followup-shell");
const followupQuestion = document.getElementById("followup-question");
const specificityBar = document.getElementById("specificity-bar");
const specificityLabel = document.getElementById("specificity-label");
const specificityCopy = document.getElementById("specificity-copy");

function selectedValues(name) {
  return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((input) => input.value);
}

function collectStudentPayload() {
  const formData = new FormData(form);
  const applicationAreas = selectedValues("application_areas");
  const methods = selectedValues("methods");

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
    primary_interest_text: formData.get("primary_interest_text"),
    interests_freetext: formData.get("primary_interest_text"),
    application_areas: applicationAreas,
    methods,
    checkbox_areas: [...applicationAreas, ...methods],
    reference_examples: formData.get("reference_examples"),
    goal: formData.get("goal"),
    commitment_hours: Number(formData.get("commitment_hours") || 0),
    followup_answer: formData.get("followup_answer"),
  };
}

function applyDraft(draft) {
  if (!draft) {
    return;
  }

  Object.entries(draft).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);
    if (!field || value == null) {
      return;
    }

    if (field instanceof RadioNodeList) {
      const values = Array.isArray(value) ? value : [value];
      [...field].forEach((input) => {
        input.checked = values.includes(input.value);
      });
      return;
    }

    if (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) {
      field.value = Array.isArray(value) ? value.join(", ") : String(value);
    }
  });

  if (draft.followupQuestion) {
    followupShell.classList.remove("is-hidden");
    followupQuestion.textContent = draft.followupQuestion;
  }
}

function updateSpecificityMeter() {
  const payload = collectStudentPayload();
  const interestWords = String(payload.primary_interest_text || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;

  let score = 0;
  if (interestWords >= 8) score += 35;
  if (interestWords >= 16) score += 10;
  score += Math.min(payload.methods.length * 10, 20);
  score += Math.min(payload.application_areas.length * 10, 20);
  if (String(payload.reference_examples || "").trim()) score += 15;

  specificityBar.style.width = `${Math.min(score, 100)}%`;
  specificityBar.className = "meter-bar";

  if (score < 40) {
    specificityLabel.textContent = "Too broad";
    specificityCopy.textContent = "Add a specific research topic, then choose at least one method and one application area.";
    specificityBar.classList.add("meter-low");
  } else if (score < 75) {
    specificityLabel.textContent = "Usable";
    specificityCopy.textContent = "You have enough signal to start matching, but one concrete example or clearer topic would improve precision.";
    specificityBar.classList.add("meter-medium");
  } else {
    specificityLabel.textContent = "Strong";
    specificityCopy.textContent = "This profile has enough detail for a precision-first faculty match.";
    specificityBar.classList.add("meter-high");
  }
}

function persistDraft() {
  const payload = collectStudentPayload();
  payload.followupQuestion = followupQuestion.textContent || "";
  saveDraft(payload);
  updateSpecificityMeter();
}

async function submitForm(event) {
  event.preventDefault();
  const payload = collectStudentPayload();

  statusEl.textContent = "Generating matches...";
  buttonEl.disabled = true;
  buttonEl.textContent = "Working...";

  try {
    const response = await fetch("/api/match", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json().catch(() => ({ error: "Request failed" }));
    if (!response.ok) {
      statusEl.textContent = result.error || "Unable to generate matches.";
      return;
    }

    if (result.status === "needs_followup") {
      followupShell.classList.remove("is-hidden");
      followupQuestion.textContent = result.followup_question || "Please add one more specific detail.";
      persistDraft();
      statusEl.textContent = "One more detail will help us narrow to stronger faculty matches.";
      document.querySelector('textarea[name="followup_answer"]').focus();
      return;
    }

    if (result.status === "ready") {
      saveLastResults(result);
      clearDraft();
      window.location.href = "/results";
      return;
    }

    statusEl.textContent = "Unexpected response from the matching service.";
  } catch (error) {
    statusEl.textContent = "Unable to connect to the matching service.";
  } finally {
    buttonEl.disabled = false;
    buttonEl.textContent = "Generate Matches";
  }
}

function resetDraftState() {
  clearDraft();
  form.reset();
  followupShell.classList.add("is-hidden");
  followupQuestion.textContent = "";
  statusEl.textContent = "Draft cleared for this browser.";
  updateSpecificityMeter();
}

const draft = loadDraft();
applyDraft(draft);
updateSpecificityMeter();

form.addEventListener("input", persistDraft);
form.addEventListener("change", persistDraft);
form.addEventListener("submit", submitForm);
document.getElementById("clear-draft-button").addEventListener("click", resetDraftState);
