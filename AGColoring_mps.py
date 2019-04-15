from MessagePassingSystem import *
import math
import lib, vis


class Processor(AbstractProcessor):
    def __init__(self, pid, is_async, delta, q, color):
        super().__init__(pid=pid, is_async=is_async)
        self.delta = delta
        self.q = q
        self.color = (math.floor(color / self.q), color % self.q)

    # Upon receiving PAYLOAD msg
    # If we run in sync environment, worker will receive messages
    # received in previous round
    def worker(self, msgs, srcs):
        assert len(msgs) == len(self.neighbors)
        if any(map(lambda x: x[1][1] == self.color[1], msgs)):
            self.color = (self.color[0], (self.color[0] + self.color[1]) % self.q)
        else:
            self.color = (0, self.color[1])
            self.log('My Color: %s' % str(self.color))
            self.go_inactive()

        self.send_to_neighbors((MsgType.PAYLOAD, self.color))

    # Upon receiving no msg
    def init_config(self):
        self.send_to_neighbors((MsgType.PAYLOAD, self.color))


if __name__ == '__main__':
    n = 10

    G = lib.gen_random_graph(n, 10)
    # vis.plot(G, node_text={id: id for id in G.nodes()})

    delta = lib.calc_delta(G)
    print('Maximum degree: ' + str(delta))

    mps = MessagePassingSystem(proc_class=Processor,
                               proc_args={
                                   pid: {'delta': delta, 'q': lib.choose_prime(delta), 'color': pid
                                    } for pid in G.nodes()},
                               n_proc=n,
                               edges=G.edges(),
                               is_async=False,
                               max_channel_delay=0)
    mps.start()
