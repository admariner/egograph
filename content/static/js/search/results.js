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
		edges: {
			color: { 
				inherit: "from" // where edges inherit their color
			},
		},
	};

	// Update network
	network = new vis.Network(container, data, options);

	// Get progress element
	let progress_el = $('#progress')

	// Event - stabilization progress update
	network.on("stabilizationProgress", function (params) {
		// Calculate progress and update element
		let progress = Math.round((params.iterations / params.total) * 100) + "%";
		progress_el.html(progress).css('width', progress);
		progress_el;
	});
	
	// Event - stabilization finished
	network.once("stabilizationIterationsDone", function () {
		// Show 100%
		progress_el.html("100%").css('width', '100%');
		// Pause (for effect)
		setTimeout(function () {
			// Remove progress bar
			$('.progress').remove();
			// Show graph
			$('#graph').show();
			// Stablize again (just to fit to the window)
			network.stabilize(0);
			// Stop all simulation
			network.stopSimulation();
		}, 1000);
	});
}

// Draw graph on load event
window.addEventListener("load", () => {
	draw();
});
