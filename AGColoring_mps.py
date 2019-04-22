from MessagePassingSystem import *
import math
import lib, vis


class Processor(AbstractProcessor):
    def __init__(self, pid, is_async, delta, q, color):
        super().__init__(pid=pid, is_async=is_async)
        self.delta = delta
        self.q = q
        self.color = (math.floor(color / self.q), color % self.q)

        self.reduced_color = None

        # Stage == 0 means we are in the middle of AG coloring.
        # Stage == 1 means that we are doing color reduction.
        self.stage = 0

    # Upon receiving PAYLOAD msg
    # If we run in sync environment, worker will receive messages
    # received in previous round
    def worker(self, msgs, srcs):
        # assert len(msgs) == len(self.neighbors)
        if self.stage == 0:
            # Messages for first stage AGColoring
            if any(map(lambda x: x[1][1] == self.color[1], msgs)):
                self.color = (self.color[0], (self.color[0] + self.color[1]) % self.q)
            else:
                self.color = (0, self.color[1])
                self.log('My Color: %s' % str(self.color))
                self.stage = 1
                self.reduced_color = self.color[1]

            self.send_to_neighbors((MsgType.PAYLOAD, self.color, 0))
        elif self.stage == 1:
            # We'll still receive all stage 0 messages.
            # First respond to those still in stage 0.
            unfinished, finalized = lib.list_group_by(lambda x: x[2] == 0 and x[1][0] != 0, msgs)

            if unfinished:
                # Some of neighbors are still in stage 0.
                # Wait for an extra round by sending stage 0 message
                self.send_to_neighbors((MsgType.PAYLOAD, self.color, 0))
            else:
                # Now all of our neighbors are in stage 1.
                if self.reduced_color <= self.delta + 1:
                    # We're already in range.
                    self.log('Reduced color: ' + str(self.reduced_color))
                    self.save_result_once(self.reduced_color)
                    self.go_inactive()
                else:
                    # We need to recolor ourself (in the context of stage 1)
                    # The initial input would be finalized stage 0 colors.
                    # stage 0 messages would be: (PAYLOAD, color_tuple, stage_mark)
                    # stage 1 messages would be: (PAYLOAD, color_integer, stage_mark)
                    # if the stage mark is 0, we extract the second item of the color tuple
                    # if the stage mark is 1, we extract only the color_integer
                    finalized_colors = [msg[1][1] if msg[2] == 0 else msg[1] for msg in finalized]
                    remaining_colors = set([i for i in range(self.delta + 1)]) - set(finalized_colors)
                    self.reduced_color = min(remaining_colors)

                self.send_to_neighbors((MsgType.PAYLOAD, self.reduced_color, 1))

    # Upon receiving no msg
    def init_config(self):
        self.send_to_neighbors((MsgType.PAYLOAD, self.color))


if __name__ == '__main__':
    n = 10

    G = lib.gen_random_graph(n)

    delta = lib.calc_delta(G)
    print('Maximum degree: ' + str(delta))

    color_mapping = {pid: random.randrange(10 * (pid + 1), 10 * (pid + 2)) for pid in G.nodes()}
    mps = MessagePassingSystem(proc_class=Processor,
                               proc_args={
                                   pid: {'delta': delta,
                                         'q': lib.choose_prime(delta),
                                         'color': color_mapping[pid]
                                    } for pid in G.nodes()},
                               n_proc=n,
                               edges=G.edges(),
                               is_async=False,
                               max_channel_delay=0)
    mps.start()
    mps.wait_for_all()
    text = "Maximum degree: %s\nNumber of Colors: %s" % (delta,
                                                         len(set([x[0] for x in mps.global_shared_memory.values()])))
    node_text = {id: 'PID: %s, original color %s, final color: %s'
                     % (id, color_mapping[id], mps.global_shared_memory[id][0]) for id in G.nodes()}
    vis.plot(G, node_text=node_text, text=text)
