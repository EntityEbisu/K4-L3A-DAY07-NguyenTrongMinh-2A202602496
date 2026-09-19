from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if not question or not question.strip():
            return "I could not answer because the question was empty."

        if self.store.get_collection_size() == 0:
            return "I could not find any information in the knowledge base."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "I could not find any relevant context for your question."

        context_sections = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source") or metadata.get("doc_id") or f"doc_{index}"
            text = (result.get("content") or "").strip()
            context_sections.append(f"[{index}] Source: {source}\n{text}")

        prompt = (
            "Answer the question using only the information in the provided context. "
            "If the context does not contain enough information, say that explicitly.\n\n"
            "Context:\n"
            + "\n\n".join(context_sections)
            + "\n\nQuestion: "
            + question.strip()
            + "\n\nAnswer:"
        )
        return self.llm_fn(prompt)
