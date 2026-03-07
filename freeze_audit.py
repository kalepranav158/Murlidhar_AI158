import argparse
import subprocess
import sys
from dataclasses import dataclass
from typing import List


@dataclass
class CheckResult:
    name: str
    passed: bool
    code: int


def run_command(name: str, command: List[str]) -> CheckResult:
    print(f"\n=== {name} ===")
    print("$", " ".join(command))
    completed = subprocess.run(command)
    passed = completed.returncode == 0
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    return CheckResult(name=name, passed=passed, code=completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run backend freeze audit checks.")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only freeze suite and skip canonical regression suite.",
    )
    args = parser.parse_args()

    python = sys.executable
    checks: List[CheckResult] = []

    checks.append(
        run_command(
            "Syntax check",
            [python, "-m", "py_compile", "backend/main.py", "backend/models/db.py", "tests/freeze/test_backend_freeze.py"],
        )
    )

    checks.append(
        run_command(
            "Backend freeze suite",
            [python, "-m", "pytest", "tests/freeze/test_backend_freeze.py", "-q"],
        )
    )

    if not args.quick:
        checks.append(
            run_command(
                "Canonical regression suite",
                [python, "-m", "pytest", "tests/freeze/test_edge_cases.py", "tests/freeze/test_curriculum.py", "-q"],
            )
        )

    print("\n=== Freeze Audit Summary ===")
    for item in checks:
        print(f"- {item.name}: {'PASS' if item.passed else 'FAIL'}")

    failed = [item for item in checks if not item.passed]
    if failed:
        print("\nFreeze audit failed.")
        return 1

    print("\nFreeze audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
