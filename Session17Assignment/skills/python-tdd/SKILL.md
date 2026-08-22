---
name: python-tdd
description: Guidelines for fixing failing Python functions using Test-Driven Development without modifying tests or judges.
capabilities:
  - edit_code
  - run_command
---

# Python TDD Engineering Guidelines

When fixing Python bugs:

## 1. Respect Protected Paths & The Judge
- Do **NOT** attempt to modify test files (`tests/**`), `conftest.py`, or CI files.
- The test suite is the immutable judge of your work.

## 2. Anchored Edits
- Always read the target file before attempting an edit.
- Provide sufficient context lines around target code to ensure the target anchor is unique.

## 3. Root Cause Resolution
- Address the underlying division by zero, null check, or missing boundary condition in the implementation.
- Do not swallow exceptions in the calling test or delete failing test cases.
