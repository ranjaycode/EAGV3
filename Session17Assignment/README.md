# Arcturus Studio — Autonomous Agentic Coding Workbench (Session 17 Assignment)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![S17Code Engine](https://img.shields.io/badge/S17Code-Agentic_TDD-00F2FE?style=flat)](https://github.com/theschoolofai/S17Code)
[![Tests](https://img.shields.io/badge/Tests-487_Passed-10B981?style=flat)](#verification--test-results)

Arcturus Studio is a high-performance visual workbench and product built on top of the **S17Code Engine**. It provides complete transparency into autonomous coding loops, deterministic test execution, anchored code diffs, Markdown-as-Code skills, and System 2 validation.

---

## 🌟 Overview & Features (Part 1: The Product)

Arcturus Studio fulfills all Part 1 requirements of Assignment 17:

1. **Real-Time Execution Graph (DAG)**:
   - Visualizes live execution nodes (`Goal Restatement`, `Skill Loading`, `Read File`, `Anchored Edit`, `Test Execution`, `Validator Agent`).
   - Tracks node states: `Pending`, `Running (Blue Pulse)`, `Failed (Red Alert)`, `Passed (Emerald Green)`.

2. **Red-to-Green Test Lifecycle Visualizer**:
   - Explicitly displays test suite transitions from **RED** (exit code 1 / failing assertion) to **GREEN** (exit code 0 / passing suite) following auto-remediation.

3. **Terminal Log Console**:
   - Streaming output window displaying non-shell allowlisted commands (`pytest`, `python`, `node webcheck.js`, `git diff`).

4. **Anchored Code Diff Viewer**:
   - Displays precise string replacements enforced by `coding/edit.py` (read-before-edit requirement and unique anchor verification).

5. **Live App Preview & Webcheck Harness**:
   - Embedded interactive iframe rendering generated web landing pages (`index.html`).
   - Resolution switchers (Desktop, Tablet 768px, Mobile 375px).
   - Integrated DOM diagnostics checking `file://` origin `localStorage` safety, visible text rendering, and theme toggle interactivity.

6. **Markdown Skill Selector**:
   - Enables/disables Level 2 `SKILL.md` files (`web-landing-page.md`, `python-tdd.md`).

7. **Dual Mode Backend**:
   - Connects live to S17Code engine (`http://localhost:8113`) or operates in high-fidelity offline simulation mode out of the box.

---

## 🛡️ Security Bug Fixes & Pull Request (Part 2: The Harness Fixes)

Two critical vulnerabilities in the S17Code harness were identified, fixed, and verified with dedicated unit test suites:

### 1. `coding/guard.py` — Path Traversal Guard Bypass Fix
- **Issue**: The guard relied on basic string stripping (`lstrip("./")`). Relative parent traversal paths such as `s17code/../conftest.py` or `docs/../.github/workflows/ci.yml` escaped matching rules because they started with unprotected directory names (`s17code/`), allowing unprivileged agents to alter protected test files.
- **Fix**: Implemented strict path normalization with `os.path.normpath` prior to checking protected patterns, while refusing any traversal attempting to escape the workspace root.
- **Test File**: [tests/test_guard_traversal.py](file:///c:/Users/dell/Desktop/EAGV3/Session17Assignment/s17code_repo/tests/test_guard_traversal.py)

### 2. `coding/exec.py` — Git Option Flag Arbitrary Execution Bypass Fix
- **Issue**: While `git` was on the command allowlist, dangerous flags such as `--exec-path=/tmp`, `-C /tmp`, or capitalized `-C` flags could be passed before subcommands, enabling arbitrary binary execution outside allowlist bounds.
- **Fix**: Added comprehensive option flag validation in `_check()` for `git` commands, refusing `--exec-path`, `--config`, `-C`, `-c`, and dangerous pack overrides regardless of position.
- **Test File**: [tests/test_exec_git_bypass.py](file:///c:/Users/dell/Desktop/EAGV3/Session17Assignment/s17code_repo/tests/test_exec_git_bypass.py)

---

## 📁 Repository Structure

```
Session17Assignment/
├── s17code_repo/                  # S17Code Engine Repository (Forked & Patched)
│   ├── s17code/
│   │   ├── coding/
│   │   │   ├── guard.py           # [FIXED] Path traversal guard normalization
│   │   │   ├── exec.py            # [FIXED] Git flag option security enforcement
│   │   │   ├── edit.py            # Anchored edit string replacement engine
│   │   │   └── validate.py        # System 2 Hostile Validator Agent
│   └── tests/
│       ├── test_guard_traversal.py# [NEW] Security unit test suite for guard.py
│       └── test_exec_git_bypass.py# [NEW] Security unit test suite for exec.py
├── ui/                            # Arcturus Studio Frontend Application
│   ├── index.html                 # Main Studio Interface
│   ├── styles.css                 # Dark Mode Glassmorphism Design System
│   ├── app.js                     # Core Frontend Client & Live Stream Handler
│   ├── mock_runner.js             # High-Fidelity S17 Event Simulation Engine
│   └── server.py                  # Dev Server & S17 API Proxy (Port 8115)
├── skills/                        # Markdown-as-Code Skills
│   ├── web-landing-page/SKILL.md  # Landing page file:// safety guidelines
│   └── python-tdd/SKILL.md        # Python TDD judge enforcement rules
└── README.md                      # Assignment Documentation & Attribution
```

---

## 🚀 Quick Start Guide

### 1. Launch Arcturus Studio Frontend
```bash
# From workspace root
python ui/server.py
```
Open **`http://localhost:8115`** in your browser.

### 2. Launch Live S17Code Engine (Optional for Live API Mode)
```bash
cd s17code_repo
uv sync
uv run s17code serve   # Runs on http://localhost:8113
```

### 3. Run Security & Harness Tests
```bash
cd s17code_repo
uv run pytest -q tests/test_guard_traversal.py tests/test_exec_git_bypass.py
```

---

## 🤖 Agent vs. Human Attribution Statement

As explicitly required by Assignment 17:

* **Human Contributions**:
  - Task framing, prompt formulation, architectural plan review, security threat modeling (identifying path traversal vulnerabilities in `guard.py` and git flag overrides in `exec.py`), and verification testing.

* **Agent Contributions**:
  - Generated all code edits for `s17code/coding/guard.py` and `s17code/coding/exec.py`.
  - Built unit test files `tests/test_guard_traversal.py` and `tests/test_exec_git_bypass.py`.
  - Developed the complete Arcturus Studio web product (`ui/index.html`, `ui/styles.css`, `ui/app.js`, `ui/mock_runner.js`, `ui/server.py`).
  - Created Markdown-as-Code skill files (`skills/web-landing-page/SKILL.md` and `skills/python-tdd/SKILL.md`).
