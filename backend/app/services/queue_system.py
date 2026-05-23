"""
Queue and Retry System with Exponential Backoff
Implements payment queues, webhook queues, settlement queues, and dead-letter queues
"""

import asyncio
import random
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import json


class QueueType(Enum):
    """Queue types"""
    PAYMENT = "payment"
    WEBHOOK = "webhook"
    SETTLEMENT = "settlement"
    RECONCILIATION = "reconciliation"
    NOTIFICATION = "notification"
    WITHDRAWAL = "withdrawal"


class JobStatus(Enum):
    """Job status states"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class RetryStrategy(Enum):
    """Retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    IMMEDIATE = "immediate"


@dataclass
class Job:
    """Queue job"""
    job_id: str
    queue_type: QueueType
    payload: Dict[str, Any]
    status: JobStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempt_number: int = 0
    max_attempts: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "queue_type": self.queue_type.value,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "attempt_number": self.attempt_number,
            "max_attempts": self.max_attempts,
            "retry_strategy": self.retry_strategy.value,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


class QueueSystem:
    """
    Queue and retry system with exponential backoff
    Simulates BullMQ/Celery behavior
    """
    
    def __init__(self):
        self._queues: Dict[QueueType, List[Job]] = {
            QueueType.PAYMENT: [],
            QueueType.WEBHOOK: [],
            QueueType.SETTLEMENT: [],
            QueueType.RECONCILIATION: [],
            QueueType.NOTIFICATION: [],
            QueueType.WITHDRAWAL: []
        }
        self._dead_letter_queue: List[Job] = []
        self._job_handlers: Dict[QueueType, Callable] = {}
        self._processing_locks: Dict[str, asyncio.Lock] = {}
        
        # Configuration
        self.default_max_attempts = 3
        self.default_retry_strategy = RetryStrategy.EXPONENTIAL_BACKOFF
        self.default_retry_delay_base = 2  # seconds
        self.max_retry_delay = 300  # 5 minutes
        
    def register_handler(self, queue_type: QueueType, handler: Callable) -> None:
        """Register a handler for a queue type"""
        self._job_handlers[queue_type] = handler
    
    async def enqueue(
        self,
        queue_type: QueueType,
        payload: Dict[str, Any],
        max_attempts: Optional[int] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Job:
        """
        Enqueue a job
        Returns job record
        """
        job_id = f"JOB_{uuid.uuid4().hex[:16]}"
        
        job = Job(
            job_id=job_id,
            queue_type=queue_type,
            payload=payload,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            max_attempts=max_attempts or self.default_max_attempts,
            retry_strategy=retry_strategy or self.default_retry_strategy,
            metadata=metadata
        )
        
        self._queues[queue_type].append(job)
        return job
    
    async def dequeue(self, queue_type: QueueType) -> Optional[Job]:
        """
        Dequeue a pending job
        Returns job or None if queue is empty
        """
        queue = self._queues[queue_type]
        
        # Find next pending job that is ready to process
        for i, job in enumerate(queue):
            if job.status == JobStatus.PENDING:
                # Check if retry delay has passed
                if job.next_retry_at and job.next_retry_at > datetime.utcnow():
                    continue
                return queue.pop(i)
        
        return None
    
    async def process_job(self, job: Job) -> Job:
        """
        Process a job with its registered handler
        Returns updated job
        """
        handler = self._job_handlers.get(job.queue_type)
        if not handler:
            raise ValueError(f"No handler registered for queue type: {job.queue_type.value}")
        
        # Get lock for job
        if job.job_id not in self._processing_locks:
            self._processing_locks[job.job_id] = asyncio.Lock()
        
        async with self._processing_locks[job.job_id]:
            job.status = JobStatus.PROCESSING
            job.processed_at = datetime.utcnow()
            job.attempt_number += 1
            
            try:
                # Call handler
                result = await handler(job.payload)
                
                # Mark as completed
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.error_message = None
                
                return job
                
            except Exception as e:
                # Handle failure
                error_message = str(e)
                job.error_message = error_message
                
                if job.attempt_number >= job.max_attempts:
                    # Max attempts reached, move to dead letter queue
                    job.status = JobStatus.DEAD_LETTER
                    self._dead_letter_queue.append(job)
                else:
                    # Schedule retry
                    job.status = JobStatus.RETRYING
                    job.next_retry_at = self._calculate_next_retry(job)
                    self._queues[job.queue_type].append(job)
                
                return job
    
    def _calculate_next_retry(self, job: Job) -> datetime:
        """Calculate next retry time based on strategy"""
        base_delay = self.default_retry_delay_base
        
        if job.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(base_delay ** job.attempt_number, self.max_retry_delay)
        elif job.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = min(base_delay * job.attempt_number, self.max_retry_delay)
        elif job.retry_strategy == RetryStrategy.FIXED_INTERVAL:
            delay = base_delay
        else:
            delay = 0
        
        return datetime.utcnow() + timedelta(seconds=delay)
    
    async def process_queue(
        self,
        queue_type: QueueType,
        max_concurrent: int = 5
    ) -> List[Job]:
        """
        Process all pending jobs in a queue
        Returns list of processed jobs
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore():
            async with semaphore:
                job = await self.dequeue(queue_type)
                if job:
                    return await self.process_job(job)
                return None
        
        tasks = []
        while True:
            job = await self.dequeue(queue_type)
            if not job:
                break
            tasks.append(process_with_semaphore())
        
        if not tasks:
            return []
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and convert exceptions to failed jobs
        processed_jobs = []
        for result in results:
            if isinstance(result, Exception):
                # Create failed job from exception
                job = Job(
                    job_id=f"ERR_{uuid.uuid4().hex[:16]}",
                    queue_type=queue_type,
                    payload={"error": str(result)},
                    status=JobStatus.FAILED,
                    created_at=datetime.utcnow(),
                    error_message=str(result)
                )
                processed_jobs.append(job)
            elif result:
                processed_jobs.append(result)
        
        return processed_jobs
    
    async def process_all_queues(self, max_concurrent: int = 5) -> Dict[QueueType, List[Job]]:
        """
        Process all queues
        Returns dictionary of queue types to processed jobs
        """
        results = {}
        
        for queue_type in QueueType:
            results[queue_type] = await self.process_queue(queue_type, max_concurrent)
        
        return results
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        for queue in self._queues.values():
            for job in queue:
                if job.job_id == job_id:
                    return job
        for job in self._dead_letter_queue:
            if job.job_id == job_id:
                return job
        return None
    
    def get_queue_jobs(self, queue_type: QueueType, status: Optional[JobStatus] = None) -> List[Job]:
        """Get jobs in a queue, optionally filtered by status"""
        jobs = self._queues[queue_type]
        if status:
            return [j for j in jobs if j.status == status]
        return jobs.copy()
    
    def get_dead_letter_jobs(self) -> List[Job]:
        """Get all dead letter jobs"""
        return self._dead_letter_queue.copy()
    
    async def retry_dead_letter_job(self, job_id: str) -> Job:
        """Retry a dead letter job"""
        for i, job in enumerate(self._dead_letter_queue):
            if job.job_id == job_id:
                # Remove from dead letter queue
                dlq_job = self._dead_letter_queue.pop(i)
                
                # Reset job for retry
                dlq_job.status = JobStatus.PENDING
                dlq_job.attempt_number = 0
                dlq_job.next_retry_at = None
                dlq_job.error_message = None
                
                # Re-enqueue
                self._queues[dlq_job.queue_type].append(dlq_job)
                
                return dlq_job
        
        raise ValueError(f"Dead letter job not found: {job_id}")
    
    async def purge_queue(self, queue_type: QueueType) -> int:
        """Purge all jobs from a queue"""
        count = len(self._queues[queue_type])
        self._queues[queue_type].clear()
        return count
    
    async def purge_dead_letter_queue(self) -> int:
        """Purge dead letter queue"""
        count = len(self._dead_letter_queue)
        self._dead_letter_queue.clear()
        return count
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {}
        
        for queue_type, jobs in self._queues.items():
            pending = len([j for j in jobs if j.status == JobStatus.PENDING])
            processing = len([j for j in jobs if j.status == JobStatus.PROCESSING])
            completed = len([j for j in jobs if j.status == JobStatus.COMPLETED])
            failed = len([j for j in jobs if j.status == JobStatus.FAILED])
            retrying = len([j for j in jobs if j.status == JobStatus.RETRYING])
            
            stats[queue_type.value] = {
                "total": len(jobs),
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "retrying": retrying
            }
        
        stats["dead_letter"] = {
            "total": len(self._dead_letter_queue)
        }
        
        return stats
    
    def clear_all(self) -> None:
        """Clear all queues (for testing)"""
        for queue_type in QueueType:
            self._queues[queue_type].clear()
        self._dead_letter_queue.clear()
        self._processing_locks.clear()


# Global queue system instance
queue_system = QueueSystem()
