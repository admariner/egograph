var network = null;

function draw() {

	// Instantiate our network object.
	var container = document.getElementById("graph");
	var data = {
		nodes: graph_data.nodes, // [{ 'id': 0, 'value': 1100, 'label': 'poodle', 'group': 0 }]
		edges: graph_data.edges, // [{ 'from': 0, 'to': 1, 'value': 1250 }]
	};
	var options = {
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

window.addEventListener("load", () => {
	draw();
});
