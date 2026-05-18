#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_URL = "https://github.com/Coldcard/firmware.git"
APT_PACKAGES = [
    "build-essential",
    "git",
    "python3",
    "python3-pip",
    "python3-venv",
    "make",
    "libudev-dev",
    "gcc-arm-none-eabi",
    "libffi-dev",
    "xterm",
    "swig",
    "libpcsclite-dev",
    "python-is-python3",
    "autoconf",
    "libtool",
    "libsdl2-dev",
    "libsdl2-image-dev",
    "libsdl2-mixer-dev",
    "libsdl2-ttf-dev",
]
MODEL_FLAGS = {"mk4": ["--mk4"], "mk5": [], "q1": ["--q1"]}


@dataclass(frozen=True)
class Paths:
    workdir: Path
    firmware: Path
    env_dir: Path
    unix_dir: Path
    mpy_cross_dir: Path
    simulator: Path


def run_command(
    cmd: list[str],
    cwd: Path | None,
    dry_run: bool,
    env: dict[str, str] | None = None,
) -> None:
    printable = " ".join(cmd)
    print(f"$ {printable}")
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, check=True, env=env)


def confirm_action(message: str, yes: bool) -> bool:
    if yes:
        return True
    answer = input(f"{message} [y/N]: ").strip().lower()
    return answer in {"y", "yes", "s", "si"}


def create_paths(workdir: str | None) -> Paths:
    base = (
        Path(workdir).expanduser().resolve()
        if workdir
        else (Path.home() / "coldcard-emulate").resolve()
    )
    firmware = base / "firmware"
    return Paths(
        workdir=base,
        firmware=firmware,
        env_dir=firmware / "ENV",
        unix_dir=firmware / "unix",
        mpy_cross_dir=firmware / "external" / "micropython" / "mpy-cross",
        simulator=firmware / "unix" / "simulator.py",
    )


def is_linux_or_wsl() -> bool:
    if sys.platform.startswith("linux"):
        return True
    return False


def check_environment(paths: Paths) -> None:
    print("Validando entorno...")
    if not is_linux_or_wsl():
        raise RuntimeError("Este script soporta Linux/WSL.")

    required = ["git", "python3", "make"]
    missing = [name for name in required if shutil.which(name) is None]
    if missing:
        raise RuntimeError(f"Faltan dependencias en PATH: {', '.join(missing)}")

    rel = ""
    if Path("/proc/version").exists():
        rel = Path("/proc/version").read_text(encoding="utf-8", errors="ignore")
    env = "WSL" if "microsoft" in rel.lower() else "Linux"
    print(f"OK: entorno {env}, workdir={paths.workdir}")


def install_system_dependencies(paths: Paths, yes: bool, dry_run: bool) -> None:
    _ = paths
    if not dry_run and not confirm_action(
        "Instalar dependencias del sistema con apt-get?", yes
    ):
        raise RuntimeError("Operacion cancelada por el usuario.")
    run_command(["sudo", "apt-get", "update"], cwd=None, dry_run=dry_run)
    run_command(
        ["sudo", "apt-get", "install", "-y", *APT_PACKAGES], cwd=None, dry_run=dry_run
    )


def _git_has_local_changes(repo_dir: Path, dry_run: bool) -> bool:
    if dry_run:
        return False
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def clone_or_update_firmware(paths: Paths, yes: bool, dry_run: bool) -> None:
    if paths.firmware.exists() and not (paths.firmware / ".git").is_dir():
        raise RuntimeError(f"{paths.firmware} existe pero no es un repositorio Git.")

    if not paths.firmware.exists():
        if not dry_run:
            paths.workdir.mkdir(parents=True, exist_ok=True)
        run_command(
            ["git", "clone", "--recursive", REPO_URL, str(paths.firmware)],
            cwd=paths.workdir,
            dry_run=dry_run,
        )
    else:
        if _git_has_local_changes(paths.firmware, dry_run):
            if not confirm_action(
                "El repo firmware tiene cambios locales. Continuar con update?", yes
            ):
                raise RuntimeError("Operacion cancelada por el usuario.")

        run_command(
            ["git", "fetch", "--all", "--prune"],
            cwd=paths.firmware,
            dry_run=dry_run,
        )
        run_command(["git", "pull", "--ff-only"], cwd=paths.firmware, dry_run=dry_run)

    run_command(
        ["git", "submodule", "update", "--init", "--recursive"],
        cwd=paths.firmware,
        dry_run=dry_run,
    )

    libngu_dir = paths.firmware / "external" / "libngu"
    if libngu_dir.is_dir():
        run_command(
            ["git", "submodule", "update", "--init", "--recursive"],
            cwd=libngu_dir,
            dry_run=dry_run,
        )


def ensure_python_env(paths: Paths, dry_run: bool) -> None:
    if not paths.env_dir.exists():
        run_command(
            ["python3", "-m", "venv", str(paths.env_dir)],
            cwd=paths.firmware,
            dry_run=dry_run,
        )

    pip = paths.env_dir / "bin" / "pip"
    run_command(
        [
            str(pip),
            "install",
            "--no-cache-dir",
            "-U",
            "pip",
            "setuptools",
            "pysdl2-dll",
        ],
        cwd=paths.firmware,
        dry_run=dry_run,
    )
    run_command(
        [str(pip), "install", "--no-cache-dir", "-r", "requirements.txt"],
        cwd=paths.firmware,
        dry_run=dry_run,
    )


def build_simulator(paths: Paths, dry_run: bool) -> None:
    ensure_python_env(paths, dry_run=dry_run)
    unix_dir = paths.firmware / "unix"
    build_env = os.environ.copy()
    build_env.pop("VARIANT", None)
    build_env["CFLAGS_EXTRA"] = "-Wno-dangling-pointer -Wno-error=enum-int-mismatch"
    build_env["PWD"] = str(unix_dir)
    run_command(["make", "setup"], cwd=unix_dir, dry_run=dry_run, env=build_env)
    run_command(["make", "ngu-setup"], cwd=unix_dir, dry_run=dry_run, env=build_env)
    run_command(["make", "clean"], cwd=unix_dir, dry_run=dry_run, env=build_env)
    run_command(["make", "V=1"], cwd=unix_dir, dry_run=dry_run, env=build_env)


def run_simulator(paths: Paths, model: str, dry_run: bool) -> None:
    python_bin = paths.env_dir / "bin" / "python3"
    cmd = [str(python_bin), str(paths.simulator), "-w", *MODEL_FLAGS[model]]
    run_command(cmd, cwd=paths.unix_dir, dry_run=dry_run)


def parse_args() -> argparse.Namespace:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--workdir", help="Directorio de trabajo (default: ~/coldcard-emulate)"
    )
    common.add_argument("--yes", action="store_true", help="No pedir confirmaciones")
    common.add_argument(
        "--dry-run", action="store_true", help="Mostrar comandos sin ejecutarlos"
    )

    parser = argparse.ArgumentParser(
        description="CLI para Coldcard emulator", parents=[common]
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", parents=[common])
    subparsers.add_parser("install", parents=[common])
    subparsers.add_parser("clone", parents=[common])
    subparsers.add_parser("build", parents=[common])

    run_parser = subparsers.add_parser("run", parents=[common])
    all_parser = subparsers.add_parser("all", parents=[common])

    for sub in (run_parser, all_parser):
        sub.add_argument(
            "--model",
            choices=["mk4", "mk5", "q1"],
            default="mk4",
            help="Modelo a emular (default: mk4)",
        )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = create_paths(args.workdir)

    if args.command == "check":
        check_environment(paths)
        return 0
    if args.command == "install":
        install_system_dependencies(paths, yes=args.yes, dry_run=args.dry_run)
        return 0
    if args.command == "clone":
        clone_or_update_firmware(paths, yes=args.yes, dry_run=args.dry_run)
        return 0
    if args.command == "build":
        build_simulator(paths, dry_run=args.dry_run)
        return 0
    if args.command == "run":
        run_simulator(paths, model=args.model, dry_run=args.dry_run)
        return 0
    if args.command == "all":
        check_environment(paths)
        install_system_dependencies(paths, yes=args.yes, dry_run=args.dry_run)
        clone_or_update_firmware(paths, yes=args.yes, dry_run=args.dry_run)
        build_simulator(paths, dry_run=args.dry_run)
        run_simulator(paths, model=args.model, dry_run=args.dry_run)
        return 0

    raise RuntimeError(f"Comando no soportado: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as err:
        print(f"ERROR: comando fallo con codigo {err.returncode}", file=sys.stderr)
        raise SystemExit(err.returncode)
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.", file=sys.stderr)
        raise SystemExit(130)
