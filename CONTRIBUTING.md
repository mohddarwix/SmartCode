# Contributing to SmartCode

Thank you for your interest in SmartCode.
This is primarily a portfolio/academic project (LAU COE 416, Spring 2026), so contributions are welcome but the maintainers are not actively monitoring issues on a regular schedule.

---

## Bug Reports

Open a [GitHub Issue](../../issues) and include:

- A clear title describing the problem.
- Steps to reproduce (browser, OS, whether you are running locally or using the live demo).
- What you expected vs. what actually happened.
- Any relevant console errors or screenshots.

Please search existing issues before opening a new one.

---

## Pull Requests

1. **Fork** the repository and create a branch from `main`:
   ```
   git checkout -b fix/your-short-description
   ```
2. Make your changes (see code style below).
3. Run the tests locally and make sure they pass (see [DEVELOPMENT.md](DEVELOPMENT.md)).
4. Open a PR against the `main` branch with a clear description of what changed and why.

Keep PRs focused — one logical change per PR makes review faster.

---

## Code Style

| Area | Tool | Command |
|------|------|---------|
| Python | [Black](https://black.readthedocs.io/) | `black backend/` |
| JavaScript / JSX | [Prettier](https://prettier.io/) (via ESLint) | `npm run lint` |

Neither formatter is enforced by a pre-commit hook yet, but the CI lint job will catch deviations on PRs.

---

## Commit Messages

Use **imperative present tense** in the subject line (50 chars or fewer):

```
Add hint throttle to prevent API abuse
Fix JWT expiry not being refreshed on re-login
Remove unused analytics middleware
```

Reference the issue number in the body when applicable:

```
Fix submission score rounding for partial credit

Scores were floored instead of rounded, causing edge-case
off-by-one failures for borderline passing submissions.

Closes #42
```

---

## Scope Note

SmartCode is a closed course project with a live deployment managed by its authors.
We welcome bug fixes and documentation improvements. Feature additions that significantly
change the learning-path logic or admin interface may take longer to review — please
open an issue to discuss before investing significant time.
