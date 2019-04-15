from MessagePassingSystem import *


class Processor(AbstractProcessor):
    def worker(self, msg, src):
        if msg[0] == MsgType.PAYLOAD:
            # Message with payload

            if msg[1] == 'Probe':
                j, k, d = msg[2], msg[3], msg[4]
                if j == self.pid:
                    # TERMINATE
                    self.send_to_all_except((MsgType.TERMINATION,), src)
                    self.terminate()
                elif j > self.pid and d < math.pow(2, k):
                    self.send_to_all_except((MsgType.PAYLOAD, 'Probe', j, k, d + 1), src)
                elif j > self.pid and d >= math.pow(2, k):
                    self.send((MsgType.PAYLOAD, 'Reply', j, k), src)

            elif msg[1] == 'Reply':
                j, k = msg[2], msg[3]
                if j != self.pid:
                    self.send_to_all_except(msg, src)
                else:
                    self.received_replies.add(src)
                    if len(self.received_replies) == 2:
                        for nb in self.neighbors:
                            self.send((MsgType.PAYLOAD, 'Probe', self.pid, k + 1, 1), nb)

        elif msg[0] == MsgType.TERMINATION:
            self.send_to_all_except((MsgType.TERMINATION,), src)
            self.terminate()

    def init_config(self):
        self.received_replies = set()
        for nb in self.neighbors:
            self.send((MsgType.PAYLOAD, 'Probe', self.pid, 0, 1), nb)


if __name__ == '__main__':
    n = 7
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0)]

    mps = MessagePassingSystem(proc_class=Processor, n_proc=n, edges=edges, is_async=False, max_channel_delay=0)
    mps.start()
