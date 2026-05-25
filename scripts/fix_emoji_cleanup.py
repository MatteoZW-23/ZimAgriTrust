"""
Post-emoji-removal cleanup:
1. Fix leading spaces in label strings: label: ' Foo' -> label: 'Foo'
2. Fix empty emoji properties with FA icon classes
3. Remove any remaining stray emoji characters (extended ranges)
"""
import pathlib
import re

ADMIN_DIR = pathlib.Path(r"c:\Users\MJ\Desktop\Agric\apps\admin-dashboard\src")
PUBLIC_DIR = pathlib.Path(r"c:\Users\MJ\Desktop\Agric\apps\public-website\src")


def fix_file(filepath: pathlib.Path):
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return False

    original = content

    # Remove remaining emoji outside BMP: skin tones, symbols, etc.
    content = re.sub(r'[\U00010000-\U0010FFFF]', '', content)

    # Fix label: ' Text' -> label: 'Text'  (single or double quotes)
    content = re.sub(r"""(label:\s*['"])\s+""", r'\1', content)

    # Fix toast/showToast strings with leading space after quote
    content = re.sub(r"""(showToast\(\s*['"`])\s+""", r'\1', content)

    # Fix heading/text strings: >' Text' -> >'Text'
    content = re.sub(r"""(>\s*['"]?)\s{2,}""", r'\1', content)

    # Fix generic quoted string: '  Text -> 'Text (for JSX text content)
    # Only if it starts with whitespace right after the quote
    content = re.sub(r"""(['"])\s{2,}([A-Z])""", r'\1\2', content)

    # Fix empty emoji properties in DriverVerificationPanel
    if "emoji: ''" in content:
        emoji_map = {
            "Driver's License": "fa-id-card",
            "Vehicle Registration": "fa-file-lines",
            "Vehicle Photo": "fa-car",
            "Profile Photo": "fa-user",
            "Live Selfie": "fa-camera",
        }
        for label_part, icon in emoji_map.items():
            content = content.replace(
                f"label: '{label_part}', emoji: ''",
                f"label: '{label_part}', icon: '{icon}'"
            )
            content = content.replace(
                f'label: "{label_part}", emoji: \'\'',
                f'label: "{label_part}", icon: \'{icon}\''
            )
        # Catch remaining empty emoji properties
        content = content.replace("emoji: ''", "icon: 'fa-file'")
        content = content.replace('emoji: ""', 'icon: "fa-file"')

    # Fix double spaces left from emoji removal
    content = re.sub(r'  +', ' ', content)

    if content != original:
        filepath.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    changed = 0
    for directory in [ADMIN_DIR, PUBLIC_DIR]:
        for f in directory.rglob("*.tsx"):
            if fix_file(f):
                print(f"  Cleaned: {f.relative_to(directory.parent.parent.parent)}")
                changed += 1

    print(f"\nDone. {changed} file(s) cleaned.")


if __name__ == "__main__":
    main()
