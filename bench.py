from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "tuition"

QUERIES = [
    {
        "question": "Học phí chương trình chuẩn của HUST năm 2026-2027 dao động trong khoảng nào?",
        "gold_answer": "28 đến 40 triệu đồng/năm",
        "metadata_filter": {"audience": "student"},
    },
    {
        "question": "Nhóm chương trình Elitech của HUST thu học phí theo mức nào?",
        "gold_answer": "35 đến 68 triệu đồng/năm",
        "metadata_filter": {"audience": "student"},
    },
    {
        "question": "Các chương trình tài năng và quốc tế của HUST tính học phí theo năm hay theo kỳ?",
        "gold_answer": "Theo kỳ",
        "metadata_filter": {"audience": "student"},
    },
    {
        "question": "Theo quy định của Trường ĐHKHTN, học phí môn học được tính như thế nào?",
        "gold_answer": "165.000 đ/1 tín chỉ x số tín chỉ x hệ số môn học",
        "metadata_filter": {"audience": "all"},
    },
    {
        "question": "Học phí của chương trình chuẩn tại HUST có tăng tối đa bao nhiêu so với năm trước?",
        "gold_answer": "giữ nguyên hoặc tăng không quá 5 triệu đồng/năm",
        "metadata_filter": {"audience": "student"},
    },
]


def parse_frontmatter(file_path: Path) -> tuple[dict[str, str], str]:
    text = file_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text.strip()

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()

    frontmatter = {}
    for raw_line in parts[1].splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"\'')

    body = parts[2].strip()
    return frontmatter, body


def chunk_text(text: str, strategy: str = "recursive") -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []

    if strategy == "fixed_size":
        return FixedSizeChunker(chunk_size=500, overlap=50).chunk(normalized)
    if strategy == "by_sentences":
        return SentenceChunker(max_sentences_per_chunk=3).chunk(normalized)
    return RecursiveChunker(chunk_size=500).chunk(normalized)


def load_documents(data_dir: Path, strategy: str = "recursive") -> list[Document]:
    documents: list[Document] = []

    for file_path in sorted(data_dir.glob("*.md")):
        metadata, body = parse_frontmatter(file_path)
        if not metadata:
            continue

        doc_id = metadata.get("doc_id") or file_path.stem
        chunks = chunk_text(body, strategy=strategy)
        if not chunks:
            chunks = [body]

        for chunk_index, chunk in enumerate(chunks):
            chunk_text_value = chunk.strip()
            if not chunk_text_value:
                continue
            documents.append(
                Document(
                    id=f"{doc_id}#{chunk_index}",
                    content=chunk_text_value,
                    metadata={
                        **metadata,
                        "doc_id": doc_id,
                        "source": str(file_path),
                        "file_name": file_path.name,
                    },
                )
            )

    return documents


def as_preview(text: str, limit: int = 140) -> str:
    cleaned = " ".join(text.replace("\n", " ").split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def evaluate_queries(store: EmbeddingStore, queries: list[dict]) -> list[dict]:
    results: list[dict] = []
    for item in queries:
        question = item["question"]
        filter_value = item.get("metadata_filter")

        filtered = store.search_with_filter(question, top_k=3, metadata_filter=filter_value) if filter_value else store.search(question, top_k=3)
        unfiltered = store.search(question, top_k=3)

        results.append(
            {
                "question": question,
                "gold_answer": item["gold_answer"],
                "filtered": filtered,
                "unfiltered": unfiltered,
                "metadata_filter": filter_value,
            }
        )
    return results


def print_evaluation(results: list[dict]) -> None:
    for idx, item in enumerate(results, start=1):
        print(f"\n=== Query {idx} ===")
        print(f"Q: {item['question']}")
        print(f"Gold: {item['gold_answer']}")
        if item["metadata_filter"]:
            print(f"Filter: {item['metadata_filter']}")
        print("\nTop-3 with filter:")
        for pos, result in enumerate(item["filtered"], start=1):
            metadata = result.get("metadata", {})
            print(
                f"  {pos}. score={result.get('score', 0):.4f} | doc_id={metadata.get('doc_id')} | "
                f"title={metadata.get('title')} | preview={as_preview(result.get('content', ''))}"
            )
        print("\nTop-3 without filter:")
        for pos, result in enumerate(item["unfiltered"], start=1):
            metadata = result.get("metadata", {})
            print(
                f"  {pos}. score={result.get('score', 0):.4f} | doc_id={metadata.get('doc_id')} | "
                f"title={metadata.get('title')} | preview={as_preview(result.get('content', ''))}"
            )


def summarize_sources(data_dir: Path) -> list[dict]:
    rows = []
    with (data_dir / "sources.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
    return rows


def main() -> int:
    strategy = "recursive"
    documents = load_documents(DATA_DIR, strategy=strategy)
    if not documents:
        raise RuntimeError(f"No documents found in {DATA_DIR}")

    store = EmbeddingStore(collection_name="tuition-benchmark", embedding_fn=_mock_embed)
    store.add_documents(documents)

    print(f"Loaded {len(documents)} chunks from {len(sorted(DATA_DIR.glob('*.md')))} markdown files.")
    print(f"Strategy: {strategy}")
    print(f"Source rows: {len(summarize_sources(DATA_DIR))}")

    evaluation = evaluate_queries(store, QUERIES)
    print_evaluation(evaluation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
