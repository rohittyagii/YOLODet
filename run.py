import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS_FILE = ROOT / "requirements.txt"
STAMP_FILE = VENV_DIR / ".requirements.sha256"
MIN_PYTHON = (3, 10)


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        needed = ".".join(str(x) for x in MIN_PYTHON)
        found = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise RuntimeError(f"Python {needed}+ is required. Current: {found}")


def _run(cmd: list[str]) -> None:
    print("[run.py]", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(ROOT), check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(cmd)}")


def _create_venv_if_missing() -> None:
    py = _venv_python()
    if py.exists():
        return

    print("[run.py] Creating virtual environment in .venv ...")
    _run([sys.executable, "-m", "venv", str(VENV_DIR)])


def _requirements_hash() -> str:
    if not REQUIREMENTS_FILE.exists():
        return ""
    content = REQUIREMENTS_FILE.read_bytes()
    return hashlib.sha256(content).hexdigest()


def _install_requirements_if_needed(force_install: bool = False) -> None:
    py = _venv_python()
    req_hash = _requirements_hash()
    old_hash = STAMP_FILE.read_text(encoding="utf-8").strip() if STAMP_FILE.exists() else ""

    if not force_install and req_hash and old_hash == req_hash:
        print("[run.py] Dependencies already up to date.")
        return

    print("[run.py] Installing/updating dependencies...")
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    if REQUIREMENTS_FILE.exists():
        _run([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])

    STAMP_FILE.write_text(req_hash, encoding="utf-8")


def _normalize_passthrough(passthrough: list[str]) -> list[str]:
    if not passthrough:
        return passthrough

    # Compatibility for accidental invocation like: python run run.py
    first = passthrough[0].lower().strip()
    if first in {"run.py", "./run.py", ".\\run.py"}:
        return passthrough[1:]
    return passthrough


def _build_target_command(mode: str, passthrough: list[str]) -> list[str]:
    py = str(_venv_python())
    if mode == "web":
        return [py, "launch_web_yolo.py", *passthrough]
    if mode == "backend":
        return [py, "web_yolo_app.py", *passthrough]
    raise ValueError(f"Unsupported mode: {mode}")


def _wizard_prompt_mode(default_mode: str) -> tuple[str, bool, bool]:
    print("\n=== Setup Wizard ===")
    print("Choose launch mode:")
    print("  1) Web YOLO (browser opens automatically)")
    print("  2) Backend only")

    mode_map = {
        "1": "web",
        "2": "backend",
        "": default_mode,
    }

    selected = input(f"Enter choice [1-2] (default {default_mode}): ").strip()
    mode = mode_map.get(selected, default_mode)

    force_answer = input("Force reinstall dependencies? [y/N]: ").strip().lower()
    force_install = force_answer in {"y", "yes"}

    setup_only_answer = input("Setup only (do not start app)? [y/N]: ").strip().lower()
    setup_only = setup_only_answer in {"y", "yes"}

    return mode, force_install, setup_only


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-command launcher: sets up venv, installs deps, and runs the app."
    )
    parser.add_argument(
        "--mode",
        choices=["web", "backend"],
        default="web",
        help="App mode to run (default: web)",
    )
    parser.add_argument(
        "--wizard",
        action="store_true",
        help="Interactive setup wizard for first-time setup and mode selection",
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only create/update environment and dependencies, then exit",
    )
    parser.add_argument(
        "--force-install",
        action="store_true",
        help="Force reinstall of dependencies even if requirements are unchanged",
    )
    args, passthrough = parser.parse_known_args()
    passthrough = _normalize_passthrough(passthrough)

    try:
        _check_python_version()

        mode = args.mode
        force_install = args.force_install
        setup_only = args.setup_only

        if args.wizard:
            mode, wizard_force, wizard_setup_only = _wizard_prompt_mode(mode)
            force_install = force_install or wizard_force
            setup_only = setup_only or wizard_setup_only

        _create_venv_if_missing()
        _install_requirements_if_needed(force_install=force_install)

        if setup_only:
            print("[run.py] Setup completed successfully.")
            return 0

        cmd = _build_target_command(mode, passthrough)
        print(f"[run.py] Launching mode='{mode}'")
        return subprocess.call(cmd, cwd=str(ROOT))
    except Exception as exc:
        print(f"[run.py] Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())