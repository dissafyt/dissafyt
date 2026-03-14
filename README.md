# Dissafyt

Dissafyt is a Website-as-a-Service platform built on Django that dynamically renders client websites from templates and CMS data.

## 🚀 Running Locally

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Download a local LLM model for chat-style responses
# This may take several minutes and requires ~4GB disk space.
#
# If the model is hosted on Hugging Face, you will likely need a token.
# Set it like:
#   export HUGGINGFACE_TOKEN="<your token>"
#
./scripts/download_model.sh

# Set the model path for the app (example):
export LLM_MODEL_PATH="$PWD/models/ggml-alpaca-7b-q4.bin"

# Option A (local model): set LLM_MODEL_PATH as above.
# Option B (Google GenAI): set a Google API key to use the cloud model.
#   export GOOGLE_API_KEY="<your key>"

# (Optional) Set a WhatsApp number for human handoff:
# export HUMAN_WHATSAPP_NUMBER="+15551234567"

# Run database migrations
python manage.py migrate

# Start the dev server
python manage.py runserver 0.0.0.0:8000
```

Then open: `http://localhost:8000`

## 🧱 Render Deployment (build + start)

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn dissafyt_platform.wsgi --log-file -`

## 📚 Docs

See `/docs` for architecture notes and the project roadmap.
