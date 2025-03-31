"""
Visualization utilities for Kubernetes Root Cause Analysis
"""
import json
import logging
import os
import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a specialized logger for agent visualizations
agent_viz_logger = logging.getLogger("agent_visualizations")
agent_viz_logger.setLevel(logging.INFO)
agent_viz_logger.propagate = False  # Don't propagate to root logger

def generate_investigation_graph(result: Dict[str, Any], output_path: str) -> bool:
    """
    Generate an HTML visualization of the investigation flow
    
    Args:
        result: Investigation results
        output_path: Path to save the generated HTML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    agent_viz_logger.info(f"Generating investigation graph at {output_path}")
    
    try:
        # Extract key information
        phase = result.get("investigation_phase", "unknown")
        findings = result.get("findings", {})
        confidence_scores = result.get("confidence_scores", {})
        root_causes = result.get("root_causes", [])
        next_actions = result.get("next_actions", [])
        agents_activated = list(findings.keys()) if findings else []
        
        # Get the highest confidence score
        primary_cause = ""
        highest_confidence = 0
        for area, score in confidence_scores.items():
            if score > highest_confidence:
                highest_confidence = score
                primary_cause = area
                
        # Format confidence as percentage
        confidence_percentage = f"{int(highest_confidence * 100)}%"
        
        # Generate HTML for root causes
        root_causes_html = ""
        for cause in root_causes:
            category = cause.get("category", "unknown")
            description = cause.get("description", "No description")
            confidence = cause.get("confidence", 0)
            root_causes_html += f"""
            <div class="cause-item">
                <div class="cause-header">{category} ({int(confidence * 100)}%)</div>
                <div class="cause-desc">{description}</div>
            </div>
            """
        
        # Generate HTML for next actions
        actions_html = ""
        for i, action in enumerate(next_actions, 1):
            actions_html += f"""
            <div class="action-item">
                <span class="action-num">{i}.</span> {action}
            </div>
            """
            
        # Graph data - use only agent interactions for visualization
        nodes = []
        links = []
        
        # Add master node
        nodes.append({"id": "master", "label": "Master Agent", "type": "master"})
        
        # Add specialist nodes with agent interaction data only
        # This ensures we only show actual agent interactions
        for agent_type in agents_activated:
            nodes.append({"id": agent_type, "label": f"{agent_type.capitalize()} Agent", "type": agent_type})
            
            # Create bidirectional links to represent agent interactions
            links.append({"source": "master", "target": agent_type, "type": "activation"})
            
            # Check if there's evidence of data return from specialist to master
            confidence = confidence_scores.get(agent_type, 0)
            links.append({
                "source": agent_type, 
                "target": "master", 
                "type": "data_return",
                "confidence": confidence  # Store confidence score with the link
            })
        
        # Create HTML template
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Kubernetes Agent Interactions</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <script src="https://unpkg.com/dagre-d3@0.6.4/dist/dagre-d3.min.js"></script>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }
                .metrics {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 20px;
                }
                .metric-box {
                    flex: 1;
                    margin: 0 10px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    text-align: center;
                }
                .metric-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #3498db;
                    margin: 10px 0;
                }
                .metric-label {
                    font-size: 14px;
                    color: #7f8c8d;
                }
                .graph-container {
                    width: 100%;
                    height: 400px;
                    border: 1px solid #ddd;
                    margin-bottom: 20px;
                    overflow: hidden;
                }
                .node rect {
                    stroke: #333;
                    stroke-width: 1.5px;
                    fill: #fff;
                }
                .edgePath path {
                    stroke: #333;
                    stroke-width: 1.5px;
                    fill: none;
                }
                .master rect {
                    fill: #3498db;
                }
                .network rect {
                    fill: #2ecc71;
                }
                .metrics rect {
                    fill: #e74c3c;
                }
                .cluster rect {
                    fill: #f39c12;
                }
                .node text {
                    font-weight: bold;
                    fill: white;
                }
                .findings-container {
                    display: flex;
                    margin-bottom: 20px;
                }
                .findings-column {
                    flex: 1;
                    padding: 0 10px;
                }
                .findings-header {
                    font-weight: bold;
                    margin-bottom: 10px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }
                .cause-item, .action-item {
                    margin-bottom: 10px;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }
                .cause-header {
                    font-weight: bold;
                    margin-bottom: 5px;
                    color: #e74c3c;
                }
                .action-num {
                    font-weight: bold;
                    color: #3498db;
                }
                .legend {
                    display: flex;
                    justify-content: center;
                    margin-bottom: 20px;
                }
                .legend-item {
                    display: flex;
                    align-items: center;
                    margin: 0 10px;
                }
                .legend-color {
                    width: 15px;
                    height: 15px;
                    margin-right: 5px;
                }
                .agent-interactions-title {
                    margin-top: 30px;
                    font-size: 18px;
                    color: #2c3e50;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Kubernetes Agent Interactions</h1>
                
                <div class="metrics">
                    <div class="metric-box">
                        <div class="metric-label">Investigation Phase</div>
                        <div class="metric-value">{{INVESTIGATION_PHASE}}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Primary Root Cause</div>
                        <div class="metric-value">{{PRIMARY_CAUSE}}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Confidence</div>
                        <div class="metric-value">{{CONFIDENCE}}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Specialist Agents</div>
                        <div class="metric-value">{{AGENT_COUNT}}</div>
                    </div>
                </div>
                
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #3498db;"></div>
                        <div>Master Agent</div>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #2ecc71;"></div>
                        <div>Network Agent</div>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #e74c3c;"></div>
                        <div>Metrics Agent</div>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #f39c12;"></div>
                        <div>Cluster Agent</div>
                    </div>
                </div>
                
                <div class="agent-interactions-title">Agent Interaction Flow</div>
                <div class="graph-container" id="graph"></div>
                
                <div class="findings-container">
                    <div class="findings-column">
                        <div class="findings-header">Root Causes</div>
                        {{ROOT_CAUSES}}
                    </div>
                    <div class="findings-column">
                        <div class="findings-header">Recommended Actions</div>
                        {{NEXT_ACTIONS}}
                    </div>
                </div>
            </div>
            
            <script>
                // Graph data
                const nodes = {{NODES}};
                const links = {{LINKS}};
                
                // Create the graph
                const g = new dagreD3.graphlib.Graph().setGraph({})
                    .setDefaultEdgeLabel(function() { return {}; });
                
                // Add nodes to the graph
                nodes.forEach(function(node) {
                    g.setNode(node.id, {
                        label: node.label,
                        class: node.type,
                        rx: 5,
                        ry: 5,
                        width: 120,
                        height: 40
                    });
                });
                
                // Add edges to the graph
                links.forEach(function(link) {
                    // Set edge style based on link type
                    let style = {};
                    if (link.type === "activation") {
                        style = {
                            curve: d3.curveBasis,
                            style: "stroke-dasharray: 5, 5;",
                            label: "activates"
                        };
                    } else if (link.type === "data_return") {
                        style = {
                            curve: d3.curveBasis,
                            style: "stroke-width: " + (link.confidence * 5 + 1) + "px;",
                            label: Math.round(link.confidence * 100) + "%"
                        };
                    } else {
                        style = {
                            curve: d3.curveBasis
                        };
                    }
                    
                    g.setEdge(link.source, link.target, style);
                });
                
                // Create the renderer
                const render = new dagreD3.render();
                
                // Set up the SVG
                const svg = d3.select("#graph")
                    .append("svg")
                    .attr("width", "100%")
                    .attr("height", "100%");
                
                const svgGroup = svg.append("g");
                
                // Run the renderer
                render(svgGroup, g);
                
                // Center the graph
                const xCenterOffset = (document.getElementById("graph").clientWidth - g.graph().width) / 2;
                svgGroup.attr("transform", "translate(" + xCenterOffset + ", 20)");
                
                // Scale the graph to fit
                const graphWidth = g.graph().width + 40;
                const graphHeight = g.graph().height + 40;
                const containerWidth = document.getElementById("graph").clientWidth;
                const containerHeight = document.getElementById("graph").clientHeight;
                const scale = Math.min(containerWidth / graphWidth, containerHeight / graphHeight, 1);
                
                svgGroup.attr("transform", "translate(" + xCenterOffset + ", 20) scale(" + scale + ")");
            </script>
        </body>
        </html>
        """
        
        # Replace placeholders
        html_content = html_template.replace("{{INVESTIGATION_PHASE}}", phase.replace("_", " ").title())
        html_content = html_content.replace("{{PRIMARY_CAUSE}}", primary_cause.replace("_", " ").title())
        html_content = html_content.replace("{{CONFIDENCE}}", confidence_percentage)
        html_content = html_content.replace("{{AGENT_COUNT}}", str(len(agents_activated)))
        html_content = html_content.replace("{{ROOT_CAUSES}}", root_causes_html)
        html_content = html_content.replace("{{NEXT_ACTIONS}}", actions_html)
        html_content = html_content.replace("{{NODES}}", json.dumps(nodes))
        html_content = html_content.replace("{{LINKS}}", json.dumps(links))
        
        # Write the HTML file
        with open(output_path, "w") as f:
            f.write(html_content)
            
        agent_viz_logger.info(f"Agent interaction graph saved to {output_path}")
        return True
    
    except Exception as e:
        agent_viz_logger.error(f"Error generating agent interaction graph: {e}")
        return False

def generate_confidence_heatmap(result: Dict[str, Any], output_path: str) -> bool:
    """
    Generate a confidence heatmap visualization showing how confidence evolved
    
    Args:
        result: Investigation results
        output_path: Path to save the generated HTML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    agent_viz_logger.info(f"Generating confidence heatmap at {output_path}")
    
    try:
        # Extract confidence data
        confidence_history = result.get("confidence_history", {})
        current_confidence = result.get("confidence_scores", {})
        
        # If no history available, create a single point with current confidence
        if not confidence_history:
            confidence_history = {"final": current_confidence}
        
        # Get all unique areas
        areas = set()
        for point in confidence_history.values():
            areas.update(point.keys())
        areas = sorted(areas)
        
        # Get all time points and sort them
        timepoints = sorted(confidence_history.keys())
        
        # Create dataset for heatmap
        # Format: [{"timepoint": "t1", "area1": 0.5, "area2": 0.3, ...}, ...]
        dataset = []
        for timepoint in timepoints:
            data_point = {"timepoint": timepoint}
            confidence_at_point = confidence_history[timepoint]
            
            for area in areas:
                data_point[area] = confidence_at_point.get(area, 0)
                
            dataset.append(data_point)
        
        # Create HTML for the heatmap visualization
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Kubernetes Agent Confidence Heatmap</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                h1, h2 {
                    color: #2c3e50;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }
                .heatmap-container {
                    margin-top: 20px;
                    overflow-x: auto;
                }
                .axis text {
                    font-size: 12px;
                }
                .axis path,
                .axis line {
                    fill: none;
                    stroke: #000;
                    shape-rendering: crispEdges;
                }
                .cell-text {
                    font-weight: bold;
                    text-anchor: middle;
                    dominant-baseline: central;
                }
                .tooltip {
                    position: absolute;
                    background-color: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 12px;
                    pointer-events: none;
                }
                .legend {
                    margin-top: 20px;
                    text-align: center;
                }
                .legend-item {
                    display: inline-block;
                    margin: 0 10px;
                }
                .legend-color {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    margin-right: 5px;
                    vertical-align: middle;
                }
                .timeline {
                    margin-top: 20px;
                    text-align: center;
                }
                .timeline-point {
                    display: inline-block;
                    margin: 0 10px;
                    text-align: center;
                }
                .timeline-marker {
                    display: inline-block;
                    width: 15px;
                    height: 15px;
                    background-color: #3498db;
                    border-radius: 50%;
                    margin-bottom: 5px;
                }
                .line-chart {
                    margin-top: 40px;
                    height: 200px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Agent Confidence Evolution</h1>
                <p>This visualization shows how the confidence levels of different agent assessments evolved during the investigation.</p>
                
                <div class="heatmap-container" id="heatmap"></div>
                
                <div id="lineChart" class="line-chart"></div>
                
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #f7fbff;"></div>
                        <span>0%</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #9ecae1;"></div>
                        <span>50%</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #08306b;"></div>
                        <span>100%</span>
                    </div>
                </div>
            </div>
            
            <script>
                // Data for the heatmap
                const dataset = {{DATASET}};
                const areas = {{AREAS}};
                const timepoints = {{TIMEPOINTS}};
                
                // Set up dimensions
                const margin = {top: 50, right: 50, bottom: 100, left: 100};
                const width = Math.max(600, areas.length * 80) - margin.left - margin.right;
                const height = Math.max(400, timepoints.length * 60) - margin.top - margin.bottom;
                
                // Create SVG for the heatmap
                const svg = d3.select("#heatmap")
                    .append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                    .attr("transform", `translate(${margin.left},${margin.top})`);
                
                // Create color scale
                const colorScale = d3.scaleSequential()
                    .interpolator(d3.interpolateBlues)
                    .domain([0, 1]);
                
                // Create x-scale for areas
                const x = d3.scaleBand()
                    .domain(areas)
                    .range([0, width])
                    .padding(0.05);
                
                // Create y-scale for timepoints
                const y = d3.scaleBand()
                    .domain(timepoints)
                    .range([0, height])
                    .padding(0.05);
                
                // Create x-axis
                svg.append("g")
                    .attr("class", "axis")
                    .attr("transform", `translate(0,${height})`)
                    .call(d3.axisBottom(x))
                    .selectAll("text")
                    .style("text-anchor", "end")
                    .attr("dx", "-.8em")
                    .attr("dy", ".15em")
                    .attr("transform", "rotate(-45)");
                
                // Create y-axis
                svg.append("g")
                    .attr("class", "axis")
                    .call(d3.axisLeft(y));
                
                // Create tooltip
                const tooltip = d3.select("body")
                    .append("div")
                    .attr("class", "tooltip")
                    .style("opacity", 0);
                
                // Create the heatmap cells
                dataset.forEach(d => {
                    const timepoint = d.timepoint;
                    
                    areas.forEach(area => {
                        const value = d[area] || 0;
                        
                        svg.append("rect")
                            .attr("x", x(area))
                            .attr("y", y(timepoint))
                            .attr("width", x.bandwidth())
                            .attr("height", y.bandwidth())
                            .style("fill", colorScale(value))
                            .on("mouseover", function(event) {
                                tooltip.transition()
                                    .duration(200)
                                    .style("opacity", .9);
                                tooltip.html(`${area}: ${Math.round(value * 100)}%<br>Time: ${timepoint}`)
                                    .style("left", (event.pageX + 10) + "px")
                                    .style("top", (event.pageY - 28) + "px");
                            })
                            .on("mouseout", function() {
                                tooltip.transition()
                                    .duration(500)
                                    .style("opacity", 0);
                            });
                        
                        // Add text for cells with significant values
                        if (value >= 0.25) {
                            svg.append("text")
                                .attr("class", "cell-text")
                                .attr("x", x(area) + x.bandwidth() / 2)
                                .attr("y", y(timepoint) + y.bandwidth() / 2)
                                .text(`${Math.round(value * 100)}%`)
                                .style("fill", value > 0.6 ? "white" : "black");
                        }
                    });
                });
                
                // Add title to the graph
                svg.append("text")
                    .attr("x", width / 2)
                    .attr("y", -margin.top / 2)
                    .attr("text-anchor", "middle")
                    .style("font-size", "16px")
                    .text("Agent Confidence Heatmap");
                
                // Line chart showing confidence evolution over time
                const lineChart = d3.select("#lineChart")
                    .append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", 250)
                    .append("g")
                    .attr("transform", `translate(${margin.left},${20})`);
                
                // Format data for line chart
                const lineData = areas.map(area => {
                    return {
                        area: area,
                        values: dataset.map(d => ({
                            timepoint: d.timepoint,
                            value: d[area] || 0
                        }))
                    };
                });
                
                // X and Y scales for the line chart
                const xLine = d3.scalePoint()
                    .domain(timepoints)
                    .range([0, width]);
                
                const yLine = d3.scaleLinear()
                    .domain([0, 1])
                    .range([200, 0]);
                
                // Color scale for lines
                const lineColorScale = d3.scaleOrdinal(d3.schemeCategory10);
                
                // Add X axis
                lineChart.append("g")
                    .attr("transform", `translate(0,${200})`)
                    .call(d3.axisBottom(xLine));
                
                // Add Y axis
                lineChart.append("g")
                    .call(d3.axisLeft(yLine).ticks(5).tickFormat(d => d * 100 + "%"));
                
                // Add lines
                const line = d3.line()
                    .x(d => xLine(d.timepoint))
                    .y(d => yLine(d.value));
                
                lineChart.selectAll(".line")
                    .data(lineData)
                    .enter()
                    .append("path")
                    .attr("class", "line")
                    .attr("d", d => line(d.values))
                    .style("fill", "none")
                    .style("stroke", (d, i) => lineColorScale(i))
                    .style("stroke-width", 2);
                
                // Add dots
                lineData.forEach((d, i) => {
                    lineChart.selectAll(".dot-" + i)
                        .data(d.values)
                        .enter()
                        .append("circle")
                        .attr("class", "dot")
                        .attr("cx", d => xLine(d.timepoint))
                        .attr("cy", d => yLine(d.value))
                        .attr("r", 5)
                        .style("fill", lineColorScale(i))
                        .on("mouseover", function(event, d) {
                            tooltip.transition()
                                .duration(200)
                                .style("opacity", .9);
                            tooltip.html(`${lineData[i].area}: ${Math.round(d.value * 100)}%<br>Time: ${d.timepoint}`)
                                .style("left", (event.pageX + 10) + "px")
                                .style("top", (event.pageY - 28) + "px");
                        })
                        .on("mouseout", function() {
                            tooltip.transition()
                                .duration(500)
                                .style("opacity", 0);
                        });
                });
                
                // Add legend
                const legend = lineChart.selectAll(".legend")
                    .data(areas)
                    .enter()
                    .append("g")
                    .attr("class", "legend")
                    .attr("transform", (d, i) => `translate(0,${i * 20})`);
                
                legend.append("rect")
                    .attr("x", width + 10)
                    .attr("width", 18)
                    .attr("height", 18)
                    .style("fill", (d, i) => lineColorScale(i));
                
                legend.append("text")
                    .attr("x", width + 35)
                    .attr("y", 9)
                    .attr("dy", ".35em")
                    .style("text-anchor", "start")
                    .text(d => d);
                
                // Chart title
                lineChart.append("text")
                    .attr("x", width / 2)
                    .attr("y", -5)
                    .attr("text-anchor", "middle")
                    .style("font-size", "14px")
                    .text("Confidence Evolution Over Time");
            </script>
        </body>
        </html>
        """
        
        # Replace placeholders
        html_content = html_template.replace("{{DATASET}}", json.dumps(dataset))
        html_content = html_content.replace("{{AREAS}}", json.dumps(list(areas)))
        html_content = html_content.replace("{{TIMEPOINTS}}", json.dumps(timepoints))
        
        # Write the HTML file
        with open(output_path, "w") as f:
            f.write(html_content)
            
        agent_viz_logger.info(f"Confidence heatmap saved to {output_path}")
        return True
        
    except Exception as e:
        agent_viz_logger.error(f"Error generating confidence heatmap: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Sample result data
    sample_result = {
        "investigation_phase": "root_cause_determination",
        "root_causes": [
            {
                "category": "network_policy",
                "component": "allow-backend-to-database",
                "description": "Misconfigured network policy preventing backend from connecting to database",
                "confidence": 0.85
            }
        ],
        "next_actions": [
            "Update network policy to allow backend pods to connect to database",
            "Restart affected pods",
            "Monitor connection status"
        ],
        "confidence_scores": {
            "network": 0.85,
            "network_policy": 0.9,
            "service_connectivity": 0.7
        },
        "findings": {
            "network": {},
            "metrics": {}
        },
        "confidence_history": {
            "2023-05-01T12:00:00": {"network": 0.3, "metrics": 0.2},
            "2023-05-01T12:05:00": {"network": 0.5, "metrics": 0.3, "network_policy": 0.6},
            "2023-05-01T12:10:00": {"network": 0.7, "metrics": 0.4, "network_policy": 0.8},
            "2023-05-01T12:15:00": {"network": 0.85, "metrics": 0.5, "network_policy": 0.9, "service_connectivity": 0.7}
        }
    }
    
    # Generate example visualizations
    generate_investigation_graph(sample_result, "example_graph.html")
    generate_confidence_heatmap(sample_result, "example_heatmap.html") 