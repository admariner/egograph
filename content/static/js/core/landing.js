//////////////////////////////////////////////////////////
// Get context data 
const data_json = JSON.parse(document.getElementById('chart_data').textContent);

// Debug
debug_mode && console.log(data_json);

// Color list
const colors = [
	'#6baed6', // 0- light blue
	'#e77cf7', // pink
	'#fdae6b', // orange
	'#ffe962', // yellow
	'#50adff', // blue
	'#63c197', // 5 - green
	'#f2a6cb', // dull pink
	'#39cccc', // teal
]

// Create data object
var data = {
    // Labels
	'days': [],
    // Data
	'nodes': [],
	'edges': [],
    'node_edge_completion': [],
    'node_edge_recency': [],
}

//////////////////////////////////////////////////////////
// Create day dict {day: {nodes: 1, edges: 2}}

let day_dict = {};

// Nodes
for (const d of data_json.nodes_data) {
    // Format day
    let day = moment(d.day).format('YYYY-MM-DD');
    // Add day/nodes
    if (day in day_dict) {
	    day_dict[day]['nodes'] = d.total;
        day_dict[day]['nodes_completed'] = d.completed;
        day_dict[day]['recency'] = d.recency_avg;
    } else {
        day_dict[day] = {
            'nodes': d.total,
            'nodes_completed': d.completed,
            'recency': d.recency_avg,
        }
    }
}

// Edges
for (const d of data_json.edges_data) {
    // Format day
    let day = moment(d.day).format('YYYY-MM-DD');
    // Add day/nodes
    if (day in day_dict) {
	    day_dict[day]['edges'] = d.total;
    } else {
        day_dict[day] = {
            'edges': d.total 
        }
    }
}

// Debug
debug_mode && console.log(day_dict);

//////////////////////////////////////////////////////////
// Create data

// Created sorted list of days
const sorted_days = Object.keys(day_dict).sort();

// Calc cumulative nodes/edges
sorted_days.forEach(function (day, i) {
    // Add days
    data['days'].push(day);
    // Add completion
    const completion = ((day_dict[day]['nodes_completed'] / day_dict[day]['nodes']) * 100).toFixed(1)
    data['node_edge_completion'].push(completion);
    // Add Recency
    if (day_dict[day]['recency']) {
        data['node_edge_recency'].push(day_dict[day]['recency'].toFixed(1));
    }
    // If first day
    if (i == 0) {
        data['nodes'].push(day_dict[day]['nodes']);
        data['edges'].push(day_dict[day]['edges']);
    }
    // If not first day, increment
    else {
        data['nodes'].push(data['nodes'][i-1] + day_dict[day]['nodes']);
        data['edges'].push(data['edges'][i-1] + day_dict[day]['edges']);
    }
});

// Debug
debug_mode && console.log(data);

//////////////////////////////////////////////////////////////////////////////////////
// CHART - Nodes / Edges

//
const node_color = colors[1];
const edge_color = colors[0];

//
var chart1 = new Chart($("#chart1"), {
    type: 'line',
    data: {
        labels: data.days,
        datasets: [{
                label: "Edges",
                data: data.edges,
                steppedLine: true,
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderColor: node_color,
                borderWidth: 1.5,
                pointBackgroundColor: node_color,
                pointBorderColor: node_color,
                pointRadius: 0,
                pointHoverRadius: 0,
                showLine: true,
                lineTension: 0, // straight lines
            },
            {
                label: "Nodes",
                data: data.nodes,
                steppedLine: true,
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderColor: edge_color,
                borderWidth: 1.5,
                pointBackgroundColor: edge_color,
                pointBorderColor: edge_color,
                pointRadius: 0,
                pointHoverRadius: 0,
                showLine: true,
                lineTension: 0, // straight lines
            }
        ]
    },
    options: {
        tooltips: {
            callbacks: {
                label: function (tooltipItems, tooltipData) {	
					return tooltipData.datasets[tooltipItems.datasetIndex].label + ': ' + numberWithCommas(tooltipItems.yLabel);
				}
            }
        },
        scales: {
            xAxes: [{
                display: true,
                type: 'time',
                time: {
                    tooltipFormat: 'll', //'ll HH:mm'
                    unit: 'day', // always display this
                }
            }],
            yAxes: [{
                display: false,
                ticks: {
                    max: Math.max(Math.max(...data.nodes), Math.max(...data.edges)),
					min: 0,
                    callback: function (value, index, values) {
						return numberAxisFormat(value);
					}
                }
            }]
        }
    }
});


//////////////////////////////////////////////////////////////////////////////////////
// CHART - Edge completion

//
const edge_completion_color = colors[5];

//
var chart1 = new Chart($("#chart2"), {
    type: 'line',
    data: {
        labels: data.days,
        datasets: [{
                label: "Edge Completion",
                data: data.node_edge_completion,
                steppedLine: true,
                backgroundColor: edge_completion_color,
                borderColor: edge_completion_color,
                borderWidth: 1.5,
                pointBackgroundColor: edge_completion_color,
                pointBorderColor: edge_completion_color,
                pointRadius: 0,
                pointHoverRadius: 0,
                showLine: true,
                lineTension: 0, // straight lines
                fill: 'start',
            }   
        ]
    },
    options: {
        tooltips: {
            callbacks: {
                label: function (tooltipItems, tooltipData) {	
					return tooltipData.datasets[tooltipItems.datasetIndex].label + ': ' + numberWithCommas(tooltipItems.yLabel) + '%';;
				}
            }
        },
        scales: {
            xAxes: [{
                display: true,
                type: 'time',
                time: {
                    tooltipFormat: 'll', //'ll HH:mm'
                    unit: 'day', // always display this
                }
            }],
            yAxes: [{
                display: false,
                ticks: {
                    max: 100,
					min: 0,
                    callback: function (value, index, values) {
						return numberAxisFormat(value);
					}
                }
            }]
        }
    }
});

//////////////////////////////////////////////////////////////////////////////////////
// CHART - Edge recency

//
const edge_recency_color = colors[8];

//
var chart1 = new Chart($("#chart3"), {
    type: 'line',
    data: {
        labels: data.days,
        datasets: [{
                label: "Edge Recency",
                data: data.node_edge_recency,
                steppedLine: true,
                backgroundColor: edge_recency_color,
                borderColor: edge_recency_color,
                borderWidth: 1.5,
                pointBackgroundColor: edge_recency_color,
                pointBorderColor: edge_recency_color,
                pointRadius: 0,
                pointHoverRadius: 0,
                showLine: true,
                lineTension: 0, // straight lines
                fill: 'start',
            }   
        ]
    },
    options: {
        tooltips: {
            callbacks: {
                label: function (tooltipItems, tooltipData) {	
					return tooltipData.datasets[tooltipItems.datasetIndex].label + ': ' + numberWithCommas(tooltipItems.yLabel) + ' days';;
				}
            }
        },
        scales: {
            xAxes: [{
                display: true,
                type: 'time',
                time: {
                    tooltipFormat: 'll', //'ll HH:mm'
                    unit: 'day', // always display this
                }
            }],
            yAxes: [{
                display: false,
                ticks: {
                    max: Math.max(...data.node_edge_recency),
					min: 0,
                    callback: function (value, index, values) {
						return numberAxisFormat(value);
					}
                }
            }]
        }
    }
});
