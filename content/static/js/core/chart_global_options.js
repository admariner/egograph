//////////////////////////////////////////////////////////////////////////////////////
// GLOBAL CHARTJS OPTIONS

//
const numberWithCommas = (x) => {
	return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

//
function numberAxisFormat(number) {
    // Millions
	if (number >= 1e6) {
        // If whole
        if (number / 1e6 % 1 == 0) {
            return numberWithCommas((number / 1e6).toFixed(0)) + 'M';
        } else {
            return numberWithCommas((number / 1e6).toFixed(1)) + 'M';
        }
	}
    // Thousand
	else if (number >= 1e3) {
		return numberWithCommas((number / 1e3).toFixed(0)) + "k";
	}
    //
	else {
		return numberWithCommas(number.toFixed(0));
	}
}

//
Chart.defaults.global.defaultFontFamily = 'Cerebri Sans';
Chart.defaults.global.defaultFontSize = 11.44;
Chart.defaults.global.defaultFontColor = 'black';
//
Chart.defaults.global.title.display = false;
Chart.defaults.global.legend.display = false;
Chart.defaults.global.legend.onClick = null; // disable clickable legend
Chart.defaults.global.layout.padding = 0;
//
//Chart.defaults.line.spanGaps = true; // don't show null values
Chart.defaults.global.tooltips.enabled = true;
Chart.defaults.global.tooltips.mode = 'index';
Chart.defaults.global.tooltips.intersect = false;

// Reverse item sort of tooltips
Chart.defaults.global.tooltips.itemSort = function (a, b) {
	return b.datasetIndex - a.datasetIndex;
};

// Show tooltip at top of chart
Chart.Tooltip.positioners.custom = function (elements, position) {
	// If no elements, no tooltip
	if (!elements.length) {
		return false;
	}
	// Set position
	var i, len;
	var x = NaN; // default to no tooltip
	var y = NaN; // default to no tooltip
	for (i = 0, len = elements.length; i < len; ++i) {
		var el = elements[i];
		// for each data element, check if exists and has value
		if (el && el.hasValue()) {
			var pos = el.tooltipPosition();
			x = pos.x; // x value of element (should all be the same)
			y = 0; // bottom of chart (el._yScale.bottom)
		}
	}
	// Return
	return {
		x: x,
		y: y
	};
}
Chart.defaults.global.tooltips.position = 'custom';
//
Chart.defaults.global.animation.duration = 0; // general animation time
Chart.defaults.global.hover.animationDuration = 0; // duration of animations when hovering an item
Chart.defaults.global.responsive = true;
Chart.defaults.global.responsiveAnimationDuration = 0; // animation duration after a resize
Chart.defaults.global.maintainAspectRatio = false;
Chart.defaults.global.events = ["mousemove", "mouseout", "click", "touchstart", "touchmove", "touchend"]; // remove tooltip on mobile touchend
//
Chart.scaleService.updateScaleDefaults('linear', {
	gridLines: {
		drawOnChartArea: false,
		color: 'rgba(0, 0, 0, .5)',
		lineWidth: 0.5,
	},
	ticks: {
		maxTicksLimit: 4,
	}
});
Chart.scaleService.updateScaleDefaults('logarithmic', {
	gridLines: {
		drawOnChartArea: false,
		color: 'rgba(0, 0, 0, 1)',
		lineWidth: 0.5,
	},
	ticks: {
		maxTicksLimit: 4,
	}
});
Chart.scaleService.updateScaleDefaults('time', {
	//offset: true, // prevents first/last bar from being cut in half
	//barPercentage: 0.5,
	//categoryPercentage: 1,
	//barThickness: 3,
	//maxBarThickness: 20,
	//minBarLength: 2,
	gridLines: {
		display: true,
		drawOnChartArea: false,
		color: 'rgba(0, 0, 0, .5)',
		lineWidth: 0.5,
	},
	ticks: {
		maxTicksLimit: 3,
		maxRotation: 0, // disable label rotation
		minRotation: 0 // disable label rotation
	}
});
Chart.scaleService.updateScaleDefaults('category', {
	//maxBarThickness: 25,
	//barPercentage: .75,
	//categoryPercentage: 1,
	//barThickness: 'flex', // If a day is missing it stretches the bar
	minBarLength: 2,
	gridLines: {
		drawOnChartArea: false,
		color: 'rgba(0, 0, 0, 1)',
		lineWidth: 0.5,
	},
});
