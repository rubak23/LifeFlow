# LifeFlow Blood Bank

LifeFlow is a portfolio-ready educational Blood Establishment Computer Software prototype. It manages donor medical records, donation intake, infectious-disease screening, automatic release of safe blood units, patient laboratory orders, inventory, hospital requests, matching, forecasting, QR chain of custody, administration, and an audit trail.

The interface uses an operational command-center layout rather than a generic marketing site or standard card dashboard. The five course-extension functions are integrated into the relevant workflows and are not presented as a promotional page inside the application.

## Safety notice

This is an educational course project and is not validated for clinical use. Compatibility and donor-eligibility rules are simplified demonstrations. Real decisions require qualified staff, laboratory testing, approved procedures, and applicable regulation.

## Quick start in PyCharm

1. Extract the ZIP and open the `lifeflow-site` folder.
2. Use Python 3.10 or newer.
3. Open `run.py` and press the green **Run** button in PyCharm.
4. Open `http://localhost:4173` in a browser.

Terminal alternative: `python run.py`.

No package installation is required. The local application uses a real SQLite database at `data/lifeflow.db`; donor records, donations, generated blood units, screening results, patient laboratory orders, requests, reservations, and audit events remain saved after closing the browser or restarting the application. The published web preview uses browser storage because static hosting cannot run Python.

## Technologies

- Python 3 standard library for the local web server and JSON API
- SQLite for persistent application data
- HTML, CSS and modern JavaScript for the Hebrew RTL interface

## Tests

Run `python -m unittest discover -s tests -p "test_*.py"` for database tests. With Node.js 20 or newer, run `npm test` for domain tests. Together they cover persistence, auditing, double-reservation protection, compatibility, smart matching, rare-type protection, forecasting, and donor eligibility.

## Structure

```text
dist/      Website, styling, interactions and domain logic
tests/     Automated unit tests
docs/      Architecture and safety decisions
server.py  Python API and SQLite persistence
run.py     One-click local launcher for PyCharm
README.md  Setup and project guide
CREDITS.txt Team submission details
```

All names, records, units, and metrics are fictional. Do not enter real protected health information.
