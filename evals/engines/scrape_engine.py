from __future__ import annotations

import asyncio
import inspect
import importlib
from types import ModuleType
from typing import List, Optional, Tuple, Type, cast, Callable

from evals.suites.types import ScrapeOutput, Task
from engines.base import Scraper as EngineScraper


class ScrapeEngine:
    def __init__(self, engine_name: str, max_workers: int) -> None:
        scraper_cls: Optional[Type] = None
        try:
            mod: ModuleType = importlib.import_module(f"engines.{engine_name}")
            # pick the first valid engine class implementing the Scraper protocol
            for attr in dir(mod):
                obj = getattr(mod, attr)
                try:
                    if (
                        isinstance(obj, type)
                        and obj is not EngineScraper
                        and hasattr(obj, "scrape")
                        and issubclass(obj, EngineScraper)  # runtime_checkable protocol
                    ):
                        scraper_cls = obj
                        break
                except TypeError:
                    continue
        except Exception:
            scraper_cls = None
        if scraper_cls is None:
            raise ValueError(f"Scrape engine not found: {engine_name}")
        assert scraper_cls is not None
        self.scraper_cls: Type = cast(Type, scraper_cls)
        self.engine_name = engine_name
        self.max_workers = max_workers

    async def _scrape_async(self, scraper, task: Task, run_id: str) -> ScrapeOutput:
        res = await scraper.scrape(task.url, run_id)
        content = res.get("content")
        return ScrapeOutput(
            scraper=str(res.get("scraper") or self.engine_name),
            url=str(res.get("url") or task.url),
            status_code=res.get("status_code"),
            error=res.get("error"),
            created_at=res.get("created_at"),
            format=res.get("format"),
            content_size=res.get("content_size"),
            content=content,
        )

    def _scrape_sync(self, scraper, task: Task, run_id: str) -> ScrapeOutput:
        res = scraper.scrape(task.url, run_id)
        content = res.get("content")
        return ScrapeOutput(
            scraper=str(res.get("scraper") or self.engine_name),
            url=str(res.get("url") or task.url),
            status_code=res.get("status_code"),
            error=res.get("error"),
            created_at=res.get("created_at"),
            format=res.get("format"),
            content_size=res.get("content_size"),
            content=content,
        )

    async def scrape_tasks(
        self,
        tasks: List[Task],
        run_id: str,
        resume_lookup: Optional[dict[str, bool]] = None,
        on_result: Optional[Callable[[Task, ScrapeOutput], None]] = None,
    ) -> List[Tuple[Task, ScrapeOutput]]:
        scraper = self.scraper_cls()
        is_async = inspect.iscoroutinefunction(getattr(scraper, "scrape", None))

        results: List[Tuple[Task, ScrapeOutput]] = []

        if is_async:
            sem = asyncio.Semaphore(self.max_workers)

            async def worker(t: Task) -> Tuple[Task, ScrapeOutput]:
                async with sem:
                    out = await self._scrape_async(scraper, t, run_id)
                    return (t, out)
            results: List[Tuple[Task, ScrapeOutput]] = []
            coros = [worker(t) for t in tasks]
            for coro in asyncio.as_completed(coros):
                t_out = await coro
                results.append(t_out)
                if on_result is not None:
                    try:
                        on_result(*t_out)
                    except Exception:
                        pass
        else:
            # For sync scrapers, sequential or future: could add ThreadPool here if needed
            for t in tasks:
                out = self._scrape_sync(scraper, t, run_id)
                pair = (t, out)
                results.append(pair)
                if on_result is not None:
                    try:
                        on_result(*pair)
                    except Exception:
                        pass

        return results


