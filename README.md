# Storage Array Pytest Automation Framework

A vendor-neutral, extensible pytest project for validating storage-array features:
replication, RAID creation, zoning, multipathing, snapshots, clones, metadata, and
cross-feature workflows.

The project includes a fully runnable in-memory simulator. Replace or extend the
adapter layer to connect to a real array REST API, CLI, SDK, SAN switch, or host.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
pytest -m smoke
pytest -m regression
pytest -n auto
```

HTML and JUnit reports are written to `reports/`; logs are written to `logs/`.

## Select a backend

The default configuration uses `simulator` and requires no hardware.

```bash
pytest --config config/lab.yaml --backend simulator
pytest --config config/lab.yaml --backend rest
```

For a real array, implement the methods in
`src/storage_framework/adapters/rest_array.py` and provide credentials through
environment variables (recommended) or a protected YAML file.

## Useful commands

```bash
pytest tests/raid -m raid
pytest -m "snapshot and not destructive"
pytest --run-destructive -m destructive
pytest --keep-resources
pytest --collect-only -q
```

Destructive tests are skipped unless `--run-destructive` is supplied.

## Architecture

- `src/storage_framework/core`: contracts, configuration, exceptions, waiters
- `src/storage_framework/adapters`: simulator and real-array adapter template
- `src/storage_framework/clients`: feature-focused service libraries
- `tests`: feature test suites and integration workflows
- `conftest.py`: command-line options, fixtures, cleanup, logging, test metadata
- `config`: lab and environment definitions

## Adding a vendor implementation

1. Subclass `StorageArrayAdapter`.
2. Implement all required operations using the vendor API/SDK/CLI.
3. Register the adapter in `conftest.py::_build_adapter`.
4. Keep vendor response translation inside the adapter; tests should use the
   normalized framework models.

## Safety

Use a dedicated automation tenant/pool and non-production hosts. Keep secrets out
of source control. Validate deletion scope before enabling destructive tests.
