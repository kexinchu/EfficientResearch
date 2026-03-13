"""Experiment command: quick experiment design from a research idea.

Takes a research idea and produces an experiment plan with code scaffolds.
Retrieves local context from paper library to ground experiment design.
"""
import json
from pathlib import Path
from typing import Optional


def run_experiment(
    idea: str,
    save_to_obsidian: bool = False,
    output_dir: Optional[str] = None,
) -> dict:
    """Design experiments for a given research idea.

    Args:
        idea: Research idea or hypothesis to design experiments for.
        save_to_obsidian: Whether to write the plan to Obsidian vault.
        output_dir: Directory to save the markdown report (default: cwd/experiments/).

    Returns:
        dict with keys: experiment_output, report_path
    """
    from researchbot.agents.experimenter import run as experimenter_run
    from researchbot.tools.io import write_markdown

    # ── Phase 0: Retrieve local context ──
    print("[experiment] Retrieving context from local knowledge base...")
    local_context = _retrieve_local_context(idea)
    if local_context:
        print(f"[experiment] Found relevant context ({len(local_context)} chars)")

    print("[experiment] Designing experiments...")

    # Build input for experimenter, enriched with local context
    exp_input = {
        "hypotheses": [{"id": "H1", "claim": idea}],
        "contribution_statement": idea,
        "contribution_type": "empirical",
        "deep_research_output": {},
        "skeptic_output": {},
    }

    # Inject local context as deep_research_output so experimenter sees related baselines
    if local_context:
        exp_input["deep_research_output"] = {
            "annotated_bib": [],
            "baseline_checklist": [],
            "metrics_checklist": [],
            "gap_summary": f"Context from local paper library:\n{local_context}",
        }

    experiment_output = experimenter_run(exp_input)

    plan = experiment_output.get("experiment_plan", [])
    print(f"[experiment] Generated {len(plan)} experiment(s)")

    # Format report
    report = _format_experiment_report(idea, experiment_output, local_context)

    out_dir = Path(output_dir) if output_dir else Path.cwd() / "experiments"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_idea = "".join(c for c in idea if c.isalnum() or c in " -_")[:60].strip()
    report_path = out_dir / f"{safe_idea}.md"
    write_markdown(report_path, report)
    print(f"[experiment] Report saved to: {report_path}")

    if save_to_obsidian:
        from researchbot.config import get_obsidian_vault_path
        obsidian_path = Path(get_obsidian_vault_path()) / "Idea" / f"Experiment - {safe_idea}.md"
        write_markdown(obsidian_path, report)
        print(f"[experiment] Also saved to Obsidian: {obsidian_path}")

    return {
        "experiment_output": experiment_output,
        "report_path": str(report_path),
    }


def _retrieve_local_context(idea: str) -> str:
    """Try to retrieve relevant context from local knowledge base."""
    try:
        from researchbot.scholar.context_retriever import retrieve_context
        return retrieve_context(idea, max_results=10, max_chars=3000)
    except Exception as e:
        print(f"[experiment] Context retrieval skipped: {e}")
        return ""


def _format_experiment_report(idea: str, output: dict, local_context: str = "") -> str:
    """Format experiment design into a Markdown report."""
    lines = [
        f"# Experiment Design: {idea[:100]}",
        "",
        "---",
        "",
    ]

    # Local context
    if local_context:
        lines.append("## Related Work (from local library)")
        lines.append("")
        lines.append(local_context)
        lines.append("")
        lines.append("---")
        lines.append("")

    # Experiment plan
    lines.append("## Experiment Plan")
    for exp in output.get("experiment_plan", []):
        if isinstance(exp, dict):
            lines.append(f"### {exp.get('id', '?')}: {exp.get('name', 'Unnamed')}")
            for key in ["objective", "setup", "expected_outcome", "metrics", "baselines"]:
                val = exp.get(key, "")
                if val:
                    if isinstance(val, list):
                        lines.append(f"- **{key.replace('_', ' ').title()}**:")
                        for item in val:
                            lines.append(f"  - {item}")
                    else:
                        lines.append(f"- **{key.replace('_', ' ').title()}**: {val}")
            lines.append("")

    # Code snippets
    snippets = output.get("code_snippets", {})
    if snippets:
        lines.append("## Code Scaffolds")
        for name, code in snippets.items():
            lines.append(f"### {name}")
            lines.append(f"```python\n{code}\n```")
            lines.append("")

    # Result tables
    tables = output.get("result_tables", [])
    if tables:
        lines.append("## Expected Result Tables")
        lines.append("```json")
        lines.append(json.dumps(tables, indent=2))
        lines.append("```")
        lines.append("")

    # Summary
    summary = output.get("result_summary", "")
    if summary:
        lines.append("## Result Summary")
        lines.append(summary)

    return "\n".join(lines)
