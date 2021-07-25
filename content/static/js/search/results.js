// Get data
const graph_data = JSON.parse(JSON.parse(document.getElementById('graph_data').textContent));

// Draw function
var network = null;
function draw() {

	// Instantiate our network object.
	var container = document.getElementById("graph");
	var data = {
		nodes: graph_data.nodes, // [{ 'id': 0, 'value': 1100, 'label': 'poodle', 'group': 0 }]
		edges: graph_data.edges, // [{ 'from': 0, 'to': 1, 'value': 1250 }]
	};
	var options = {
		autoResize: true, // resize graph when container is resized
		clickToUse: true, // react to mouse and touch events only when active
		nodes: {
			shape: "dot",
			font: {
				size: 16, // px
				strokeColor: '#ffffff',
				strokeWidth: 8, // px
			}
		},
	};
	network = new vis.Network(container, data, options);
}

// Draw graph on load event
window.addEventListener("load", () => {
	draw();
});
