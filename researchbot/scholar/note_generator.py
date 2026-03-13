"""Generate structured reading notes from paper metadata using LLM + Scholar skill."""
import json

from researchbot.models import PaperMetadata, PaperNote, IdeaNote


def generate_paper_note(meta: PaperMetadata) -> PaperNote:
    """Generate a structured paper reading note from metadata + abstract.

    Uses the Scholar skill (skills/scholar/SKILL.md) for deep, structured analysis.
    Produces: problem → importance → method (motivation/challenge/design) → results → summary → limitations → insights.
    """
    from researchbot.tools.llm import call_llm
    from researchbot.tools.skills_loader import get_skill_prompt

    # Load scholar skill as system prompt
    system = get_skill_prompt("scholar")

    user = f"Title: {meta.title}\n\nAbstract: {meta.abstract}\n\nOutput JSON only."

    raw = call_llm(system, user, json_mode=True, max_tokens=2500)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    note = PaperNote(
        title=meta.title,
        paper_type=meta.paper_type,
        authors=meta.authors,
        year=meta.year,
        venue=meta.venue,
        source_url=meta.source_url or meta.pdf_url,
        tags=data.get("tags", meta.tags),
        problem=data.get("problem", ""),
        importance=data.get("importance", ""),
        motivation=data.get("motivation", ""),
        challenge=data.get("challenge", ""),
        design=data.get("design", ""),
        key_results=data.get("key_results", ""),
        summary=data.get("summary", ""),
        limitations=data.get("limitations", ""),
        insights=data.get("insights", ""),
    )
    return note


def generate_idea_note(raw_text: str) -> IdeaNote:
    """Generate a structured idea note from free-form text.

    Uses LLM to structure the idea into hypothesis/motivation/related/questions.
    """
    from researchbot.tools.llm import call_llm

    system = """You are a senior systems/ML researcher. Given a raw research idea or thought, structure it into a clear research idea note.

Output JSON with these keys:
{
  "title": "A concise title for this idea (< 80 chars)",
  "hypothesis": "The core hypothesis or claim",
  "motivation": "Why this matters, what gap it addresses",
  "related_directions": "Related work or research directions to explore",
  "open_questions": "Key open questions to resolve",
  "next_steps": "Concrete next steps to investigate",
  "tags": ["tag1", "tag2", ...]
}"""

    user = f"Raw idea/thought:\n\n{raw_text}\n\nOutput JSON only."

    raw = call_llm(system, user, json_mode=True, max_tokens=1500)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    return IdeaNote(
        title=data.get("title", "Untitled Idea"),
        tags=data.get("tags", []),
        hypothesis=data.get("hypothesis", ""),
        motivation=data.get("motivation", ""),
        related_directions=data.get("related_directions", ""),
        open_questions=data.get("open_questions", ""),
        next_steps=data.get("next_steps", ""),
    )
