"""Classify papers into paper_type using LLM zero-shot classification."""
import json

from researchbot.config import get_paper_types
from researchbot.models import PaperMetadata


def classify_paper(meta: PaperMetadata) -> str:
    """Classify a paper into one of the configured paper types.

    Uses LLM for zero-shot classification based on title + abstract.
    Falls back to keyword matching if LLM is unavailable.
    """
    paper_types = get_paper_types()

    # Try keyword-based first (fast, no API call)
    keyword_result = _keyword_classify(meta, paper_types)

    # If keyword gives a confident match, use it
    if keyword_result != "Other":
        return keyword_result

    # Use LLM for ambiguous cases
    try:
        return _llm_classify(meta, paper_types)
    except Exception as e:
        print(f"[classifier] LLM classification failed: {e}, using keyword fallback")
        return keyword_result


def _keyword_classify(meta: PaperMetadata, paper_types: list[str]) -> str:
    """Simple keyword-based classification."""
    text = f"{meta.title} {meta.abstract}".lower()

    keyword_map = {
        "MLSys": ["mlsys", "machine learning system", "ml system", "training system",
                   "inference system", "model serving", "distributed training",
                   "gpu cluster", "deep learning system"],
        "Systems": ["operating system", "file system", "distributed system",
                    "storage system", "network system", "kernel", "scheduler",
                    "microservice", "serverless"],
        "LLM": ["large language model", "llm", "language model", "gpt", "transformer",
                "pre-training", "fine-tuning", "instruction tuning", "rlhf",
                "alignment", "chain of thought", "in-context learning"],
        "Agents": ["agent", "multi-agent", "tool use", "planning", "reasoning",
                   "autonomous", "agentic", "react", "function calling"],
        "RAG": ["retrieval-augmented", "retrieval augmented", "rag ",
                "retrieve and generate", "knowledge-grounded"],
        "Retrieval": ["information retrieval", "dense retrieval", "sparse retrieval",
                      "passage retrieval", "document retrieval", "re-ranking",
                      "embedding model", "bi-encoder", "cross-encoder"],
        "VectorSearch": ["vector search", "vector database", "approximate nearest neighbor",
                         "ann ", "hnsw", "ivf", "faiss", "similarity search",
                         "vector index", "embedding search"],
        "Databases": ["database", "query processing", "query optimization",
                      "transaction", "sql", "nosql", "olap", "oltp",
                      "data warehouse", "index structure"],
        "Security": ["security", "privacy", "adversarial", "attack", "defense",
                     "vulnerability", "malware", "encryption", "differential privacy",
                     "federated learning"],
        "Multimodal": ["multimodal", "vision-language", "image-text", "visual question",
                       "video understanding", "cross-modal", "clip", "diffusion model"],
    }

    best_type = "Other"
    best_count = 0
    for ptype, keywords in keyword_map.items():
        if ptype not in paper_types:
            continue
        count = sum(1 for kw in keywords if kw in text)
        if count > best_count:
            best_count = count
            best_type = ptype

    return best_type


def _llm_classify(meta: PaperMetadata, paper_types: list[str]) -> str:
    """Use LLM for classification."""
    from researchbot.tools.llm import call_llm

    system = (
        "You are a research paper classifier. Given a paper's title and abstract, "
        "classify it into exactly one of the provided categories. "
        "Respond with a JSON object: {\"paper_type\": \"<category>\"}."
    )
    user = (
        f"Categories: {', '.join(paper_types)}\n\n"
        f"Title: {meta.title}\n\n"
        f"Abstract: {meta.abstract[:1500]}\n\n"
        "Classify this paper. Output JSON only."
    )
    raw = call_llm(system, user, json_mode=True, max_tokens=100)
    try:
        result = json.loads(raw)
        ptype = result.get("paper_type", "Other")
        if ptype in paper_types:
            return ptype
    except (json.JSONDecodeError, KeyError):
        pass
    return "Other"
