import time
import traceback
from datetime import datetime
from multiprocessing import Process, Semaphore, JoinableQueue


class BaseNode(object):
    def __init__(self, concurrency=1, *args, **kw):
        self.concurrency = concurrency

        self.input_queue = JoinableQueue()
        self.output_queue = JoinableQueue()

        self.processes = []

        self.semaphore = Semaphore(concurrency)

        self.pipes = []
        self.start_time = None
        self.initialize(*args, **kw)

    def initialize(self):
        pass

    def finished(self):
        pass

    def log(self, msg):
        print("%s: %s" % (datetime.now(), msg))

    def send(self, data):
        for pipe in self.pipes:
            pipe.semaphore.acquire()
            self.output_queue.put(data)

    def into(self, pipe):
        pipe.input_queue = self.output_queue
        self.pipes.append(pipe)

    def start(self):
        self.start_time = time.time()
        for _ in xrange(self.concurrency):
            p = Process(target=self._consume_input)
            self.processes.append(p)
            p.start()

        for pipe in self.pipes:
            pipe.start()

    def done(self):
        for pipe in self.pipes:
            pipe.input_queue.join()
            pipe.finished()


class Emitter(BaseNode):
    def emit(self):
        for i in xrange(100):
            yield i

    def _consume_input(self):
        for data in self.emit():
            self.send(data)
        self.done()


class Pipe(BaseNode):
    def process(self, data):
        raise NotImplemented()

    def _consume_input(self):
        while True:
            data = self.input_queue.get()
            try:
                output = self.process(data)
                items = iter(output)
                for output in items:
                    self.send(output)
            except TypeError:
                self.send(output)
            except Exception:
                print("Failed to process")
                print(traceback.format_exc())
            self.semaphore.release()
            self.input_queue.task_done()