from __future__ import annotations

import re
import statistics
from typing import List, Tuple

from ..suites.types import AnalyzerResult, Task, ScrapeOutput


def smart_tokenize(text: str) -> list[str]:
    return re.findall(r"\d+/\d+|[\w'-]+", (text or "").lower())




class QualityAnalyzer:
    def analyze_one(self, task: Task, output: ScrapeOutput, lie_weight: float = 4.0) -> AnalyzerResult:
        def strip_markdown(md: str) -> str:
            if not md:
                return ""
            text = md
            # Remove code fences and inline code
            text = re.sub(r"```[\s\S]*?```", " ", text)
            text = re.sub(r"`[^`]+`", " ", text)
            # Images ![alt](url) -> alt
            text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
            # Links [text](url) -> text
            text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
            # Strip markdown emphasis and headings markers
            text = re.sub(r"^[#>\-\*\+\s]+", "", text, flags=re.MULTILINE)
            text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
            # Tables: drop pipes
            text = re.sub(r"\|", " ", text)
            # Collapse multiple spaces/newlines
            text = re.sub(r"\s+", " ", text).strip()
            return text

        content_text = output.content or ""
        if (output.format or "").lower() == "markdown":
            content_text = strip_markdown(content_text)

        content_words = smart_tokenize(content_text)
        truth_words = smart_tokenize(task.truth_text or "")
        lie_words = smart_tokenize(task.lie_text or "")

        # Snippet-mode metrics: recall and noise on best-matching window (length ~= important snippet)
        def window_scores(content_tokens: list[str], imp_tokens: list[str]) -> tuple[float, float, float]:
            if not content_tokens or not imp_tokens:
                return 0.0, 0.0, 0.0
            win = max(len(imp_tokens), 1)
            best_recall = 0.0
            best_precision = 0.0
            imp_set = set(imp_tokens)
            for i in range(0, max(len(content_tokens) - win + 1, 1)):
                window = content_tokens[i:i+win]
                wset = set(window)
                recall = len(wset & imp_set) / max(len(imp_set), 1)
                precision = len(wset & imp_set) / max(len(wset), 1)
                # Prefer higher recall; if tie, higher precision
                if (recall > best_recall) or (abs(recall - best_recall) < 1e-9 and precision > best_precision):
                    best_recall = recall
                    best_precision = precision
            # F1 from best window
            if best_recall + best_precision > 0:
                f1 = 2 * (best_precision * best_recall) / (best_precision + best_recall)
            else:
                f1 = 0.0
            return best_recall, best_precision, f1

        recall_snippet, precision_snippet, f1_snippet = window_scores(content_words, truth_words)

        def is_block_page(text: str) -> bool:
            if not text:
                return False
            t = text.lower()
            # Common block-page markers
            needles = [
                "attention required",
                "cloudflare",
                "verify you are a human",
                "access denied",
                "bot detection",
                "datadome",
                "akamai bot manager",
                "imperva",
                "sucuri website firewall",
            ]
            return any(n in t for n in needles)

        # If both important and not-important snippets are empty (e.g., known 4xx pages), force success rate False
        if not truth_words and not lie_words:
            success = 0.0
        else:
            success = bool(
                (output.status_code is not None and 200 <= int(output.status_code) < 400)
                and not output.error
                and bool(output.content)
                and (output.content_size is not None and int(output.content_size) > 0)
                and not is_block_page(output.content or "")
            )

        return AnalyzerResult(
            success=success,
            recall=recall_snippet,
            precision=precision_snippet,
            f1=f1_snippet,
        )

    def summarize(self, results: List[AnalyzerResult]) -> dict:
        if not results:
            return {
                "success": 0.0,
                "avg_recall": 0.0,
                "avg_precision": 0.0,
                "avg_f1": 0.0,
            }
        return {
            "success_rate": sum(1 for r in results if r.success) / len(results),
            "avg_recall": sum(r.recall for r in results) / len(results),
            "avg_precision": sum(r.precision for r in results) / len(results),
            "avg_f1": sum(r.f1 for r in results) / len(results),
        }


