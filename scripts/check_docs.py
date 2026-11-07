"""Check relative Markdown links and required portable skill metadata."""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
errors = []
files = [root / "README.md", *root.glob("docs/*.md"), *root.glob("skills/*/SKILL.md")]
for path in files:
    text = path.read_text(encoding="utf-8")
    for link in re.findall(r"\]\(([^)]+)\)", text):
        if "://" in link or link.startswith("#"):
            continue
        if not (path.parent / link.split("#")[0]).exists():
            errors.append(f"{path.relative_to(root)}: missing {link}")
    if path.name == "SKILL.md":
        if not re.match(r"^---\nname: [a-z0-9-]+\ndescription: .+\n---\n", text):
            errors.append(f"{path}: invalid skill metadata")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Checked {len(files)} documentation files")
