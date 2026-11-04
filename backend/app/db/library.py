from app.db.database import get_connection

CREATE_CASE_LIBRARY = """
CREATE TABLE IF NOT EXISTS case_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    citation TEXT,
    court TEXT,
    decided_year INTEGER,
    outcome TEXT NOT NULL CHECK (outcome IN ('Accepted', 'Rejected')),
    content TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


def ensure_case_library():
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_CASE_LIBRARY)
        conn.commit()
    finally:
        conn.close()


def insert_case(user_id, case):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_CASE_LIBRARY)
            cur.execute(
                """
                INSERT INTO case_library
                (title, citation, court, decided_year, outcome, content, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, title, citation, court, decided_year,
                          outcome, content, created_by, created_at
                """,
                (
                    case.title.strip(),
                    _blank_to_none(case.citation),
                    _blank_to_none(case.court),
                    case.decided_year,
                    case.outcome,
                    case.content.strip(),
                    user_id,
                )
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        conn.close()


def list_cases(limit):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_CASE_LIBRARY)
            cur.execute(
                """
                SELECT id, title, citation, court, decided_year,
                       outcome, NULL::text AS content, created_by, created_at
                FROM case_library
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cur.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def get_case(case_id):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_CASE_LIBRARY)
            cur.execute(
                """
                SELECT id, title, citation, court, decided_year,
                       outcome, content, created_by, created_at
                FROM case_library
                WHERE id = %s
                """,
                (case_id,)
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        conn.close()


def delete_case(case_id, user_id):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_CASE_LIBRARY)
            cur.execute(
                """
                DELETE FROM case_library
                WHERE id = %s AND created_by = %s
                RETURNING id
                """,
                (case_id, user_id)
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        conn.close()


def load_precedents(limit=500):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_CASE_LIBRARY)
            cur.execute(
                """
                SELECT id, title, citation, court, decided_year,
                       outcome, content, created_by, created_at
                FROM case_library
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cur.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def _blank_to_none(value):
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
