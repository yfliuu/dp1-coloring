import threading, time
import queue
import random
from enum import Enum, auto
from collections import defaultdict as dd


class Status(Enum):
    AWAKENED = auto(),
    AWAITING_MSG = auto(),
    MSG_DELIVERED = auto(),
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
    def __init__(self, pid=None, is_async=True, verbose=True):
        # One in_buf/out_buf for all incoming/outgoing channels.
        # We will label the message with sender/receiver.
        self.in_buf = queue.Queue()
        self.out_buf = queue.Queue()
        self.pid = pid
        self.thread = threading.Thread(target=self.core)
        self.verbose = verbose
        self.status = Status.TERMINATED
        self.neighbors = set()
        self.is_async = is_async
        self.inactive = False

        # Tree related
        self.root = None
        self.parent = None
        self.children = set()

    def core(self):
        self.status = Status.AWAKENED
        self.init_config()
        if self.is_async:
            while self.status != Status.TERMINATED:
                # Signal message passing core that we're awaiting messages
                self.status = Status.AWAITING_MSG

                # Get our package and call handler.
                # get blocks if there's no messages.
                # TODO: Inactive shutdown for asynchronous system
                # TODO: Tests required
                msg, src = self.in_buf.get(block=True)
                self.status = Status.TASK_DONE
                self.worker(msg, src)
        else:
            while self.status != Status.TERMINATED:
                # Signal message passing core that we're awaiting messages
                self.status = Status.AWAITING_MSG

                # Wait for the sync core to deliver our messages
                while self.status != Status.MSG_DELIVERED and self.is_alive():
                    pass

                # This is for inactive shutdown.
                if not self.is_alive():
                    break

                # Get all packages received in this round and call handler.
                msgs, srcs = [], []
                while not self.in_buf.empty():
                    msg, src = self.in_buf.get_nowait()
                    msgs.append(msg)
                    srcs.append(src)
                self.status = Status.TASK_DONE
                self.worker(msgs, srcs)
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

    def send_to_neighbors(self, msg):
        for nb in self.neighbors:
            self.send(msg, nb)

    def send_to_all_except(self, msg, src):
        for nb in self.neighbors:
            if nb != src:
                self.send(msg, nb)

    def terminate(self):
        self.status = Status.TERMINATED

    # Inactive is useful when you only forward messages.
    # If all processors are in INACTIVE mode, system will shutdown.
    def go_inactive(self):
        self.inactive = True

    def set_status(self, status):
        self.status = status

    def is_alive(self):
        return self.status != Status.TERMINATED

    def log(self, msg):
        if self.verbose:
            print('PID %s: %s' % (self.pid, msg))


class MessagePassingSystem:
    # TODO: Using Thread pool to improve performance
    # proc_args is a dict with mapping {pid: {'property1': value1, 'property2': value2, ...}}
    def __init__(self, proc_class, proc_args, n_proc, edges, is_async, max_channel_delay=0, verbose=True):
        self.max_channel_delay = max_channel_delay

        if not issubclass(proc_class, AbstractProcessor):
            ValueError('proc_class must inherit AbstractProcessor')

        self.processors = [proc_class(pid=pid, is_async=is_async, **proc_args[pid]) for pid in range(n_proc)]
        self.verbose = verbose
        self.msg_buf = dd(queue.Queue)

        # Synchronous rounds, used in is_async=false
        self.round = 1

        self.edges = edges
        self.edge_dict = dd(set)
        for edge in edges:
            self.edge_dict[edge[0]].add(edge[1])
            self.edge_dict[edge[1]].add(edge[0])

        if is_async:
            self.thread = threading.Thread(target=self.async_core)
        else:
            self.thread = threading.Thread(target=self.sync_core)

    def all_inactive(self):
        return all([p.inactive for p in self.processors])

    def all_status(self, status):
        return all([p.status == status for p in self.processors])

    def all_alive_status(self, status):
        return all([p.status == status for p in self.processors if p.status != Status.TERMINATED])

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
            # Here we don't need to check if the sender is alive.
            # If a sender sends a message and terminates, that message should be delivered.
            if self.processors[target].is_alive():
                self.msg_buf[target].put((item, p.pid))
                p.log('msg sent %s -> %s : %s' % (p.pid, target, ' '.join([str(k) for k in item])))
        except queue.Empty:
            pass

    def clear_msg_buf(self):
        for target in self.msg_buf:
            try:
                delivered = False
                while not self.msg_buf[target].empty():
                    pkg = self.msg_buf[target].get()
                    self.processors[target].in_buf.put(pkg)
                    delivered = True

                if delivered:
                    self.processors[target].set_status(Status.MSG_DELIVERED)
            except queue.Empty:
                pass

    def sync_core(self):
        while not self.all_status(Status.TERMINATED):
            # Wait for all alive processors to finish their computing task
            while not self.all_alive_status(Status.AWAITING_MSG):
                pass

            # Simulate the latency of channel
            if self.max_channel_delay > 0:
                time.sleep(random.uniform(0, self.max_channel_delay))

            # self.log('round %s' % (self.round,))
            # self.round += 1

            # Push all messages ready to be sent to msg_buf
            # If we push directly to target's in_buf, then some messages that should
            # be send next round would be inserted to in_buf and be send this round.
            for p in self.processors:
                self.clear_out_buf(p)

            # Deliver pending messages.
            self.clear_msg_buf()

            # All processors is in inactive mode, system shutdown
            if self.all_inactive():
                for p in self.processors:
                    p.terminate()

        self.log('All processors have terminated or are in inactive state, message passing system shutdown')

    def async_core(self):
        while not self.all_status(Status.TERMINATED):
            indexes = [i for i in range(len(self.processors))]
            random.shuffle(indexes)
            for i in indexes:
                p = self.processors[i]

                # Go through all messages awaiting delivery, flip a coin to decide whether to send it.
                # If we send out immediately it won't feel like async.
                # The message won't be lost and can have arbitrary delay.
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
