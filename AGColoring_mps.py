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
        self.round = -1
        self.first_stage_finalized = False
        self.color_history = [self.color]
        self.j = None
        self.color_palette = set(range(self.delta + 1))

    # Upon receiving PAYLOAD msg
    # If we run in sync environment, worker will receive messages
    # received in previous round
    def worker(self, msgs, srcs):
        self.round += 1
        if self.round < self.q:
            if any(map(lambda x: x[1][1] == self.color[1], msgs)):
                if not self.first_stage_finalized:
                    self.color = (self.color[0], (self.color[0] + self.color[1]) % self.q)
                    self.log('Round %d: Conflict! New Color: %s' % (self.round, str(self.color)))
            else:
                self.color = (0, self.color[1])
                if not self.first_stage_finalized:
                    self.log('My Color: %s, finalized at round %d' % (str(self.color), self.round))
                    self.first_stage_finalized = True
            self.color_history.append(self.color)
            self.send_to_neighbors((self.round + 1, self.color, 0))
        else:
            assert self.first_stage_finalized
            if self.j is None:
                self.j = self.q
                self.send_to_neighbors((self.j, self.color, 1))
            else:
                if self.j > self.delta:
                    if self.color[1] == self.j:
                        used_colors = set([msg[1][1] for msg in msgs])
                        color_picked = min(self.color_palette - used_colors)
                        self.color = (0, color_picked)
                        self.log('Round %d: Final Color: %d' % (self.j, color_picked))
                    self.color_history.append(self.color)
                    self.j -= 1
                    self.send_to_neighbors((self.j, self.color, 1))
                else:
                    self.save_result_once('color_history', self.color_history)
                    self.save_result_once('color', self.color)
                    self.go_inactive()

    # Upon receiving no msg
    def init_config(self):
        self.send_to_neighbors((0, self.color, 0))


if __name__ == '__main__':
    n = 10

    G = lib.gen_random_graph(n)
    # G = lib.gen_ring(n)

    delta = lib.calc_delta(G)
    color_mapping = {pid: pid for pid in G.nodes()}
    print('Maximum degree: ' + str(delta))

    q = lib.choose_prime(math.sqrt(n))
    if q <= 2 * delta:
        q = lib.choose_prime(2 * delta)

    mps = MessagePassingSystem(proc_class=Processor,
                               proc_args={
                                   pid: {'delta': delta,
                                         'q': q,
                                         'color': color_mapping[pid]
                                    } for pid in G.nodes()},
                               n_proc=n,
                               edges=G.edges(),
                               is_async=False,
                               max_channel_delay=0)
    mps.start()
    mps.wait_for_all()
    final_color_mapping = {i: x['color'][1] for i, x in mps.global_shared_memory.items()}
    text = "q=%d\n delta=%s\n #colors=%s\n AG rounds: %d\n FR rounds: %d" % \
           (q, delta, len(set(final_color_mapping.values())),
            max([lib.count_rounds(obj['color_history']) for obj in mps.global_shared_memory.values()], default=0),
            q - delta - 1)
    node_text = {pid: 'PID: %s, original color %s, final color: %s'
                     % (pid, color_mapping[pid], mps.global_shared_memory[pid]['color'][1]) for pid in G.nodes()}
    vis.plot(G, color_mapping=final_color_mapping, node_text=node_text, text=text)
