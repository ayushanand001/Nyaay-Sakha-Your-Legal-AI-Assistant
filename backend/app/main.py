from fastapi import FastAPI
import resend
import os
from app.routes.auths import router as auth_router

resend.api_key = os.getenv("RESEND_API_KEY")
app = FastAPI()

app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "message": "Nyaay Sakha API is running"
    }

@app.post("/send-email")
def send_email():

    params = {
        "from": "onboarding@resend.dev",
        "to": ["your_email@gmail.com"],
        "subject": "Nyaay Sakha Test",
        "html": "<h2>Hello from Nyaay Sakha!</h2><p>Resend is working.</p>"
    }

    email = resend.Emails.send(params)

    return {
        "message": "Email sent",
        "email": str(email)
    }