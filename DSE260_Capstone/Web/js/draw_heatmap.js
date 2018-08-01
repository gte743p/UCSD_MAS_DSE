// adapted from http://bl.ocks.org/ianyfchang/8119685
function draw_heatmap(hm_data, heat_times, heatmapname) {

    // alert(Array.from(Array(7).keys()).map(function(d,i) {return i * 2}));
    var margin = {top: 100, right: 10, bottom: 150, left: 100};
    //var margin2 = {top: 100, right: 10, bottom: 150, left: 100};

    var cellSize = 10;
    // alert(Array.from(Array(7).keys()).map(function(d,i) {return (i+1) * cellSize}));
    var col_number = 48;
    var row_number = 7;
    var width = cellSize * col_number; // - margin.left - margin.right,
    var height = cellSize * row_number; // - margin.top - margin.bottom,
    //gridSize = Math.floor(width / 24),
    // legendElementWidth = cellSize * 2.5,
    // colorBuckets = 21,
    // colors = ['#005824', '#1A693B', '#347B53', '#4F8D6B', '#699F83', '#83B09B', '#9EC2B3', '#B8D4CB', '#D2E6E3', '#EDF8FB', '#FFFFFF', '#F1EEF6', '#E6D3E1', '#DBB9CD', '#D19EB9', '#C684A4', '#BB6990', '#B14F7C', '#A63467', '#9B1A53', '#91003F'];
    // /yyp/ hcrow = [49, 11, 30, 4, 18, 6, 12, 20, 19, 33, 32, 26, 44, 35, 38, 3, 23, 41, 22, 10, 2, 15, 16, 36, 8, 25, 29, 7, 27, 34, 48, 31, 45, 43, 14, 9, 39, 1, 37, 47, 42, 21, 40, 5, 28, 46, 50, 17, 24, 13], // change to gene name or probe id
    hcrow = [1,2,3,4,5,6,7];
    // hccol = [6, 5, 41, 12, 42, 21, 58, 56, 14, 16, 43, 15, 17, 46, 47, 48, 54, 49, 37, 38, 25, 22, 7, 8, 2, 45, 9, 20, 24, 44, 23, 19, 13, 40, 11, 1, 39, 53, 10, 52, 3, 26, 27, 60, 50, 51, 59, 18, 31, 32, 30, 4, 55, 28, 29, 57, 36, 34, 33, 35], // change to gene name or probe id
    hcclen = heat_times.length;
    hccol = Array.from(Array(hcclen).keys());
    min = 0;
    max = heat_times.length;
    function range (start, end) { return [...Array(1+end-start).keys()].map(v => start+v) }
    hccol = range(0,47);
    // var hccol = function (min, max) {
    //     var len = max - min + 1;
    //     var arr = new Array(len);s
    //     for (var i=0; i<len; i++) {
    //         arr[i] = min + i;
    //     }
    //     return arr;
    // };
    // rowLabel = ['1759080_s_at', '1759302_s_at', '1759502_s_at', '1759540_s_at', '1759781_s_at', '1759828_s_at', '1759829_s_at', '1759906_s_at', '1760088_s_at', '1760164_s_at', '1760453_s_at', '1760516_s_at', '1760594_s_at', '1760894_s_at', '1760951_s_at', '1761030_s_at', '1761128_at', '1761145_s_at', '1761160_s_at', '1761189_s_at', '1761222_s_at', '1761245_s_at', '1761277_s_at', '1761434_s_at', '1761553_s_at', '1761620_s_at', '1761873_s_at', '1761884_s_at', '1761944_s_at', '1762105_s_at', '1762118_s_at', '1762151_s_at', '1762388_s_at', '1762401_s_at', '1762633_s_at', '1762701_s_at', '1762787_s_at', '1762819_s_at', '1762880_s_at', '1762945_s_at', '1762983_s_at', '1763132_s_at', '1763138_s_at', '1763146_s_at', '1763198_s_at', '1763383_at', '1763410_s_at', '1763426_s_at', '1763490_s_at', '1763491_s_at'], // change to gene name or probe id
    // colLabel = ['con1027', 'con1028', 'con1029', 'con103', 'con1030', 'con1031', 'con1032', 'con1033', 'con1034', 'con1035', 'con1036', 'con1037', 'con1038', 'con1039', 'con1040', 'con1041', 'con108', 'con109', 'con110', 'con111', 'con112', 'con125', 'con126', 'con127', 'con128', 'con129', 'con130', 'con131', 'con132', 'con133', 'con134', 'con135', 'con136', 'con137', 'con138', 'con139', 'con14', 'con15', 'con150', 'con151', 'con152', 'con153', 'con16', 'con17', 'con174', 'con184', 'con185', 'con186', 'con187', 'con188', 'con189', 'con191', 'con192', 'con193', 'con194', 'con199', 'con2', 'con200', 'con201', 'con21']; // change to contrast name

    var gridSize = Math.floor(width / 48);
    var legendElementWidth = gridSize * 4;
    var colorBucket = 10;
    var colors = Object.values(colormaps2['Reds']);
    // add white for zero values
    colors.unshift('#ffffff');
        
    // days
    var rowLabel = daysOfWeek
    // var rowLabel = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
    //times
    var colLabel = heat_times;
    //= ["1a", "2a", "3a", "4a", "5a", "6a", "7a", "8a", "9a", "10a", "11a", "12a", "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p", "10p", "11p", "12p"];

    var legLabels = ['0', '1', ' 2 ', ' 3 ', ' 4 ', ' 5 '];
    // d3.tsv("data_heatmap.tsv",
    //     function (d) {
    //         return {
    //             row: +d.row_idx,
    //             col: +d.col_idx,
    //             value: +d.log2ratio
    //         };
    //     },
    var heatmapChart = function (hm_data) {
        var data = [];
        for (row in hm_data) {
            data.push({'row': +hm_data[row].day, 'col': +hm_data[row].hour,
                'value': (hm_data[row].value).toFixed(1),
                'segment_id': hm_data[row].segment_id,
                'street': hm_data[row].street});
        }

        // function (error, data) {
        var colorScale = d3.scale.threshold()
        	// .domain([1, 10, 20, 30, 40, 50, 60, 70, 80, 90])
            .domain([0, 1, 2, 3, 4, 5])
            .range(colors);

        d3.select("#" + heatmapname).remove();
        // svg.remove();
        // hm = document.createElement('div');
        // hm.setAttribute("id","heatmap");
        // hm.id = 'heatmap';
        // d3.select("body").append(hm);

        var body = document.getElementsByTagName('body')[0];

        var newdiv = document.createElement('div');   //create a div
        newdiv.id = heatmapname;                      //add an id
        newdiv.width = width;
        newdiv.height = height;
        newdiv.overflow = "auto";
        body.appendChild(newdiv);                 //append to the doc.body

        // document.getElementById('heatmap').style.width = 960;
        // document.getElementById('heatmap').style.height = 480;


        // d3.select("body").append("div").text("heatmap");
        var svg = d3.select("#" + heatmapname)
            // svg """#heatmap").append("svg")
            // var svg = d3.select("#heatmap")
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
        ;
        // var rowSortOrder = false;
        // var colSortOrder = false;
        var rowLabels = svg.append("g")
            .selectAll(".rowLabelg")
            .data(rowLabel)
            .enter()
            .append("text")
            .text(function (d) { return d; })
            .attr("x", 0)
            .attr("y", function (d, i) { return hcrow.indexOf(i+1) * cellSize; })
            .style("text-anchor", "end")
            .attr("transform", "translate(-15," + cellSize / 1.0 + ")")
            .attr("class", function (d, i) { return "rowLabel mono r" + i;})
            .on("mouseover", function (d) {d3.select(this).classed("text-hover", true);})
            .on("mouseout", function (d) {d3.select(this).classed("text-hover", false);})
            // .on("click", function (d, i) {
            //     rowSortOrder = !rowSortOrder;
            //     sortbylabel("r", i, rowSortOrder);
            //     d3.select("#order").property("selectedIndex", 4).node().focus();
            //     ;
            // })
        ;

        var colLabels = svg.append("g")
            .selectAll(".colLabelg")
            .data(colLabel)
            .enter()
            .append("text")
            .text(function (d) { return d; })
            .attr("x", 0)
            .attr("y", function (d, i) { return hccol.indexOf(i) * cellSize; })
            .style("text-anchor", "left")
            .attr("transform", "translate(" + cellSize / 2 + ",-16) rotate (-90)")
            .attr("class", function (d, i) { return "colLabel mono c" + i;})
            .on("mouseover", function (d) {d3.select(this).classed("text-hover", true);})
            .on("mouseout", function (d) {d3.select(this).classed("text-hover", false);})
            // .on("click", function (d, i) {
            //     colSortOrder = !colSortOrder;
            //     sortbylabel("c", i, colSortOrder);
            //     d3.select("#order").property("selectedIndex", 4).node().focus();
            //     ;
            // })
        ;


        var heatMap = svg.append("g").attr("class", "g3")
            .selectAll(".cellg")
            .data(data, function (d) {return d.row + ":" + d.col;})
            .enter()
            .append("rect")
            .attr("x", function (d) { return (d.col) * gridSize; })
            .attr("y", function (d) { return (d.row) * gridSize; })
            .attr("class", function (d) {return "cell cell-border cr" + (d.row) + " cc" + (d.col);})
            .attr("width", cellSize)
            .attr("height", cellSize)
            .style("fill", function (d) { return colorScale(d.value-1); })
            .style("fill-opacity", c3_color_opacity)
            .on("click", function(d) {
                daySelector.value = rowLabel[d.row];
                daySelector_change();
                slider.value = getKeyByValue(timestamp_lookup, colLabel[d.col]);
                slider_change();
                                

                   // var rowtext=d3.select(".r"+(d.row-1));
                   // if(rowtext.classed("text-selected")==false){
                   //     rowtext.classed("text-selected",true);
                   // }else{
                   //     rowtext.classed("text-selected",false);
                   // }
            })
            .on("mouseover", function (d) {
            		//highlight text
                d3.select(this).classed("cell-hover", true);
                d3.selectAll(".rowLabel").classed("text-highlight", function (r, ri) { return ri == (d.row);});
                d3.selectAll(".colLabel").classed("text-highlight", function (c, ci) { return ci == (d.col);});

                //Update the tooltip position and value
                d3.select("#tooltip")
                    .style("left", (d3.event.pageX - 150) + "px")
                    .style("top", (d3.event.pageY - 70) + "px")
                    .select("#value")
                    .text("Traffic Delay at level " + parseInt(d.value) + " on Selected Segment of " + d.street + " on " + rowLabel[d.row] + " at " + colLabel[d.col]);
                    //.text("Day: " + rowLabel[d.row] + ", Time: " + colLabel[d.col] + ", Pct Congested: " + d.value + ", Segment ID: " + d.segment_id);
                // + "\nrow-col-idx:" + d.row + "," + d.col + "\ncell-xy " + this.x.baseVal.value + ", "
                // + this.y.baseVal.value);
                //Show the tooltip
                d3.select("#tooltip").classed("hidden", false);
            })
            .on("mouseout", function () {
                d3.select(this).classed("cell-hover", false);
                d3.selectAll(".rowLabel").classed("text-highlight", false);
                d3.selectAll(".colLabel").classed("text-highlight", false);
                d3.select("#tooltip").classed("hidden", true);
            })
        ;

        var legend = svg.selectAll(".legend")
        // .data([-10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            .data(legLabels)
            .enter().append("g")
            .attr("class", "legend");

        legend.append("rect")
            .attr("x", function (d, i) { return legendElementWidth * i; })
            .attr("y", height + (cellSize * 2))
            .attr("width", legendElementWidth)
            .attr("height", cellSize)
            .style("fill", function (d, i) { return colors[i]; })  // colors[i+1]
            .style("fill-opacity", c3_color_opacity);

        legend.append("text")
            .attr("class", "mono")
            .text(function (d) { return d; })
            .attr("width", legendElementWidth)
            .attr("x", function (d, i) { return legendElementWidth * i; })
            .attr("y", height + (cellSize * 4));
    };
    heatmapChart(hm_data, heat_times);
}