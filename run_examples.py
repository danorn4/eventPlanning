"""Runs the same questions under several prompting strategies and writes the results
to results_examples.md (readable) and results_examples.json (raw).

Uses ask() from nl_query.py, so it needs the same .env settings.
Run: python run_examples.py
"""
import json
import os

import psycopg
from openai import OpenAI
from psycopg.rows import dict_row

import nl_query as nlq

# (label, strategy, use_notes)
CONFIGS = [
    ("zero_shot (schema only)", "zero_shot", False),
    ("single_domain (schema + examples)", "single_domain", False),
    ("cross_domain (schema + library examples)", "cross_domain", False),
    ("zero_shot + notes", "zero_shot", True),
]

# Avoid the exact wording of the single_domain examples, so that strategy isn't helped unfairly
QUESTIONS = [
    "Which DJs are in Provo?",
    "Which caterers charge the least per person?",
    "Which venues can hold at least 200 guests?",
    "Which clients have more than one event?",
    "What is the total confirmed booking cost for each event in 2027?",
    "Which vendors have an average rating of 4.5 or higher?",
    "Which florists are free on 2027-06-12?",
    "Which photo boths are in Orem?",  # deliberate typo
    "What's the cheapest way to cover catering and a photo booth for 100 guests?",
    "Find me something cozy and rustic",
]


def main():
    for var in ("DATABASE_URL_READONLY", "OPENAI_API_KEY", "OPENAI_MODEL"):
        if not os.getenv(var):
            print(f"Missing {var} in .env")
            return

    client = OpenAI()
    results = []
    with psycopg.connect(nlq.DB_URL, row_factory=dict_row) as conn:
        schema = nlq.get_schema_text(conn)
        for q in QUESTIONS:
            print("\nQuestion:", q)
            for label, strategy, use_notes in CONFIGS:
                entry, answer, usage = nlq.ask(client, conn, schema, q, strategy, use_notes)
                status = "ran" if entry["success"] else "ERROR"
                print(f"  {label:<42} {status:<6} {usage.prompt}+{usage.completion} tokens")
                results.append({
                    "question": q, "config": label, "sql": entry["sql"],
                    "ran_ok": entry["success"], "row_count": entry.get("row_count"),
                    "retried": entry.get("retried"), "error": entry["error"], "answer": answer,
                    "prompt_tokens": usage.prompt, "completion_tokens": usage.completion,
                    "est_cost_usd": round(usage.cost(), 6),
                })

    with open("results_examples.json", "w") as f:
        json.dump(results, f, indent=2)
    write_markdown(results)

    tp = sum(r["prompt_tokens"] for r in results)
    tc = sum(r["completion_tokens"] for r in results)
    cost = sum(r["est_cost_usd"] for r in results)
    print(f"\nDone. {len(results)} runs, {tp} prompt + {tc} completion tokens, about ${cost:.4f}")
    print("Wrote results_examples.md and results_examples.json")


def write_markdown(results):
    labels = [c[0] for c in CONFIGS]
    lines = ["# Results: same questions, different prompting strategies\n",
             f"Model: `{nlq.SQL_MODEL}`. 'Ran' means the SQL executed without error. "
             "It does NOT mean the answer is correct. Check the 'Correct?' lines by hand.\n",
             "## Summary (did the SQL run?)\n",
             "| Question | " + " | ".join(labels) + " |",
             "|---|" + "---|" * len(labels)]
    for q in QUESTIONS:
        row = [next(("ran" if r["ran_ok"] else "ERROR") for r in results
                    if r["question"] == q and r["config"] == lab) for lab in labels]
        lines.append(f"| {q} | " + " | ".join(row) + " |")

    lines.append("\n## Details\n")
    for q in QUESTIONS:
        lines.append(f"### {q}\n")
        for lab in labels:
            r = next(r for r in results if r["question"] == q and r["config"] == lab)
            lines.append(f"**{lab}** ({r['prompt_tokens']}+{r['completion_tokens']} tokens"
                         + (", needed a retry" if r["retried"] else "") + ")\n")
            lines.append("```sql\n" + (r["sql"] or "(none)") + "\n```")
            if r["error"]:
                lines.append(f"Error: {r['error']}\n")
            lines.append(f"Answer: {r['answer']}\n")
            lines.append("Correct? (fill in: yes / no / partly, and why)\n")
    with open("results_examples.md", "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
