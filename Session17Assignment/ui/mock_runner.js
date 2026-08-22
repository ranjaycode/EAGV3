/**
 * Arcturus Studio — High-Fidelity S17Code Event Simulation Engine
 * Simulates real-time DAG graph transitions, anchored code edits, pytest execution,
 * and webcheck harness validation cycles for offline/demo use.
 */

window.ArcturusMockRunner = {
  simulateRun: function(presetKey, callbacks) {
    const events = this.getEventSequence(presetKey);
    let stepIndex = 0;

    callbacks.onStart({ runId: 'mock-run-' + Date.now(), totalSteps: events.length });

    const interval = setInterval(() => {
      if (stepIndex >= events.length) {
        clearInterval(interval);
        callbacks.onComplete({ status: 'SUCCESS' });
        return;
      }

      const evt = events[stepIndex];
      callbacks.onEvent(evt);
      stepIndex++;
    }, 1200);

    return () => clearInterval(interval);
  },

  getEventSequence: function(presetKey) {
    if (presetKey === 'python-tdd') {
      return [
        { type: 'node_start', node_id: 'node_1', title: 'Restate Goal & Constraints', status: 'running' },
        { type: 'log', message: '[planner] Restated goal: Fix ZeroDivisionError in average() in calc.py preserving test judge.', level: 'sys' },
        { type: 'node_complete', node_id: 'node_1', status: 'passed' },

        { type: 'node_start', node_id: 'node_2', title: 'Read Target File: calc.py', status: 'running' },
        { type: 'log', message: '[capability] read_code(path="calc.py", start_line=1, end_line=30)', level: 'cmd' },
        { type: 'log', message: 'def average(numbers):\n    """Mean of a list. Returns 0 for an empty list."""\n    return sum(numbers) / len(numbers)', level: 'out' },
        { type: 'node_complete', node_id: 'node_2', status: 'passed' },

        { type: 'node_start', node_id: 'node_3', title: 'Run Test Judge (Initial Test Run)', status: 'running' },
        { type: 'log', message: '[exec] pytest -q tests/test_calc.py', level: 'cmd' },
        { type: 'log', message: 'FAILED tests/test_calc.py::test_average_empty - ZeroDivisionError: division by zero', level: 'fail' },
        { type: 'log', message: '[lifecycle] Test status: RED (Exit code 1)', level: 'fail' },
        { type: 'node_complete', node_id: 'node_3', status: 'failed' },

        { type: 'node_start', node_id: 'node_4', title: 'Anchored Code Edit: calc.py', status: 'running' },
        { type: 'log', message: '[edit] Applying anchored replacement in calc.py...', level: 'sys' },
        { type: 'diff', file: 'calc.py', old_str: 'return sum(numbers) / len(numbers)', new_str: 'if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)' },
        { type: 'node_complete', node_id: 'node_4', status: 'passed' },

        { type: 'node_start', node_id: 'node_5', title: 'Run Test Judge (Verification)', status: 'running' },
        { type: 'log', message: '[exec] pytest -q tests/test_calc.py', level: 'cmd' },
        { type: 'log', message: '5 passed in 0.04s', level: 'pass' },
        { type: 'log', message: '[lifecycle] Test status transition: RED → GREEN (Exit code 0)', level: 'pass' },
        { type: 'node_complete', node_id: 'node_5', status: 'passed' },

        { type: 'node_start', node_id: 'node_6', title: 'Hostile Validator Agent Check', status: 'running' },
        { type: 'log', message: '[validate] Spawning fresh validation context with no edit permissions...', level: 'sys' },
        { type: 'log', message: '[validate] Suit passed. Code docstring contract satisfied.', level: 'pass' },
        { type: 'node_complete', node_id: 'node_6', status: 'passed' }
      ];
    }

    if (presetKey === 'security-fix') {
      return [
        { type: 'node_start', node_id: 'sec_1', title: 'Security Audit: coding/guard.py', status: 'running' },
        { type: 'log', message: '[security] Testing relative path traversal bypass: s17code/../conftest.py...', level: 'sys' },
        { type: 'log', message: '[exec] pytest -q tests/test_guard_traversal.py', level: 'cmd' },
        { type: 'log', message: 'PASSED tests/test_guard_traversal.py::test_guard_path_traversal_attempts_refused', level: 'pass' },
        { type: 'node_complete', node_id: 'sec_1', status: 'passed' },

        { type: 'node_start', node_id: 'sec_2', title: 'Security Audit: coding/exec.py Git Flags', status: 'running' },
        { type: 'log', message: '[exec] pytest -q tests/test_exec_git_bypass.py', level: 'cmd' },
        { type: 'log', message: 'PASSED tests/test_exec_git_bypass.py::test_exec_git_dangerous_flag_bypasses_refused', level: 'pass' },
        { type: 'node_complete', node_id: 'sec_2', status: 'passed' }
      ];
    }

    // Default Landing Page Preset
    return [
      { type: 'node_start', node_id: 'lp_1', title: 'Restate Landing Page Goal', status: 'running' },
      { type: 'log', message: '[planner] Restated goal: Build production landing page Arcturus with offline file:// safety.', level: 'sys' },
      { type: 'node_complete', node_id: 'lp_1', status: 'passed' },

      { type: 'node_start', node_id: 'lp_2', title: 'Load Skill: web-landing-page.md', status: 'running' },
      { type: 'log', message: '[skill] Loaded skill web-landing-page.md (Level 2 disclosure: try/catch localStorage requirement).', level: 'sys' },
      { type: 'node_complete', node_id: 'lp_2', status: 'passed' },

      { type: 'node_start', node_id: 'lp_3', title: 'Generate Single-File HTML', status: 'running' },
      { type: 'log', message: '[edit] Writing index.html (30,661 bytes, 33 inline SVG icons, zero external CDNs)...', level: 'sys' },
      { type: 'diff', file: 'index.html', old_str: '<!-- empty -->', new_str: '<!DOCTYPE html><html><head><title>Arcturus</title></head><body>...</body></html>' },
      { type: 'node_complete', node_id: 'lp_3', status: 'passed' },

      { type: 'node_start', node_id: 'lp_4', title: 'Run Webcheck Harness (Initial Run)', status: 'running' },
      { type: 'log', message: '[exec] node webcheck.js index.html', level: 'cmd' },
      { type: 'log', message: 'FAIL [file:// origin] SecurityError: localStorage is unavailable on file:// origin', level: 'fail' },
      { type: 'log', message: '[lifecycle] Test status: RED (Webcheck failed)', level: 'fail' },
      { type: 'node_complete', node_id: 'lp_4', status: 'failed' },

      { type: 'node_start', node_id: 'lp_5', title: 'Anchored Code Fix: Wrap localStorage', status: 'running' },
      { type: 'log', message: '[edit] Replacing top-level localStorage access with try/catch guard in index.html...', level: 'sys' },
      { type: 'diff', file: 'index.html', old_str: 'const theme = localStorage.getItem("theme");', new_str: 'let theme; try { theme = localStorage.getItem("theme"); } catch(e) { theme = "dark"; }' },
      { type: 'node_complete', node_id: 'lp_5', status: 'passed' },

      { type: 'node_start', node_id: 'lp_6', title: 'Run Webcheck Harness (Verification)', status: 'running' },
      { type: 'log', message: '[exec] node webcheck.js index.html', level: 'cmd' },
      { type: 'log', message: 'PASS [file:// origin] visible chars: 53809 | clickable: 4 | theme toggle response: OK', level: 'pass' },
      { type: 'log', message: '[lifecycle] Test status transition: RED → GREEN (Webcheck passed)', level: 'pass' },
      { type: 'node_complete', node_id: 'lp_6', status: 'passed' }
    ];
  }
};
