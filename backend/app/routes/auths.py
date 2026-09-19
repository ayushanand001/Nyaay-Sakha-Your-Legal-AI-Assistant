from fastapi import APIRouter, HTTPException
from app.schemas.auth import RegisterRequest, VerifyRegistrationRequest ,ResendOTPRequest, LoginRequest
from app.db.database import get_connection
from app.core.security import hash_password, verify_password
from app.core.mail import conf
from fastapi_mail import FastMail, MessageSchema, MessageType
from datetime import datetime, timedelta, timezone
import random

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(data: RegisterRequest):

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT id FROM users WHERE email = %s",
                (data.email.lower(),)
            )

            if cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )

            otp = str(random.randint(100000, 999999))

            otp_hash = hash_password(otp)

            password_hash = hash_password(data.password)

            expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

            cur.execute(
                """
                INSERT INTO pending_registrations
                (name, email, password_hash, phone, otp_hash, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    data.name,
                    data.email.lower(),
                    password_hash,
                    data.phone,
                    otp_hash,
                    expires_at
                )
            )

            registration_id = cur.fetchone()[0]

        conn.commit()

        message = MessageSchema(
            subject="Nyaay Sakha - Email Verification",
            recipients=[data.email.lower()],
            body=f"""
            <html>
                <body>
                    <h2>Nyaay Sakha</h2>

                    <p>Your verification OTP is:</p>

                    <h1>{otp}</h1>

                    <p>This OTP is valid for 10 minutes.</p>

                    <p>If you did not request this registration, please ignore this email.</p>
                </body>
            </html>
            """,
            subtype=MessageType.html
        )

        await FastMail(conf).send_message(message)

        return {
            "message": "Registration created. OTP verification required.",
            "registration_id": str(registration_id)
        }

    finally:
        conn.close()


@router.post("/verify-registration")
def verify_registration(data: VerifyRegistrationRequest):

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id, name, email, password_hash, phone,
                       otp_hash, expires_at
                FROM pending_registrations
                WHERE id = %s
                """,
                (data.registration_id,)
            )

            registration = cur.fetchone()

            if not registration:
                raise HTTPException(
                    status_code=404,
                    detail="Registration not found"
                )

            (
                registration_id,
                name,
                email,
                password_hash,
                phone,
                otp_hash,
                expires_at
            ) = registration

            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(
                    status_code=400,
                    detail="OTP expired"
                )

            if not verify_password(data.otp, otp_hash):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid OTP"
                )

            cur.execute(
                """
                INSERT INTO users
                (name, email, password_hash, phone, email_verified)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    name,
                    email,
                    password_hash,
                    phone,
                    True
                )
            )

            cur.execute(
                """
                DELETE FROM pending_registrations
                WHERE id = %s
                """,
                (registration_id,)
            )

        conn.commit()

        return {
            "message": "Registration successful"
        }

    finally:
        conn.close()

@router.post("/resend-otp")
async def resend_otp(data: ResendOTPRequest):

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id, email
                FROM pending_registrations
                WHERE id = %s
                """,
                (data.registration_id,)
            )

            registration = cur.fetchone()

            if not registration:
                raise HTTPException(
                    status_code=404,
                    detail="Registration not found"
                )

            registration_id, email = registration

            otp = str(random.randint(100000, 999999))

            otp_hash = hash_password(otp)

            expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

            cur.execute(
                """
                UPDATE pending_registrations
                SET otp_hash = %s,
                    expires_at = %s
                WHERE id = %s
                """,
                (
                    otp_hash,
                    expires_at,
                    registration_id
                )
            )

        conn.commit()

        message = MessageSchema(
            subject="Nyaay Sakha - New Verification OTP",
            recipients=[email],
            body=f"""
            <html>
                <body>
                    <h2>Nyaay Sakha</h2>

                    <p>Your new verification OTP is:</p>

                    <h1>{otp}</h1>

                    <p>This OTP is valid for 10 minutes.</p>

                    <p>Your previous OTP is no longer valid.</p>
                </body>
            </html>
            """,
            subtype=MessageType.html
        )

        await FastMail(conf).send_message(message)

        return {
            "message": "New OTP sent successfully"
        }

    finally:
        conn.close()