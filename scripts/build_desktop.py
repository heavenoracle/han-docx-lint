from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "packaging" / "pyinstaller" / "gui_entry.py"
DIST = ROOT / "dist"
WORK = ROOT / "build" / "pyinstaller"


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True, cwd=ROOT)


def main() -> int:
    if not ENTRY.is_file():
        raise SystemExit(f"missing PyInstaller entry script: {ENTRY}")

    shutil.rmtree(DIST, ignore_errors=True)
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)

    app_name = "han-docx-lint-gui" if sys.platform.startswith("win") else "HanDocxLint"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        app_name,
        "--distpath",
        str(DIST),
        "--workpath",
        str(WORK),
        "--specpath",
        str(WORK),
    ]
    if sys.platform.startswith("win"):
        command.append("--onefile")
    command.append(str(ENTRY))
    run(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
