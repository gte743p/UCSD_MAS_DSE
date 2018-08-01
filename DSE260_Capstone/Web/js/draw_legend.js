
// CREATE LEGEND
// legend
legend = L.control({position: 'bottomleft'});

legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend'),
    labels = [];

	div.innerHTML = '<b>Traffic Level</b><br>';    
    //div.innerHTML += '<i style background: #FFFFFF"></i> ' + 
    //		'<i style="background: #FFFFFF"></i> 0% <br>'
    // loop through density intervals and generate a label with colored square for each interval
    for (var i = 0; i < grades.length; i++) {
		div.innerHTML += '<i style=""background:' + getColor(grades[i]) + '"></i> ' +
        '<i style="background:' + getColor(grades[i]) + '"></i> ' + parseFloat(grades[i]) + '<br>';
    }

    return div;
};

