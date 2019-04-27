import plotly
import plotly.graph_objs as go
import lib
import random


def edge_trace(G):
    xs, ys = [], []
    for edge in G.edges():
        x0, y0 = G.node[edge[0]]['pos']
        x1, y1 = G.node[edge[1]]['pos']
        xs += (x0, x1, None)
        ys += (y0, y1, None)
    return go.Scatter(x=xs, y=ys, line=dict(width=0.5,color='#888'), hoverinfo='none', mode='lines')


def node_trace(G, color_mapping, i2c_mapping, node_text):
    # color scale options
    # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
    # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
    # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |

    xs, ys = [], []
    colors = []
    hover_text = []
    if i2c_mapping is None:
        integer2color = {i: 'rgb(%s,%s,%s)' % values
                         for i, values in enumerate([(
                            random.randint(0, 255),
                            random.randint(0, 255),
                            random.randint(0, 255)) for _ in range(len(color_mapping) * 2)])}
    else:
        integer2color = i2c_mapping
    for node, adjacencies in enumerate(G.adjacency()):
        x, y = G.node[node]['pos']
        xs.append(x)
        ys.append(y)

        node_color = color_mapping[node]
        colors.append(integer2color[node_color])
        hover_text.append(node_text[node])

    return go.Scatter(x=xs, y=ys, text=hover_text,
        mode='markers', hoverinfo='text',
        marker=dict(
            # showscale=True,
            # colorscale='YlGnBu',
            # reversescale=True,
            color=colors,
            size=20,
            # colorbar=dict(
            #     thickness=15,
            #     title='Node Connections',
            #     xanchor='left',
            #     titleside='right'
            # ),
            line=dict(width=2)))


def fig(G, color_mapping, i2c_mapping=None, **kwargs):
    layout = go.Layout(title='Locally-iterative Graph Coloring', titlefont=dict(size=16), showlegend=False,
                       hovermode='closest', margin=dict(b=20, l=5, r=5, t=40),
                       annotations=[dict(
                           text=kwargs.pop('text', ''), showarrow=False,
                           xref="paper", yref="paper",
                           x=0.005, y=-0.002)],
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    return go.Figure(data=[edge_trace(G), node_trace(G, color_mapping, i2c_mapping, **kwargs)], layout=layout)


def plot(G, color_mapping=None, filename='gcoloring.html', i2c_mapping=None, auto_open=True, **kwargs):
    if color_mapping is None:
        color_mapping = lib.trivial_coloring(G)
    plotly.offline.plot(fig(G, color_mapping, i2c_mapping, **kwargs), filename=filename, auto_open=auto_open)


if __name__ == '__main__':
    G = lib.gen_random_graph()
    color_mapping = {i: i for i in range(len(G.nodes()))}
    plot(G, color_mapping)
