from __future__ import annotations

import os
import sys
from pathlib import Path
import uuid
import tempfile
import shutil
import typer  # type: ignore

# Ensure project root on sys.path for src imports
PACKAGE_ROOT = Path(__file__).resolve().parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from evals.suites.quality_suite import ContentQualitySuite  # type: ignore
from evals.io_utils import ensure_output_dir  # type: ignore


app = typer.Typer()


@app.command()
def run(
    scrape_engine: str = typer.Option(..., "--scrape_engine", help="Scrape engine name (scraper)."),
    suite: str = typer.Option("quality", help="Suite to run (default: quality)."),
    output_dir: str = typer.Option(..., "--output-dir", help="Output directory for artifacts and summary."),
    dataset: str = typer.Option(..., "--dataset", help="Path to dataset CSV (id,url,truth_text,lie_text)."),
    lie_weight: float = typer.Option(4.0, help="Weight for lie bigram penalty in ordered metrics."),
    resume: bool = typer.Option(False, "--resume", help="Resume execution; requires existing output directory."),
    rerun: bool = typer.Option(False, "--rerun", help="Recreate output directory (deletes existing)."),
    analysis_only: bool = typer.Option(False, "--analysis-only", help="Only run analysis using existing scrape outputs."),
    max_workers: int = typer.Option(10, "--max-workers", help="Concurrency limit."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with temporary directory and clean up at the end."),
):
    # Handle dry run with temporary directory
    if dry_run:
        temp_dir = tempfile.mkdtemp(prefix="scrapers_benchmark_dry_run_")
        base = Path(temp_dir)
        typer.echo(f"[dry-run] Using temporary directory: {base}")
    else:
        base = Path(output_dir)
    
    engine_key = f"{scrape_engine}_{suite}"
    engine_out = base / engine_key
    # analysis-only must never mutate outputs; require existing per-engine outputs
    if analysis_only:
        if not engine_out.exists() or not any(engine_out.iterdir()):
            typer.echo(f"[analysis-only] Output directory for {engine_key} is empty or missing at {engine_out}. Provide an existing run directory or drop --analysis-only.")
            raise typer.Exit(code=1)
    else:
        # Only prepare/clean the per-engine directory
        ensure_output_dir(engine_out, rerun=rerun, resume=resume)

    if suite != "quality":
        raise typer.Exit(code=1)

    suite_impl = ContentQualitySuite(
        scrape_engine=scrape_engine,
        output_dir=base,
        dry_run=dry_run,
        max_workers=max_workers,
        dataset_csv=Path(dataset),
        lie_weight=lie_weight,
    )

    import asyncio

    try:
        # In analysis-only mode, force resume=True to avoid directory checks blocking
        effective_resume = True if analysis_only else resume
        asyncio.run(suite_impl.run(resume=effective_resume, analysis_only=analysis_only))
        
        # Clean up temporary directory for dry runs
        if dry_run:
            typer.echo(f"[dry-run] Cleaning up temporary directory: {base}")
            shutil.rmtree(base, ignore_errors=True)
            typer.echo("[dry-run] Cleanup completed successfully")
            
    except RuntimeError as e:
        typer.echo(str(e))
        # Clean up temporary directory even on error
        if dry_run:
            typer.echo(f"[dry-run] Cleaning up temporary directory after error: {base}")
            shutil.rmtree(base, ignore_errors=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()


