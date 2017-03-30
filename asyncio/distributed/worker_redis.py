import os
import signal
import asyncio
import aioredis
import traceback
import sys

class CancelJob(Exception):
    pass

class ImmediateExit(Exception):
    pass

class HandledExit(Exception):
    pass

class TerminateWorker(Exception):
    pass

class Worker:
    def __init__(self, *,
                 loop: asyncio.AbstractEventLoop = None,
                 worker_settings: dict = None,
                 handlers: dict = {}
                 ) -> None:
        self.loop = loop or getattr(self, 'loop', None) or asyncio.get_event_loop()
        self.worker_settings = worker_settings or {}
        self._worker_redis_pool = None
        self._is_running = True
        signal.signal(signal.SIGINT, self.handle_sig)
        signal.signal(signal.SIGTERM, self.handle_sig)
        signal.signal(signal.SIGUSR1, self.handle_sig_usr)
        self._task_exception = None
        self.__handlers = handlers
        self._pending_tasks = set()  # type: set(asyncio.futures.Future)
        self.jobs_complete = 0
        self.jobs_failed = 0
        self._shutdown_lock = asyncio.Lock(loop=self.loop)

    async def create_redis_pool(self) -> aioredis.RedisPool:
        return await aioredis.create_pool(
            (
                self.worker_settings['HOST'],
                self.worker_settings['PORT'],
            ), loop=self.loop,
            db=self.worker_settings['DB'],
            password=self.worker_settings.get('PASSWORD'),
        )

    async def get_redis_pool(self) -> aioredis.RedisPool:
        if self._worker_redis_pool is None:
            self._worker_redis_pool = await self.create_redis_pool()
        return self._worker_redis_pool

    async def get_redis_conn(self):
        pool = await self.get_redis_pool()
        return pool.get()

    async def close(self):
        if self._worker_redis_pool:
            self._worker_redis_pool.close()
            await self._worker_redis_pool.wait_closed()
            await self._worker_redis_pool.clear()

    def handle_sig_usr(self, signum, frame):
        self.handle_sig(signum, frame)  # TODO: make some changes!!

    def handle_sig(self, signum, frame):
        self._is_running = False  # Stop poll from redis

        # self.ioloop.create_task(self.close())
        print('pid=%d, got signal: %d, stopping...' % (os.getpid(), signum))
        signal.signal(signal.SIGINT, self.handle_sig_force)
        signal.signal(signal.SIGTERM, self.handle_sig_force)
        signal.signal(signal.SIGALRM, self.handle_sig_force)
        signal.alarm(30)  # after 30 secs exit
        raise HandledExit()

    def handle_sig_force(self, signum, frame):
        print('pid=%d, got signal: %d again, forcing exit' % (os.getpid(), signum))
        raise ImmediateExit(
            'Warning: force exit, %d tasks are died.' % len(list(filter(lambda x: not x.done(), self._pending_tasks))))

    async def poll(self):
        mq_list = self.__handlers.keys()
        while self._is_running:
            async with await self.get_redis_conn() as redis:
                msg = await redis.blpop(*list(mq_list))
                if not msg:
                    continue
                queue_name, data = msg
                queue_name = queue_name.decode('utf-8')
                handlers = self.__handlers.get(queue_name, [])
                for handler in handlers:
                    self.schedule(queue_name, handler, data)

    async def run_job(self, queue_name, func, *args, **kwargs):
        try:
            result = await func(*args, **kwargs)
        except CancelJob as e:
            # job is cancelled.
            print('The job has been cancelled.')
        except Exception as e:
            print('run_job task error ', str(e))
            traceback.print_exc(file=sys.stdout)
            if isinstance(e, HandledExit):
                return 0
            elif isinstance(e, TerminateWorker):
                raise e

            self._task_exception = e
            return 1
        else:
            # TODO: log
            print('job has successfully done.')
            return 0

    def job_callback(self, task):
        self._pending_tasks.remove(task)
        print('_pending_tasks length %d', len(self._pending_tasks))
        self.jobs_complete += 1
        task_exception = task.exception()
        if task_exception:
            self._is_running = False
            self._task_exception = task_exception
        elif task.result():
            self.jobs_failed += 1
            print('Task complete, %d jobs done, %d failed' % (self.jobs_complete, self.jobs_failed))

    def schedule(self, queue_name, handler, data):
        task = self.loop.create_task(self.run_job(queue_name, handler, data))
        task.add_done_callback(self.job_callback)
        self._pending_tasks.add(task)

    async def shutdown(self):
        with await self._shutdown_lock:
            if self._pending_tasks:
                print('Shutting down worker, waiting for %d jobs to finish' % len(self._pending_tasks))
                await asyncio.wait(self._pending_tasks, loop=self.loop)
            await self.close()

    async def start(self):
        try:
            await self.poll()
        finally:
            await self.shutdown()
            if self._task_exception:
                print('Found task exception "%s"' % self._task_exception)
                raise self._task_exception
