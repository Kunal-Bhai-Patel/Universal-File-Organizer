"""Small, safe tests for Universal File Organizer.

Every test uses a new temporary directory.  No real Downloads folder or
personal folder is used.
"""

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import file_organizer


class FileOrganizerTests(unittest.TestCase):
    """Test the most important safety and organization rules."""

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.target = Path(self.temp_directory.name)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_category_classification_is_case_insensitive(self):
        self.assertEqual(file_organizer.category_for_file(Path("PHOTO.JPG")), "Photos")
        self.assertEqual(file_organizer.category_for_file(Path("notes.PdF")), "PDFs")
        self.assertIsNone(file_organizer.category_for_file(Path("data.unknown")))

    def test_libreoffice_extensions_are_documents(self):
        for extension in (".ods", ".odp", ".odg", ".odf", ".odb", ".odt"):
            with self.subTest(extension=extension):
                self.assertEqual(
                    file_organizer.category_for_file(Path(f"example{extension.upper()}")),
                    "Documents",
                )

    def test_unknown_extension_goes_to_uncategorised(self):
        unknown = self.target / "application.xyz"
        unknown.write_bytes(b"dummy file")

        result = file_organizer.scan_folder(self.target)

        self.assertEqual(result.plans[0].category, "UnCategorised")
        self.assertEqual(result.plans[0].destination.name, "application.xyz")

    def test_file_without_extension_goes_to_uncategorised(self):
        unknown = self.target / "file_without_extension"
        unknown.write_bytes(b"dummy file")

        result = file_organizer.scan_folder(self.target)

        self.assertEqual(result.plans[0].category, "UnCategorised")

    def test_uncategorised_folder_is_protected(self):
        (self.target / "UnCategorised").mkdir()

        result = file_organizer.scan_folder(self.target)

        self.assertEqual(result.plans, [])
        self.assertEqual(result.skipped[0][0].name, "UnCategorised")

    def test_duplicate_file_gets_numbered_name(self):
        photos = self.target / "Photos"
        photos.mkdir()
        (photos / "photo.jpg").write_text("old", encoding="utf-8")
        incoming = self.target / "photo.jpg"
        incoming.write_text("new", encoding="utf-8")

        result = file_organizer.scan_folder(self.target)

        self.assertEqual(result.plans[0].destination.name, "photo (1).jpg")

    def test_duplicate_uncategorised_file_is_moved_without_overwriting(self):
        uncategorised = self.target / "UnCategorised"
        uncategorised.mkdir()
        existing = uncategorised / "unknown.xyz"
        existing.write_text("old", encoding="utf-8")
        incoming = self.target / "unknown.xyz"
        incoming.write_text("new", encoding="utf-8")

        result = file_organizer.scan_folder(self.target)
        file_organizer.apply_plans(self.target, result.plans)

        self.assertEqual(existing.read_text(encoding="utf-8"), "old")
        self.assertEqual(
            (uncategorised / "unknown (1).xyz").read_text(encoding="utf-8"),
            "new",
        )

    def test_duplicate_folder_gets_numbered_name(self):
        folders = self.target / "Folders"
        folders.mkdir()
        (folders / "Project").mkdir()
        (self.target / "Project").mkdir()

        result = file_organizer.scan_folder(self.target)

        self.assertEqual(result.plans[0].destination.name, "Project (1)")

    def test_ordinary_folder_is_planned_for_folders_category(self):
        ordinary = self.target / "Project files"
        ordinary.mkdir()

        result = file_organizer.scan_folder(self.target)

        self.assertEqual(result.plans[0].category, "Folders")
        self.assertEqual(result.plans[0].destination.name, "Project files")

    def test_existing_category_folders_are_protected(self):
        (self.target / "Photos").mkdir()
        (self.target / "Folders").mkdir()

        result = file_organizer.scan_folder(self.target)

        self.assertEqual(result.plans, [])
        skipped_names = {path.name for path, _reason in result.skipped}
        self.assertEqual(skipped_names, {"Photos", "Folders"})

    def test_preview_does_not_create_category_folders(self):
        (self.target / "picture.png").write_bytes(b"image")

        result = file_organizer.scan_folder(self.target)
        output = io.StringIO()
        with redirect_stdout(output):
            file_organizer.print_preview(self.target, result)

        self.assertFalse((self.target / "Photos").exists())
        self.assertTrue((self.target / "picture.png").exists())
        self.assertIn("Photos: 1 item(s)", output.getvalue())

    def test_symbolic_links_are_skipped(self):
        real_file = self.target / "real.txt"
        real_file.write_text("real", encoding="utf-8")
        link = self.target / "link.txt"
        try:
            link.symlink_to(real_file)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symbolic links are unavailable: {error}")

        result = file_organizer.scan_folder(self.target)

        skipped_names = {path.name for path, _reason in result.skipped}
        self.assertIn("link.txt", skipped_names)

    def test_windows_junctions_are_skipped(self):
        if os.name != "nt":
            self.skipTest("Windows junctions are only available on Windows")

        real_folder = self.target / "real_folder"
        real_folder.mkdir()
        junction = self.target / "junction_folder"
        command = ["cmd", "/c", "mklink", "/J", str(junction), str(real_folder)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            self.skipTest(f"junction creation was unavailable: {completed.stderr}")

        result = file_organizer.scan_folder(self.target)

        skipped_names = {path.name for path, _reason in result.skipped}
        self.assertIn("junction_folder", skipped_names)


if __name__ == "__main__":
    unittest.main()
