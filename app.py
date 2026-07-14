from flask import Flask, request, render_template_string
import heapq
import networkx as nx
import plotly.graph_objects as go

app = Flask(__name__)

# --- Dijkstra Implementation ---
def dijkstra(graph, source):
    n = len(graph)
    dist = [float('inf')] * n
    prev = [None] * n
    dist[source] = 0
    pq = [(0, source)]
    visited = set()

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
    return dist, prev

def reconstruct_path(prev, source, target):
    path = []
    node = target
    visited = set()
    while node is not None and node not in visited:
        visited.add(node)
        path.append(node)
        node = prev[node]
    path.reverse()
    if path and path[0] == source:
        return path
    return []

# --- Plotly Graph Visualization ---
def draw_graph_plotly(graph, paths):
    G = nx.Graph()
    for u in graph:
        for v, w in graph[u]:
            G.add_edge(u, v, weight=w)

    pos = nx.spring_layout(G, seed=42)

    # Edges
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='gray'),
        hoverinfo='none',
        mode='lines'
    )

    # Nodes
    node_x, node_y, labels = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        labels.append(str(node))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=labels,
        textposition="top center",
        marker=dict(size=20, color='lightblue'),
        hoverinfo='text'
    )

    # Highlight shortest paths
    path_edges_x, path_edges_y = [], []
    for path in paths:
        if len(path) > 1:
            for u, v in zip(path, path[1:]):
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                path_edges_x += [x0, x1, None]
                path_edges_y += [y0, y1, None]

    path_trace = go.Scatter(
        x=path_edges_x, y=path_edges_y,
        line=dict(width=3, color='red'),
        hoverinfo='none',
        mode='lines'
    )

    fig = go.Figure(data=[edge_trace, path_trace, node_trace])
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
    return fig.to_html(full_html=False)

# --- HTML Template ---
TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Dijkstra Shortest Path</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 8px 12px; border: 1px solid #ccc; }
        th { background: #f2f2f2; }
    </style>
</head>
<body>
    <h2>Dijkstra's Algorithm (Shortest Paths)</h2>
    <form method="post">
        <label>Number of vertices:</label>
        <input type="number" name="vertices" required><br><br>
        
        <label>Edges (format: u v w, one per line):</label><br>
        <textarea name="edges" rows="6" cols="40" required></textarea><br><br>
        
        <label>Source vertex:</label>
        <input type="number" name="source" required><br><br>
        
        <button type="submit">Run Dijkstra</button>
    </form>
    {% if result %}
        <h3>Results (from source {{src}}):</h3>
        <table>
            <tr><th>Vertex</th><th>Distance</th><th>Path</th></tr>
            {% for v, d, path in result %}
                <tr>
                    <td>{{v}}</td>
                    <td>{{d}}</td>
                    <td>{{path}}</td>
                </tr>
            {% endfor %}
        </table>
        <h3>Graph Visualization:</h3>
        {{ graph_html|safe }}
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST", "HEAD"])
def index():
    result = None
    src = None
    graph_html = None

    if request.method == "POST":
        try:
            n = int(request.form["vertices"])
            edges_input = request.form["edges"].strip().splitlines()
            src = int(request.form["source"])

            if src < 0 or src >= n:
                raise ValueError("Source vertex out of range")

            # Build graph (undirected)
            graph = {i: [] for i in range(n)}
            for line in edges_input:
                try:
                    u, v, w = map(int, line.split())
                    graph[u].append((v, w))
                    graph[v].append((u, w))
                except ValueError:
                    raise ValueError(f"Invalid edge format: {line}")

            dist, prev = dijkstra(graph, src)

            result = []
            paths = []
            for v in range(n):
                path = reconstruct_path(prev, src, v)
                paths.append(path)
                path_str = " -> ".join(map(str, path)) if path else "No path"
                d = dist[v] if dist[v] != float("inf") else "INF"
                result.append((v, d, path_str))

            # Generate interactive graph HTML
            graph_html = draw_graph_plotly(graph, paths)

        except Exception as e:
            result = [("Error", "Invalid input", str(e))]

    return render_template_string(TEMPLATE, result=result, src=src, graph_html=graph_html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
