from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
import contextlib
from typing import List

import typer  # type: ignore

app = typer.Typer()


def discover_engines(engines_dir: Path) -> List[str]:
    engines: List[str] = []
    for fp in engines_dir.glob("*.py"):
        name = fp.stem
        if name in {"base", "__init__"}:
            continue
        engines.append(name)
    engines.sort()
    return engines


async def run_one_engine(
    engine: str,
    suite: str,
    output_dir: Path,
    dataset: Path,
    timeout_s: int,
    extra_args: List[str],
) -> int:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    cmd = [
        sys.executable,
        str(Path(__file__).parent / "run_eval.py"),
        "--scrape_engine",
        engine,
        "--suite",
        suite,
        "--output-dir",
        str(output_dir),
        "--dataset",
        str(dataset),
        *extra_args,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
    )

    async def _drain(prefix: str):
        assert proc.stdout is not None
        async for line in proc.stdout:
            try:
                sys.stdout.write(f"[{prefix}] "+line.decode(errors="replace"))
            except Exception:
                pass

    drain_task = asyncio.create_task(_drain(engine))

    try:
        returncode = await asyncio.wait_for(proc.wait(), timeout=timeout_s)
    except asyncio.TimeoutError:
        with contextlib.suppress(Exception):
            proc.kill()
        returncode = 124
    await drain_task
    return returncode


@app.command()
def run_all(
    dataset: str = typer.Option(..., "--dataset", help="Path to dataset CSV (relative to scrape_evals/)"),
    suite: str = typer.Option("quality", help="Suite name"),
    output_dir: str = typer.Option("runs", help="Output base directory (relative to scrape_evals/)"),
    concurrency: int = typer.Option(0, help="Number of concurrent engines (0 = CPUs)"),
    timeout_minutes: int = typer.Option(45, help="Per-engine timeout in minutes"),
    resume: bool = typer.Option(False, help="Pass --resume to run_eval"),
    rerun: bool = typer.Option(False, help="Pass --rerun to run_eval (avoid with parallel; pre-clean instead)"),
    analysis_only: bool = typer.Option(False, help="Pass --analysis-only to run_eval"),
    dry_run: bool = typer.Option(False, help="Pass --dry-run to run_eval"),
    max_workers: int = typer.Option(None, help="Pass --max-workers to run_eval", rich_help_panel="Engine flags"),
):
    scrape_evals_root = Path(__file__).parent
    engines_dir = scrape_evals_root / "engines"
    engines = discover_engines(engines_dir)
    if not engines:
        typer.echo("No engines found under scrape_evals/engines")
        raise typer.Exit(1)

    out_base = scrape_evals_root / output_dir
    out_base.mkdir(parents=True, exist_ok=True)

    # NOTE: If running in parallel, prefer pre-clean outside instead of per-process --rerun
    extra: List[str] = []
    if resume:
        extra.append("--resume")
    if rerun:
        extra.append("--rerun")
    if analysis_only:
        extra.append("--analysis-only")
    if dry_run:
        extra.append("--dry-run")
    if max_workers is not None:
        extra += ["--max-workers", str(max_workers)]

    # Concurrency
    if concurrency <= 0:
        concurrency = os.cpu_count() or 4

    # Optionally pre-clean when --rerun set to avoid races across processes
    if rerun:
        for eng in engines:
            eng_dir = out_base / f"{eng}_{suite}"
            if eng_dir.exists():
                try:
                    for p in eng_dir.rglob("*"):
                        try:
                            if p.is_file():
                                p.unlink()
                        except Exception:
                            pass
                    for p in sorted(eng_dir.rglob("*"), reverse=True):
                        try:
                            if p.is_dir():
                                p.rmdir()
                        except Exception:
                            pass
                    eng_dir.rmdir()
                except Exception:
                    pass
        # Do not pass --rerun to children to avoid concurrent deletes
        extra = [a for a in extra if a != "--rerun"]

    sem = asyncio.Semaphore(concurrency)
    timeout_s = timeout_minutes * 60

    async def _runner(eng: str):
        async with sem:
            rc = await run_one_engine(
                eng, suite, out_base, scrape_evals_root / dataset, timeout_s, extra,
            )
            if rc != 0:
                typer.echo(f"[warn] engine={eng} exited with {rc}")

    async def _main():
        await asyncio.gather(*[_runner(e) for e in engines])

    asyncio.run(_main())
    typer.echo("All engines attempted.")


if __name__ == "__main__":
    app()


