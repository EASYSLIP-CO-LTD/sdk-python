"""Check that the complete response and request examples are tracked and unchanged."""

import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
expected = json.loads((root / "fixtures.sha256.json").read_text())
actual = {
    p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted((root / "fixtures").rglob("*"))
    if p.is_file()
}
tracked = set(
    subprocess.check_output(["git", "ls-files", "fixtures"], cwd=root, text=True).splitlines()
)
assert len(actual) == 127, len(actual)
assert actual == expected, "Fixture content changed"
assert tracked == set(actual), "Fixture files are missing from Git"
print("127 tracked fixtures: SHA-256 PASS")
