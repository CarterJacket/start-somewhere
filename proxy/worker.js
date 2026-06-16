/**
 * Start Somewhere - Claude API proxy (Cloudflare Worker)
 *
 * Holds the Anthropic API key server-side so the public site can call Claude
 * without ever exposing the key in the browser. Supports two modes:
 *   - "analyze": job-description -> structured skill JSON (powers job-analyzer.html)
 *   - "ask":     free-text career question -> coaching answer (powers ask.html)
 *
 * The system prompts live here, not in the frontend, so the key cannot be
 * repurposed as a general-purpose Claude endpoint. Input sizes and output
 * tokens are capped to bound cost per call.
 *
 * DEPLOY (see proxy/README.md for the full walkthrough):
 *   1. Create a Worker at dash.cloudflare.com
 *   2. Paste this file in
 *   3. Add an encrypted secret named ANTHROPIC_API_KEY (your key)
 *   4. Deploy, copy the workers.dev URL, put it in ss-ai-config.js
 */

// --- Config -----------------------------------------------------------------

// Browser origins allowed to call this Worker. Add your custom domain here too.
const ALLOWED_ORIGINS = [
  "https://carterjacket.github.io",
  "http://localhost:4322",
  "http://127.0.0.1:4322",
  "http://localhost:8000",
];

// Cheap, fast model for both modes. For richer career advice you can switch the
// "ask" mode to "claude-sonnet-4-6" below; it costs more but reads better.
const MODEL_ANALYZE = "claude-haiku-4-5-20251001";
const MODEL_ASK = "claude-haiku-4-5-20251001";

const MAX_INPUT_CHARS = 12000;   // cap a single job description / question
const MAX_SKILLS = 120;          // cap the known-skills list the client may send
const MAX_HISTORY_TURNS = 8;     // cap prior conversation turns for "ask"
const ANTHROPIC_VERSION = "2023-06-01";

// --- Worker entry ------------------------------------------------------------

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const cors = corsHeaders(origin);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }
    if (request.method !== "POST") {
      return json({ error: "Method not allowed" }, 405, cors);
    }
    if (!env.ANTHROPIC_API_KEY) {
      return json({ error: "Server missing ANTHROPIC_API_KEY secret" }, 500, cors);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "Invalid JSON body" }, 400, cors);
    }

    const mode = body.mode;
    const input = typeof body.input === "string" ? body.input.trim() : "";

    if (!input) return json({ error: "Missing 'input'" }, 400, cors);
    if (input.length > MAX_INPUT_CHARS) {
      return json({ error: "Input too long" }, 413, cors);
    }

    let payload;
    if (mode === "analyze") {
      payload = buildAnalyzePayload(input, body.skills);
    } else if (mode === "ask") {
      payload = buildAskPayload(input, body.history);
    } else {
      return json({ error: "Unknown 'mode' (expected 'analyze' or 'ask')" }, 400, cors);
    }

    // Forward to Anthropic. The key never leaves the Worker.
    const upstream = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": env.ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
      },
      body: JSON.stringify(payload),
    });

    const text = await upstream.text();
    // Pass the Anthropic response straight through; the client reads
    // data.content[0].text exactly as it did with the direct call.
    return new Response(text, {
      status: upstream.status,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  },
};

// --- Prompt builders ---------------------------------------------------------

function buildAnalyzePayload(jobDesc, skills) {
  const known = Array.isArray(skills)
    ? skills.filter((s) => typeof s === "string").slice(0, MAX_SKILLS)
    : [];
  const skillLine = known.length
    ? `\n- "name": Skill name. MUST match one from this list when possible: ${known.join(", ")}`
    : `\n- "name": Skill name`;

  const systemPrompt =
`You are a job description analyzer. Given a job posting, extract structured information and return ONLY valid JSON (no markdown) with this exact structure:
{
  "company": "Company Name or null if not found",
  "job_title": "The job title",
  "skills": [
    {${skillLine}
      "importance": "required" or "preferred",
      "context": "Brief 1-sentence explanation of why this job needs this skill"
    }
  ],
  "summary": "A 2-3 sentence summary of what this role is about and what kind of candidate would thrive"
}

Rules:
- Map skills to the provided list whenever there is a reasonable match (e.g. "Excel" maps to "Computers and Electronics"; "SQL" or "data analysis" maps to "Mathematics" or "Programming"; "communication skills" maps to "Speaking" or "Writing"; "project management" maps to "Administration and Management").
- Include 5-10 skills maximum, prioritizing the most important ones.
- Mark skills explicitly listed as "required" or "must have" as "required". Everything else is "preferred".
- Be specific in the context field; reference the actual job duties mentioned.
- Return ONLY the JSON object, no markdown formatting.`;

  return {
    model: MODEL_ANALYZE,
    max_tokens: 1024,
    system: systemPrompt,
    messages: [{ role: "user", content: "Analyze this job posting:\n\n" + jobDesc }],
  };
}

function buildAskPayload(question, history) {
  const systemPrompt =
`You are the career coach inside "Start Somewhere," a free web app that helps people early in their careers or exploring new paths. Your audience is students, recent graduates, and career changers, many of whom feel overwhelmed about where to begin.

How to respond:
- Be warm, concrete, and encouraging. No corporate filler.
- Give a clear next step the person can take this week, not just theory.
- When relevant, point them toward the kinds of tools Start Somewhere offers: exploring skills, building a skill with free courses, analyzing a job posting, or short skill sprints.
- Keep answers tight: a few short paragraphs or a short list. Avoid walls of text.
- You are not a substitute for professional or financial advice; if asked about money, legal, or mental-health specifics, gently suggest a qualified professional.
- Do not invent statistics or cite sources you are unsure of.`;

  const turns = Array.isArray(history)
    ? history
        .filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
        .slice(-MAX_HISTORY_TURNS)
        .map((m) => ({ role: m.role, content: m.content.slice(0, MAX_INPUT_CHARS) }))
    : [];

  return {
    model: MODEL_ASK,
    max_tokens: 900,
    system: systemPrompt,
    messages: [...turns, { role: "user", content: question }],
  };
}

// --- Helpers -----------------------------------------------------------------

function corsHeaders(origin) {
  const allow = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}
