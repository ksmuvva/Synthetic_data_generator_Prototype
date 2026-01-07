"""
Batch processing for large-scale synthetic data generation.

Provides parallel and distributed processing capabilities
for generating large synthetic datasets.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, list, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
from pathlib import Path
import pandas as pd


@dataclass
class BatchJob:
    """Single batch processing job."""

    job_id: str
    pattern_path: str
    count: int
    output_path: str
    worker_id: int = 0


@dataclass
class BatchResult:
    """Result of batch processing."""

    job_id: str
    status: str  # pending, running, completed, failed
    records_generated: int = 0
    output_file: Optional[str] = None
    error: Optional[str] = None


class BatchProcessor:
    """
    Process batch generation jobs.

    Supports parallel processing across multiple workers
    for scalable synthetic data generation.
    """

    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize processor.

        Args:
            max_workers: Maximum number of workers (default: CPU count)
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.results = {}

    def process_batch(
        self,
        jobs: list[BatchJob],
        parallel: bool = True,
    ) -> dict[str, BatchResult]:
        """
        Process batch of generation jobs.

        Args:
            jobs: List of batch jobs
            parallel: Use parallel processing

        Returns:
            Dictionary mapping job IDs to results
        """
        if parallel and len(jobs) > 1:
            return self._process_parallel(jobs)
        else:
            return self._process_sequential(jobs)

    def _process_sequential(
        self, jobs: list[BatchJob]
    ) -> dict[str, BatchResult]:
        """Process jobs sequentially."""
        results = {}

        for job in jobs:
            result = self._process_single_job(job)
            results[job.job_id] = result

        return results

    def _process_parallel(
        self, jobs: list[BatchJob]
    ) -> dict[str, BatchResult]:
        """Process jobs in parallel."""
        results = {}

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._process_single_job, job): job for job in jobs}

            for future in futures:
                job = futures[future]
                try:
                    result = future.result()
                    results[job.job_id] = result
                except Exception as e:
                    results[job.job_id] = BatchResult(
                        job_id=job.job_id,
                        status="failed",
                        error=str(e),
                    )

        return results

    def _process_single_job(self, job: BatchJob) -> BatchResult:
        """Process a single job."""
        # Import here to avoid issues in multiprocessing
        from synth.patterns.storage import PatternStorage
        from synth.generation.sampler import StatisticalSampler

        try:
            # Load pattern
            storage = PatternStorage()
            pattern = storage.load_pattern(Path(job.pattern_path).name)

            # Generate data
            sampler = StatisticalSampler()
            df = sampler.generate(pattern, job.count)

            # Save output
            output_path = Path(job.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)

            return BatchResult(
                job_id=job.job_id,
                status="completed",
                records_generated=job.count,
                output_file=str(output_path),
            )

        except Exception as e:
            return BatchResult(
                job_id=job.job_id,
                status="failed",
                error=str(e),
            )


class ProcessWorker:
    """
    Worker process for batch generation.

    Handles individual generation tasks in distributed setup.
    """

    def __init__(self, worker_id: int):
        """Initialize worker."""
        self.worker_id = worker_id

    def process_task(self, task: BatchJob) -> BatchResult:
        """Process a single task."""
        processor = BatchProcessor(max_workers=1)
        return processor._process_single_job(task)
