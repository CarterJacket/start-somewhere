"""Start Somewhere - LLM evaluation harness.

Scores the two production LLM features:

  1. Job Analyzer (structured extraction) - rule-based scoring on the JSON output:
     valid JSON, has a title, sane skill count, every skill maps to the known
     O*NET taxonomy, valid importance values, and at least one expected category.

  2. Career Coach (free-text advice) - LLM-as-judge: a stronger model grades each
     answer pass/fail against a written rubric.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...      # the SDK reads this; never hardcode
    python run_evals.py                      # full suite
    python run_evals.py --analyzer-only
    python run_evals.py --qa-only

Writes results.md and results.json next to this file.
"""

import argparse
import json
import os
import sys
import time

try:
    from anthropic import Anthropic
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r requirements.txt")

from known_skills import KNOWN_SKILLS
from cases import ANALYZER_CASES, QA_CASES

MODEL_ANALYZE = "claude-haiku-4-5-20251001"
MODEL_ASK = "claude-haiku-4-5-20251001"
JUDGE_MODEL = "claude-sonnet-4-6"  # a stronger model grades the coach's answers

# --- Prompts (mirror proxy/worker.js so evals reflect production) -------------

ANALYZE_SYSTEM = (
    "You are a job description analyzer. Given a job posting, extract structured "
    "information and return ONLY valid JSON (no markdown) with this exact structure:\n"
    "{\n"
    '  "company": "Company Name or null if not found",\n'
    '  "job_title": "The job title",\n'
    '  "skills": [\n'
    "    {\n"
    '      "name": "Skill name. MUST match one from this list when possible: '
    + ", ".join(KNOWN_SKILLS) + '",\n'
    '      "importance": "required" or "preferred",\n'
    '      "context": "Brief 1-sentence explanation of why this job needs this skill"\n'
    "    }\n"
    "  ],\n"
    '  "summary": "A 2-3 sentence summary of what this role is about and what kind of candidate would thrive"\n'
    "}\n\n"
    "Rules:\n"
    "- Map skills to the provided list whenever there is a reasonable match.\n"
    "- Include 5-10 skills maximum, prioritizing the most important ones.\n"
    '- Mark skills explicitly listed as "required" or "must have" as "required". Everything else is "preferred".\n'
    "- Be specific in the context field; reference the actual job duties mentioned.\n"
    "- Return ONLY the JSON object, no markdown formatting."
)

ASK_SYSTEM = (
    'You are the career coach inside "Start Somewhere," a free web app that helps '
    "people early in their careers or exploring new paths. Be warm, concrete, and "
    "encouraging. Give a clear next step the person can take this week. Keep answers "
    "tight. You are not a substitute for professional, financial, or mental-health "
    "advice; if asked about those specifics, gently suggest a qualified professional. "
    "Do not invent statistics."
)


def strip_fences(text):
    return text.replace("```json", "").replace("```", "").strip()


def analyze(client, desc):
    msg = client.messages.create(
        model=MODEL_ANALYZE, max_tokens=1024, system=ANALYZE_SYSTEM,
        messages=[{"role": "user", "content": "Analyze this job posting:\n\n" + desc}],
    )
    return strip_fences(msg.content[0].text)


def score_analyzer(raw, case):
    checks = {}
    try:
        data = json.loads(raw)
        checks["valid_json"] = True
    except json.JSONDecodeError:
        return {"valid_json": False}, None

    skills = data.get("skills", []) if isinstance(data, dict) else []
    names = [s.get("name") for s in skills if isinstance(s, dict)]

    checks["has_job_title"] = bool(data.get("job_title"))
    checks["sane_skill_count"] = 1 <= len(skills) <= 12
    checks["skills_in_taxonomy"] = len(names) > 0 and all(n in KNOWN_SKILLS for n in names)
    checks["valid_importance"] = all(
        isinstance(s, dict) and s.get("importance") in ("required", "preferred") for s in skills
    )
    checks["matches_expected"] = any(n in case["expect_any"] for n in names)
    return checks, names


def judge(client, question, answer, rubric):
    judge_system = (
        "You are a strict evaluator of a career-coaching assistant. Given the user "
        "question, the assistant's answer, and a rubric, decide if the answer meets "
        "the rubric. Return ONLY JSON: "
        '{"pass": true|false, "reason": "one sentence"}'
    )
    content = (
        f"USER QUESTION:\n{question}\n\nASSISTANT ANSWER:\n{answer}\n\n"
        f"RUBRIC (the answer must satisfy this):\n{rubric}"
    )
    msg = client.messages.create(
        model=JUDGE_MODEL, max_tokens=300, system=judge_system,
        messages=[{"role": "user", "content": content}],
    )
    try:
        return json.loads(strip_fences(msg.content[0].text))
    except json.JSONDecodeError:
        return {"pass": False, "reason": "judge returned unparseable output"}


def run_analyzer(client):
    rows = []
    print("\n=== Job Analyzer (rule-based) ===")
    for case in ANALYZER_CASES:
        raw = analyze(client, case["desc"])
        checks, names = score_analyzer(raw, case)
        passed = all(checks.values())
        rows.append({"id": case["id"], "passed": passed, "checks": checks, "skills": names})
        mark = "PASS" if passed else "FAIL"
        fails = [k for k, v in checks.items() if not v]
        print(f"  [{mark}] {case['id']:<22} {'' if passed else 'failed: ' + ', '.join(fails)}")
        time.sleep(0.2)
    return rows


def run_qa(client):
    rows = []
    print("\n=== Career Coach (LLM-as-judge) ===")
    for case in QA_CASES:
        msg = client.messages.create(
            model=MODEL_ASK, max_tokens=900, system=ASK_SYSTEM,
            messages=[{"role": "user", "content": case["question"]}],
        )
        answer = msg.content[0].text
        verdict = judge(client, case["question"], answer, case["rubric"])
        passed = bool(verdict.get("pass"))
        rows.append({"id": case["id"], "passed": passed, "reason": verdict.get("reason", ""), "answer": answer})
        print(f"  [{'PASS' if passed else 'FAIL'}] {case['id']:<22} {verdict.get('reason','')}")
        time.sleep(0.2)
    return rows


def write_report(analyzer_rows, qa_rows):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "results.json"), "w") as f:
        json.dump({"analyzer": analyzer_rows, "qa": qa_rows}, f, indent=2)

    lines = ["# Eval results\n"]
    if analyzer_rows:
        passed = sum(r["passed"] for r in analyzer_rows)
        lines.append(f"## Job Analyzer: {passed}/{len(analyzer_rows)} cases passed\n")
        # per-check pass rate
        all_checks = {}
        for r in analyzer_rows:
            for k, v in r["checks"].items():
                all_checks.setdefault(k, []).append(v)
        lines.append("| Check | Pass rate |")
        lines.append("|---|---|")
        for k, vals in all_checks.items():
            lines.append(f"| {k} | {sum(vals)}/{len(vals)} |")
        lines.append("")
    if qa_rows:
        passed = sum(r["passed"] for r in qa_rows)
        lines.append(f"## Career Coach: {passed}/{len(qa_rows)} cases passed\n")
        lines.append("| Case | Result | Judge reason |")
        lines.append("|---|---|---|")
        for r in qa_rows:
            lines.append(f"| {r['id']} | {'PASS' if r['passed'] else 'FAIL'} | {r['reason']} |")
        lines.append("")
    with open(os.path.join(here, "results.md"), "w") as f:
        f.write("\n".join(lines))
    print(f"\nWrote results.md and results.json to {here}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyzer-only", action="store_true")
    ap.add_argument("--qa-only", action="store_true")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY in your environment first.")
    client = Anthropic()

    analyzer_rows = [] if args.qa_only else run_analyzer(client)
    qa_rows = [] if args.analyzer_only else run_qa(client)

    if analyzer_rows:
        p = sum(r["passed"] for r in analyzer_rows)
        print(f"\nAnalyzer: {p}/{len(analyzer_rows)} passed")
    if qa_rows:
        p = sum(r["passed"] for r in qa_rows)
        print(f"Coach: {p}/{len(qa_rows)} passed")
    write_report(analyzer_rows, qa_rows)


if __name__ == "__main__":
    main()
