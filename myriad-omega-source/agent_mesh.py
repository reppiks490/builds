"""10,000 independent, non-spinning asyncio actors for MYRIAD Ω.

Each actor has its own mailbox and task identity. All use the same capabilities,
model router and five-brain dispatch path; actors do not each load a model.
The mesh runs in-process and must not be confused with 10,000 OS processes or
10,000 simultaneous LLM inference sessions.
"""
from __future__ import annotations
import asyncio
from collections import Counter
from datetime import datetime, timezone
import threading
import time

class MeshError(RuntimeError):
    pass

class AgentMesh:
    def __init__(self, agent_ids, job_handler, *, max_parallel=2, start_timeout=25):
        self.ids=tuple(agent_ids)
        if len(self.ids)!=len(set(self.ids)):
            raise ValueError('Duplicate agent identity')
        self._index={agent_id:i for i,agent_id in enumerate(self.ids)}
        self._job_handler=job_handler
        self._max_parallel=max_parallel
        self._ready=threading.Event()
        self._thread=threading.Thread(target=self._thread_main,name='myriad-10k-actor-mesh',daemon=True)
        self._loop=None
        self._mailboxes=[]
        self._tasks=[]
        self._stopping=False
        self._started=0
        self._completed=0
        self._failed=0
        self._inflight=0
        self._dispatches=0
        self._heartbeat=0.0
        self._start_time=time.monotonic()
        self._boot_error=None
        self._thread.start()
        if not self._ready.wait(start_timeout):
            raise MeshError('10,000-actor startup timed out')
        if self._boot_error:
            raise MeshError('Actor startup failed: '+str(self._boot_error))
        snap=self.status()
        if snap['ready_actors']!=len(self.ids):
            raise MeshError('Partial actor startup: '+str(snap))

    def _thread_main(self):
        try:asyncio.run(self._main())
        except BaseException as exc:
            self._boot_error=exc
            self._ready.set()

    async def _main(self):
        self._loop=asyncio.get_running_loop()
        self._semaphore=asyncio.Semaphore(self._max_parallel)
        self._stop=asyncio.Event()
        self._mailboxes=[asyncio.Queue(maxsize=1) for _ in self.ids]
        self._tasks=[asyncio.create_task(self._actor(i),name=self.ids[i]) for i in range(len(self.ids))]
        # Allow every independently scheduled coroutine to reach its mailbox.
        for _ in range(5):
            if self._started==len(self.ids):break
            await asyncio.sleep(0)
        self._heartbeat=time.monotonic()
        self._monitor=asyncio.create_task(self._watchdog())
        self._ready.set()
        await self._stop.wait()
        self._stopping=True
        self._monitor.cancel()
        for task in self._tasks:task.cancel()
        await asyncio.gather(*self._tasks,return_exceptions=True)
        await asyncio.gather(self._monitor,return_exceptions=True)

    async def _watchdog(self):
        while True:
            self._heartbeat=time.monotonic()
            await asyncio.sleep(1.0)

    async def _actor(self,i):
        self._started+=1
        queue=self._mailboxes[i]
        while True:
            job=await queue.get()
            try:
                async with self._semaphore:
                    self._inflight+=1
                    try:
                        await asyncio.to_thread(self._job_handler,job)
                        self._completed+=1
                    except Exception:
                        self._failed+=1
                    finally:self._inflight-=1
            finally:queue.task_done()

    async def _enqueue(self,agent_id,job_id):
        if self._stopping:raise MeshError('Agent mesh shutting down')
        try:i=self._index[agent_id]
        except KeyError as exc:raise MeshError('Unknown agent '+str(agent_id)) from exc
        queue=self._mailboxes[i]
        if queue.full():raise MeshError('Agent mailbox is full')
        queue.put_nowait(job_id)
        self._dispatches+=1
        return True

    async def _enqueue_many(self,assignments):
        if self._stopping:raise MeshError('Agent mesh shutting down')
        seen=set()
        for agent_id,job_id in assignments:
            if agent_id not in self._index or agent_id in seen:
                raise MeshError('Unknown or duplicate actor in batch')
            seen.add(agent_id)
            if self._mailboxes[self._index[agent_id]].full():
                raise MeshError('One or more agent mailboxes occupied')
        for agent_id,job_id in assignments:
            self._mailboxes[self._index[agent_id]].put_nowait(job_id)
        self._dispatches+=len(assignments)
        return len(assignments)

    def dispatch_many(self,assignments):
        """Atomic bulk enrollment; safe for boot certification, not LLM fan-out."""
        items=list(assignments)
        if not items:return 0
        return asyncio.run_coroutine_threadsafe(self._enqueue_many(items),self._loop).result(timeout=10)

    def dispatch(self,agent_id,job_id):
        if not self._loop or self._stopping:raise MeshError('Agent mesh unavailable')
        return asyncio.run_coroutine_threadsafe(self._enqueue(agent_id,job_id),self._loop).result(timeout=5)

    async def _get_status(self):
        ready=sum(not task.done() for task in self._tasks)
        busy=sum(not q.empty() for q in self._mailboxes)
        return {'mode':'in_process_async_actor_fleet','total_registered':len(self.ids),
            'ready_actors':ready,'active_jobs':self._inflight,
            'queued_mailboxes':busy,'dispatches':self._dispatches,
            'completed_dispatches':self._completed,'handler_errors':self._failed,
            'max_parallel_model_pipelines':self._max_parallel,
            'mesh_heartbeat_age_seconds':round(time.monotonic()-self._heartbeat,3),
            'uptime_seconds':round(time.monotonic()-self._start_time,3),
            'models_loaded_per_actor':0,
            'all_actors_ready':ready==len(self.ids),
            'scope':'single Python host; not remote/cloud deployment'}

    def status(self):
        if not self._loop or self._stopping or not self._thread.is_alive():
            return {'mode':'offline','total_registered':len(self.ids),'ready_actors':0,'all_actors_ready':False}
        return asyncio.run_coroutine_threadsafe(self._get_status(),self._loop).result(timeout=5)

    async def _get_agent(self,agent_id):
        try:i=self._index[agent_id]
        except KeyError as exc:raise MeshError('Unknown actor') from exc
        task=self._tasks[i]
        return {'agent':agent_id,'actor_alive':not task.done(),
                'mailbox_depth':self._mailboxes[i].qsize(),
                'execution_model':'shared, capacity-limited five-brain model gateway'}

    def agent_status(self,agent_id):
        if not self._loop or self._stopping:raise MeshError('Actor mesh unavailable')
        return asyncio.run_coroutine_threadsafe(self._get_agent(agent_id),self._loop).result(timeout=5)

    def stop(self,timeout=8):
        if self._stopping:return
        if self._loop and self._thread.is_alive():
            try:asyncio.run_coroutine_threadsafe(self._signal_stop(),self._loop).result(timeout=3)
            except (RuntimeError,TimeoutError):pass
        self._thread.join(timeout=timeout)
        self._stopping=True

    async def _signal_stop(self):self._stop.set()
