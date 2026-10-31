#!/usr/bin/env python3
"""Bind an experimental app to actual source without replaying old acceptance.

Shared build plumbing only. No gameplay, product approval or scoring logic.
"""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
app = Path(sys.argv[1]).resolve()
assert app.is_relative_to(root / "native-probe/build"), "App output must stay in isolated workspace"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources = [p for folder in ("SimCore", "Persistence", "App", "Data/Campaign", "Data/Rules")
           for p in sorted((root / "native-probe" / folder).rglob("*")) if p.is_file()]
assert not any(p.suffix in {".js", ".html", ".mjs"} for p in app.rglob("*")), "Native product required"
manifest = {
    "formatVersion": 1,
    "experimental": True,
    "acceptanceInferred": False,
    "builtAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "toolchain": subprocess.check_output(["swiftc", "--version"], text=True),
    "sourceSha256": {str(p.relative_to(root)): sha(p) for p in sources},
    "packagedResourceSha256": {str(p.relative_to(app / "Contents/Resources")): sha(p)
                              for p in sorted((app / "Contents/Resources").rglob("*"))
                              if p.is_file() and p.name != "BuildManifest.json"},
    "productPath": "Swift native core and AppKit/SpriteKit/Metal application",
    "limitation": "Build/source identity only; not proof of live GUI, solvability or new capability correctness."
}
(app / "Contents/Resources/BuildManifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
