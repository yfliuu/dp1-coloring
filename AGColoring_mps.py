from MessagePassingSystem import *


class Processor(AbstractProcessor):
    def __init__(self, delta, q, color):
        super().__init__()
        self.received_replies = set()
        self.delta = delta
        self.q = q
        self.color = (math.floor(color / self.q), color % self.q)

    def worker(self, msg, src):
        while True:
            self.send_to_neighbors((MsgType.PAYLOAD, self.color))

    def init_config(self):
        self.received_replies = set()
        for nb in self.neighbors:
            self.send((MsgType.PAYLOAD, 'Probe', self.pid, 0, 1), nb)


if __name__ == '__main__':
    pass
