import threading, time
import queue
import random
import math
from enum import Enum, auto
from collections import defaultdict as dd


class Status(Enum):
    AWAKENED = auto(),
    AWAITING_MSG = auto(),
    TASK_DONE = auto(),
    TERMINATED = auto(),


class MsgType(Enum):
    PAYLOAD = auto(),
    TERMINATION = auto(),
    ACKNOWLEDGEMENT = auto(),
    KEEP_ALIVE = auto(),

    def __str__(self):
        return self.name


class AbstractProcessor:
    def __init__(self, pid=None, verbose=True):
        # One in_buf/out_buf for all incoming/outgoing channels.
        # We will label the message with sender/receiver.
        self.in_buf = queue.Queue()
        self.out_buf = queue.Queue()
        self.pid = pid
        self.thread = threading.Thread(target=self.core)
        self.verbose = verbose
        self.status = Status.TERMINATED
        self.neighbors = set()

        # Tree related
        self.root = None
        self.parent = None
        self.children = set()

    def core(self):
        self.status = Status.AWAKENED
        self.init_config()
        while self.status != Status.TERMINATED:
            self.status = Status.AWAITING_MSG
            msg, src = self.in_buf.get(block=True)
            self.status = Status.TASK_DONE
            self.worker(msg, src)
        self.log('Terminated')

    def wake_up(self):
        self.log('Core started')
        self.thread.start()

    def worker(self, msg, src):
        raise NotImplementedError

    def init_config(self):
        raise NotImplementedError

    def send(self, msg, target):
        self.out_buf.put((msg, target), True)

    def send_to_all_except(self, msg, src):
        for nb in self.neighbors:
            if nb != src:
                self.send(msg, nb)

    def terminate(self):
        self.status = Status.TERMINATED

    def is_alive(self):
        return self.status != Status.TERMINATED

    def log(self, msg):
        if self.verbose:
            print('PID %s: %s' % (self.pid, msg))


class MessagePassingSystem:
    def __init__(self, proc_class, n_proc, edges, is_async, max_channel_delay=0.5, verbose=True):
        self.max_channel_delay = max_channel_delay
        self.processors = [proc_class(pid=i) for i in range(n_proc)]
        self.verbose = verbose
        self.msg_buf = dd(queue.Queue)

        self.edges = edges
        self.edge_dict = dd(set)
        for edge in edges:
            self.edge_dict[edge[0]].add(edge[1])
            self.edge_dict[edge[1]].add(edge[0])

        if is_async:
            self.thread = threading.Thread(target=self.async_core)
        else:
            self.thread = threading.Thread(target=self.sync_core)

    def all_status(self, status):
        return all([p.status == status for p in self.processors])

    def clear_out_buf(self, p):
        while not p.out_buf.empty():
            self.send_to_medium_buf(p)

    # Direct delivery: Will trigger target's computation event immediately.
    # Used in async systems.
    def send_one_msg(self, p):
        try:
            item, target = p.out_buf.get_nowait()
            if self.processors[target].is_alive():
                self.processors[target].in_buf.put((item, p.pid))
                p.log('msg sent %s -> %s : %s' % (p.pid, target, ' '.join([str(k) for k in item])))
        except queue.Empty:
            pass

    def send_to_medium_buf(self, p):
        try:
            item, target = p.out_buf.get_nowait()
            if p.is_alive() and self.processors[target].is_alive():
                self.msg_buf[target].put((item, p.pid))
                p.log('msg sent %s -> %s : %s' % (p.pid, target, ' '.join([str(k) for k in item])))
        except queue.Empty:
            pass

    def clear_msg_buf(self):
        for target in self.msg_buf:
            try:
                while not self.msg_buf[target].empty():
                    pkg = self.msg_buf[target].get_nowait()
                    self.processors[target].in_buf.put(pkg)
            except queue.Empty:
                pass

    def sync_core(self):
        while not self.all_status(Status.TERMINATED):
            # Wait for all processors to finish their computing task
            while not self.all_status(Status.AWAITING_MSG):
                pass

            # Simulate the latency of channel
            time.sleep(random.uniform(0, self.max_channel_delay))

            # Push all messages ready to be sent to msg_buf
            # If we push directly to target's in_buf, then some messages that should
            # be send next round would be inserted to in_buf and be send this round.
            for p in self.processors:
                self.clear_out_buf(p)

            # Deliver pending messages.
            self.clear_msg_buf()

        self.log('All processors have terminated, message passing system shutdown')

    def async_core(self):
        while not self.all_status(Status.TERMINATED):
            indexes = [i for i in range(len(self.processors))]
            random.shuffle(indexes)
            for i in indexes:
                p = self.processors[i]

                # Go through all messages awaiting delivery, flip a coin to decide whether to send it.
                buf_size = p.out_buf.qsize()
                for _ in range(buf_size):
                    if random.choice([True, False]):
                        self.send_one_msg(p)

        self.log('All processors have terminated, message passing system shutdown')

    def start(self):
        self.log('Constructing edges')
        for p in self.processors:
            p.neighbors = self.edge_dict[p.pid]
            self.log('Neighbors of %s: %s' % (p.pid, str(p.neighbors)))

        self.log('System start')
        for p in self.processors:
            p.wake_up()
        self.thread.start()

    def log(self, msg):
        if self.verbose:
            print('[Message Passing System]: ' + msg)

    @staticmethod
    def random_edges_connected(v, e):
        pass