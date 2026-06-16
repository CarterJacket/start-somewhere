# Start Somewhere - LLM evals

A small evaluation suite for the two production LLM features. It demonstrates
two standard techniques:

- **Rule-based scoring** for the Job Analyzer, whose output is structured JSON
  and therefore checkable: valid JSON, has a title, sane skill count, every
  skill maps to the known O*NET taxonomy, valid importance values, and at least
  one expected category per case (16 cases).
- **LLM-as-judge** for the Career Coach, whose output is free text: a stronger
  model grades each answer pass/fail against a written rubric (4 cases),
  including a safety case that must refuse to give specific financial advice.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # the SDK reads this; it is never written to disk
python run_evals.py                   # full suite
python run_evals.py --analyzer-only   # just the structured-output checks
python run_evals.py --qa-only         # just the coach + judge
```

Outputs a scorecard to the terminal plus `results.md` (a readable table) and
`results.json` (full detail). Cost is a few cents per full run on Haiku, with
the judge calls on Sonnet.

## Files

```
run_evals.py     harness: runs cases, scores, writes the report
cases.py         the test cases (16 analyzer + 4 coach)
known_skills.py  the O*NET taxonomy the analyzer maps to
requirements.txt anthropic SDK
```

The system prompts in `run_evals.py` mirror `../proxy/worker.js`, so the eval
measures what production actually does. If you change a prompt in the Worker,
update it here too.
