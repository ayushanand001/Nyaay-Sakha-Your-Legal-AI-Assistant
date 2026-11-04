from app.db.database import get_connection

CREATE_UPLOADS = """
CREATE TABLE IF NOT EXISTS uploaded_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    content_type TEXT NOT NULL,
    extension TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    extracted_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


def insert_upload(user_id, filename, stored_path, content_type, extension, size_bytes, text):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_UPLOADS)
            cur.execute(
                """
                INSERT INTO uploaded_documents
                (user_id, original_filename, stored_path, content_type,
                 extension, size_bytes, extracted_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, original_filename, content_type, size_bytes,
                          extracted_text, created_at, stored_path
                """,
                (
                    user_id,
                    filename,
                    stored_path,
                    content_type,
                    extension,
                    size_bytes,
                    text,
                )
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        conn.close()


def list_uploads(user_id, limit):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_UPLOADS)
            cur.execute(
                """
                SELECT id, original_filename, content_type, size_bytes,
                       left(extracted_text, 500), created_at, stored_path,
                       char_length(extracted_text)
                FROM uploaded_documents
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            rows = cur.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def get_upload(upload_id, user_id):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_UPLOADS)
            cur.execute(
                """
                SELECT id, original_filename, content_type, size_bytes,
                       extracted_text, created_at, stored_path
                FROM uploaded_documents
                WHERE id = %s AND user_id = %s
                """,
                (upload_id, user_id)
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        conn.close()


def delete_upload(upload_id, user_id):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_UPLOADS)
            cur.execute(
                """
                DELETE FROM uploaded_documents
                WHERE id = %s AND user_id = %s
                RETURNING stored_path
                """,
                (upload_id, user_id)
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        conn.close()
