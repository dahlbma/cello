#!/usr/bin/env python3
"""List common microtube racks that are empty in either database.

The script only reads the database. It does not delete or update any rows.

Run from the repository root with:

    ./.venv/bin/python "tools/matrix_to_be deleted.py"

Connection defaults are read from ``tools/config.py``. They can be
overridden with the ``CELLO_DB_HOST``, ``CELLO_DB_USER``,
``CELLO_DB_PASSWORD`` and ``CELLO_DB_PORT`` environment variables, or with
command-line options.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, List, Tuple

DISCARDED_MATRIX_ID = "DISCARDED"
DEFAULT_DDD_SCHEMA = "ddd_microtube"
DEFAULT_MICROTUBE_SCHEMA = "microtube"
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def load_tool_database_config() -> Dict[str, Any]:
    config_path = Path(__file__).resolve().with_name("config.py")
    spec = importlib.util.spec_from_file_location("cello_backend_config", config_path)
    if spec is None or spec.loader is None:
        return {}

    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    database_config = getattr(config_module, "database", {})
    return database_config if isinstance(database_config, dict) else {}


def valid_identifier(value: str, option_name: str) -> str:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"{option_name} must contain only letters, numbers and underscores"
        )
    return value


def build_query(ddd_schema: str, microtube_schema: str) -> str:
    """Build the status query after schema names have been validated."""
    valid_identifier(ddd_schema, "--ddd-schema")
    valid_identifier(microtube_schema, "--microtube-schema")

    return f"""
        WITH common_racks AS (
            SELECT DISTINCT d.matrix_id
            FROM `{ddd_schema}`.`matrix` AS d
            INNER JOIN `{microtube_schema}`.`matrix` AS m
                ON m.matrix_id = d.matrix_id
            WHERE d.matrix_id <> %s
              AND m.matrix_id <> %s
        )
        SELECT
            common_racks.matrix_id,
            CASE WHEN EXISTS (
                SELECT 1
                FROM `{ddd_schema}`.`matrix_tube` AS dmt
                WHERE dmt.matrix_id = common_racks.matrix_id
            ) THEN 1 ELSE 0 END AS ddd_has_tubes,
            CASE WHEN EXISTS (
                SELECT 1
                FROM `{microtube_schema}`.`matrix_tube` AS mt
                WHERE mt.matrix_id = common_racks.matrix_id
            ) THEN 1 ELSE 0 END AS microtube_has_tubes
        FROM common_racks
        ORDER BY common_racks.matrix_id
    """


def find_common_rack_statuses(
    connection: Any,
    ddd_schema: str,
    microtube_schema: str,
) -> List[Tuple[str, bool, bool]]:
    query = build_query(ddd_schema, microtube_schema)
    cursor = connection.cursor()
    try:
        cursor.execute(query, (DISCARDED_MATRIX_ID, DISCARDED_MATRIX_ID))
        return [
            (str(matrix_id), bool(ddd_has_tubes), bool(microtube_has_tubes))
            for matrix_id, ddd_has_tubes, microtube_has_tubes in cursor.fetchall()
        ]
    finally:
        cursor.close()


def print_matrix_ids(title: str, matrix_ids: List[str]) -> None:
    print(f"{title} ({len(matrix_ids)}):")
    if matrix_ids:
        print("\n".join(matrix_ids))
    else:
        print("(none)")


def parse_args(database_config: Dict[str, Any]) -> argparse.Namespace:
    environment = os.environ
    parser = argparse.ArgumentParser(
        description=(
            "List matrix_ids that exist in both microtube databases and are "
            "empty in one or both of them."
        )
    )
    parser.add_argument(
        "--host",
        default=environment.get("CELLO_DB_HOST", database_config.get("host", "localhost")),
        help="MySQL host (default: CELLO_DB_HOST or tools/config.py)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(environment.get("CELLO_DB_PORT", database_config.get("port", 3306))),
        help="MySQL port (default: 3306)",
    )
    parser.add_argument(
        "--database",
        default=environment.get("CELLO_DB_NAME", database_config.get("db", "")),
        help="Default MySQL database (default: CELLO_DB_NAME or tools/config.py)",
    )
    parser.add_argument(
        "--user",
        default=environment.get("CELLO_DB_USER", database_config.get("user")),
        help="MySQL user (default: CELLO_DB_USER or tools/config.py)",
    )
    parser.add_argument(
        "--password",
        default=environment.get("CELLO_DB_PASSWORD", database_config.get("password")),
        help="MySQL password (prefer CELLO_DB_PASSWORD for shell history safety)",
    )
    parser.add_argument(
        "--ddd-schema",
        default=environment.get("CELLO_DDD_SCHEMA", DEFAULT_DDD_SCHEMA),
        help=f"DDD schema (default: {DEFAULT_DDD_SCHEMA})",
    )
    parser.add_argument(
        "--microtube-schema",
        default=environment.get("CELLO_MICROTUBE_SCHEMA", DEFAULT_MICROTUBE_SCHEMA),
        help=f"Live schema (default: {DEFAULT_MICROTUBE_SCHEMA})",
    )
    return parser.parse_args()


def connect_to_database(args: argparse.Namespace) -> Any:
    try:
        import MySQLdb
    except ImportError as error:
        raise RuntimeError(
            "MySQLdb is not installed. Install the project's MySQL driver in "
            ".venv, for example: .venv/bin/pip install mysqlclient"
        ) from error

    if not args.user:
        raise RuntimeError("No database user configured; use --user or CELLO_DB_USER")

    password = args.password
    if password is None:
        password = getpass("MySQL password: ")

    return MySQLdb.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        passwd=password,
        db=args.database or None,
        charset="utf8mb4",
        use_unicode=True,
    )


def main() -> int:
    database_config = load_tool_database_config()
    args = parse_args(database_config)

    try:
        connection = connect_to_database(args)
        try:
            statuses = find_common_rack_statuses(
                connection,
                args.ddd_schema,
                args.microtube_schema,
            )
        finally:
            connection.close()
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    ddd_empty = [matrix_id for matrix_id, ddd_has_tubes, _ in statuses if not ddd_has_tubes]
    microtube_empty = [
        matrix_id
        for matrix_id, _, microtube_has_tubes in statuses
        if not microtube_has_tubes
    ]
    empty_in_both = [
        matrix_id
        for matrix_id, ddd_has_tubes, microtube_has_tubes in statuses
        if not ddd_has_tubes and not microtube_has_tubes
    ]

    print(f"Common non-discarded racks checked: {len(statuses)}")
    print()
    print_matrix_ids(
        f"{args.ddd_schema} empty racks (deletion candidates)",
        ddd_empty,
    )
    print()
    print_matrix_ids(
        f"{args.microtube_schema} empty racks (deletion candidates)",
        microtube_empty,
    )
    print()
    print_matrix_ids("Empty in both databases", empty_in_both)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
