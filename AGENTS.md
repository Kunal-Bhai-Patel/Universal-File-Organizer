# Repository guide

Universal File Organizer is a beginner-oriented Windows-friendly Python program. Its runtime uses only the standard library.

- `file_organizer.py` contains folder selection, classification, preview, and move logic. Keep its explanations and code approachable for beginners.
- `app_entry.py` is the packaged executable entry point; `build_exe.ps1` builds it with separately installed PyInstaller.
- `test_file_organizer.py` contains `unittest` tests using temporary directories. Run `py -m unittest -v` from the repository root (or use the selected Python interpreter with `-m unittest -v`).
- `README.md` documents behavior and setup; update it when user-visible behavior changes. `build/` and `dist/` contain generated build output.

Preserve the organizer's safety rules: scan only immediate children, preview before moving, require explicit confirmation, avoid overwriting existing items, and skip links, junctions, temporary downloads, protected category folders, and the running script. Test changes using temporary directories, never personal folders. Keep category definitions, protected-folder behavior, preview output, tests, and documentation consistent when changing categories.
