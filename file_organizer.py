"""Universal File Organizer.

This program organizes files in one folder only.  It never scans inside
subfolders, and it asks for confirmation before it changes anything.
"""

# Import os so we can compare paths in a way that works on Windows.
import os

# Import shutil.  shutil contains the function used to move files and folders.
import shutil

# Import tkinter only when the graphical folder picker is needed.
import tkinter as tk
from tkinter import filedialog

# Import dataclass to make small, readable objects for planned moves.
from dataclasses import dataclass

# Import Path.  Path gives us simple tools for working with files and folders.
from pathlib import Path


# =====================================================
# USER SETTINGS — CHANGE THESE VALUES
# =====================================================

TARGET_FOLDER = ""  # Enter a folder path here.

# Example:
# TARGET_FOLDER = r"C:\Users\username\Downloads"


# These are the file categories that the organizer can use.
# The dictionary key is the folder name, and the value is a set of extensions.
CATEGORY_EXTENSIONS = {
    "Photos": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic", ".tiff", ".svg"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
    "Audios": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus"},
    "Documents": {
        ".txt", ".doc", ".docx", ".rtf", ".odt", ".ods", ".odp", ".odg", ".odf", ".odb",
        ".csv", ".xls", ".xlsx", ".ppt", ".pptx",
    },
    "PDFs": {".pdf"},
    "Zips": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz"},
}

# These extensions usually mean that a download is still being created.
TEMPORARY_EXTENSIONS = {".crdownload", ".part", ".tmp"}

# The last category is for ordinary folders, rather than files.
FOLDER_CATEGORY = "Folders"

# Unknown regular files go into this folder.  The program only uses their
# names and extensions; it never opens, executes, or inspects their contents.
UNCATEGORISED_CATEGORY = "UnCategorised"


@dataclass
class MovePlan:
    """Describe one item that could be moved.

    A dataclass is a simple container for related values.  Here it keeps the
    original item, its category, and the planned destination together.
    """

    source: Path
    category: str
    destination: Path


@dataclass
class ScanResult:
    """Store everything discovered during the preview scan."""

    plans: list[MovePlan]
    skipped: list[tuple[Path, str]]
    unknown_files: list[Path]
    inaccessible_items: list[tuple[Path, str]]


def is_link_or_junction(path: Path) -> bool:
    """Return True for a symbolic link or Windows junction.

    Links can point outside the selected folder.  Skipping them prevents the
    organizer from accidentally affecting files somewhere else.
    """

    if path.is_symlink():
        return True

    # Path.is_junction exists in Python 3.12 and later.  getattr also lets
    # this educational program run on older Python versions.
    junction_checker = getattr(path, "is_junction", None)
    return bool(junction_checker and junction_checker())


def category_for_file(path: Path) -> str | None:
    """Return the category for a file, or None when the extension is unknown."""

    # suffix is the part after the final dot.  casefold makes matching
    # case-insensitive, so PHOTO.JPG and photo.jpg behave the same way.
    extension = path.suffix.casefold()

    for category, extensions in CATEGORY_EXTENSIONS.items():
        if extension in extensions:
            return category

    return None


def path_key(path: Path) -> str:
    """Create a case-insensitive key for comparing Windows-style names."""

    return os.path.normcase(str(path.absolute()))


def item_exists(path: Path) -> bool:
    """Return True when a path is occupied, including by a broken link."""

    return path.exists() or path.is_symlink()


def available_destination(desired: Path, reserved: set[str]) -> Path:
    """Find a destination that does not overwrite an existing item.

    If ``report.pdf`` is occupied, this function tries ``report (1).pdf``,
    then ``report (2).pdf``, and so on.  Folders use the same idea without a
    file extension.
    """

    candidate = desired
    counter = 1

    while item_exists(candidate) or path_key(candidate) in reserved:
        if desired.suffix:
            candidate = desired.with_name(
                f"{desired.stem} ({counter}){desired.suffix}"
            )
        else:
            candidate = desired.with_name(f"{desired.name} ({counter})")
        counter += 1

    reserved.add(path_key(candidate))
    return candidate


def existing_category_folder(target: Path, category: str) -> Path:
    """Return an existing category folder, or its future path.

    Windows compares names without caring about upper/lowercase.  Looking for
    an existing folder this way also avoids suggesting a second folder named
    ``photos`` when ``Photos`` already exists.
    """

    wanted_name = category.casefold()
    try:
        for child in target.iterdir():
            if (
                child.is_dir()
                and not is_link_or_junction(child)
                and child.name.casefold() == wanted_name
            ):
                return child
    except OSError:
        pass

    return target / category


def is_category_folder(path: Path) -> bool:
    """Return True when a folder name is one of the protected categories."""

    protected_names = {name.casefold() for name in CATEGORY_EXTENSIONS}
    protected_names.add(FOLDER_CATEGORY.casefold())
    protected_names.add(UNCATEGORISED_CATEGORY.casefold())
    return path.name.casefold() in protected_names


def scan_folder(target: Path) -> ScanResult:
    """Scan only the immediate children of target and create a preview plan."""

    plans: list[MovePlan] = []
    skipped: list[tuple[Path, str]] = []
    unknown_files: list[Path] = []
    inaccessible_items: list[tuple[Path, str]] = []
    reserved_destinations: set[str] = set()

    # Resolve the script path once so the script itself is never moved.
    script_path = Path(__file__).resolve()

    try:
        children = list(target.iterdir())
    except OSError as error:
        inaccessible_items.append((target, str(error)))
        return ScanResult(plans, skipped, unknown_files, inaccessible_items)

    for item in children:
        # This loop examines one immediate child at a time.  It does not call
        # rglob or walk, so it never recursively enters subfolders.
        try:
            if is_link_or_junction(item):
                skipped.append((item, "symbolic link or junction"))
                continue

            if item.resolve() == script_path:
                skipped.append((item, "the running Python script"))
                continue

            if item.is_dir():
                if item.resolve() == script_path.parent:
                    skipped.append((item, "the folder containing this script"))
                elif is_category_folder(item):
                    skipped.append((item, "protected category folder"))
                else:
                    destination_folder = existing_category_folder(target, FOLDER_CATEGORY)
                    destination = available_destination(
                        destination_folder / item.name, reserved_destinations
                    )
                    plans.append(MovePlan(item, FOLDER_CATEGORY, destination))
                continue

            if not item.is_file():
                skipped.append((item, "not an ordinary file or folder"))
                continue

            if item.suffix.casefold() in TEMPORARY_EXTENSIONS:
                skipped.append((item, "temporary or incomplete download"))
                continue

            category = category_for_file(item)
            if category is None:
                # An unsupported extension is simply a file type that is not
                # in CATEGORY_EXTENSIONS.  We do not open the file.  We only
                # place its name in the UnCategorised destination folder.
                category = UNCATEGORISED_CATEGORY
                unknown_files.append(item)

            destination_folder = existing_category_folder(target, category)
            destination = available_destination(
                destination_folder / item.name, reserved_destinations
            )
            plans.append(MovePlan(item, category, destination))
        except OSError as error:
            # One troublesome item should not stop the rest of the preview.
            inaccessible_items.append((item, str(error)))

    return ScanResult(plans, skipped, unknown_files, inaccessible_items)


def print_preview(target: Path, result: ScanResult) -> None:
    """Print the planned moves and skipped items in beginner-friendly text."""

    print("\n========================================")
    print("       UNIVERSAL FILE ORGANIZER")
    print("========================================")
    print(f"\nSelected folder:\n{target}")

    file_count = sum(plan.category != FOLDER_CATEGORY for plan in result.plans)
    folder_count = sum(plan.category == FOLDER_CATEGORY for plan in result.plans)
    print(f"\nFiles found: {file_count}")
    print(f"Folders found: {folder_count}")
    print("\nPlanned organization:")

    for category in [*CATEGORY_EXTENSIONS, FOLDER_CATEGORY, UNCATEGORISED_CATEGORY]:
        category_plans = [plan for plan in result.plans if plan.category == category]
        print(f"{category}: {len(category_plans)} item(s)")
        for plan in category_plans:
            if plan.source.name != plan.destination.name:
                print(f"  {plan.source} -> {plan.destination} (duplicate adjustment)")
            else:
                print(f"  {plan.source} -> {plan.destination}")

    print(f"\nUnsupported files going to {UNCATEGORISED_CATEGORY}: {len(result.unknown_files)}")
    for item in result.unknown_files:
        print(f"  {item.name}")

    print(f"Skipped items: {len(result.skipped)}")
    for item, reason in result.skipped:
        print(f"  {item.name} ({reason})")

    if result.inaccessible_items:
        print("\nItems that could not be inspected:")
        for item, error in result.inaccessible_items:
            print(f"  {item}: {error}")


def apply_plans(target: Path, plans: list[MovePlan]) -> None:
    """Create needed category folders and carry out planned moves."""

    created_categories: set[str] = set()

    for plan in plans:
        try:
            # Create the destination folder only after the user confirms.
            destination_folder = existing_category_folder(target, plan.category)
            category_key = path_key(destination_folder)
            if category_key not in created_categories:
                destination_folder.mkdir(parents=False, exist_ok=True)
                created_categories.add(category_key)

            # The preview may be old, so choose a fresh safe name right before
            # moving.  This protects against a new file appearing meanwhile.
            destination = available_destination(
                destination_folder / plan.source.name, set()
            )
            shutil.move(str(plan.source), str(destination))
            print(f"Moved: {plan.source.name} -> {destination}")
        except (OSError, shutil.Error) as error:
            print(f"Could not move {plan.source}: {error}")


def choose_target_folder() -> Path | None:
    """Use the manual setting or open the Windows folder picker."""

    if TARGET_FOLDER.strip():
        return Path(TARGET_FOLDER).expanduser()

    try:
        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askdirectory(title="Choose a folder to organize")
        root.destroy()
    except tk.TclError as error:
        print(f"The folder picker could not open: {error}")
        return None

    if not selected:
        print("No folder was selected. Nothing was changed.")
        return None

    return Path(selected)


def main() -> None:
    """Run the safe preview, confirmation, and organization workflow."""

    target = choose_target_folder()
    if target is None:
        return

    try:
        if not target.exists() or not target.is_dir():
            print(f"This is not an accessible folder: {target}")
            return
        if is_link_or_junction(target):
            print("The selected folder is a symbolic link or junction. Nothing was changed.")
            return

        result = scan_folder(target)
        print_preview(target, result)

        if not result.plans:
            print("\nThere are no items to organize. Nothing was changed.")
            return

        answer = input("\nDo you want to organize this folder? [Y] Yes / [N] No: ")
        if answer.strip().casefold() != "y":
            print("No changes were made.")
            return

        apply_plans(target, result.plans)
        print("\nFinished.")
    except (OSError, ValueError) as error:
        print(f"The organizer stopped safely because of an error: {error}")


if __name__ == "__main__":
    main()
