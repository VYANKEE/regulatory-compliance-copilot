"""
Report Agent -- no LLM call, on purpose. Just formats already-verified
output from earlier agents into a clean Markdown memo. Deterministic
templating instead of generation means no new place for hallucination to sneak in.
"""

from datetime import date


def compile_report(circular_ref: str, diffs: list[dict], verified_findings: list[dict], dropped_count: int) -> str:
    lines = [
        f"# Compliance Impact Memo — {circular_ref}",
        f"*Generated: {date.today().isoformat()}*",
        "",
        "## Executive Summary",
        "",
    ]

    not_met = [f for f in verified_findings if f["status"] == "Not Met"]
    partial = [f for f in verified_findings if f["status"] == "Partial"]
    met = [f for f in verified_findings if f["status"] == "Met" and "no current requirement" not in f["requirement"].lower()]

    lines.append(
        f"{len(not_met)} requirement(s) not met, {len(partial)} partially met, "
        f"{len(met)} met, across {len(diffs)} topic area(s) reviewed. "
        f"{dropped_count} unverifiable/ungrounded finding(s) were discarded by the Verifier Agent."
    )
    lines.append("")

    lines.append("## What Changed vs Previous Circulars")
    lines.append("")
    for d in diffs:
        lines.append(f"### {d['topic']}")
        lines.append("")
        lines.append(d["diff_text"])
        lines.append("")

    lines.append("## Policy Gaps (Verified)")
    lines.append("")
    if not not_met and not partial:
        lines.append("No unmet or partially-met requirements found across reviewed topics.")
    for f in not_met + partial:
        lines.append(f"### [{f['status']}] {f['requirement']}")
        lines.append(f"- **Topic:** {f['topic']}")
        lines.append(f"- **RBI citation:** `{f['rbi_citation']}`")
        lines.append(f"- **Gap:** {f['explanation']}")
        if f.get("suggested_policy_change"):
            lines.append(f"- **Suggested policy change:** {f['suggested_policy_change']}")
        lines.append("")

    lines.append("## Requirements Already Met")
    lines.append("")
    if not met:
        lines.append("(none recorded)")
    for f in met:
        lines.append(f"- **{f['requirement']}** — `{f['rbi_citation']}`")
    lines.append("")

    lines.append("## Citations Appendix")
    lines.append("")
    all_citations = sorted({f["rbi_citation"] for f in verified_findings if f["rbi_citation"]})
    for c in all_citations:
        lines.append(f"- `{c}`")

    return "\n".join(lines)
