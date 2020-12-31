const color1 = 'rgb(0, 117, 255',
      color2 = 'rgb(255,0,0)',
      color3 = 'rgb(255,0,0)',
      color4 = 'rgb(255,0,0)',
      color5 = 'rgb(255,0,0)',
      color6 = 'rgb(255,0,0)',
      color7 = 'rgb(255,0,0)',
      color8 = 'rgb(255,0,0)',
      color9 = 'rgb(255,0,0)';


// set the dimensions and margins of the graph
var margin = {top: 25, right: 20, bottom: 12, left: 25},
  width = 336 - margin.left - margin.right,
  height = 168 - margin.top - margin.bottom;

// append the svg object to the body of the page
var svg = d3.select("#plot")
.append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
.append("g")
  .attr("transform",
        "translate(" + margin.left + "," + margin.top + ")");

// Parse the Data
d3.csv("/static/js/csv_data.txt", function(data) {
  console.log(data);
  // Color scale: give me a specie name, I return a color
  var color = d3.scaleOrdinal()
    .domain(["domain1"]) //, "2", "3", "4", "5", "6", "7", "8", "9" ])
    .range([color1]) //,, color2, color3, color4, color5, color6, color7, color8, color9])

  // Here I set the list of dimension manually to control the order of axis:
  dimensions = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

  // For each dimension, I build a linear scale. I store all in a y object
  var y = {}
  for (i in dimensions) {
    name = dimensions[i]
    y[name] = d3.scaleLinear()
      .domain( [-2,2] ) // --> Same axis range for each group
      .range([height, 0])
  }
  
  // Build the X scale -> it find the best position for each Y axis
  x = d3.scalePoint()
    .range([0, width])
    .domain(dimensions);

  // Highlight the specie that is hovered
  var highlight = function(d){

    selected_specie = d.Species

    // first every group turns grey
    d3.selectAll(".line")
      .transition().duration(200)
      .style("stroke", "black")
      .style("opacity", "0.4")
    // Second the hovered specie takes its color
    d3.selectAll("." + selected_specie)
      .transition().duration(200)
      .style("stroke", color(selected_specie))
      .style("opacity", "1")
  }

  // Unhighlight
  var doNotHighlight = function(d){
    d3.selectAll(".line")
      .transition().duration(200).delay(1000)
      .style("stroke", function(d){ return( color(d.Species))} )
      .style("opacity", "1")
  }

  // The path function take a row of the csv as input, and return x and y coordinates of the line to draw for this raw.
  function path(d) {
      return d3.line()(dimensions.map(function(p) { return [x(p), y[p](d[p])]; }));
  }








  // Draw the lines
  svg
    .selectAll("myPath")
    .data(data)
    .enter().append("path")
    .attr("class", function (d) { return "line " + d.Species } ) // 2 class for each line: 'line' and the group name
    // .attr("d", path)
    .style("fill", "none" )
    .style("stroke", function(d){ return( color(d.Species))} )
    .style("opacity", 0.5)
    .on("mouseover", highlight)
    .on("mouseleave", doNotHighlight )









      
  // Draw the axis:
  svg.selectAll("myAxis")
    // For each dimension of the dataset I add a 'g' element:
    .data(dimensions).enter()
    .append("g")
    .attr("class", "axis")
    // I translate this element to its right position on the x axis
    .attr("transform", function(d) { return "translate(" + x(d) + ")"; })
    // And I build the axis with the call function
    .each(function(d) { d3.select(this).call(d3.axisLeft().ticks(5).scale(y[d])); })
    // Add axis title
    .append("text")
      .style("text-anchor", "middle")
      .attr("y", -9)
      .text(function(d) { return d; })
      .style("fill", "black")
})










//Width and height
var w = 900;
var h = 450;

var dataset = [ 5, 10, 13, 19, 21, 25, 22, 18, 15, 13,
                11, 12, 15, 20, 18, 17, 16, 18, 23, 25 ];

var xScale = d3.scaleBand()
                .domain(d3.range(dataset.length))
                .rangeRound([0, w])
                .paddingInner(0.05);

var yScale = d3.scaleLinear()
                .domain([0, d3.max(dataset)])
                .range([0, h]);

//Create SVG element
var svg = d3.select("body")
            .append("svg")
            .attr("width", w)
            .attr("height", h);

//Create bars
svg.selectAll("rect")
    .data(dataset)
    .enter()
    .append("rect")
    .attr("x", function(d, i) {
        return xScale(i);
    })
    .attr("y", function(d) {
        return h - yScale(d);
    })
    .attr("width", xScale.bandwidth())
    .attr("height", function(d) {
        return yScale(d);
    })
    .attr("fill", function(d) {
        return "rgb(0, 0, " + Math.round(d * 10) + ")";
    });

//Create labels
svg.selectAll("text")
    .data(dataset)
    .enter()
    .append("text")
    .text(function(d) {
        return d;
    })
    .attr("text-anchor", "middle")
    .attr("x", function(d, i) {
        return xScale(i) + xScale.bandwidth() / 2;
    })
    .attr("y", function(d) {
        return h - yScale(d) + 14;
    })
    .attr("font-family", "sans-serif")
    .attr("font-size", "11px")
    .attr("fill", "white");



//On click, update with new data			
d3.select("p")
    .on("click", function() {

        //Add one new value to dataset
        var maxValue = 25;
        var newNumber = Math.floor(Math.random() * maxValue);	//New random integer (0-24)
        dataset.push(newNumber);			 			 		//Add new number to array
        
        //Update scale domains
        xScale.domain(d3.range(dataset.length));	//Recalibrate the x scale domain, given the new length of dataset
        yScale.domain([0, d3.max(dataset)]);		//Recalibrate the y scale domain, given the new max value in dataset

        //Select…
        var bars = svg.selectAll("rect")			//Select all bars
            .data(dataset);	//Re-bind data to existing bars, return the 'update' selection
                                            //'bars' is now the update selection					
        //Enter…
        bars.enter()	//References the enter selection (a subset of the update selection)
            .append("rect")	//Creates a new rect
            .attr("x", w)		//Initial x position of the rect beyond the right edge of SVG
            .attr("y", function(d) {	//Sets the y value, based on the updated yScale
                return h - yScale(d);
            })
            .attr("width", xScale.bandwidth())	//Sets the width value, based on the updated xScale
            .attr("height", function(d) {			//Sets the height value, based on the updated yScale
                return yScale(d);
            })
            .attr("fill", function(d) {				//Sets the fill value
                return "rgb(0, 0, " + Math.round(d * 10) + ")";
            })
            .merge(bars)							//Merges the enter selection with the update selection
            .transition()							//Initiate a transition on all elements in the update selection (all rects)
            .duration(500)
            .attr("x", function(d, i) {				//Set new x position, based on the updated xScale
                return xScale(i);
            })
            .attr("y", function(d) {				//Set new y position, based on the updated yScale
                return h - yScale(d);
            })
            .attr("width", xScale.bandwidth())		//Set new width value, based on the updated xScale
            .attr("height", function(d) {			//Set new height value, based on the updated yScale
                return yScale(d);
            });

        //Update all labels
        var labels = svg.selectAll("text")
                                        .data(dataset);
        
        labels.enter()
            .append("text")
            .text(function(d) {
                return d;
            })
            .attr("text-anchor", "middle")
            .attr("font-family", "sans-serif")
            .attr("font-size", "11px")
            .attr("fill", function(d) {
                    if (d < 0.07 * maxValue){	return "black"	}
                else {	return "white"	}
            })
            .attr("x", function(d, i) {
                return w + xScale.bandwidth() / 2;
            })
            .attr("y", function(d) {
                if (d < 0.07 * maxValue){	return h - yScale(d) - 7	}
            else {	return h - yScale(d) + 14;	}
            })
            .merge(labels)
            .transition()
            .duration(500)
            .attr("x", function(d, i) { //Set new x position, based on the updated xScale
                return xScale(i) + xScale.bandwidth() / 2;
            })

    });