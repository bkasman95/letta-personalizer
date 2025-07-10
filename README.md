# Personalized Email UI Demo

This simple Flask application demonstrates how to:

1. Select a user profile from an in-memory list
2. Provide a custom prompt
3. Generate a personalised email template using Letta (if configured) or a local fallback generator.

## Quick Start

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure Letta Cloud or self-hosted server
export LETTA_API_KEY=<your-letta-api-key>         # For Letta Cloud
# export LETTA_BASE_URL=http://localhost:8283      # For self-hosted server

# Run the app
python app.py
```

Then open `http://localhost:5000` in your browser.

If `LETTA_API_KEY` or `LETTA_BASE_URL` is **not** set (or the `letta-client` package is missing),
the app falls back to a simple string-based email generator.

## File Overview

- `app.py` – Flask backend + Letta integration
- `templates/index.html` – Basic HTML/JS front-end
- `requirements.txt` – Python dependencies

## Extending the Demo

1. Add more users to the `USERS` dictionary in `app.py`.
2. Replace the inline fallback generator with your own logic or templates.
3. Customise memory blocks or tool configuration when creating the Letta agent. 