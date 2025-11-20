from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .suites.types import Task, ScrapeOutput, AnalyzerResult


def load_tasks_from_csv(csv_path: Path, limit: Optional[int] = None) -> List[Task]:
    tasks: List[Task] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            tasks.append(
                Task(
                    id=str(row.get("id") or i),
                    url=row["url"].strip(),
                    truth_text=(row.get("truth_text") or "").strip(),
                    lie_text=(row.get("lie_text") or "").strip(),
                )
            )
    return tasks


def ensure_output_dir(output_dir: Path, rerun: bool, resume: bool) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        if rerun:
            shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            return
        if not resume:
            raise RuntimeError(
                f"Output directory '{output_dir}' is not empty. Use --rerun to recreate or --resume to continue."
            )
    output_dir.mkdir(parents=True, exist_ok=True)


def task_dir(base: Path, engine: str, suite: str, task_id: str) -> Path:
    return base / f"{engine}_{suite}" / task_id


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_task(path: Path, task: Task) -> None:
    write_json(path, asdict(task))


def write_scrape_output(path: Path, output: ScrapeOutput) -> None:
    write_json(path, asdict(output))


def write_analyzer_output(path: Path, result: AnalyzerResult) -> None:
    write_json(path, asdict(result))


def summary_results_path(base: Path, engine: str, suite: str) -> Path:
    return base / "results" / f"{engine}_{suite}.json"


