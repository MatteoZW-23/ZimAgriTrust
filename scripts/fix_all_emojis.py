"""
Replace all emoji characters in admin-dashboard and public-website TSX files
with Font Awesome icon markup or clean text.
"""
import pathlib
import re

ADMIN_DIR = pathlib.Path(r"c:\Users\MJ\Desktop\Agric\apps\admin-dashboard\src")
PUBLIC_DIR = pathlib.Path(r"c:\Users\MJ\Desktop\Agric\apps\public-website\src")

# Emoji -> text/icon replacements for string contexts (labels, toasts, button text)
EMOJI_TEXT_MAP = {
    "\u2705": "",      # white heavy check mark
    "\u274c": "",      # cross mark
    "\U0001f6ab": "",  # no entry sign
    "\u26a0\ufe0f": "", # warning sign
    "\u26a0": "",      # warning sign (no variant)
    "\U0001faa8": "",  # ID card emoji
    "\U0001f4ca": "",  # bar chart
    "\U0001f504": "",  # counterclockwise arrows
    "\U0001f5d1\ufe0f": "", # wastebasket
    "\U0001f5d1": "",  # wastebasket
    "\U0001f451": "",  # crown
    "\U0001f510": "",  # closed lock with key
    "\U0001f4f6": "",  # antenna bars
    "\U0001f50b": "",  # battery
    "\U0001f69a": "",  # delivery truck
    "\U0001f4f8": "",  # camera with flash
    "\U0001f933": "",  # selfie
    "\U0001f4ed": "",  # mailbox (open, no mail)
    "\U0001f4cb": "",  # clipboard
    "\u23f3": "",      # hourglass not done
    "\u2713": "",      # check mark (thin)
    "\u2716": "",      # heavy multiplication x
    "\u2715": "",      # multiplication x
    "\u2714": "",      # heavy check mark (thin)
}

def clean_emojis_in_string(text: str) -> str:
    """Remove known emojis from a string and clean up leftover whitespace."""
    for emoji, replacement in EMOJI_TEXT_MAP.items():
        text = text.replace(emoji, replacement)
    # Also remove any remaining emoji-like characters in common Unicode ranges
    # (supplementary multilingual plane, emoticons, etc.)
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
    text = re.sub(r'[\u2600-\u27BF]', '', text)
    # Clean double spaces left behind
    text = re.sub(r'  +', ' ', text)
    # Clean leading space after quote
    text = re.sub(r"(['\"])\\s+", r"\1", text)
    return text


def process_file(filepath: pathlib.Path):
    """Process a single TSX file to remove emojis."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return False

    original = content

    # Remove emoji characters globally
    for emoji, replacement in EMOJI_TEXT_MAP.items():
        content = content.replace(emoji, replacement)

    # Remove any remaining common emoji characters
    content = re.sub(r'[\U0001F300-\U0001F9FF]', '', content)
    content = re.sub(r'[\u2600-\u27BF]', '', content)

    # Clean up double spaces left behind
    content = re.sub(r'  +', ' ', content)

    if content != original:
        filepath.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    changed = 0
    for directory in [ADMIN_DIR, PUBLIC_DIR]:
        for f in directory.rglob("*.tsx"):
            if process_file(f):
                print(f"  Fixed: {f.relative_to(directory.parent.parent.parent)}")
                changed += 1

    print(f"\nDone. {changed} file(s) updated.")


if __name__ == "__main__":
    main()
