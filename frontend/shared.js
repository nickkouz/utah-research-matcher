export const STORAGE_KEYS = {
  formDraft: "urm.formDraft.v1",
  lastResults: "urm.lastResults.v1",
  savedFaculty: "urm.savedFaculty.v1",
};

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function readStorage(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (error) {
    return fallback;
  }
}

export function writeStorage(key, value) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

export function loadDraft() {
  return readStorage(STORAGE_KEYS.formDraft, null);
}

export function saveDraft(draft) {
  writeStorage(STORAGE_KEYS.formDraft, {
    ...draft,
    updatedAt: new Date().toISOString(),
  });
}

export function clearDraft() {
  window.localStorage.removeItem(STORAGE_KEYS.formDraft);
}

export function loadLastResults() {
  return readStorage(STORAGE_KEYS.lastResults, null);
}

export function saveLastResults(results) {
  writeStorage(STORAGE_KEYS.lastResults, {
    ...results,
    savedAt: new Date().toISOString(),
  });
}

export function loadSavedFaculty() {
  return readStorage(STORAGE_KEYS.savedFaculty, []);
}

export function toggleSavedFaculty(facultyId) {
  const saved = new Set(loadSavedFaculty());
  if (saved.has(facultyId)) {
    saved.delete(facultyId);
  } else {
    saved.add(facultyId);
  }
  const list = [...saved];
  writeStorage(STORAGE_KEYS.savedFaculty, list);
  return list;
}

export function isFacultySaved(facultyId) {
  return loadSavedFaculty().includes(facultyId);
}

export function formatRelativeDate(isoString) {
  if (!isoString) {
    return "Not saved yet";
  }
  const value = new Date(isoString);
  if (Number.isNaN(value.getTime())) {
    return "Recently updated";
  }
  return value.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function facultyProfileLink(faculty) {
  return faculty.profile_url || "#";
}
