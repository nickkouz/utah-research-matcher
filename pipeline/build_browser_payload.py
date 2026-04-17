from __future__ import annotations

from pathlib import Path

from pipeline.faculty_data import FACULTY_BROWSER_PATH, resolve_faculty_dataset_path, write_faculty_browser_payload


def run(
    source_path: Path | None = None,
    destination_path: Path = FACULTY_BROWSER_PATH,
) -> Path:
    return write_faculty_browser_payload(
        source_path or resolve_faculty_dataset_path(),
        destination_path,
    )


if __name__ == "__main__":
    output = run()
    print(output)
