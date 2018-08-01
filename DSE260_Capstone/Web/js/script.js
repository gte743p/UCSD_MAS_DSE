// set global vars
var geojson, geojson2;
var street;
var selectedDay;
var selectedTimeIdx;
var selectedTime;
var selectPredictor;
var selectedSegment;
var selectedSegmentWt = 10; // weight of selectedSegment highligh
var grades = [0, 1, 2, 3, 4, 5];
var daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
var numTimestamps = Object.keys(timestamp_lookup).length;
var time_data;
var days_data;
var legend, legend2;
var c3_color_opacity = 0.8;
var times = Object.keys(timestamp_lookup).map(function(e) {
    return timestamp_lookup[e];
});
var info, info2;

// set access token
var mapboxAccessToken = 'pk.eyJ1IjoiZ3RlNzQzcCIsImEiOiJjamR0MW1udXowdHY0MzNwN2IwM2Rob3MwIn0.0OADSSNt4qODanp9L0dAxQ';

// create map and set view to midpoint of bounding box
var map = L.map('mapid')
map.setView([(bounds[1][0] + bounds[0][0]) * 0.5, (bounds[1][1] + bounds[0][1]) * 0.5], 15);

L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token='+mapboxAccessToken, {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
    minZoom: 15,
    maxZoom: 18,
    id: 'mapbox.streets'
}).addTo(map);

// create map and set view to midpoint of bounding box
var map2 = L.map('mapid2')
map2.setView([(bounds[1][0] + bounds[0][0]) * 0.5, (bounds[1][1] + bounds[0][1]) * 0.5], 15);

L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token='+mapboxAccessToken, {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery ¬© <a href="http://mapbox.com">Mapbox</a>',
    minZoom: 15,
    maxZoom: 18,
    id: 'mapbox.streets'
}).addTo(map2);

map.sync(map2);
map2.sync(map);


// draw bounding box - how to set fill-opacity to 0? the below doesn't seem to work
//var boundingBox = L.rectangle(bounds, {color: "#777", weight: 7, 'fillOpacity': 0.1}).addTo(map);
//var boundingBox2 = L.rectangle(bounds, {color: "#777", weight: 7, 'fillOpacity': 0.1}).addTo(map2);


// from http://leafletjs.com/examples/choropleth/
var cmap = 'Reds';

function getColor(d) {
    return d === grades[5]  ? colormaps['Reds'][9] :
        d === grades[4]  ? colormaps['Reds'][7] :
        d === grades[3]  ? colormaps['Reds'][5] :
        d === grades[2]  ? colormaps['Reds'][4] :
        d === grades[1]  ? colormaps['Reds'][2] :
        '#ffffff';
}

function style(feature) {
    selectedTimeIdx = document.getElementById("timeSlider").value
    selectedTime = timestamp_lookup[selectedTimeIdx];
    selectedDay = document.getElementById("daySelector").value
    
    var pct = feature.properties.data[selectedDay]["level_max"][selectedTimeIdx]
	var wt = 4;

	// set opacity to 0 if pct = 0
	if (pct == 0) {
		op = 0.9
	} 
	else {
		op = 0.9
	}
		
	// set weight for selectedSegment
    if (typeof selectedSegment != 'undefined') {
		if (feature == selectedSegment.target.feature) {
			wt = selectedSegmentWt;
		}
    }
		
    return {
        color: getColor(pct),
        weight: wt,
        opacity: op
    };
}


function style2(feature) {
    selectedTimeIdx = document.getElementById("timeSlider").value
    selectedTime = timestamp_lookup[selectedTimeIdx];
    selectedDay = document.getElementById("daySelector").value
    selectPredictor = document.getElementById("predictorSelector").value
    
    // var pct = feature.properties.data[selectedDay]["level_max_preds_cluster_baseline"][selectedTimeIdx]
    var pct = feature.properties.data[selectedDay][selectPredictor][selectedTimeIdx]
    var wt = 4;

    // set opacity to 0 if pct = 0
    if (pct == 0) {
        op = 0.9
    } 
    else {
        op = 0.9
    }
        
    // set weight for selectedSegment
    if (typeof selectedSegment != 'undefined') {
        if (feature == selectedSegment.target.feature) {
            wt = selectedSegmentWt;
        }
    }
        
    return {
        color: getColor(pct),
        weight: wt,
        opacity: op
    };
}

// L.geoJson(segments_geojson, {style: style}).addTo(map);
// L.geoJson(segments_geojson, {style: style}).addTo(map2);


function mouseoverFunction(e) {
    highlightFeature(e);
    // update graph
    //updateGraph(e.target.feature);
    //var col_data = getCountyData(e.target.feature);
    //draw_c3(col_data);
    //draw_c3(getCountyData(e.target.feature));
    //county_name = getCountyData(e.target.feature.properties.name);
}


function highlightFeature(e) {
    var layer = e.target;
	var wt = 5;

		// set weight for selectedSegment
    if (typeof selectedSegment != 'undefined') {
    		if (layer == selectedSegment.target) {
    				wt = selectedSegmentWt;
    		}
    }

    layer.setStyle({
        weight: wt,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.7
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
        if (typeof selectedSegment != 'undefined') {
		        selectedSegment.target.bringToFront();
		    }
    }
    
    info.update(layer.feature.properties);
    info2.update(layer.feature.properties);
}

function clickHighlight(e) {
    var layer = e.target;

    layer.setStyle({
        weight: selectedSegmentWt,
        //color: '#666',
        dashArray: '',
        fillOpacity: 0.25
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
    
    //info.update(layer.feature.properties);
}


function mouseoutFunction(e) {
	resetHighlight(e);
	info.update();
    info2.update();
	// remove graphsvg
	// d3.select("#graphsvg").remove();
}


function resetHighlight(e) {
    // geojson.resetStyle(e.target);
    // geojson2.resetStyle(e.target);

    geojson.setStyle(style);
    geojson2.setStyle(style2);
    //info.update();
}

function drawLineGraph() {
	// selectedSegment is a global variable that is set to the clicked segment event
	street = selectedSegment.target.feature.properties.street;
    time_data = getTimeData(selectedSegment.target.feature);
    draw_c3_time(time_data);
}

function drawBarGraph() {
    // selectedSegment is a global variable that is set to the clicked segment event
	street = selectedSegment.target.feature.properties.street;
    days_data = getDaysData(selectedSegment.target.feature, selectedSegment.target.feature.properties.segment_id);
    draw_c3_days(days_data);
}


// get data for given county for graph
function getTimeData(f) {   
    var time_idx;
    var timeData = [];
    var v;
    
    for (time_idx = 0; time_idx < numTimestamps; time_idx++) {
            v = f.properties["data"][selectedDay]["level_max"][time_idx]
            timeData.push({time: time_idx, val: v});
    }
    return timeData;
}

function clickFunction(e) {
	// selectedSegment is a global variable that is set to the clicked segment event
	selectedSegment = e;
    
    // update both charts on click
	// drawLineGraph();
	// drawBarGraph();
	  
	// reset styles to unhighlight previously highlighted segment
	geojson.setStyle(style);
	geojson2.setStyle(style2);

	// set style to highlight
	clickHighlight(selectedSegment);


    var hm_data = [];
    var segment_id = e['target']['feature']['properties']['segment_id'];
    var street = e['target']['feature']['properties']['street'];
    for (day in daysOfWeek) {
        for (time in times)  {
            val = e['target']['feature']['properties']['data'][daysOfWeek[day]]['level_max'][time];
            // for (val in values) {
            // console.log('segment_id: ' + e.target.feature.properties.segment_id);
            // console.log('day: ' + day + ' time: ' + times[time] + ' val: ' + values[val]);
            //only want day and time index since heatmap will index into the dya dn times arrays
            hm_data.push({'day':day, 'hour':time, 'value':val, 'street': street, 'segment_id': segment_id});
            // }
        }
    }
    var heat_times = [];
    time_data = getTimeData(selectedSegment.target.feature);
    for (var i = 0; i < time_data.length; i++) {
        heat_times.push(timestamp_lookup[i]);
    }
    draw_heatmap(hm_data, heat_times, "heatmap");


    // Heatmap2
    var hm_data = [];
    for (day in daysOfWeek) {
        for (time in times)  {
            // val = e['target']['feature']['properties']['data'][daysOfWeek[day]]['level_max_preds_cluster_baseline'][time];
            val = e['target']['feature']['properties']['data'][daysOfWeek[day]][selectPredictor][time];

            // for (val in values) {
            // console.log('segment_id: ' + e.target.feature.properties.segment_id);
            // console.log('day: ' + day + ' time: ' + times[time] + ' val: ' + values[val]);
            //only want day and time index since heatmap will index into the dya dn times arrays
            hm_data.push({'day':day, 'hour':time, 'value':val, 'street': street, 'segment_id': segment_id});
            // }
        }
    }
    var heat_times = [];
    time_data = getTimeData(selectedSegment.target.feature);
    for (var i = 0; i < time_data.length; i++) {
        heat_times.push(timestamp_lookup[i]);
    }
    draw_heatmap(hm_data, heat_times, "heatmap2");
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: mouseoverFunction,
        mouseout: mouseoutFunction,
        click: clickFunction
    });
}

geojson = L.geoJson(segment_preds_geojson, {
    style: style,
    onEachFeature: onEachFeature
}).addTo(map);

geojson2 = L.geoJson(segment_preds_geojson, {
    style: style2,
    onEachFeature: onEachFeature
}).addTo(map2);

// custom info control
info = L.control();

info.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update();
    return this._div;
};

// method that we will use to update the control based on feature properties passed
info.update = function (props) {
    selectedTime = timestamp_lookup[selectedTimeIdx]
    selectedDay = document.getElementById("daySelector").value
    //console.log(props);
    
	this._div.innerHTML = (props ?
    '<b>' + props.street + ' - ' + 
    timestamp_lookup[selectedTimeIdx] + ' on ' + selectedDay + '</b><br />' +
    // (props.data[selectedDay]["level_max"][selectedTimeIdx]).toFixed(1) + 
    // 'Level Traffic Delay'
    ' has Traffic Delay at Level ' + '<b>' + (props.data[selectedDay]["level_max"][selectedTimeIdx]) + '</b>'
    : 'Mouseover a Street Segment');
};

info.addTo(map);

// custom info control
info2 = L.control();

info2.onAdd = function (map2) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update();
    return this._div;
};


// method that we will use to update the control based on feature properties passed
info2.update = function (props) {
    selectedTime = timestamp_lookup[selectedTimeIdx]
    selectedDay = document.getElementById("daySelector").value
    //console.log(props);
    
    // this._div.innerHTML = (props ?
    // '<b>' + props.street + ' - ' + 
    // timestamp_lookup[selectedTimeIdx] + ' on ' + selectedDay + '</b><br />' +
    // ' has Traffic Delay at Level ' + '<b>' + (props.data[selectedDay]["level_max_preds_cluster_baseline"][selectedTimeIdx]) + '</b>'
    // : 'Mouseover a Street Segment');

    this._div.innerHTML = (props ?
    '<b>' + props.street + ' - ' + 
    timestamp_lookup[selectedTimeIdx] + ' on ' + selectedDay + '</b><br />' +
    ' has Traffic Delay at Level ' + '<b>' + (props.data[selectedDay][selectPredictor][selectedTimeIdx]) + '</b>'
    : 'Mouseover a Street Segment');
};
info2.addTo(map2);



legend.addTo(map);
// legend2.addTo(map2);

// slider - from https://www.w3schools.com/howto/howto_js_rangeslider.asp
var slider = document.getElementById("timeSlider");

// slider_change function to use in c3 chart as well as slider.oninput
function slider_change() {
	selectedTimeIdx = slider.value;
	//console.log(selectedTimeIdx);
	geojson.setStyle(style);
    geojson2.setStyle(style2);
	document.getElementById("title").innerHTML = "Traffic in San Diego on " + selectedDay + " at " + timestamp_lookup[selectedTimeIdx]
	
	// draw bar graph if selected segment is defined
	// if (typeof selectedSegment != 'undefined') {
	// 	drawBarGraph();
 //    }
}

slider.oninput = function() {
	slider_change();
}


// function getKeyByValue(object, value) {
//     return Object.keys(object).find(key => object[key] === value);
// }

function predictorChangeFunc() {
    geojson2.setStyle(style2);
}

function dayChangeFunc() {
    geojson.setStyle(style);
    geojson2.setStyle(style2);
}


