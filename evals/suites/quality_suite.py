from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from .types import AsyncBaseSuite, Task, TaskResult
from ..engines.scrape_engine import ScrapeEngine
from ..analysis.quality_analyzer import QualityAnalyzer
from ..io_utils import (
    ensure_output_dir,
    load_tasks_from_csv,
    read_json,
    summary_results_path,
    task_dir,
    write_analyzer_output,
    write_scrape_output,
    write_task,
)


class ContentQualitySuite(AsyncBaseSuite):
    def __init__(self, scrape_engine: str, output_dir: Path, dry_run: bool, max_workers: int, dataset_csv: Path, lie_weight: float = 4.0) -> None:
        super().__init__(scrape_engine, output_dir, dry_run, max_workers)
        self.dataset_csv = dataset_csv
        self.lie_weight = lie_weight
        self.analyzer = QualityAnalyzer()

    def load_tasks(self) -> List[Task]:
        limit = 5 if self.dry_run else None
        self.tasks = load_tasks_from_csv(self.dataset_csv, limit=limit)
        return self.tasks

    async def run(self, *, resume: bool, analysis_only: bool) -> List[TaskResult]:
        # Prepare
        suite_key = "quality"
        # Directory already prepared by CLI; do not mutate here
        engine = ScrapeEngine(self.scrape_engine, self.max_workers)
        tasks = self.load_tasks()
        run_id = str(uuid.uuid4())

        results: List[TaskResult] = []

        # Scrape phase
        if not analysis_only:
            to_scrape: List[Task] = []
            for t in tasks:
                out_dir = task_dir(self.output_dir, engine.engine_name, suite_key, t.id)
                scrape_path = out_dir / "scrape_output.json"
                write_task(out_dir / "task.json", t)
                if resume and scrape_path.exists():
                    continue
                print(f"{datetime.now().isoformat()} phase=scrape_start suite={suite_key} engine={engine.engine_name} run_id={run_id} task_id={t.id} url={t.url}")
                to_scrape.append(t)

            if to_scrape:
                def _on_result(t: Task, out):
                    out_dir_local = task_dir(self.output_dir, engine.engine_name, suite_key, t.id)
                    write_scrape_output(out_dir_local / "scrape_output.json", out)
                    print(
                        f"{datetime.now().isoformat()} phase=scrape_done suite={suite_key} engine={engine.engine_name} run_id={run_id} task_id={t.id} url={t.url} "
                        f"status_code={out.status_code} content_size={out.content_size} format={out.format} error={out.error} saved={out_dir_local / 'scrape_output.json'}"
                    )

                await engine.scrape_tasks(to_scrape, run_id=run_id, on_result=_on_result)

        # Analysis phase
        analyzer_results = []
        for t in tasks:
            out_dir = task_dir(self.output_dir, engine.engine_name, suite_key, t.id)
            scrape_path = out_dir / "scrape_output.json"
            if not scrape_path.exists():
                if analysis_only:
                    raise RuntimeError(f"Missing scrape output for task {t.id}. Run without --analysis-only or use --resume.")
                else:
                    # Skip tasks that weren't scraped this run
                    continue
            scrape_dict = read_json(scrape_path)
            # Minimal adaptation to ScrapeOutput fields
            from .types import ScrapeOutput, AnalyzerResult
            scr_out = ScrapeOutput(
                scraper=str(scrape_dict.get("scraper") or engine.engine_name),
                url=str(scrape_dict.get("url") or t.url),
                status_code=scrape_dict.get("status_code"),
                error=scrape_dict.get("error"),
                created_at=scrape_dict.get("created_at"),
                format=scrape_dict.get("format"),
                content_size=scrape_dict.get("content_size"),
                content=scrape_dict.get("content"),
            )
            print(f"{datetime.now().isoformat()} phase=analyze_start suite={suite_key} engine={engine.engine_name} run_id={run_id} task_id={t.id} url={t.url}")
            analysis = self.analyzer.analyze_one(t, scr_out, lie_weight=self.lie_weight)
            write_analyzer_output(out_dir / "grader_output.json", analysis)
            results.append(TaskResult(task=t, scrape_output=scr_out, analyzer_result=analysis))
            analyzer_results.append(analysis)
            print(
                f"{datetime.now().isoformat()} phase=analyze_done suite={suite_key} engine={engine.engine_name} run_id={run_id} task_id={t.id} url={t.url} "
                f"success={analysis.success} recall={analysis.recall:.3f} precision={analysis.precision:.3f} f1={analysis.f1:.3f}"
            )

        # Summary
        summary = self.analyzer.summarize(analyzer_results)
        write_task(summary_results_path(self.output_dir, engine.engine_name, suite_key), Task(id="summary", url="", truth_text="", lie_text=""))  # dummy for path ensure
        from ..io_utils import write_json
        write_json(summary_results_path(self.output_dir, engine.engine_name, suite_key), summary)  # type: ignore[arg-type]
        print(
            f"{datetime.now().isoformat()} phase=summary suite={suite_key} engine={engine.engine_name} run_id={run_id} "
            f"tasks={len(tasks)} analyzed={len(analyzer_results)} success_rate={summary.get('success_rate')} avg_f1={summary.get('avg_f1')}"
        )
        return results


