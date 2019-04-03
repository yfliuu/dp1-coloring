import math


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

    for i in range(2, min(n, int(math.sqrt(n)) + 1)):
        if i % n == 0:
            return True
    return False


# Trivially coloring all nodes with a different color.
def trivial_coloring(G):
    return {i: i for i in range(len(G.nodes()))}
