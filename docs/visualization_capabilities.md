# Visualization Capabilities
## Kubernetes Root Cause Analysis System

This document outlines the visualization capabilities of the Kubernetes Root Cause Analysis system, with a focus on flowcharts and decision trees that represent the investigation process.

## Overview

The visualization subsystem transforms complex investigation data into intuitive, interactive diagrams that help users understand:

1. The investigation flow and decision points
2. Evidence relationships and correlations
3. Confidence levels in different hypotheses
4. The reasoning process that led to conclusions
5. Timeline of investigation events

## Key Visualization Types

### 1. Investigation Flow Diagram

This diagram displays the entire investigation process as a directed graph, showing:

- Initial symptoms assessment
- Specialist agent activations
- Decision points and branches taken
- Evidence collection steps
- Hypothesis evaluation phases
- Final root cause determination

#### Implementation Details

```python
# utils/visualizations.py (excerpt)
import plotly.graph_objects as go
from pyvis.network import Network
import networkx as nx

def generate_investigation_graph(investigation_result, output_path):
    """Generate interactive investigation flow diagram"""
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes for each phase
    phases = ["Initial Assessment", "Evidence Collection", "Hypothesis Testing", 
              "Root Cause Determination", "Recommendation Generation"]
    
    for i, phase in enumerate(phases):
        G.add_node(phase, level=i)
    
    # Add specialist agent nodes
    specialists = investigation_result.get("specialist_activations", {})
    for agent_type, activations in specialists.items():
        for i, activation in enumerate(activations):
            node_id = f"{agent_type}_{i}"
            G.add_node(node_id, 
                      label=f"{agent_type.capitalize()} Agent",
                      title=activation.get("task_description", ""),
                      level=activation.get("investigation_phase_index", 1))
            
            # Connect to appropriate phase
            phase_index = activation.get("investigation_phase_index", 1)
            G.add_edge(phases[phase_index], node_id)
            
            # Connect back to next phase if it returned to master
            if activation.get("returned_to_master", True):
                G.add_edge(node_id, phases[phase_index + 1])
    
    # Add decision nodes
    decisions = investigation_result.get("decision_points", [])
    for i, decision in enumerate(decisions):
        node_id = f"decision_{i}"
        G.add_node(node_id,
                  label=f"Decision: {decision.get('question', 'Unknown')}",
                  shape="diamond",
                  level=decision.get("investigation_phase_index", 2))
        
        # Connect to appropriate phase
        phase_index = decision.get("investigation_phase_index", 2)
        G.add_edge(phases[phase_index], node_id)
        
        # Connect to result node
        result_node = f"result_{i}"
        G.add_node(result_node,
                  label=f"Result: {decision.get('outcome', 'Unknown')}",
                  shape="box",
                  level=phase_index)
        G.add_edge(node_id, result_node)
        G.add_edge(result_node, phases[phase_index + 1])
    
    # Convert to PyVis network
    net = Network(height="900px", width="100%", directed=True)
    net.from_nx(G)
    
    # Set node colors based on type
    for node in net.nodes:
        if node["label"].startswith("Decision"):
            node["color"] = "#FFA500"  # Orange for decisions
        elif any(node["label"].startswith(agent) for agent in ["Cluster", "Network", "Workload", "Config"]):
            node["color"] = "#00BFFF"  # Blue for specialist agents
        elif node["label"] in phases:
            node["color"] = "#32CD32"  # Green for investigation phases
        else:
            node["color"] = "#DDDDDD"  # Gray for other nodes
    
    # Set physics options for better layout
    net.set_options("""
    {
      "physics": {
        "hierarchicalRepulsion": {
          "centralGravity": 0.0,
          "springLength": 100,
          "springConstant": 0.01,
          "nodeDistance": 120
        },
        "solver": "hierarchicalRepulsion",
        "stabilization": {
          "iterations": 100
        }
      },
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "LR",
          "sortMethod": "directed",
          "levelSeparation": 150
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 300
      }
    }
    """)
    
    # Save the network visualization
    net.save_graph(output_path)
```

### 2. Decision Tree Visualization

This diagram represents the logical decision tree used to determine the investigation path:

- Conditional nodes with evaluation criteria
- Branch paths based on evidence thresholds
- Confidence scores at each decision point
- Final outcome leaves showing reasoning

#### Implementation Details

```python
# utils/visualizations.py (excerpt)
def visualize_decision_tree(decision_tree, investigation_result, output_path):
    """Generate visualization of the decision tree used in the investigation"""
    # Create a DiGraph for the decision tree
    G = nx.DiGraph()
    
    # Helper function to recursively build the tree graph
    def build_tree_graph(node, node_id="root"):
        if isinstance(node, str) or node is None:
            # Leaf node (specialist agent or END)
            G.add_node(node_id, label=str(node), shape="box")
            return
        
        # Decision node
        if hasattr(node, "condition_fn"):
            # Extract condition function name
            condition_name = node.condition_fn.__name__
            G.add_node(node_id, label=condition_name, shape="diamond")
            
            # Add true branch
            true_id = f"{node_id}_true"
            G.add_edge(node_id, true_id, label="True")
            build_tree_graph(node.true_branch, true_id)
            
            # Add false branch
            false_id = f"{node_id}_false"
            G.add_edge(node_id, false_id, label="False")
            build_tree_graph(node.false_branch, false_id)
    
    # Build the graph
    build_tree_graph(decision_tree.root_node)
    
    # Create interactive visualization with plotly
    fig = go.Figure()
    
    # Helper for node positions
    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    
    # Add edges
    edge_x = []
    edge_y = []
    edge_text = []
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_text.append(edge[2].get("label", ""))
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines")
    
    fig.add_trace(edge_trace)
    
    # Add nodes
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_shape = []
    
    for node in G.nodes(data=True):
        x, y = pos[node[0]]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node[1].get("label", node[0]))
        
        # Color and shape based on node type
        if node[1].get("shape") == "diamond":
            node_color.append("#FFA500")  # Orange for decisions
            node_shape.append("diamond")
            node_size.append(15)
        else:
            node_color.append("#00BFFF")  # Blue for specialist agents/results
            node_shape.append("circle")
            node_size.append(10)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_text,
        hoverinfo="text",
        marker=dict(
            color=node_color,
            size=node_size,
            line_width=2))
    
    fig.add_trace(node_trace)
    
    fig.update_layout(
        title="Investigation Decision Tree",
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=900,
        height=600,
        plot_bgcolor="white"
    )
    
    # Write to HTML file
    fig.write_html(output_path)
```

### 3. Evidence Relationship Graph

This visualization shows the connections between different pieces of evidence:

- Evidence nodes colored by resource type
- Connection strength based on correlation
- Highlighted critical evidence that led to conclusions
- Interactive filtering by confidence level

#### Implementation Example

```python
# utils/visualizations.py (excerpt)
def generate_evidence_graph(evidence_items, output_path):
    """Generate graph showing relationships between evidence items"""
    G = nx.Graph()
    
    # Add evidence nodes
    for i, evidence in enumerate(evidence_items):
        G.add_node(i, 
                  label=evidence.get("resource_type", "Unknown"),
                  title=evidence.get("analysis", ""),
                  value=evidence.get("confidence", 0.5) * 10)  # Node size by confidence
    
    # Add edges between related evidence
    for i, evidence1 in enumerate(evidence_items):
        for j, evidence2 in enumerate(evidence_items):
            if i >= j:
                continue
                
            # Connect if they share related resources
            related1 = set(evidence1.get("related_resources", []))
            related2 = set(evidence2.get("related_resources", []))
            
            common = related1.intersection(related2)
            if common:
                weight = len(common) / max(len(related1), len(related2))
                G.add_edge(i, j, weight=weight, title=f"Relationship strength: {weight:.2f}")
    
    # Convert to interactive visualization
    net = Network(height="800px", width="100%", notebook=False)
    net.from_nx(G)
    
    # Color nodes by resource type
    color_map = {
        "Pod": "#FF6347",           # Tomato
        "Service": "#4682B4",        # Steel Blue
        "Deployment": "#2E8B57",     # Sea Green
        "Node": "#9370DB",           # Medium Purple
        "ConfigMap": "#DAA520",      # Goldenrod
        "Secret": "#CD5C5C",         # Indian Red
        "Ingress": "#20B2AA",        # Light Sea Green
        "NetworkPolicy": "#4169E1",  # Royal Blue
        "PersistentVolume": "#8A2BE2", # Blue Violet
        "Event": "#FF8C00",          # Dark Orange
        "Log": "#696969"             # Dim Gray
    }
    
    for node in net.nodes:
        resource_type = node.get("label", "Unknown")
        node["color"] = color_map.get(resource_type, "#CCCCCC")
    
    # Set interactive options
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "iterations": 100
        }
      },
      "edges": {
        "smooth": {
          "type": "continuous",
          "forceDirection": "none"
        },
        "color": {
          "inherit": "both"
        },
        "width": 0.5
      }
    }
    """)
    
    # Save the visualization
    net.save_graph(output_path)
```

### 4. Confidence Heatmap

This visualization displays the confidence in different hypotheses over time:

- Time series of confidence scores
- Color gradient indicating confidence level
- Major events in the investigation timeline
- Final confidence scores for different root causes

#### Implementation Details

```python
# utils/visualizations.py (excerpt)
import plotly.express as px
import pandas as pd

def generate_confidence_heatmap(confidence_history, output_path):
    """Generate heatmap of confidence scores over time"""
    # Convert confidence history to DataFrame
    data = []
    
    for timestamp, scores in confidence_history.items():
        for category, score in scores.items():
            data.append({
                "Timestamp": timestamp,
                "Category": category.capitalize(),
                "Confidence": score
            })
    
    df = pd.DataFrame(data)
    
    # Create heatmap
    fig = px.density_heatmap(
        df,
        x="Timestamp",
        y="Category",
        z="Confidence",
        color_continuous_scale="Viridis",
        title="Root Cause Confidence Evolution"
    )
    
    fig.update_layout(
        xaxis_title="Investigation Timeline",
        yaxis_title="Potential Root Cause Category",
        coloraxis_colorbar_title="Confidence Score",
        height=600,
        width=900
    )
    
    # Save as HTML file
    fig.write_html(output_path)
```

### 5. Investigation Timeline

This visualization shows the progression of the investigation:

- Chronological events on a timeline
- Key decision points and evidence collection
- Agent activations and major findings
- Duration of each investigation phase

## Interactive Dashboard Integration

These visualizations are integrated into a comprehensive dashboard that provides:

1. Overview of the investigation status
2. Drill-down capabilities for detailed exploration
3. Filtering options to focus on specific aspects
4. Export capabilities for reports and presentations
5. Real-time updates during ongoing investigations

### Dashboard Implementation

```python
# utils/dashboard.py (excerpt)
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

def create_dashboard(investigation_results):
    """Create interactive dashboard for investigation results"""
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Generate all visualization files
    evidence_path = "static/evidence_graph.html"
    generate_evidence_graph(investigation_results.get("evidence", []), evidence_path)
    
    flow_path = "static/investigation_flow.html" 
    generate_investigation_graph(investigation_results, flow_path)
    
    tree_path = "static/decision_tree.html"
    decision_tree = build_investigation_decision_tree()
    visualize_decision_tree(decision_tree, investigation_results, tree_path)
    
    heatmap_path = "static/confidence_heatmap.html"
    generate_confidence_heatmap(investigation_results.get("confidence_history", {}), heatmap_path)
    
    # Create the dashboard layout
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Kubernetes Root Cause Analysis Dashboard"), width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Investigation Summary"),
                    dbc.CardBody([
                        html.H5("Initial Symptoms"),
                        html.P(investigation_results.get("initial_symptoms", "")),
                        html.H5("Primary Root Cause"),
                        html.P(investigation_results.get("primary_root_cause", "Unknown")),
                        html.H5("Confidence"),
                        html.P(f"{investigation_results.get('primary_confidence', 0)*100:.1f}%"),
                        html.H5("Investigation Duration"),
                        html.P(f"{investigation_results.get('duration_seconds', 0)/60:.1f} minutes")
                    ])
                ])
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recommended Actions"),
                    dbc.CardBody([
                        html.Ol([
                            html.Li(action) for action in investigation_results.get("next_actions", [])
                        ])
                    ])
                ])
            ], width=8)
        ], className="mb-4"),
        
        dbc.Tabs([
            dbc.Tab([
                html.Iframe(
                    src=flow_path,
                    style={"width": "100%", "height": "800px", "border": "none"}
                )
            ], label="Investigation Flow"),
            
            dbc.Tab([
                html.Iframe(
                    src=tree_path,
                    style={"width": "100%", "height": "800px", "border": "none"}
                )
            ], label="Decision Tree"),
            
            dbc.Tab([
                html.Iframe(
                    src=evidence_path,
                    style={"width": "100%", "height": "800px", "border": "none"}
                )
            ], label="Evidence Relationships"),
            
            dbc.Tab([
                html.Iframe(
                    src=heatmap_path,
                    style={"width": "100%", "height": "800px", "border": "none"}
                )
            ], label="Confidence Evolution")
        ])
    ], fluid=True)
    
    return app
```

## Human-in-the-Loop Interaction

The visualization system supports human interaction through:

1. Decision point overrides
2. Evidence priority adjustments
3. Manual hypothesis injection
4. Investigation path steering
5. Additional context provision

## Visualization Deployment

The visualization capabilities can be deployed as:

1. Standalone HTML reports
2. Integrated dashboard in the Kubernetes operator UI
3. Embedded visualizations in incident management systems
4. Exportable SVG/PNG for documentation
5. Live updating views during ongoing investigations

## Technical Requirements

- Python visualization libraries: Plotly, NetworkX, PyVis, Dash
- Modern web browser with JavaScript support
- Persistent storage for investigation history
- WebSocket support for real-time updates
- Appropriate RBAC for dashboard access 