from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class EvalSample:
    id: str
    question: str
    expected_answer: str
    relevant_keywords: List[str] = field(default_factory=list)
    relevant_filenames: List[str] = field(default_factory=list)


def load_eval_dataset(path: str | Path) -> List[EvalSample]:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    return [
        EvalSample(
            id=item["id"],
            question=item["question"],
            expected_answer=item["expected_answer"],
            relevant_keywords=item.get("relevant_keywords", []),
            relevant_filenames=item.get("relevant_filenames", []),
        )
        for item in raw
    ]
