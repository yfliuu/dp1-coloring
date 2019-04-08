import math
import networkx as nx


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


# Trivially coloring all nodes with a different color.
def trivial_coloring(G):
    return {i: i for i in range(len(G.nodes()))}


def calc_delta(G):
    return max([d for _, d in G.degree])


def gen_random_graph(n=100, radius=0.125):
    return nx.random_geometric_graph(n, radius)


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