---
name: web-landing-page
description: Rules for generating single-file offline landing pages without breaking storage APIs or DOM animations.
capabilities:
  - edit_code
  - run_command
---

# Web Landing Page Engineering Guidelines

When asked to create or edit a single-file landing page (`index.html`):

## 1. Offline Storage API Safety (CRITICAL)
- **NEVER** access `localStorage` or `sessionStorage` at the top-level script scope.
- On `file://` origins (opening directly from disk), accessing `localStorage` throws a `SecurityError`.
- **ALWAYS** wrap storage accesses in safe try/catch guards:
  ```javascript
  function getStoredTheme() {
    try {
      return localStorage.getItem('theme');
    } catch (e) {
      return null;
    }
  }
  ```

## 2. Animation & Visibility Safety
- Elements styled with `opacity: 0` or `transform: translateY(...)` for entrance animations MUST have a JavaScript fallback or immediate reveal if `IntersectionObserver` or JS triggers fail.
- Ensure all interactive elements (theme toggle, accordion triggers, mobile drawer) respond instantly to user clicks and update DOM attributes (e.g. `data-theme="light"` or `data-theme="dark"`).

## 3. Self-Contained Integrity
- Use inline SVG icons, embedded CSS, and pure Vanilla JavaScript.
- Zero external dependencies or network CDNs so the page renders offline perfectly.
