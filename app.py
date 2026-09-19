from flask import Flask, redirect, request, session
import os
import secrets
import hashlib
import base64
import requests
from openai import OpenAI
app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
CLIENT_ID = os.environ.get("X_CLIENT_ID")
CLIENT_SECRET = os.environ.get("X_CLIENT_SECRET")
REDIRECT_URI = "https://x-ai-bot-dkl6.onrender.com/callback"

AUTH_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"

SCOPES = [
    "tweet.read",
    "tweet.write",
    "users.read",
    "offline.access"
]


def create_code_verifier():
    return secrets.token_urlsafe(64)


def create_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@app.route("/")
def home():
    return "X AI Bot is running!"


@app.route("/login")
def login():
    verifier = create_code_verifier()
    challenge = create_code_challenge(verifier)

    state = secrets.token_urlsafe(32)

    session["code_verifier"] = verifier
    session["state"] = state

    url = (
        f"{AUTH_URL}"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={'%20'.join(SCOPES)}"
        f"&state={state}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )

    return redirect(url)


@app.route("/callback")
def callback():
    if request.args.get("state") != session.get("state"):
        return "State mismatch", 400

    code = request.args.get("code")

    if not code:
        return "Authorization failed", 400

    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": session["code_verifier"],
    }

    response = requests.post(
        TOKEN_URL,
        data=data,
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30
    )

    if response.status_code != 200:
        return f"Token error: {response.text}", 400

    token_data = response.json()

    session["access_token"] = token_data["access_token"]

    return "X account connected successfully! 🚀"


@app.route("/me")
def me():
    access_token = session.get("access_token")

    if not access_token:
        return "X account is not connected. Open /login first."

    response = requests.get(
        "https://api.x.com/2/users/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=30
    )

    return response.text
@app.route("/generate")
def generate():
    topic = request.args.get("topic", "Tesla and AI")

    response = client.responses.create(
        model="gpt-5",
        input=f"""
Write one strong, concise X post about:

{topic}

Rules:
- English
- Intelligent and engaging
- One clear idea
- No unnecessary hashtags
- No emojis
"""
    )

    return response.output_text

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
