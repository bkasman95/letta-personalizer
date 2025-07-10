from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime

try:
    from letta_client import Letta
except ImportError:
    Letta = None  # Letta SDK not installed / available

app = Flask(__name__)

# ---------------------------------------------------------------------------
# User data store (in-memory for demo purposes)
# ---------------------------------------------------------------------------
USERS = {
    "user1": {
        "external_id": "user1",
        "first_name": "Jon",
        "has_profile_picture": True,
        "dob": "1988-02-14",
        "favorite_color": "blue",
        "favorite_album": "Abbey Road",
        "last_contact_date": "2025-02-02",
    },
    # Additional mock users
    "user2": {
        "external_id": "user2",
        "first_name": "Alice",
        "has_profile_picture": False,
        "dob": "1992-07-09",
        "favorite_color": "green",
        "favorite_album": "1989",
        "last_contact_date": "2025-03-15",
    },
    "user3": {
        "external_id": "user3",
        "first_name": "Carlos",
        "has_profile_picture": True,
        "dob": "1985-11-30",
        "favorite_color": "red",
        "favorite_album": "Thriller",
        "last_contact_date": "2025-01-20",
    },
    "user4": {
        "external_id": "user4",
        "first_name": "Mei",
        "has_profile_picture": True,
        "dob": "1998-05-22",
        "favorite_color": "purple",
        "favorite_album": "Future Nostalgia",
        "last_contact_date": "2024-12-11",
    },
}

# Cache of {external_id: agent_id} when using Letta
AGENT_CACHE = {}

# Initialise Letta client if credentials exist
LETTA_TOKEN = os.getenv("LETTA_API_KEY")
LETTA_BASE_URL = os.getenv("LETTA_BASE_URL")

letta_client = None
if LETTA_TOKEN or LETTA_BASE_URL:
    # Only initialise if either credential is provided and SDK is installed
    if Letta is None:
        raise RuntimeError(
            "letta-client package not installed. Run `pip install letta-client`."
        )
    # Use token if provided (Letta Cloud) otherwise rely on base_url for self-hosted
    client_kwargs = {}
    if LETTA_TOKEN:
        client_kwargs["token"] = LETTA_TOKEN
    if LETTA_BASE_URL:
        client_kwargs["base_url"] = LETTA_BASE_URL

    letta_client = Letta(**client_kwargs)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _ensure_agent_for_user(user):
    """Create (or fetch cached) agent for a given user record."""
    ext_id = user["external_id"]
    if ext_id in AGENT_CACHE:
        return AGENT_CACHE[ext_id]

    if not letta_client:
        return None  # We are in offline mode

    memory_blocks = [
        {
            "label": "human",
            "value": f"The user's name is {user['first_name']}.",
        },
        {
            "label": "persona",
            "value": "You are an AI assistant that crafts engaging, personalised email templates.",
        },
        {
            "label": "profile",
            "value": (
                f"Has profile picture: {user['has_profile_picture']}.\n"
                f"Date of birth: {user['dob']}.\n"
                f"Favourite colour: {user['favorite_color']}.\n"
                f"Favourite album: {user['favorite_album']}.\n"
                f"Last contact date: {user['last_contact_date']}."
            ),
            "description": "Metadata about the recipient used for personalisation.",
        },
    ]

    agent = letta_client.agents.create(
        memory_blocks=memory_blocks,
        model="openai/gpt-4o-mini",
        embedding="openai/text-embedding-3-small",
    )
    AGENT_CACHE[ext_id] = agent.id
    return agent.id


def _fallback_generate_email(user, prompt):
    """Very naive offline email generator when Letta is not configured."""
    subj = (
        f"{user['first_name']}, it's been a while since {user['last_contact_date']}!"
        f" Have you been spinning {user['favorite_album']} lately?"
    )
    body = (
        f"Hi {user['first_name']},<br/><br/>"
        f"I hope you're doing great! The last time we connected was on {user['last_contact_date']}. "
        f"I was just thinking about your favourite album, {user['favorite_album']}, and wondered if it's still at the top of your playlist. "
        f"I'd love to hear what you're listening to these days.\n<br/><br/>Cheers,\n<br/>Your AI email assistant"
    )
    return {
        "template_name": "catch-up",
        "subject": subj,
        "body": body,
        "plaintext_body": body.replace("<br/>", "\n").replace("<br>", "\n"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", users=USERS.values())


@app.route("/get_message", methods=["POST"])
def get_message():
    data = request.get_json()
    user_id = data.get("user_id")
    prompt = data.get("prompt", "").strip()

    if not user_id or user_id not in USERS:
        return jsonify({"error": "Invalid user_id"}), 400
    if not prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    user = USERS[user_id]

    # Use Letta if configured
    if letta_client:
        agent_id = _ensure_agent_for_user(user)
        response = letta_client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": prompt}],
        )
        # Extract assistant content (first assistant_message found)
        assistant_content = next(
            (
                msg.content
                for msg in response.messages
                if msg.message_type == "assistant_message"
            ),
            None,
        )
        return jsonify({"response": assistant_content})

    # Fallback offline generation
    template = _fallback_generate_email(user, prompt)
    return jsonify(template)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True) 