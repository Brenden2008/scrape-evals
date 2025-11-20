from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional, Protocol, Union


# Core data structures for suite execution


@dataclass
class Task:
    id: str
    url: str
    truth_text: str
    lie_text: str


@dataclass
class ScrapeOutput:
    # Subset/superset of scrapers.base.ScrapeResult with only fields we need here
    scraper: str
    url: str
    status_code: Optional[int]
    error: Optional[str]
    created_at: Optional[str]
    format: Optional[Literal["markdown", "text", "html"]]
    content_size: Optional[int]
    content: Optional[str]


@dataclass
class AnalyzerResult:
    success: bool
    recall: float
    precision: float
    f1: float


@dataclass
class TaskResult:
    task: Task
    scrape_output: ScrapeOutput
    analyzer_result: AnalyzerResult


class AsyncBaseSuite(abc.ABC):
    def __init__(self, scrape_engine: str, output_dir: Path, dry_run: bool, max_workers: int) -> None:
        self.scrape_engine = scrape_engine
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.max_workers = max_workers
        self.tasks: List[Task] = []

    @abc.abstractmethod
    def load_tasks(self) -> List[Task]:
        ...

    @abc.abstractmethod
    async def run(self, *, resume: bool, analysis_only: bool) -> List[TaskResult]:
        ...


