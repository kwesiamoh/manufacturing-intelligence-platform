# Data Classification, Retention & Handling

## Classification levels

### Public / External Reference

Publicly available datasets, standards references, and public metadata.

Handling:
- preserve source attribution;
- retain licence/reference notes;
- store checksums where practical.

### Internal Project

Synthetic enterprise data, transformation code, SQL models, DAX measures,
architecture documents, and portfolio outputs.

Handling:
- version control permitted;
- no credentials in repository;
- generated artifacts should be reproducible from source/code where practical.

### Restricted Secret

Examples:
- PostgreSQL passwords;
- API tokens;
- cloud access keys;
- private connection strings.

Handling:
- never commit to Git;
- use runtime prompts, environment variables, `.env` files excluded by
  `.gitignore`, or a secret-management service in a deployed architecture.

## Retention

### Bronze
Retain indefinitely for portfolio reproducibility unless source licence terms
require otherwise.

### Silver / Gold
Regenerable from Bronze and transformation code. Retain for convenience, but
treat code and provenance as the authoritative reproducibility layer.

### Model artifacts
Retain only accepted/final models plus sufficient metadata to reproduce them.

### Logs
Retain validation and orchestration logs needed to demonstrate pipeline runs and
data-quality evidence.

## Personal data

The current platform does not intentionally model personal employee or customer
data.

If personal data were introduced in a future implementation, additional privacy
controls, legal basis, minimization, access restriction, and retention rules
would be required.
