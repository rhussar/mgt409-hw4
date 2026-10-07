# Campus Customs — Homework 4

A Yale-inspired apparel storefront with React, TypeScript, FastAPI, SQLite, and a PydanticAI shopping assistant. The assistant looks up product facts in the supplied database, returns clickable matches, and remembers chats for signed-in shoppers.

## Local data and key

Extract the assignment's `data.zip` into this `hw4` folder. The local paths should be `data/campus_customs.db` and `data/products/`. The data pack is required to run the shop and is excluded from Git.

Copy `.env.example` to `.env` and replace the placeholder with a valid `PORTKEY_API_KEY` or set `OPENAI_API_KEY` instead. Keep `.env` private. The model defaults to `gpt-5.6`; `CAMPUS_CUSTOMS_MODEL` can override it. Without a key, the catalogue and accounts work, while `/api/chat` returns a service-unavailable response.

## Run locally

Use Python 3.12 or newer and Node.js 20 or newer. From `hw4`, start the backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn main:app --reload --port 8000
```

In another terminal, from `hw4`:

```bash
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173/>. Vite proxies `/api` and `/media` to FastAPI on port 8000. The API health check is <http://127.0.0.1:8000/api/health>. For the supplied test account, use `test@campuscustoms.yale.edu` and password `password`.

## Review the work

- `AI_prompts.md` records the prompts used for all 13 problems.
- `output/harness.md` explains the schema, agent, tools, safety, and setup.
- `output/design.md` and `output/usability.md` explain the design and improvements.
- Open `output/app_check.html` locally for captioned screenshots of the live shop.
- `output/audit_trail.json` keeps append-only tool and agent-run events without secrets or chat text.

Build the frontend with `npm run build` from `frontend`. The backend dependencies are also available from the root `requirements.txt`.
