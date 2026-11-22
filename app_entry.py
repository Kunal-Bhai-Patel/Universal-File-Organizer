"""Small entry point used only by the standalone Windows executable.

The normal ``file_organizer.py`` command-line program is intentionally left
unchanged. This wrapper adds one helpful behavior for double-click users: the
console stays open until they press Enter, so the result or an error can be read.
"""

import file_organizer


def main() -> None:
    """Run the organizer and keep the packaged console readable."""

    try:
        file_organizer.main()
    except Exception as error:  # Keep unexpected EXE errors visible to users.
        print(f"The organizer stopped safely because of an unexpected error: {error}")
    finally:
        try:
            input("\nPress Enter to close this window...")
        except EOFError:
            # This only happens when the EXE is launched without an input
            # stream. In that unusual case there is nothing to wait for.
            pass


if __name__ == "__main__":
    main()
