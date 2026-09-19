# Optional validation helpers

`python tools/generate_fixtures.py` regenerates and validates synthetic protocol examples.

`python tools/browser_smoke.py` checks the browser renderer with in-memory protocol responses. It additionally requires Playwright and an installed Chromium at `/usr/bin/chromium`; adjust that executable path for your environment. It does not require browser network access and does not replace the HTTP integration tests.

Playwright is a development-only optional dependency, not needed to run ThreadDesk or the standard unittest suite.
