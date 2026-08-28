from __future__ import annotations

import getpass
import os
from pathlib import Path
from typing import Any


def _external_libpq_password_configured() -> bool:
    """Return whether libpq can resolve a password without an inline prompt."""
    if os.environ.get("PGPASSWORD"):
        return True

    configured_file = os.environ.get("PGPASSFILE")
    if configured_file:
        return Path(configured_file).expanduser().is_file()

    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        return bool(
            appdata
            and (Path(appdata) / "postgresql" / "pgpass.conf").is_file()
        )
    return (Path.home() / ".pgpass").is_file()


def connection_parameters(args: Any) -> dict[str, Any]:
    """Build psycopg connection parameters without logging credential values."""
    parameters = {
        "host": args.host,
        "port": args.port,
        "dbname": args.dbname,
        "user": args.user,
    }
    if not _external_libpq_password_configured():
        parameters["password"] = getpass.getpass(
            f"Password for PostgreSQL user {args.user}: "
        )
    return parameters
