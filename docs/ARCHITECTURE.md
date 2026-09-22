# Architecture and safety notes

LifeFlow is a static single-page course prototype. Hash routes work without server rewrites. Domain logic is isolated in `dist/domain.mjs` for automated testing. Fictional demo records persist in browser local storage; a production system should replace this with authenticated APIs and a validated database.

## Five new functions

1. Explainable smart blood-unit ranking.
2. Shortage and expiration forecasting.
3. Mass-casualty emergency mode.
4. Donor eligibility and next-donation planning.
5. QR unit profile and chain-of-custody tracking.

## Demonstrated safety controls

- Unavailable units are excluded from matching.
- Allocation changes a unit to Reserved to prevent double use.
- O-negative stock is protected when an exact match exists.
- Eligibility is presented as a staff-reviewed recommendation.
- Important actions create audit entries.

Production use would require server authentication, encryption, immutable audit storage, electronic signatures, backups, monitoring, formal validation, and institution-approved medical rules.
