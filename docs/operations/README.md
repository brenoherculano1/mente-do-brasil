# Mente do Brasil Operations

This folder contains the application-side production foundation for operating
Mente do Brasil after staging or production infrastructure is created.

## Documents

- [Observability](observability.md): structured logs, request IDs, health and readiness endpoints, and future alert requirements.
- [Recovery runbook](recovery_runbook.md): backup, restore, rebuild, rollback, and validation steps.
- Public release configuration validation: run `./.venv/bin/python scripts/validate_public_release_config.py` for prelaunch mode, and `./.venv/bin/python scripts/validate_public_release_config.py --public` before a future public release.

## Scripts

- `scripts/backup_serving_db.sh`
- `scripts/restore_serving_db.sh`
- `scripts/rebuild_serving_db.sh`
- `scripts/validate_public_release_config.py`

The scripts do not contain hardcoded passwords. Local database credentials must
come from `.env`, Docker Compose service environment, or the deployment secret
manager used in a future infrastructure phase.
