# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`judgeling` is a single-file Python CLI tool (`src/judgeling.py`) for testing algorithm solutions against problem definitions. It compiles user solutions (C++/Java/Python/shell), generates test datasets, validates inputs, and checks outputs via judges or checkers. Designed for competitive programming workflows — the companion problem repository lives at `../acm-problems/problems/`.

## Commands

Run the tool:
```bash
python3 src/judgeling.py -P <problem_path_or_id> -S solution1.cpp [solution2.cpp ...]
```

Filter datasets/testcases with regex: `-D <regex>` and `-T <regex>`

Run tests (from the `test/` directory — paths inside `test.py` are relative, so `cd test` first):
```bash
cd test && python3 test.py
# or a single test:
cd test && python3 test.py -v TestCall.test_wrong_solution_is_reported_as_wrong_answer
```

Tests use `unittest` (no pytest) and invoke `src/judgeling.py` as a subprocess, checking return codes and, for a few cases, captured stderr log output.

Lint / format / typecheck (tools live in `.venv/bin/`, installed via `uv sync`):
```bash
.venv/bin/ruff check src/judgeling.py test/test.py
.venv/bin/ruff format src/judgeling.py test/test.py
.venv/bin/pyright
```
The git pre-commit hook (`.pre-commit-config.yaml`) only runs `ruff format` on commit — it does **not** run `ruff check`, `pyright`, or the test suite. Run those manually before considering a change done. As of the last check there are 6 pre-existing `ruff check` findings (global-statement, subprocess `check=`, mutable default arg, unclosed file handles in `test.py`) that predate this guidance — don't treat them as caused by your change, but don't add new ones either; fix them only if the task calls for it.

## Architecture

The entire tool is a single file `src/judgeling.py` (intentionally kept under 1000 lines — this is a hard constraint, not a suggestion; if a change would push it over, look for something to cut or simplify rather than accepting the growth). Configuration lives in `config.json` (global, at the repo root) and optional `config_local.json` (local overrides, also at the repo root). Per-problem overrides go in `<problem>/.judgeling_config.json`.

### Core flow in `main()`

1. Load config chain: `config.json` → `config_local.json` → per-problem `.judgeling_config.json`
2. Resolve problem folder via `find_problem_folder()` — checks CWD first, then `../acm-problems/problems/` recursively
3. Discover problem components from the file structure config (`gen/`, `val/`, `jud/`, `chk/`, `sol/`, `pic/`)
4. Determine checking mechanism: **judge** (standalone correctness check), **checker** (compare against referential solution), or **cross_check** (compare user solutions against each other)
5. Generate datasets (with source-hash-based caching to skip unchanged generators)
6. Validate inputs, run solutions, check outputs, report summary

### Key classes

- **Program** — base class: wraps a source file, handles compilation and execution
- **Solution(Program)** — tracks timing (`Timer`) and bad testcases, can be disqualified
- **Generator(Program)** — generates datasets into `<problem>/.tmp/data/<gen_name>/`, uses `HashFile` to cache
- **Dataset** / **Testcase** — represent generated test data (`.in`/`.out` file pairs)
- **Mechanism** enum — `judge`, `checker`, `cross_check`
- **Result** enum — `OK(0)`, `WRONG_ANSWER(1)`, `PRESENTATION_ERROR(2)`, `TIMELIMIT_EXCEEDED(3)`, `RUNTIME_ERROR(4)`, `BAD_INVOCATION(43)`

### Problem definition structure

Each problem folder contains:
- `def.toml` — name, input/output descriptions
- `gen/` — dataset generators (each generator creates a named dataset)
- `val/` — input validators
- `sol/` — referential solutions
- `jud.cpp` — judge (checks input + user output)
- `chk.cpp` — checker (compares referential + user output)
- `pic/` — painter for visual representation

Components can be a single file (`jud.cpp`) or a directory of files (`gen/small.cpp`, `gen/large.cpp`). All build artifacts and generated data go into `<problem>/.tmp/`.

Two example/test fixture trees exist and are easy to confuse:
- `test/example/` — a full, real problem definition (array sorting) used by most tests in `test/test.py`.
- `test/fixtures/` — standalone extra files (a deliberately wrong solution, a Java solution, a manual input, a minimal no-checker problem) used to exercise specific edge cases against `test/example` or on their own.

### Compilation

Each entry in `config.json`'s `languages.compiled` list is a template, not hardcoded logic — `compile_src()` in `src/judgeling.py` expands `{flag}`, `{exe}`, `{source}`, `{build}`, `{class}` placeholders in three fields:
- `command` (required) — how to compile.
- `run` (optional) — how to invoke the compiled result; defaults to `[{exe}]` (a single directly-executable binary, e.g. C++'s `g++ ... -o {exe}`).
- `artifact` (optional) — the file whose existence/hash gates the compilation-skip cache; defaults to `{exe}`.

C++ compiles straight to an executable with `g++ -O2 -g -std=c++17 -lm -pedantic -DJUDGELING -o <exe> <source>` and runs that binary directly. Java compiles with `javac -d {build} {source}` and runs via `java -cp {build} {class}` — this means a Java solution's public class name must match its filename (standard Java convention), and package declarations are not supported (classes are assumed top-level in `{build}`). Python and shell files are treated as interpreted (invoked via the configured interpreter, no compile step). Source hash caching (`HashFile`) skips recompilation when the source hasn't changed, checked against each language's `artifact` path.

To add a new compiled language, add an entry to `languages.compiled` in `config.json` — no Python changes needed unless its invocation shape doesn't fit the `command`/`run`/`artifact` template (e.g. multi-file output, needing a wrapper script).

### Exit codes

- `0` — success
- `1` — user error (bad solution path, invalid testcase)
- `2` — problem definition error (broken generator, no checking mechanism)
- `129` — invalid CLI arguments

## Working effectively on this repo

- After any change to `src/judgeling.py`, run the full test suite (`cd test && python3 test.py`) and `ruff check` — both are cheap and catch most regressions immediately; there is no CI to lean on.
- Prefer extending the `config.json` template mechanism (see Compilation above) over adding special-case Python logic for a new language or tool.
- The tool assumes a Unix environment (it uses the `resource` module for CPU-time measurement via `RUSAGE_CHILDREN`); don't add Windows-specific accommodations.
- The known-but-unimplemented feature list lives in `README.md` under `# TODOS`; check there before proposing new work so you don't duplicate an already-scoped idea, and remove an item from that list when you implement it.
- Two inline `# todo` comments in `src/judgeling.py` mark small known gaps: summary result reporting doesn't split cleanly by return code (near the bad-testcase-recording logic in `main()`), and `find_problem_folder()` doesn't warn when a problem query matches more than one definition.
