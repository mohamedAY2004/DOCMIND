"""Seed utilities.

After editing ``seed_initial.py``, apply changes by running it again from ``src/``:

    python -m seeds.seed_initial

That truncates seeded tables and inserts the current definitions (requires DB URL in ``.env``).
Also available via Docker: ``docker compose run --rm migrate`` from ``backend/docker/`` (runs migrations + seed).
"""
