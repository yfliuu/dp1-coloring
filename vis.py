import plotly
import plotly.graph_objs as go

import networkx as nx


def gen_random_graph(n=100, radius=0.125):
    return nx.random_geometric_graph(n, radius)


def edge_trace(G):
    xs, ys = [], []
    for edge in G.edges():
        x0, y0 = G.node[edge[0]]['pos']
        x1, y1 = G.node[edge[1]]['pos']
        xs += (x0, x1, None)
        ys += (y0, y1, None)
    return go.Scatter(x=xs, y=ys, line=dict(width=0.5,color='#888'), hoverinfo='none', mode='lines')


def node_trace(G, color_mapping):
    # color scale options
    # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
    # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
    # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |

    xs, ys = [], []
    colors = []
    hover_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        x, y = G.node[node]['pos']
        xs.append(x)
        ys.append(y)

        node_color = color_mapping[node]
        colors.append(node_color)
        hover_text.append('Color assigned: ' + str(node_color))

    return go.Scatter(x=xs, y=ys, text=hover_text, 
        mode='markers', hoverinfo='text',
        marker=dict(
            # showscale=True,
            # colorscale='YlGnBu',
            # reversescale=True,
            color=colors,
            size=10,
            # colorbar=dict(
            #     thickness=15,
            #     title='Node Connections',
            #     xanchor='left',
            #     titleside='right'
            # ),
            line=dict(width=2)))


def fig(G, color_mapping):
    delta = max([d for _, d in G.degree])
    layout = go.Layout(title='Graph coloring', titlefont=dict(size=16), showlegend=False,
                       hovermode='closest', margin=dict(b=20, l=5, r=5, t=40),
                       annotations=[dict(
                           text="Maximum degree: " + str(delta), showarrow=False,
                           xref="paper", yref="paper",
                           x=0.005, y=-0.002)],
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    return go.Figure(data=[edge_trace(G), node_trace(G, color_mapping)], layout=layout)


def plot(G, color_mapping):
    plotly.offline.plot(fig(G, color_mapping), filename='gcoloring.html')


if __name__ == '__main__':
    G = gen_random_graph()
    color_mapping = {i: i for i in range(len(G.nodes()))}
    plot(G, color_mapping)
