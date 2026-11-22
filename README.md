# Universal File Organizer

Universal File Organizer is a portable, safety-first Windows utility built by Kunal Bhai Patel to sort cluttered folders—such as a messy Downloads directory—into organized category folders. Pick a folder, review the proposed moves in the console, and type **Y** to apply them. The application runs entirely on your local machine with zero telemetry and requires no Python installation.

---

## Download & Requirements

| Property | Details |
| --- | --- |
| **Download** | [UniversalFileOrganizer.exe (v1.0.0)](https://github.com/Kunal-Bhai-Patel/Universal-File-Organizer/releases/download/v1.0.0/UniversalFileOrganizer.exe) |
| **Platform** | Windows 10 / Windows 11 (64-bit) |
| **Binary Size** | 11,097,084 bytes (~10.6 MB) |
| **SHA-256 Checksum** | `888a3c5b639558bcf668f16c2a5a61658962fd0208131dc5ac44e1ca76cea2ad` |
| **Authenticode Status** | `NotSigned` (Local developer build) |

> **Note on Windows SmartScreen & Antivirus**: Because this portable executable is built directly from Python using PyInstaller and is unsigned, Windows Defender or SmartScreen may show an unrecognized publisher prompt on first launch. You can verify the SHA-256 hash against the release notes, inspect the full Python source code in this repository, scan the executable with your standard antivirus software, and select **More info → Run anyway** if you trust the file.

---

## 5-Step Visitor Walkthrough

1. **Download**: Click **Download for Windows (64-bit)** to obtain `UniversalFileOrganizer.exe` from the latest GitHub Release. If your browser saves it to your `Downloads` folder, move the executable to your `Desktop` or a dedicated utilities directory outside the folder you intend to organize.
2. **Launch & Choose Folder**: Double-click `UniversalFileOrganizer.exe` in File Explorer. In the native **Choose a folder to organize** dialog, navigate to a sample folder and click **Select Folder**.
3. **Review the Console Preview**: The terminal displays the selected folder path, file and folder counts, item counts per category, planned source and destination paths, duplicate adjustments, and skipped items. If you cancel the folder picker or if the directory is empty, the program exits safely without a confirmation prompt.
4. **Confirm or Cancel**: At the prompt:
   ```text
   Do you want to organize this folder? [Y] Yes / [N] No:
   ```
   Type **Y** (or `y`) and press **Enter** to move the listed items. Type **N** and press **Enter** to cancel immediately. Nothing is modified when cancelled.
5. **Review Results**: The console reports each moved item and any errors encountered during the move, then displays `Press Enter to close this window...`. Open the folder in File Explorer to verify your neatly sorted categories.

---

## Walkthrough Visuals

### 1. Folder Selection Dialog
In the native Windows dialog, select your target folder and click **Select Folder**:
```text
+-----------------------------------------------------------------------+
| Choose a folder to organize                                   [_][#][X]|
+-----------------------------------------------------------------------+
|  Folder: [ C:\SampleFolder                                          ] |
|                                                                       |
|  [Select Folder]   [Cancel]                                           |
+-----------------------------------------------------------------------+
```

### 2. Console Preview
The console shows exact counts, destinations, duplicate adjustments, and skipped items before anything moves:
```text
========================================
       UNIVERSAL FILE ORGANIZER
========================================

Selected folder:
C:\SampleFolder

Files found: 5
Folders found: 1

Planned organization:
Photos: 1 item(s)
  photo.jpg -> Photos\photo.jpg
Videos: 0 item(s)
Audios: 0 item(s)
Documents: 1 item(s)
  notes.odt -> Documents\notes.odt
PDFs: 1 item(s)
  manual.pdf -> PDFs\manual.pdf
Zips: 1 item(s)
  archive.zip -> Zips\archive.zip
Folders: 1 item(s)
  ExampleFolder -> Folders\ExampleFolder
UnCategorised: 1 item(s)
  unknown.xyz -> UnCategorised\unknown.xyz

Unsupported files going to UnCategorised: 1
  unknown.xyz

Skipped items: 1
  unfinished.part (temporary or incomplete download)

Do you want to organize this folder? [Y] Yes / [N] No: Y
Moved: photo.jpg -> Photos\photo.jpg
Moved: notes.odt -> Documents\notes.odt
Moved: manual.pdf -> PDFs\manual.pdf
Moved: archive.zip -> Zips\archive.zip
Moved: ExampleFolder -> Folders\ExampleFolder
Moved: unknown.xyz -> UnCategorised\unknown.xyz

Finished.

Press Enter to close this window...
```

### 3. Resulting Organized Folders
In File Explorer, items are grouped into dedicated category directories, while incomplete downloads remain untouched at root:
```text
SampleFolder\
├── Documents\
│   └── notes.odt
├── Folders\
│   └── ExampleFolder\
├── PDFs\
│   └── manual.pdf
├── Photos\
│   └── photo.jpg
├── UnCategorised\
│   └── unknown.xyz
├── Zips\
│   └── archive.zip
└── unfinished.part
```

---

## Implementation & Code Architecture

| File | Responsibility |
| --- | --- |
| `file_organizer.py` | Main behavior. `choose_target_folder()` uses the optional `TARGET_FOLDER` source setting or tkinter's native folder picker. `scan_folder()` plans moves for immediate children using `Path.iterdir()`. `category_for_file()` uses the final suffix and case-insensitive matching. `print_preview()` displays the plan. `main()` checks the confirmation before `apply_plans()` creates category folders and moves items with `shutil.move()`. |
| `app_entry.py` | Packaged entry point. Calls the same organizer and waits for Enter in a `finally` block before closing the console, allowing users to read results and errors. |
| `build_exe.ps1` | Windows PowerShell build. Prefers Python 3.13 via the Windows launcher and can fall back to a `python` command that is at least 3.10. Checks for PyInstaller and bundles the app and tkinter into one console executable using `--onefile --console --clean`, writing to `dist\UniversalFileOrganizer.exe`. Recommend Python 3.13 for building. |
| `test_file_organizer.py` | Standard-library unit tests using temporary folders. Covers classification, LibreOffice files, unknown types, existing category folders, ordinary folders, duplicate names, preview behavior, symbolic links, and a Windows junction test. (13 tests total: 11 passed, 2 skipped due to Windows non-elevated user privilege for symlink/junction creation). |

---

## Category Destinations & Rules

The organizer sorts immediate child items into eight destinations:

| Category Folder | Formats & Types | Description |
| --- | --- | --- |
| `Photos` | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.heic`, `.tiff`, `.svg` | Raster and vector images |
| `Videos` | `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v` | Video containers and clips |
| `Audios` | `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma`, `.opus` | Sound files and music |
| `Documents` | `.txt`, `.doc`, `.docx`, `.rtf`, `.odt`, `.ods`, `.odp`, `.odg`, `.odf`, `.odb`, `.csv`, `.xls`, `.xlsx`, `.ppt`, `.pptx` | Text, spreadsheets, presentations (Office & LibreOffice OpenDocument) |
| `PDFs` | `.pdf` | Portable Document Format files |
| `Zips` | `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz`, `.tgz` | Compressed archives (moved intact) |
| `Folders` | Existing ordinary directories | Subdirectories are moved intact with all their nested contents |
| `UnCategorised` | Unknown extensions and extensionless regular files | Regular files whose extension is not in `CATEGORY_EXTENSIONS` |

### Key Safety Guarantees & Constraints

1. **Non-Recursive Scan**: The tool only scans the immediate top level of the selected folder (`Path.iterdir()`). It never scans inside subfolders or extracts archive files.
2. **Name-Based Classification**: The tool inspects only file paths and extensions using `path.suffix.casefold()`. It never executes, opens, or inspects the binary content of any file.
3. **Skipped Items for Safety**:
   - Immediate symbolic links and Windows directory junctions are skipped.
   - Protected category folders (`Photos`, `Documents`, etc.) are recognized and skipped.
   - Temporary and in-progress downloads ending in `.crdownload`, `.part`, or `.tmp` are skipped.
   - In source mode (`file_organizer.py`), the running script itself is automatically detected and skipped. The distributed executable (`UniversalFileOrganizer.exe`) is not covered by that self-skip; always keep the executable outside the folder being organized.
4. **Duplicate Name Adjustments**: If a destination path is already occupied (e.g. `photo.jpg` already exists in `Photos`), the utility plans the file as `photo (1).jpg`, `photo (2).jpg`, etc. Before each individual move, the utility re-checks available destination names to avoid accidental overwrites.
5. **Preview Safety vs. Individual Moves**: The preview scan creates no folders and moves no files. Confirmation occurs only when the user types `Y` or `y`. Moves are applied individually; if a filesystem error occurs midway (e.g. permission locked on a single file), earlier moves remain in place. There is no automatic undo.
6. **Ordinary Directory Prerequisite**: Destination logic expects category destinations to be ordinary directories. Do not run the tool against target folders containing redirected category paths or junction loops.

---

## Running from Source

You can run the script directly with Python without compiling an executable. Only Python's standard library is used.

### Run in PowerShell
```powershell
py file_organizer.py
```
or
```powershell
python file_organizer.py
```

### Run Unit Tests
```powershell
py -m unittest -v
```

### Headless / Automated Folder Configuration
To bypass the graphical folder picker, set `TARGET_FOLDER` at the top of `file_organizer.py`:
```python
TARGET_FOLDER = r"C:\path\to\Downloads"
```
When `TARGET_FOLDER` is left empty (`""`), the graphical picker (`tkinter.filedialog.askdirectory`) opens automatically.

### Customizing Categories
To add new file types, edit the `CATEGORY_EXTENSIONS` dictionary in `file_organizer.py`. For example, to send Markdown files to `Documents`:
```python
CATEGORY_EXTENSIONS["Documents"].add(".md")
```

---

## Building the Windows Executable

To compile `UniversalFileOrganizer.exe` on Windows 10/11 (64-bit):

1. Install Python 3.13 (recommended).
2. Install PyInstaller:
   ```powershell
   py -3.13 -m pip install pyinstaller
   ```
3. Run the automated build script:
   ```powershell
   .\build_exe.ps1
   ```
The standalone executable will be written to `dist\UniversalFileOrganizer.exe`.

---

## Privacy & Security

- **100% Offline**: Universal File Organizer does not require internet access, does not open network sockets, and never uploads files.
- **Inspectable Source**: All sorting rules, exclusion checks, and file operations are plain standard-library Python code.
