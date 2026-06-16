# Start Somewhere - Claude API proxy

A tiny Cloudflare Worker that holds the Anthropic API key server-side so the
public site can call Claude without exposing the key in the browser. It powers
the job analyzer and the career Q&A assistant.

## Why this exists

The site is static (GitHub Pages), so there is no server to keep a secret. If
the frontend called `api.anthropic.com` directly, the key would be visible in
the browser and anyone could spend it. This Worker is that missing server: the
key lives only here, as an encrypted secret.

## Deploy (about 15 minutes, no command line required)

1. Go to **dash.cloudflare.com** and sign in (free account is fine).
2. In the left sidebar: **Workers & Pages** -> **Create** -> **Create Worker**.
3. Give it a name (e.g. `start-somewhere-ai`) and click **Deploy** to create the
   starter, then **Edit code**.
4. Delete the starter code, paste in the full contents of `worker.js`, and click
   **Deploy**.
5. Add your key as a secret: open the Worker -> **Settings** -> **Variables and
   Secrets** -> **Add** -> type **Secret**, name it exactly `ANTHROPIC_API_KEY`,
   paste your key as the value, **Save and deploy**.
6. Copy the Worker URL (looks like `https://start-somewhere-ai.<you>.workers.dev`).
7. Open `ss-ai-config.js` in this repo and set `window.SS_AI_PROXY` to that URL.

That is it. The job analyzer and `ask.html` will now route through the Worker.

## Set a spending backstop (recommended)

In the Anthropic Console -> **Billing** -> set a monthly **usage limit** (for
example $5). This caps the blast radius no matter what. The Worker also caps
input length and output tokens per call, and only accepts the two known modes,
so the key cannot be used as a general Claude endpoint. CORS is locked to the
site origin, which stops casual browser abuse from other pages (note: it does
not stop a determined person using curl, which is why the spend limit matters).

## Local testing

The Worker allows `http://localhost:4322` and `http://localhost:8000` origins so
you can test the pages locally against the deployed Worker. To change allowed
origins, edit `ALLOWED_ORIGINS` at the top of `worker.js` and redeploy.

## Models

Both modes default to `claude-haiku-4-5-20251001` (cheap and fast). For richer
career advice, change `MODEL_ASK` in `worker.js` to `claude-sonnet-4-6` and
redeploy. The system prompts that constrain each mode live in `worker.js`.
