# coding=utf-8
"""Wait for all subtasks have done.
"""
import tornado
import tornado.locks
from tornado.concurrent import Future


class ProcessWaiter(tornado.locks._TimeoutGarbageCollector):

    def __init__(self):
        super(ProcessWaiter, self).__init__()
        self._value = 0

    def __repr__(self):
        res = super(ProcessWaiter, self).__repr__()
        extra = 'locked' if self._value == 0 else 'unlocked,value:{0}'.format(
            self._value)
        if self._waiters:
            extra = '{0},waiters:{1}'.format(extra, len(self._waiters))
        return '<{0} [{1}]>'.format(res[1:-1], extra)

    def __enter__(self):
        self.processing()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.done()
        
    def processing(self):
        """Increment the counter and wake one waiter."""
        self._value -= 1

    def done(self):
        self._value += 1
        if self._value == 0:
            # wake all waiters and release them
            while self._waiters:
                waiter = self._waiters.popleft()
                waiter.set_result(tornado.locks._ReleasingContextManager(waiter))

    def wait_all_done(self, timeout=None):
        waiter = Future()
        if self._value == 0:
            waiter.set_result(tornado.locks._ReleasingContextManager(self))
        elif self._value < 0:
            self._waiters.append(waiter)
            if timeout:
                def on_timeout():
                    waiter.set_exception(tornado.gen.TimeoutError())
                    self._garbage_collect()
                io_loop = tornado.ioloop.IOLoop.current()
                timeout_handle = io_loop.add_timeout(timeout, on_timeout)
                waiter.add_done_callback(
                    lambda _: io_loop.remove_timeout(timeout_handle))
        else:
            raise ProcessWaiterSemaphoreException('Semaphore value is positive (val:%d)' % self._value)
        return waiter


class ProcessWaiterSemaphoreException(Exception):
    pass
