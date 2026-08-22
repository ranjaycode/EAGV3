# Session 17 Assignment — YouTube Demo Video Script (900 Points)

## Title: Arcturus Studio — Autonomous Agentic Coding & TDD Workbench (Session 17)

### Video Outline (3 to 5 Minutes)

#### 0:00 – 0:45: Introduction & Architecture
- **Voiceover**: "Welcome to the demonstration of Arcturus Studio, an autonomous coding agent workbench built on top of the S17Code engine. Today we're showcasing two main parts: a rich front-end product providing 100% visibility into agent execution, and four critical security/engine bug fixes in the S17Code harness."
- **Screen**: Show Arcturus Studio running at `http://localhost:8115`. Point out the sticky header, dark mode design system, live status indicators, and dual execution mode (Live S17 vs Simulation).

#### 0:45 – 1:45: Part 1 - Arcturus Studio Visibility & Red-to-Green Test Lifecycle
- **Voiceover**: "Here in the sidebar, we select our active Markdown Skill—`web-landing-page.md`—which instructs the agent on `file://` origin safety and try/catch guards. When we click 'LAUNCH AGENT RUN', watch the Execution DAG."
- **Action**: Click **"LAUNCH AGENT RUN"**.
- **Visuals**:
  1. Show nodes populating live: `Restate Goal` → `Load Skill` → `Generate HTML` → `Run Webcheck (Initial)`.
  2. Point out the **RED (FAIL)** test node when webcheck finds an un-guarded `localStorage` call.
  3. Show the anchored code edit in the **Anchored Diffs** tab adding the `try/catch` block.
  4. Show the second `Run Webcheck` node transitioning from **RED to GREEN (PASS)**!
  5. Show the **App Preview & Webcheck** tab with all 4 diagnostic checkmarks green!

#### 1:45 – 3:00: Part 2 - Four S17Code Backend Security Bug Fixes
- **Voiceover**: "Now let's look at Part 2: four security and engine bug fixes implemented in S17Code."
- **Visuals**:
  1. **Fix 1 (`guard.py`)**: Show relative path traversal bypass (`s17code/../conftest.py`) being caught and refused. Show `tests/test_guard_traversal.py`.
  2. **Fix 2 (`exec.py`)**: Show dangerous git flag option overrides (`git --exec-path=...`, `git -C /tmp`) being refused by `_check()`. Show `tests/test_exec_git_bypass.py`.
  3. **Fix 3 (`edit.py`)**: Show `EditLedger` path normalization fixing false refusals on `./calc.py` vs `calc.py`. Show `tests/test_edit_ledger_normalization.py`.
  4. **Fix 4 (`validate.py`)**: Show validator execution check preventing untested artifacts from returning false pass statuses. Show `tests/test_validate_execution.py`.

#### 3:00 – 3:30: Verification & Conclusion
- **Action**: Run `python proofs/run_all_proofs.py` in terminal.
- **Voiceover**: "Running our master verifier script confirms all 10 unit tests pass 100%, our UI server is live, and skills are verified. The complete README details all human vs agent contributions. Thank you!"
