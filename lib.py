import math
import networkx as nx
import random


def choose_prime(delta):
    # Choose the first prime number between [delta, 2*delta]
    for n in range(delta, 2 * delta + 1):
        if is_prime(n):
            return n


def is_prime(n):
    if n == 2:
        return True
    elif n == 1:
        return False

    for i in range(2, min(n, math.ceil(math.sqrt(n)) + 1)):
        if n % i == 0:
            return False
    return True


def list_group_by(pred, lst):
    yes, no = [], []
    for item in lst:
        if pred(item): yes.append(item)
        else: no.append(item)
    return yes, no


# Trivially coloring all nodes with a different color.
def trivial_coloring(G):
    return {i: i for i in range(len(G.nodes()))}


def calc_delta(G):
    return max([d for _, d in G.degree])


def dist2(G, edge):
    pos1 = G.nodes[edge[0]]['pos']
    pos2 = G.nodes[edge[1]]['pos']
    return (pos1[0] - pos2[0]) * (pos1[0] - pos2[0]) + (pos1[1] - pos2[1]) * (pos1[1] - pos2[1])


def dist(p1, p2):
    return (wp1[0] - wp2[0]) * (wp1[0] - wp2[0]) + (wp1[1] - wp2[1]) * (wp1[1] - wp2[1])


def gen_random_graph(n=100):
    g = nx.random_geometric_graph(n, 10)
    attrs = {edge: {'weight': dist2(g, edge)} for edge in g.edges()}
    G = nx.minimum_spanning_tree(g)
    nx.set_edge_attributes(G, attrs)
    for _ in range(random.randint(n, n * 2)):
        v1 = random.randrange(0, n)
        v2 = random.randrange(0, n)
        if v1 != v2:
            if not G.has_edge(v1, v2):
                G.add_edge(v1, v2)
    return G


def gen_ring(n=100):
    G = nx.random_geometric_graph(n, 0)
    for i in range(n):
        G.add_edge(i, (i + 1) % n, weight=1)
    return G

def draw_graph(G):
    nx.draw(G, pos=nx.spring_layout(G))


# def ksquare_coloring(G):
#     delta = calc_delta(G)
#     colors = {i: False for i in range(delta * delta)}
#     current_color = 0
#     color_mapping = {i: None for i in range(len(G.nodes()))}

#     for nid, deg in sorted(G.degree.items(), key=lambda x: x: [1]):
#         for neighbor_of_nid in G.neighbors(nid):
#             color_mapping[neighbor_of_nid] = current_color
#             colors[current_color] = True
#             current_color += 1
#

