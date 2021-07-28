// Get data
const graph_data = JSON.parse(JSON.parse(document.getElementById('graph_data').textContent));

// Draw function
var network;
function draw() {

	// Instantiate our network object.
	var container = document.getElementById("graph");

	// Organize data
	var data = {
		nodes: graph_data.nodes, // [{ 'id': 0, 'value': 1100, 'label': 'poodle', 'group': 0 }]
		edges: graph_data.edges, // [{ 'from': 0, 'to': 1, 'value': 1250 }]
	};

	// Set options
	const options = {
		autoResize: true, // resize graph when container is resized
		clickToUse: true, // react to mouse and touch events only when active
		nodes: {
			shape: "dot",
			font: {
				size: 12,
				face: "Tahoma",
				strokeColor: '#ffffff',
				strokeWidth: 4, // px
			},
			scaling: {
				min: 1,
				max: 600,
			},
		},
		edges: {
			color: { 
				inherit: "from", // where edges inherit their color
				opacity: 0.4
			},
			smooth: {
				enabled: false // straight edges, should help performance
			},
			scaling: {
				min: 1,
				max: 10,
			},
		},
		physics: false,
		/*
		{
			solver: 'barnesHut',
			barnesHut: {
				theta: 3, // default 0.5. Higher values are faster but generate a more simplistic graph
			},
			minVelocity: 30, // default 0.1. Lowest movements speeds allowable, leads to quicker stablization
			stabilization: {
				iterations: 1000, // max iterations, but will stop sooner if minvelocity is hit
				updateInterval: 10 // interval to send progress event
			} 
		},
		*/
		interaction: {
			dragNodes: false,
			dragView: false,
			zoomView: false,
			selectable: false,
			selectConnectedEdges: false,
			hoverConnectedEdges: false,
		},
	};

	// Update network
	network = new vis.Network(container, data, options);

	// Stablize again (just to fit to the window)
	network.stabilize(0);
}

// Draw graph on load event
window.addEventListener("load", () => {
	draw();
});

