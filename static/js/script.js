var canvas, ctx, flag = false,
    prevX = 0,
    currX = 0,
    prevY = 0,
    currY = 0,
    dot_flag = false,
    sketchSequence1 = 0,
    sketchSequence2 = 0,
    sketchSequence3 = 0,
    sketchSequence4 = 0,
    absStroke,
    absVector,
    canvas2,
    ctx2;

const canvas_size = 336 

const intervalTime = 10; //interval in milliseconds for recording points of stroke
const timerText = document.getElementById("title");
let intervalID;
var blankSketch = true; // won't allow user to add the sketch if they haven't drawn anything

// drawing style
var x = "rgba(0,0,0,1)",
    y = 4;


function init() {
    canvas = document.getElementById('myCanvas');
    ctx = canvas.getContext("2d");
    w = canvas.width;
    h = canvas.height;
    fillCanvas();

    //  SETTING UP PREDICTION CANVAS
    canvas2 = document.getElementById('predCanvas');
    ctx2 = canvas2.getContext("2d");

    absVector = [];

    canvas.addEventListener("mousemove", function (e) {
        findxy('move', e)
    }, false);
    canvas.addEventListener("mousedown", function (e) {
        findxy('down', e)
    }, false);
    canvas.addEventListener("mouseup", function (e) {
        findxy('up', e)
    }, false);
    canvas.addEventListener("mouseout", function (e) {
        findxy('out', e)
    }, false);

    // SLIDERS
    sliders();
 }


function draw() {
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(currX, currY);
    ctx.strokeStyle = x;
    ctx.lineWidth = y;
    ctx.lineCap = "round";
    ctx.stroke();
    ctx.closePath();
}

function findxy(res, e) {
    var scrolltop = this.scrollY;

    prevX = currX;
    prevY = currY;
    currX = e.clientX - canvas.offsetLeft;
    currY = e.clientY - canvas.offsetTop + scrolltop;

    if (res == 'down') {
        // tracks vector with absolute x and y
        let xArray = [];
        let yArray = [];
        
        absStroke = [xArray, yArray];

        let absX;
        let absY;
        let absT = 0; //for debugging timer

        // intervalID = setInterval(function () {
        //     // absVector
        //     absT += 1;
        //     absX = currX;
        //     absY = currY;

        //     xArray.push(absX);
        //     yArray.push(absY);

        //     timerText.innerHTML = absT+" | "+absX+","+absY; //for debugging timer

        // }, intervalTime);


        flag = true;
        dot_flag = true;
        blankSketch = false;
        if (dot_flag) {
            ctx.beginPath();
            ctx.fillStyle = x;
            ctx.fillRect(currX, currY, y, y);
            ctx.closePath();
            dot_flag = false;
        }
    }
    if (res == 'up' || res == "out") {
        if (flag == true) {
            clearInterval(intervalID);
            timerText.innerHTML = "Sketch Canvas";

            //absVector
            absVector.push(absStroke);
        }
        flag = false;
    }

    if (res == 'move') {
        if (flag) {
            draw();
        }
    }

}

var addCount = 0 // keeps track of how many sketches have been added so it can't be pressed once it reaches max.
var absDataStorage = [];
var relDataStorage = [];
var absSeqDataStr = false;
var relSeqDataStr = false;

function addSketch() {
    // displays sketch, erases canvas
    // in the future will need to store data somewhere and feed data into interpolation model or something else
    if (blankSketch == false) {
        // checks that something has been drawn so that blankSketches aren't added
        // could also add more restrictions here (minimum amount of points?...)
        // currently only supports adding a max of 4 sketches

        canvas = document.getElementById('myCanvas');
        let dataURI = canvas.toDataURL(); // png for displaying sketch on website
        let sketchInput = ctx.getImageData(0, 0, w, h);
        console.log(sketchInput);

        // converting absVector into relVector with relative distances and pen states
        let relVector = abs2relConverter(absVector);
        // console.log("AbsVec:"+absVector);
        // console.log("RelVec:"+relVector);

        // saving vector arrays as JSONs and storing it (currently just being stored in an array)
        absSeqDataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(absVector));
        relSeqDataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(relVector));
        absDataStorage.push(absSeqDataStr);
        relDataStorage.push(relSeqDataStr);

        // if (addCount == 0) {
        //     sketch1.src = dataURI; 
        // }
        // else if (addCount == 1) {
        //     sketch2.src = dataURI;
        // }
        // if (addCount == 2) {
        //     sketch3.src = dataURI;
        // }
        // else if (addCount == 3) {
        //     sketch4.src = dataURI;
        // }
        // else if (addCount > 3) {
        //     alert('You can only add up to 4 sketches. Press "Clear All" to start over.');
        // }
        // erase();
        // blankSketch = true;
        // addCount = addCount + 1;

        // resetting vector
        absVector = [];

        // model prediction
        makePrediction(dataURI);
        savePNG(sketchInput);
    }
    else if (blankSketch == true) {
        alert("You can't add an empty sketch")
    }
}

function abs2relConverter(absvec) {
    var i, j;
    var oldX = 0;
    var oldY = 0;
    var newX, newY, deltaX, deltaY, arrLength, xArray, yArray, currStroke, centerX, centerY, newPoint, endPoint;
    var convertedVec = [[0,0,1,0,0]];
    
    for (i = 0; i < absvec.length; i++) {
        currStroke = absvec[i];
        xArray = currStroke[0];
        yArray = currStroke[1];
        arrLength = xArray.length;
        for (j = 0; j < arrLength; j++) {
            // stores coords of first point of sketch used to normalize data to start at 0,0
            if (i+j == 0) {
                var centerX = xArray[0];
                var centerY = yArray[0];
            }
            else {
                newX = xArray[j] - centerX;
                newY = yArray[j] - centerY;

                deltaX = newX - oldX;
                deltaY = newY - oldY;

                newPoint = [deltaX,deltaY, 1,0,0];
                convertedVec.push(newPoint);

                oldX = newX;
                oldY = newY;
            }
        }
        // changing last point of stroke to p2 state
        endPoint = convertedVec.pop();
        endPoint.splice(2,3, 0, 1, 0);
        convertedVec.push(endPoint);
    }
    // changing final point to p3 state
    endPoint = convertedVec.pop();
    endPoint.splice(2,3, 0, 0, 1);
    convertedVec.push(endPoint);
    return convertedVec;
}

// clears only the current sketch
function erase() {
    ctx.clearRect(0, 0, w, h);
    blankSketch = true;
    fillCanvas();
}
// clears the current sketch and removes all added sketches
function eraseAll() {
    var m = confirm("Want to clear all your sketches?");
    if (m) {
        fillCanvas();
        sketch1.src = "https://i.ya-webdesign.com/images/blank-png-1.png";
        sketch2.src = "https://i.ya-webdesign.com/images/blank-png-1.png";
        sketch3.src = "https://i.ya-webdesign.com/images/blank-png-1.png";
        sketch4.src = "https://i.ya-webdesign.com/images/blank-png-1.png";
        addCount = 0
    }
}
function fillCanvas() {
    ctx.fillStyle = "white";
    ctx.fillRect(0, 0, w, h);    
}

// model stuff
// var encoder;
// var decoder;
// var model;

// tf.loadLayersModel("0831encoder2/encoder.json").then(function(enc) {
//     encoder = enc;
//     console.log("= = = ENCODER LOADED = = =");
//     console.log(encoder);
//    });
// tf.loadLayersModel("0831decoder2/decoder.json").then(function(dec) {
//     decoder = dec;
//     console.log("= = = DECODER LOADED = = = ");
//     console.log(decoder);
//    });


// tf.loadLayersModel("CNN/model.json").then(function(model) {
//     window.model = model;
//     // window.alert('All models loaded!');
//     // $("loading-div").addClass("invisible");
//     var loading_div = document.getElementById("loading-div");
//     loading_div.style.display = "none";
//     $("body").removeClass("loading-cursor");
//     console.log("= = = CNN LOADED = = = = =");
//    });

    
// predicts performance (integer)    
function CNNpredict() {
    $("body").addClass("loading-cursor");
    resetResults();
    var pred = new Image();
    pred.onload = function() {
        ctx.drawImage(pred, 0, 0, canvas_size, canvas_size);
        data = ctx.getImageData(0, 0, canvas_size, canvas_size).data;
        document.getElementById("predict-img").src = canvas.toDataURL();
        var input = [];
        for(var i = 0; i < data.length; i += 4) {
            input.push(data[i + 0] / 255);
            input.push(data[i + 1] / 255);
            input.push(data[i + 2] / 255);
        }
        CNNpredict2(input);
    };
    pred.src = canvas.toDataURL('image/png');
}   


function CNNpredict2(input) {
    // input = [1,2,3,4,5,6,7,8,9]
    console.log("CNN Predict 2 input:")
    console.log(input)
    console.log("\nCalling pythonCNN")
    prediction = pythonCNN(input);

    // // console.log("ID: "+ count);

    // // console.log("predict inp: "+input);
    // reshaped_input = tf.reshape(input, [1,224,224,3]);
    // // console.log("reshape inp: "+reshaped_input);
      
    // var outPred = model.predict(reshaped_input);

    // var tensorData = outPred.dataSync();
    // // console.log("tensor data "+tensorData)
    // var predictDisplay = tensorData[0].toFixed(2);


    var predictDisplay = prediction;

    var output = document.getElementById("prediction");
    output.innerHTML = predictDisplay;
    
    erase();
    $("body").removeClass("loading-cursor");
}

function pythonCNN(input){
    console.log("python CNN func called with "+input);

    // let first = 10;
    // let second = 20;
    // fetch("/add")
    //   .then((response) => {
    //     return response.json();
    //   })
    //   .then((myJson) => {
    //     console.log("When I add "+first+" and "+second+" I get: "+myJson.result);
    //     callbackFunc(myJson.response);
    // });
    input = JSON.stringify(input);
    
    console.log("converted?  "+input);
    $.ajax({
        type : 'POST',
        url : "/predict",
        dataType : "json",
        contentType: 'application/json;charset=UTF-8',
        data : JSON.stringify({"inp":input}),
        success:callbackFuncCNN
    });
    // $.ajax({
    //     type: "POST",
    //     url:"/test",
    //     data:{JSinput: input},
    //     success:callbackFunc
    // });
}

function callbackFuncCNN(response) {
    console.log("Callback RESPONSE is:")
    console.log(response)
    $('#test-text').html('<li>'+JSON.stringify(response)+'</li>');
}


// makes prediction from added Sketch
function VAEpredict() { 
    console.log("vae predict called")

    resetResults();
    var pred = new Image();
    pred.onload = function() {
        ctx.drawImage(pred, 0, 0, canvas_size, canvas_size);
        data = ctx.getImageData(0, 0, canvas_size, canvas_size).data;
        document.getElementById("predict-img").src = canvas.toDataURL();
        var input = [];
        for(var i = 0; i < data.length; i += 4) {
            input.push(data[i + 0] / 255);
            input.push(data[i + 1] / 255);
            input.push(data[i + 2] / 255);
        }
        // add input to this when encoder works
        pythonVAE(input);
    };
    pred.src = canvas.toDataURL('image/png');
}   

function pythonVAE(input){
    console.log("python VAE func called");
    input = JSON.stringify(input);
    
    $.ajax({
        type : 'POST',
        url : "/VAEpredict",
        dataType : "json",
        contentType: 'application/json;charset=UTF-8',
        data : JSON.stringify({"inp":input}),
        success:callbackFuncVAE
    });
}

function callbackFuncVAE(response) {
    console.log("callback func called")

    TensorToImage(response["result"]);
    erase();
    // $('#test-text').html('<li>'+"VAE PREDICTION MADE."+Math.random()+'</li>');
}
function TensorToImage(rgbdata_reshaped) {
    console.log("tensor to image called")
    var hgt = 72;
    var wdt = 72;
    var scale = 4;
    var r,g,b;

    for(var i=0; i< hgt; i++){ 
        for(var j=0; j< wdt; j++){ 
            r = 255*rgbdata_reshaped[i][j][0]; 
            g = 255*rgbdata_reshaped[i][j][1]; 
            b = 255*rgbdata_reshaped[i][j][2]; 
            let color = "rgba("+r+","+g+","+b+", 1)";
            ctx2.fillStyle = color;  
            ctx2.fillRect( j*scale, i*scale, scale, scale); 
        } 
    }  
    let png = canvas2.toDataURL();
    updateSaved(png);
}

function reshapeArray(array, wd, channels) {
    var arr1 = [];
    for(var i=0; i< array.length; i+=channels){ 
        let newArray = [];
        for(var j=0; j< channels; j++){ 
            newArray.push(array[i+j]);
        }
        arr1.push(newArray);
    }
    var arr2 = [];
    for(var i=0; i< arr1.length; i+=wd){ 
        let newArray = [];
        for(var j=0; j< wd; j++){ 
            newArray.push(arr1[i+j]);
        }
        arr2.push(newArray);
    }
    return arr2
}

function BOTHpredict() {
    $("body").addClass("loading-cursor");

    CNNpredict();
    VAEpredict();
}
function resetResults() {
    var output1 = document.getElementById("prediction");
    output1.innerHTML = "";
}



// function TensorToImage2(tensor) {
//     console.log("start tensor to image");
//     //get the tensor shape
//     const [width, height] = tensor.shape;
//     //create a buffer array
//     const buffer = new Uint8ClampedArray(width * height * 4);
//     //create an Image data var 
//     const imageData = new ImageData(width, height);
//     //get the tensor values as data
//     const data = tensor.dataSync();
//     //map the values to the buffer
//     var i = 0;
//     for(var y = 0; y < height; y++) {
//         for(var x = 0; x < width; x++) {
//             var pos = (y * width + x) * 4;      // position in buffer based on x and y
//             buffer[pos  ] = data[i];             // some R value [0, 255]
//             buffer[pos+1] = data[i+1];           // some G value
//             buffer[pos+2] = data[i+2];           // some B value
//             buffer[pos+3] = 255;                // set alpha channel
//             i+=3;
//         }
//     }f
//     //set the buffer to the image data
//     imageData.data.set(buffer);
//     //show the image on canvas
//     document.getElementById("predict-img").src = imageData;
//     // ctx.putImageData(imageData, 0, 0);
// };



// for downloads
function downloadObjectAsJson(exportObj, exportName){
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportObj));
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", exportName + ".json");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  }
  
// Function for saving array - for mouse coordinates see prevX/Y and currX/Y
function save() {
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(lastSketch));
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", "test.json");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  }

function saveAbs() {
    if (absSeqDataStr != false) {
        var dataStr = absSeqDataStr;
        var downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href",     dataStr);
        downloadAnchorNode.setAttribute("download", "absVector.json");
        document.body.appendChild(downloadAnchorNode); // required for firefox
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    } 
}
function saveRel() {
    if (relSeqDataStr != false){
        var dataStr = relSeqDataStr;
        var downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href",     dataStr);
        downloadAnchorNode.setAttribute("download", "relVector.json");
        document.body.appendChild(downloadAnchorNode); // required for firefox
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    }
}

function savePNG(img) {
    var dataStr = img;
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", "handsketch.png");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}


var slider1,slider2,slider3,slider4,slider5,slider6,slider7,slider8,slider9;
var sliderValue1,sliderValue2,sliderValue3,sliderValue4,sliderValue5,sliderValue6,sliderValue7,sliderValue8,sliderValue9;

function sliders() {
    // getting slider objects
    slider1 = document.getElementById("slider1");
    slider2 = document.getElementById("slider2");
    slider3 = document.getElementById("slider3");
    slider4 = document.getElementById("slider4");
    slider5 = document.getElementById("slider5");
    slider6 = document.getElementById("slider6");
    slider7 = document.getElementById("slider7");
    slider8 = document.getElementById("slider8");
    slider9 = document.getElementById("slider9");
    // getting value text
    sliderValue1 = document.getElementById("sliderValue1");
    sliderValue2 = document.getElementById("sliderValue2");
    sliderValue3 = document.getElementById("sliderValue3");
    sliderValue4 = document.getElementById("sliderValue4");
    sliderValue5 = document.getElementById("sliderValue5");
    sliderValue6 = document.getElementById("sliderValue6");
    sliderValue7 = document.getElementById("sliderValue7");
    sliderValue8 = document.getElementById("sliderValue8");
    sliderValue9 = document.getElementById("sliderValue9");
    // Update the current slider value (each time you drag the slider handle)
    slider1.oninput = function() {sliderValue1.innerHTML = this.value;}
    slider2.oninput = function() {sliderValue2.innerHTML = this.value;}
    slider3.oninput = function() {sliderValue3.innerHTML = this.value;}
    slider4.oninput = function() {sliderValue4.innerHTML = this.value;}
    slider5.oninput = function() {sliderValue5.innerHTML = this.value;}
    slider6.oninput = function() {sliderValue6.innerHTML = this.value;}
    slider7.oninput = function() {sliderValue7.innerHTML = this.value;}
    slider8.oninput = function() {sliderValue8.innerHTML = this.value;}
    slider9.oninput = function() {sliderValue9.innerHTML = this.value;}
}
function sliderPredict() {
    var sliderArray = [
        Number(slider1.value),
        Number(slider2.value),
        Number(slider3.value),
        Number(slider4.value),
        Number(slider5.value),
        Number(slider6.value),
        Number(slider7.value),
        Number(slider8.value),
        Number(slider9.value),
    ];
    pythonVAE(sliderArray);
    scrollTo(0,0);
}
function resetSliders() {
    default_value = 0;
    // setting value to default
    slider1.value = default_value;
    slider2.value = default_value;
    slider3.value = default_value;
    slider4.value = default_value;
    slider5.value = default_value;
    slider6.value = default_value;
    slider7.value = default_value;
    slider8.value = default_value;
    slider9.value = default_value;
    // setting text to default
    sliderValue1.innerHTML = default_value;
    sliderValue2.innerHTML = default_value;
    sliderValue3.innerHTML = default_value;
    sliderValue4.innerHTML = default_value;
    sliderValue5.innerHTML = default_value;
    sliderValue6.innerHTML = default_value;
    sliderValue7.innerHTML = default_value;
    sliderValue8.innerHTML = default_value;
    sliderValue9.innerHTML = default_value;
} 
function randomSliders() {
    slider1.value = Math.random()*4-2;
    slider2.value = Math.random()*4-2;
    slider3.value = Math.random()*4-2;
    slider4.value = Math.random()*4-2;
    slider5.value = Math.random()*4-2;
    slider6.value = Math.random()*4-2;
    slider7.value = Math.random()*4-2;
    slider8.value = Math.random()*4-2;
    slider9.value = Math.random()*4-2;
    // setting text to default
    sliderValue1.innerHTML = slider1.value;
    sliderValue2.innerHTML = slider2.value;
    sliderValue3.innerHTML = slider3.value;
    sliderValue4.innerHTML = slider4.value;
    sliderValue5.innerHTML = slider5.value;
    sliderValue6.innerHTML = slider6.value;
    sliderValue7.innerHTML = slider7.value;
    sliderValue8.innerHTML = slider8.value;
    sliderValue9.innerHTML = slider9.value;
    CNNpredict();

    sliderPredict();
} 


// UPDATE SAVED IMAGES
var index = 0;
var paths = [];
function updateSaved(img) {
    paths[index] = img;
    $("#saved0").attr("src",paths[0]);
    $("#saved1").attr("src",paths[1]);
    $("#saved2").attr("src",paths[2]);
    $("#saved3").attr("src",paths[3]);
    $("#saved4").attr("src",paths[4]);
    $("#saved5").attr("src",paths[5]);
    $("#saved6").attr("src",paths[6]);
    $("#saved7").attr("src",paths[7]);
    $("#saved8").attr("src",paths[8]);
    $("#saved9").attr("src",paths[9]);
    $("#saved10").attr("src",paths[10]);
    index +=1
}
