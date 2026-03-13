"""Explore command: deep research exploration on a topic.

Flow: Retrieve local context → Ideator → DeepResearcher → Skeptic
Outputs a Markdown report and optionally saves to Obsidian.
"""
import json
from pathlib import Path
from typing import Optional


def run_explore(
    topic: str,
    focus: Optional[str] = None,
    save_to_obsidian: bool = False,
    output_dir: Optional[str] = None,
) -> dict:
    """Run the explore pipeline: context retrieval → Ideator → DeepResearcher → Skeptic.

    Args:
        topic: Research topic to explore.
        focus: Optional research focus (system | theory | empirical | analysis).
        save_to_obsidian: Whether to write the report to Obsidian vault.
        output_dir: Directory to save the markdown report (default: cwd/explore/).

    Returns:
        dict with keys: ideator_output, deep_research_output, skeptic_output, report_path
    """
    from researchbot.agents.ideator import run as ideator_run
    from researchbot.agents.deep_researcher import run as deep_researcher_run
    from researchbot.agents.skeptic import run as skeptic_run
    from researchbot.tools.io import write_markdown

    # ── Phase 0: Retrieve local context ──
    print("[explore] Phase 0: Retrieving context from local knowledge base...")
    local_context = _retrieve_local_context(topic)
    if local_context:
        print(f"[explore] Found relevant context ({len(local_context)} chars)")
    else:
        print("[explore] No local context found (RAG/Zotero/Obsidian not configured or empty)")

    # ── Phase 1: Ideator ──
    print("[explore] Phase 1/3: Ideator — generating hypotheses and gap analysis...")
    ideator_input = {
        "topic": topic,
        "venue": "Research exploration",
        "constraints": "",
    }
    if focus:
        ideator_input["preferred_focus"] = focus
    if local_context:
        ideator_input["retrieved_memory"] = local_context
    ideator_output = ideator_run(ideator_input)

    hypotheses = ideator_output.get("hypotheses", [])
    print(f"[explore] Ideator generated {len(hypotheses)} hypotheses")

    # ── Phase 2: DeepResearcher ──
    print("[explore] Phase 2/3: DeepResearcher — literature search and annotated bibliography...")
    deep_input = {
        "hypotheses": hypotheses,
        "scout_output": {},
        "contribution_statement": ideator_output.get("contribution_statement", ""),
    }
    deep_output = deep_researcher_run(deep_input)

    bib = deep_output.get("annotated_bib", [])
    print(f"[explore] DeepResearcher found {len(bib)} papers")

    # ── Phase 3: Skeptic ──
    print("[explore] Phase 3/3: Skeptic — adversarial review of hypotheses...")
    skeptic_input = {
        "approach_summary": ideator_output.get("contribution_statement", ""),
        "deep_research_output": deep_output,
        "hypotheses": hypotheses,
        "contribution_statement": ideator_output.get("contribution_statement", ""),
    }
    skeptic_output = skeptic_run(skeptic_input)

    print(f"[explore] Skeptic verdict: {skeptic_output.get('novelty_verdict', '?')}")

    # ── Generate report ──
    report = _format_explore_report(topic, ideator_output, deep_output, skeptic_output, local_context)

    out_dir = Path(output_dir) if output_dir else Path.cwd() / "explore"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_topic = "".join(c for c in topic if c.isalnum() or c in " -_")[:60].strip()
    report_path = out_dir / f"{safe_topic}.md"
    write_markdown(report_path, report)
    print(f"[explore] Report saved to: {report_path}")

    # Optionally save to Obsidian
    if save_to_obsidian:
        from researchbot.config import get_obsidian_vault_path
        obsidian_path = Path(get_obsidian_vault_path()) / "Explore" / f"{safe_topic}.md"
        write_markdown(obsidian_path, report)
        print(f"[explore] Also saved to Obsidian: {obsidian_path}")

    # Index the new report into RAG
    _try_index_report(report_path)

    return {
        "ideator_output": ideator_output,
        "deep_research_output": deep_output,
        "skeptic_output": skeptic_output,
        "report_path": str(report_path),
    }


def _retrieve_local_context(topic: str) -> str:
    """Try to retrieve relevant context from local knowledge base."""
    try:
        from researchbot.scholar.context_retriever import retrieve_context
        return retrieve_context(topic, max_results=15, max_chars=5000)
    except Exception as e:
        print(f"[explore] Context retrieval skipped: {e}")
        return ""


def _try_index_report(report_path: Path) -> None:
    """Try to index the explore report into RAG (best-effort)."""
    try:
        from researchbot.tools.rag import index_paper_note
        count = index_paper_note(report_path)
        if count:
            print(f"[explore] Indexed {count} chunks into RAG")
    except Exception:
        pass


def _format_explore_report(
    topic: str, ideator: dict, deep: dict, skeptic: dict,
    local_context: str = "",
) -> str:
    """Format explore results into a human-readable Markdown report."""
    lines = [
        f"# Explore: {topic}",
        "",
        "---",
        "",
    ]

    # Local context section (if any)
    if local_context:
        lines.append("## Prior Knowledge (from local library)")
        lines.append("")
        lines.append(local_context)
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Contribution Statement")
    lines.append(ideator.get("contribution_statement", "N/A"))
    lines.append("")

    lines.append("## Gap Analysis")
    for gap in ideator.get("gap_analysis", []):
        if isinstance(gap, dict):
            lines.append(f"- **{gap.get('type', '')}**: {gap.get('gap', '')} → {gap.get('opportunity', '')}")
    lines.append("")

    lines.append("## Hypotheses")
    for h in ideator.get("hypotheses", []):
        if isinstance(h, dict):
            lines.append(f"### {h.get('id', '?')}: {h.get('claim', '')}")
            lines.append(f"- **Test**: {h.get('falsifiable_test', '')}")
            lines.append(f"- **Experiment**: {h.get('minimal_experiment', '')}")
            lines.append(f"- **Expected gain**: {h.get('expected_gain', '')}")
            lines.append(f"- **Risks**: {h.get('risks', '')}")
            lines.append("")

    lines.append("## Research Proposals")
    for p in ideator.get("proposals", []):
        if isinstance(p, dict):
            lines.append(f"- **Idea**: {p.get('idea', '')}")
            lines.append(f"  - Motivation: {p.get('motivation', '')}")
            challenges = p.get("challenges", [])
            if challenges:
                lines.append(f"  - Challenges: {', '.join(str(c) for c in challenges)}")
            lines.append("")

    lines.append("## Annotated Bibliography")
    for entry in deep.get("annotated_bib", []):
        if isinstance(entry, dict):
            lines.append(f"### [{entry.get('key', '?')}] {entry.get('title', 'Untitled')}")
            lines.append(f"- **Authors**: {entry.get('authors', 'N/A')}")
            lines.append(f"- **URL**: {entry.get('url', '')}")
            lines.append(f"- **Contribution**: {entry.get('contribution', '')}")
            lines.append(f"- **Limitations**: {entry.get('limitations', '')}")
            lines.append("")

    lines.append("## Gap Summary")
    lines.append(deep.get("gap_summary", "N/A"))
    lines.append("")

    lines.append("## Skeptic Review")
    lines.append(f"**Novelty verdict**: {skeptic.get('novelty_verdict', '?')}")
    lines.append("")
    lines.append("### Rejection Risks")
    for r in skeptic.get("rejection_risks", []):
        lines.append(f"- {r}")
    lines.append("")
    lines.append("### Required Experiments")
    for e in skeptic.get("required_experiments", []):
        lines.append(f"- {e}")
    lines.append("")
    lines.append("### Threats to Validity")
    for t in skeptic.get("threats_to_validity", []):
        lines.append(f"- {t}")

    return "\n".join(lines)
