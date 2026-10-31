#!/usr/bin/env python3
"""Freeze two isolated, unpublished AIM48 experiment packages and product copies.

No network, agent launch, publication, global installation or original product
write. Preparation is deliberately separate from the timed level builds.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "experiments/aim48-paraclones"
OMIT = {"build", "node_modules", ".git", "__pycache__", ".DS_Store"}
PRODUCT_DIRS = ("native-probe", "aim/assets/b2")
PRODUCT_FILES = (
    ".aim/analysis/native-reviewer-core-expected.json",
    ".aim/analysis/campaign-reviewer-playfeel-plan.json",
    ".aim/analysis/gameplay-003/contract.json",
    ".aim/analysis/gameplay-003/current-oracles.json",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def contained_input(root, relative):
    path = root / relative
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Symlink in input path: {relative}")
    return path


def tree_hashes(root):
    hashes = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__"} for part in relative.parts) or path.suffix == ".pyc":
            continue
        contained_input(root, relative)
        if path.is_file():
            hashes[relative.as_posix()] = digest(path)
    return hashes


def copy_git_commit(source, commit, destination):
    """Copy exact tracked committed bytes, never ignored/local checkout files."""
    archive = subprocess.check_output(["git", "-C", str(source), "archive", "--format=tar", commit])
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        for item in stream.getmembers():
            relative = PurePosixPath(item.name)
            if relative.is_absolute() or ".." in relative.parts or str(relative) != item.name.rstrip("/"):
                raise ValueError("Unsafe path in upstream archive.")
            target = destination / item.name
            if item.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif item.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with stream.extractfile(item) as content:
                    target.write_bytes(content.read())
                target.chmod(item.mode & 0o777)
            else:
                raise ValueError("Links and special files are not allowed in upstream package.")


def inventory(root, directories=PRODUCT_DIRS, files=PRODUCT_FILES):
    """Only the explicit current product scope; no private benchmark traversal."""
    result = {}
    for relative in directories:
        base = contained_input(root, relative)
        if not base.is_dir() or base.is_symlink():
            raise ValueError(f"Missing or unsafe input directory: {relative}")
        for path in sorted(base.rglob("*")):
            rel = path.relative_to(root)
            if any(part in OMIT for part in rel.parts):
                continue
            if path.is_symlink():
                raise ValueError(f"Symlink in frozen product: {rel}")
            if path.is_file():
                result[rel.as_posix()] = digest(path)
    for relative in files:
        path = contained_input(root, relative)
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing or unsafe verification input: {relative}")
        result[relative] = digest(path)
    return result


def copy_tree(source, destination):
    for path in source.rglob("*"):
        if ".git" in path.relative_to(source).parts:
            continue
        if path.is_symlink():
            raise ValueError(f"Package contains a symlink: {path}")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))


def prepare(product: Path, sp_source: Path, output: Path):
    product, sp_source, output = product.resolve(), sp_source.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Use a new experiment output directory; never overwrite prior attempts.")
    if output.is_relative_to(product) or output.is_relative_to(sp_source):
        raise ValueError("Experiment output must be outside its inputs.")
    protocol = json.loads((SPEC / "protocol.json").read_text())
    before = inventory(product)
    upstream_commit = subprocess.check_output(
        ["git", "-C", str(sp_source), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(sp_source), "status", "--porcelain"], text=True)
    if dirty.strip():
        raise ValueError("Superpowers source must be a clean pinned checkout.")
    for item in ("LICENSE", "skills/writing-plans/SKILL.md",
                 "skills/subagent-driven-development/SKILL.md", "skills/executing-plans/SKILL.md"):
        if not (sp_source / item).is_file():
            raise ValueError(f"Missing upstream source: {item}")
    package = ROOT / "skills/agile-iteration-method"
    if not package.is_dir():
        raise ValueError("Build the shared public AIM base package first.")
    base_version = json.loads((package / "manifest.json").read_text())["productVersion"]
    if base_version != protocol["baseAimVersion"]:
        raise ValueError("Shared AIM package does not match the frozen base version.")
    if base_version != (ROOT / "VERSION").read_text().strip():
        raise ValueError("Generated package is stale against canonical AIM VERSION.")
    for required in (SPEC / "native/SKILL.md", SPEC / "sp/SKILL.md",
                     SPEC / "native-contract.json", ROOT / "scripts/aim_orchestrate.py",
                     ROOT / "scripts/aim_quality/orchestration.py"):
        if not required.is_file() or required.is_symlink():
            raise ValueError(f"Missing or unsafe candidate input: {required}")
    shared_before = tree_hashes(package)
    overlay_paths = [SPEC / "protocol.json", SPEC / "common-governance.md",
                     SPEC / "native/SKILL.md", SPEC / "sp/SKILL.md", SPEC / "native-contract.json",
                     SPEC / "package-manifest-experiment.py",
                     ROOT / "scripts/aim_orchestrate.py", ROOT / "scripts/aim_quality/orchestration.py"]
    overlay_before = {str(p.relative_to(ROOT)): digest(p) for p in overlay_paths}
    # Historical build.sh asserts the previously accepted gameplay's exact code
    # hashes. Keep it intact and supply a separately named common build route;
    # new experimental source must never forge that old acceptance provenance.
    shared_tools = {
        "native-probe/Verification/package-manifest-experiment.py": (SPEC / "package-manifest-experiment.py").read_bytes(),
        "native-probe/build-experiment.sh": (product / "native-probe/build.sh").read_text().replace(
            "native-probe/Verification/package-manifest.py", "native-probe/Verification/package-manifest-experiment.py").encode(),
    }
    effective = dict(before)
    effective.update({p: hashlib.sha256(raw).hexdigest() for p, raw in shared_tools.items()})
    output.mkdir(parents=True)
    save(output / "protocol.json", protocol)
    save(output / "original-source-manifest.json", before)
    save(output / "source-manifest.json", effective)
    for arm in ("native", "sp"):
        workspace = output / arm
        workspace.mkdir()
        for relative, expected in before.items():
            source = product / relative
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if digest(target) != expected:
                raise ValueError(f"Source changed during snapshot: {relative}")
        for relative, raw in shared_tools.items():
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            target.chmod(0o755)
        copy_tree(package, workspace / "method")
        method = workspace / "method"
        shutil.copy2(SPEC / arm / "SKILL.md", method / "SKILL.md")
        shutil.copy2(SPEC / "common-governance.md", method / "references/experiment-governance.md")
        if arm == "native":
            shutil.copy2(SPEC / "native-contract.json", method / "references/native-orchestration-contract.json")
        save(method / "brief.json", protocol["brief"])
        # Keep shared distribution's own VERSION accurate; candidate identity is
        # separate provenance rather than a forged stable release manifest.
        metadata = {"candidateVersion": protocol["candidateVersions"][arm],
                    "sharedBaseVersion": base_version,
                    "arm": arm, "upstreamCommit": upstream_commit if arm == "sp" else None,
                    "publication": False}
        save(method / "candidate.json", metadata)
        if arm == "native":
            shutil.copy2(ROOT / "scripts/aim_orchestrate.py", method / "scripts/aim_orchestrate.py")
            shutil.copy2(ROOT / "scripts/aim_quality/orchestration.py", method / "scripts/aim_quality/orchestration.py")
        else:
            copy_git_commit(sp_source, upstream_commit, method / "vendor/superpowers")
        (workspace / "AGENTS.md").write_text(
            "# Isolated AIM48 ParaClones experiment\n\n"
            "The human explicitly selected this experimental method instead of the ordinary pinned consumer method. "
            "Read method/SKILL.md and method/brief.json. Use only this arm's method and product; "
            "do not inspect siblings, old benchmarks, external consumer histories or global learning registries. "
            "The actual product is native-probe, not the historical web implementation. "
            "Build with native-probe/build-experiment.sh; the historical build.sh intentionally binds old acceptance hashes. "
            "Preserve original movement/replay/save invariants. All writes stay in this workspace. "
            "Use fresh --profile-root under this workspace for every app run. "
            "The shared current product snapshot was verified before timing; new capability code is part of your timed work.\n")
        (workspace / ".gitignore").write_text("native-probe/build/\n.aim/\noutput/\n*.pyc\n__pycache__/\n")
        subprocess.run(["git", "init", "-q", str(workspace)], check=True)
        subprocess.run(["git", "-C", str(workspace), "config", "user.name", "AIM Experiment"], check=True)
        subprocess.run(["git", "-C", str(workspace), "config", "user.email", "experiment@localhost"], check=True)
        subprocess.run(["git", "-C", str(workspace), "add", "."], check=True)
        # These are explicit shared verification fixtures, not inherited product
        # runtime or private history. Freeze them despite transient .aim ignores.
        subprocess.run(["git", "-C", str(workspace), "add", "-f", *PRODUCT_FILES], check=True)
        subprocess.run(["git", "-C", str(workspace), "commit", "-q", "-m", "Frozen isolated experiment input"], check=True)
        if inventory(workspace) != effective:
            raise ValueError("Product copies differ before either candidate starts.")
        for relative, expected in shared_before.items():
            if relative != "SKILL.md" and digest(method / relative) != expected:
                raise ValueError(f"Shared AIM source differs in {arm}: {relative}")
    if inventory(product) != before:
        raise ValueError("Original product changed during preparation; do not start either arm.")
    if tree_hashes(package) != shared_before or any(digest(ROOT / p) != h for p, h in overlay_before.items()):
        raise ValueError("Method source changed during preparation; do not start either arm.")
    save(output / "shared-aim-manifest.json", shared_before)
    save(output / "overlay-source-manifest.json", overlay_before)
    manifest = {"status": "prepared_not_started", "productFiles": len(effective),
                "sharedBuildTooling": list(shared_tools),
                "productManifestSha256": digest(output / "source-manifest.json"),
                "protocolSha256": digest(output / "protocol.json"),
                "sharedAimManifestSha256": digest(output / "shared-aim-manifest.json"),
                "overlayManifestSha256": digest(output / "overlay-source-manifest.json"),
                "superpowersCommit": upstream_commit,
                "superpowersLicenseSha256": digest(sp_source / "LICENSE"),
                "arms": {}}
    for arm in ("native", "sp"):
        method = output / arm / "method"
        hashes = {str(p.relative_to(method)): digest(p) for p in sorted(method.rglob("*")) if p.is_file()}
        save(output / f"{arm}-method-manifest.json", hashes)
        manifest["arms"][arm] = {"methodManifestSha256": digest(output / f"{arm}-method-manifest.json")}
    save(output / "preparation.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", type=Path, required=True)
    parser.add_argument("--superpowers-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.product, args.superpowers_source, args.output), indent=2))


if __name__ == "__main__":
    main()
