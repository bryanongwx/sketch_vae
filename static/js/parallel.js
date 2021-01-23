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

// var csv_data = "/static/js/csv/csv_data.txt";
var csv_data = [
  // fake data used for testing
  [-0.9, -0.01,-0.25,0.6, 1.17, -1, -1.88, 1.38, -0.26],
  [-0.9, 0.01, 0.25, -0.6, -1.1, 1, 1.88, 1.38, 0.26],
  [-.5,-.5,-.5,-.5,-.5,-.5,-.5,-.5,-.5]
];

// function used for testing switching the data to see if the plot would update
function replot(csv_data){
  if (csv_data == 2){
    // fake data used for testing
    csv_data = [[-2, -1.9,-1.8,-1.7,-1.6,-1.5,-1.4,-1.3,-1.2]];
  } else {
    csv_data = csv_data;
  }

  // Parse the Data
  d3.csv(csv_data, function(data) {
    data = csv_data;
    var csv_titles = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "Species"];

    // Extract the list of dimensions we want to keep in the plot. Here I keep all except the column called Species
    dimensions = d3.keys(csv_titles).filter(function(d) { return d != "Species" })
    var color = d3.scaleOrdinal()
      .domain(["domain1"]) //, "2", "3", "4", "5", "6", "7", "8", "9" ])
      .range([color1]) //,, color2, color3, color4, color5, color6, color7, color8, color9])

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
      .padding(1)
      .domain(dimensions);

    // The path function take a row of the csv as input, and return x and y coordinates of the line to draw for this raw.
    function path(d) {
        return d3.line()(dimensions.map(function(p) { return [x(p), y[p](d[p])]; }));
    }    
    
    // Draw the lines
    svg
      .selectAll("myPath")
      .data(data)
      .enter().append("path")
      .attr("d",  path)
      .style("fill", "none")
      .style("stroke", "rgb(0,0,255)")
      .style("opacity", 0.85)

    // Draw the axis:
    svg.selectAll("myAxis")
      // For each dimension of the dataset I add a 'g' element:
      .data(dimensions).enter()
      .append("g")
      // I translate this element to its right position on the x axis
      .attr("transform", function(d) { return "translate(" + x(d) + ")"; })
      // And I build the axis with the call function
      .each(function(d) { d3.select(this).call(d3.axisLeft().scale(y[d])); })
      // Add axis title
      .append("text")
        .style("text-anchor", "middle")
        .attr("y", -9)
        .text(function(d) { return d; })
        .style("fill", "black")

  })
}

// function used for testing switching the data to see if the plot would update
replot(csv_data);