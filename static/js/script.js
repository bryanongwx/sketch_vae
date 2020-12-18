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
    ctx2,
    transferCanvas,
    transferCtx,
    intCanvas0,
    intCanvas1,
    intCanvas2,
    intCanvas3,
    intCanvas4,
    intCanvas5,
    intCanvas6,
    intCanvas7,
    intCanvas8;


var panel_index= 0;

const canvas_size = 360 

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
    
    console.log("setup "+panel_index);
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
    var offsetL = document.getElementById("canvas-box").offsetLeft;
    var offsetT = document.getElementById("option0").offsetTop

    prevX = currX;
    prevY = currY;
    currX = e.clientX - offsetL;
    currY = e.clientY - offsetT + scrolltop;

    if (res == 'down') {
        // tracks vector with absolute x and y
        let xArray = [];
        let yArray = [];
        
        absStroke = [xArray, yArray];

        let absX;
        let absY;
        let absT = 0; //for debugging timer


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
function fillCanvas() {
    ctx.fillStyle = "white";
    ctx.fillRect(0, 0, w, h);    
}

var absDataStorage = [];
var relDataStorage = [];
var absSeqDataStr = false;
var relSeqDataStr = false;

function storeData() {
    console.log("storing data");
    console.log(absVector);
    // converting absVector into relVector with relative distances and pen states
    let relVector = abs2relConverter(absVector);
    // saving vector arrays as JSONs and storing it (currently just being stored in an array)
    absSeqData = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(absVector));
    relSeqData = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(relVector));
    absDataStorage.push(absSeqData);
    relDataStorage.push(relSeqData);
    
    // resetting vector
    absVector = [];
}

/**
 * COMMUNICATION WITH 
 * PYTHON FILE  
*/

// VAE PREDICTION
function VAEpredict() { 
    // console.log("vae predict called")
    live = false;
    $("body").addClass("loading-cursor");

    var pred = new Image();
    pred.onload = function() {
        ctx.drawImage(pred, 0, 0, canvas_size, canvas_size);
        data = ctx.getImageData(0, 0, canvas_size, canvas_size).data;
        
        // document.getElementById("predict-img").src = canvas.toDataURL();
        var input = [];
        for(var i = 0; i < data.length; i += 4) {
            input.push(data[i + 0]);
            input.push(data[i + 1]);
            input.push(data[i + 2]);
        }
        storeData();
        VAEencoderRequest(input);
        CNNpredict(input);
    };
    pred.src = canvas.toDataURL('image/png');
}   
// Makes request to python file
function VAEencoderRequest(input){
    // console.log("python VAE func called w/");
    // console.log(input)
    // console.log("input shape1: "+input.length)

    input = JSON.stringify(input);
    
    // console.log("input stringified");
    // console.log(input)
    $.ajax({
        type : 'POST',
        url : "/VAEencoder",
        dataType : "json",
        contentType: 'application/json;charset=UTF-8',
        data : JSON.stringify({"input":input}),
        success:callbackFuncVAE
    });
}
function VAEdecoderRequest(input){
    // console.log("python VAE decoder func called w/");
    // console.log(input)
    // console.log("input shape1: "+input.length)

    vector = JSON.stringify(input);
    
    // console.log("input stringified");
    console.log(vector)
    $.ajax({
        type : 'POST',
        url : "/VAEdecoderHelper",
        dataType : "json",
        contentType: 'application/json;charset=UTF-8',
        data : JSON.stringify({"input":vector}),
        success:callbackFuncVAE
    });
}

var current_vector;
function callbackFuncVAE(response) {
    console.log("callback func called");
    let vec = response["vector"];
    // console.log("vector response: "+vec);
    current_vector = vec[0];
    
    updateSliders(vec);
    TensorToImage(response["result"], canvas2, ctx2);
}

function TensorToImage(rgbdata_reshaped, cnv, cnv_ctx, scale=5) {

    var hgt = 72;
    var wdt = 72;

    var r,g,b;

    for(var i=0; i< hgt; i++){ 
        for(var j=0; j< wdt; j++){ 
            r = 255*rgbdata_reshaped[i][j][0]; 
            g = 255*rgbdata_reshaped[i][j][1]; 
            b = 255*rgbdata_reshaped[i][j][2]; 
            let color = "rgba("+r+","+g+","+b+", 1)";
            cnv_ctx.fillStyle = color;  
            cnv_ctx.fillRect( j*scale, i*scale, scale, scale); 
        } 
    }
    let png = cnv.toDataURL();
    current_img_data = png;

    if (live == false){
        updateSaved(png);
    }
}


// CNN PREDICTION
function CNNpredict(input) {
    input = JSON.stringify(input);
    
    // console.log("converted?  "+input);
    $.ajax({
        type : 'POST',
        url : "/CNNpredict",
        dataType : "json",
        contentType: 'application/json;charset=UTF-8',
        data : JSON.stringify({"input":input}),
        success:callbackFuncCNN
    });
}
function CNNpredictVector(input) {
    input = JSON.stringify(input);
    
    $.ajax({
        type : 'POST',
        url : "/CNNpredictVector",
        dataType : "json",
        contentType: 'application/json;charset=UTF-8',
        data : JSON.stringify({"input":input}),
        success:callbackFuncCNN
    });
}
function callbackFuncCNN(response) {
    // console.log("Callback RESPONSE is:");
    // console.log(response)
    var value = response["result"];
    // console.log(value);
    console.log("baseFactor0: "+base_factor)

    var norm_value = normalizeCNN(value);
    norm_value = norm_value.toFixed(2);

    $("body").removeClass("loading-cursor");
    $("#cnn-text-main").text(norm_value);
    updateCNNvalues(norm_value);
    erase();
}

var base_factor = 'none';
var normalized;
function normalizeCNN(value){
    console.log("normalizing with: "+value)
    console.log("baseFactor1: "+base_factor)
    if (base_factor == 'none'){
        base_factor = value;
        console.log("baseFactor2: "+base_factor)
        return 1
    }
    console.log("baseFactor2: "+base_factor);

    normalized = value/base_factor;
    return normalized
}
function baseChange(ind){
    conversion_factor = cnn_values[ind];
    console.log("base change "+cnn_values);
    console.log("baseFactor3: "+base_factor);

    // console.log(cnn_values[0]);
    var j;
    for (j = 0; j < cnn_values.length; j++) {
        
        var v = cnn_values[j]
        if (v != 0){
            v = cnn_values[j] / conversion_factor
        }
        cnn_values[j] = v.toFixed(2); 
    }
    // cnn_values = cnn_values/conversion_factor; 
    // console.log(cnn_values[0]);

    base_factor = 1/(base_factor*conversion_factor);
    var i;
    for (i = 0; i < cnn_values.length; i++) {
        id = "saved-cnn"+i;
        t = cnn_values[i]
        $("#"+id).text(t);
        }

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
    // slider9 = document.getElementById("slider9");
    // getting value text
    sliderValue1 = document.getElementById("sliderValue1");
    sliderValue2 = document.getElementById("sliderValue2");
    sliderValue3 = document.getElementById("sliderValue3");
    sliderValue4 = document.getElementById("sliderValue4");
    sliderValue5 = document.getElementById("sliderValue5");
    sliderValue6 = document.getElementById("sliderValue6");
    sliderValue7 = document.getElementById("sliderValue7");
    sliderValue8 = document.getElementById("sliderValue8");
    // sliderValue9 = document.getElementById("sliderValue9");
    // Update the current slider value (each time you drag the slider handle)
    slider1.oninput = function() {sliderValue1.innerHTML = this.value;
        liveSliderPredict(this.value);
    }
    slider2.oninput = function() {sliderValue2.innerHTML = this.value;
        liveSliderPredict(this.value);
    }
    slider3.oninput = function() {sliderValue3.innerHTML = this.value;
        liveSliderPredict(this.value);
    }
    slider4.oninput = function() {sliderValue4.innerHTML = this.value;
        liveSliderPredict(this.value);
    }
    slider5.oninput = function() {sliderValue5.innerHTML = this.value;
        liveSliderPredict(this.value);
    }
    slider6.oninput = function() {sliderValue6.innerHTML = this.value;
        liveSliderPredict(this.value);
    }
    slider7.oninput = function() {sliderValue7.innerHTML = this.value;
        liveSliderPredict(this.value);
    }
    slider8.oninput = function() {sliderValue8.innerHTML = this.value;
        liveSliderPredict(this.value);
    }
    // slider9.oninput = function() {sliderValue9.innerHTML = this.value;
    //     liveSliderPredict(this.value);
    // }
}

var live = false;
function liveSliderPredict(val) {
    val = val*100
    if (val%10 == 0) {
        live = true;
        var sliderArray = [
            Number(slider1.value),
            Number(slider2.value),
            Number(slider3.value),
            Number(slider4.value),
            Number(slider5.value),
            Number(slider6.value),
            Number(slider7.value),
            Number(slider8.value),
        ];
        VAEdecoderRequest(sliderArray);
    }
}


// $("#slider1").bind("change", function() {
//     drawGraph($("#ampSlider").val(), $("#freqSlider").val());
// });

var current_img_data = 0;

function sliderPredict() {
    live = false;
    var sliderArray = [
        Number(slider1.value),
        Number(slider2.value),
        Number(slider3.value),
        Number(slider4.value),
        Number(slider5.value),
        Number(slider6.value),
        Number(slider7.value),
        Number(slider8.value),
    ];
    // need to make sure this data is collecting correctly from the right side canvas
    var pred = new Image();
    pred.onload = function() {
        ctx.drawImage(pred, 0, 0, canvas_size, canvas_size);
        data = ctx.getImageData(0, 0, canvas_size, canvas_size).data;
        var input = [];
        for(var i = 0; i < data.length; i += 4) {
            input.push(data[i + 0]);
            input.push(data[i + 1]);
            input.push(data[i + 2]);
        }
    }
    storeData();
    VAEdecoderRequest(sliderArray);
    CNNpredict(input);
    scrollTo(0,0);
}
function resetSliders() {
    const default_value = 0;
    // setting value to default
    slider1.value = default_value;
    slider2.value = default_value;
    slider3.value = default_value;
    slider4.value = default_value;
    slider5.value = default_value;
    slider6.value = default_value;
    slider7.value = default_value;
    slider8.value = default_value;
    // slider9.value = default_value;
    // setting text to default
    sliderValue1.innerHTML = default_value;
    sliderValue2.innerHTML = default_value;
    sliderValue3.innerHTML = default_value;
    sliderValue4.innerHTML = default_value;
    sliderValue5.innerHTML = default_value;
    sliderValue6.innerHTML = default_value;
    sliderValue7.innerHTML = default_value;
    sliderValue8.innerHTML = default_value;
    // sliderValue9.innerHTML = default_value;
} 
function updateSliders(vector) {
    // console.log("update with "+vector)
    // console.log("len "+vector.length)
    // console.log("0 "+vector[0])
    // console.log("00 "+vector[0][0])
    // console.log("01 "+vector[0][1])
    vector = vector[0];


    slider1.value = vector[0];
    slider2.value = vector[1];
    slider3.value = vector[2];
    slider4.value = vector[3];
    slider5.value = vector[4];
    slider6.value = vector[5];
    slider7.value = vector[6];
    slider8.value = vector[7];
    // slider9.value = vector[8];
    // setting text to default
    sliderValue1.innerHTML = slider1.value;
    sliderValue2.innerHTML = slider2.value;
    sliderValue3.innerHTML = slider3.value;
    sliderValue4.innerHTML = slider4.value;
    sliderValue5.innerHTML = slider5.value;
    sliderValue6.innerHTML = slider6.value;
    sliderValue7.innerHTML = slider7.value;
    sliderValue8.innerHTML = slider8.value;
    // sliderValue9.innerHTML = slider9.value;
} 


// UPDATE SAVED IMAGES
var saved_index = 0;
var paths = [];
var saved0 = document.getElementById("saved0");
var saved1 = document.getElementById("saved1");
var saved2 = document.getElementById("saved2");
var saved3 = document.getElementById("saved3");
var saved4 = document.getElementById("saved4");
var saved5 = document.getElementById("saved5");
var allSaved = [saved0,saved1,saved2,saved3,saved4,saved5];
var data0 = {"src": "","perf": "", "data":"", "vector":"", "empty":true}
var data1 = {"src": "","perf": "", "data":"", "vector":"", "empty":true}
var data2 = {"src": "","perf": "", "data":"", "vector":"", "empty":true}
var data3 = {"src": "","perf": "", "data":"", "vector":"", "empty":true}
var data4 = {"src": "","perf": "", "data":"", "vector":"", "empty":true}
var data5 = {"src": "","perf": "", "data":"", "vector":"", "empty":true}
var datas = [data0,data1,data2,data3,data4,data5];

function updateSaved(img) {

    if (saved_index == 6) {
        alert("Max number of sketches reached!")
    }
    else {
        paths[saved_index] = img;
        datas[saved_index]["src"] = img;
        datas[saved_index]["data"] = current_img_data;
        datas[saved_index]["vector"] = current_vector;
        datas[saved_index]["empty"] = false;
        // console.log("cur img data: "+current_img_data);
        $("#saved0").attr("src",paths[0]);
        $("#saved1").attr("src",paths[1]);
        $("#saved2").attr("src",paths[2]);
        $("#saved3").attr("src",paths[3]);
        $("#saved4").attr("src",paths[4]);
        $("#saved5").attr("src",paths[5]);
        saved_index +=1
        
        if (no_sketches == true) {
            $("#saved0").addClass("activeSaved");                            
            no_sketches = false;
        }
        // saved0 = document.getElementById("saved0");
        // saved1 = document.getElementById("saved1");
        // saved2 = document.getElementById("saved2");
        // saved3 = document.getElementById("saved3");
        // saved4 = document.getElementById("saved4");
        // saved5 = document.getElementById("saved5");
        // allSaved = [saved0,saved1,saved2,saved3,saved4,saved5]

        // // console.log(allSaved)
    }
}
function resetSaved() {
    let m = confirm("Want to clear all your sketches?");
    if (m) {
        saved_index = 0;
        paths = [];
        cnn_values = [];
        base_factor = "none";
        $("#saved0").attr("src","/static/img/blank.png");
        $("#saved1").attr("src","/static/img/blank.png");
        $("#saved2").attr("src","/static/img/blank.png");
        $("#saved3").attr("src","/static/img/blank.png");
        $("#saved4").attr("src","/static/img/blank.png");
        $("#saved5").attr("src","/static/img/blank.png");
        
        $("#saved-cnn0").text("0");       
        $("#saved-cnn1").text("0");
        $("#saved-cnn2").text("0");
        $("#saved-cnn3").text("0");
        $("#saved-cnn4").text("0");
        $("#saved-cnn5").text("0");
        no_sketches = true;
        activeSaved("start");
        $("#saved-cnn0").removeClass("visible-block");
        $("#saved-cnn1").removeClass("visible-block");
        $("#saved-cnn2").removeClass("visible-block");
        $("#saved-cnn3").removeClass("visible-block");
        $("#saved-cnn4").removeClass("visible-block");
        $("#saved-cnn5").removeClass("visible-block");
        $("#saved-cnn0").addClass("invisible");
        $("#saved-cnn1").addClass("invisible");
        $("#saved-cnn2").addClass("invisible");
        $("#saved-cnn3").addClass("invisible");
        $("#saved-cnn4").addClass("invisible");
        $("#saved-cnn5").addClass("invisible");

        for (i = 0; i < 6; i++) {
            datas[i]["src"] = "";
            datas[i]["data"] = "";
            datas[i]["vector"] = "";
            datas[i]["empty"] = true;
        }

    }
}

var no_sketches = true;
var rememberActive = 0;
function activeSaved(num) {
    if (num == "start"){
        for (i = 0; i < 6; i++) {
            $("#saved"+i).removeClass("activeSaved");
        }
    } else {
        console.log(datas[num]["empty"]);
        if (datas[num]["empty"] == true){
            console.log("empty sketch!");
        } else {
            if (current_index == 0){
                for (i = 0; i < 6; i++) {
                    id = "saved"+i;
                    if (i == num) {
                        $("#"+id).addClass("activeSaved");
                    }
                    else {
                        $("#"+id).removeClass("activeSaved");
                    }
                }
                rememberActive = num;
                baseChange(num);

            } else if (current_index == 1) {
                intSelect(num);
            }
        }
    }
}

var cnn_values = [];

function updateCNNvalues(val){
    cnn_values.push(val);
    i = cnn_values.length - 1;
    $("#saved-cnn"+i).text(val);
    $("#cnn-values-test").text(cnn_values);
    console.log('i'+i);
    $("#saved-cnn"+i).removeClass("invisible");
    $("#saved-cnn"+i).addClass("visible-block");
} 

var selectedInt = [0,1]
function intSelect(num) {
    selectedInt.push(num);    
    remove = selectedInt.shift();
    console.log("remove: "+remove);
    $("#saved"+remove).removeClass("activeSavedint");
    $("#saved"+selectedInt[0]).addClass("activeSavedint");
    $("#saved"+selectedInt[1]).addClass("activeSavedint");

}

var intSlider = document.getElementById("int-slider");
var intSliderValue = document.getElementById("intSliderValue");
intSlider.oninput = function() {intSliderValue.innerHTML = this.value;}


// INTERPOLATION
function interpolationRequest(){    
    intInput1 = datas[selectedInt[0]];
    intInput2 = datas[selectedInt[1]];

    // display start and end on canvas

    intInput1 = JSON.stringify(intInput1["vector"]);
    intInput2 = JSON.stringify(intInput2["vector"]);
    number = parseInt(intSlider.value);
    number += 2;
    number = JSON.stringify(number);
    console.log("inputs for iunterpolation");

    $.ajax({
        type : 'POST',
        url : "/interpolation",
        dataType : "json",
        contentType: 'application/json;charset=UTF-8',
        data : JSON.stringify({"input1":intInput1, "input2":intInput2, "number":number}),
        success:callbackFuncInterpolation
    });
}

function callbackFuncInterpolation(response) {
    var intImg = [intCanvas0, intCanvas1, intCanvas2, intCanvas3, intCanvas4, intCanvas5, intCanvas6, intCanvas7, intCanvas8];
    for (m = 3; m < intImg.length; m++) {

        console.log("int"+m+"  getting invis")
        $("#int"+m).removeClass("visible-inline-block");
        $("#int"+m).addClass("invisible");
    }

    let all_ints = response["int_list"];

            
    var hgt = 72;
    var wdt = 72;
    var  scale = 1;   

    for (i = 0; i < all_ints.length; i++) {
        var rgbdata_reshaped =all_ints[i];
    
        var r,g,b;    
        for(var k=0; k< 72; k++){ 
            for(var j=0; j< 72; j++){
                r = 255*rgbdata_reshaped[k][j][0];
                g = 255*rgbdata_reshaped[k][j][1];
                b = 255*rgbdata_reshaped[k][j][2];
                let color = "rgba("+r+","+g+","+b+", 1)";
                transferCtx.fillStyle = color;  
                transferCtx.fillRect(j*1, k*1, 1, 1); 
            } 
        }
        $("#int"+i).removeClass("invisible");
        $("#int"+i).addClass("visible-inline-block");
        let png = transferCanvas.toDataURL();
        console.log("i = "+i);
        intImg[i].src = png;
    }
}

// PANEL SWITCHING
const total = 2;
var optionNames = ["Prediction", "Interpolation"];

function switchLeft() {
    console.log("old panel index: ");
    console.log(panel_index);
    console.log("switch left");
    panel_index += -1;
    update();
}
function switchRight() {
    console.log("old panel index: ");
    console.log(panel_index);
    console.log("switch rght");
    panel_index += 1;
    update();
}
current_index = 0;
function optionSwitch(index) {    
    var allOptions = document.getElementById("main-container").querySelectorAll(".visible-template"); 
    if (index != current_index) {
        current_index = index;
        
        for(var j = 0; j < allOptions.length; ++j){
            allOptions[j].classList.remove("visible-template");
        } 
        for (i = 0; i < total; i++) {
            id = "option"+i;
            if (i == index) {
                $("#"+id).addClass("visible-template");
                $("#option"+i+"-btn").removeClass("optionInactive");
                $("#option"+i+"-btn").addClass("optionActive");
            } else {
                $("#option"+i+"-btn").removeClass("optionActive");
                $("#option"+i+"-btn").addClass("optionInactive");
            }
        }
        
        switchCanvas(index)
    }
    toTop();
}


function update() {
    console.log("updating with panel_index="+panel_index);
    if (panel_index >= total) {
        panel_index = panel_index-total;
    } else if (panel_index < 0) {
        panel_index = panel_index + total;
    }
    console.log("fixed panel_index="+panel_index);
    console.log("");
    $("#option-name").text(optionNames[panel_index]);


    var allOptions = document.getElementById("main-container").querySelectorAll(".visible-template"); 
    for(var j = 0; j < allOptions.length; ++j){
        allOptions[j].classList.remove("visible-template");
    } 
    for (i = 0; i < total; i++) {
        id = "option"+i;
        if (i == panel_index) {
            $("#"+id).addClass("visible-template");
        }
    }
    console.log(document.getElementById("option0").classList)
    console.log(document.getElementById("option1").classList)
    switchCanvas()

    toTop();
}

function switchCanvas(ci="none"){ 
    if (ci == "none"){
        ci = current_index;
    }
    
    if (ci == 0){
        console.log("getting regular canvas");
        canvas = document.getElementById('myCanvas');
        ctx = canvas.getContext("2d");
        w = canvas.width;
        h = canvas.height;
        fillCanvas();
        
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

        $("#saved"+rememberActive).addClass("activeSaved");
        for (i = 0; i < 6; i++) {
            id = "saved"+i;
            $("#"+id).removeClass("activeSavedint");
        }
        console.log(document.getElementById("saved0").classList)

    } else {
        transferCanvas = document.getElementById('transferCanvas');
        transferCtx = transferCanvas.getContext("2d");
        intCanvasStart = document.getElementById('intStart');
        intCanvas0 = document.getElementById('int0');
        intCanvas1 = document.getElementById('int1');
        intCanvas2 = document.getElementById('int2');
        intCanvas3 = document.getElementById('int3');
        intCanvas4 = document.getElementById('int4');
        intCanvas5 = document.getElementById('int5');
        intCanvas6 = document.getElementById('int6');
        intCanvas7 = document.getElementById('int7');
        intCanvas8 = document.getElementById('int8');
        intCanvasEnd = document.getElementById('intEnd');

        console.log("getting other canvas");

        canvas = document.getElementById('interpolationCanvas');
        ctx = canvas.getContext("2d");
        w = canvas.width;
        h = canvas.height;
        fillCanvas();
        
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

        for (i = 0; i < 6; i++) {
            id = "saved"+i;
            $("#"+id).removeClass("activeSaved");
        }

        $("#saved0").addClass("activeSavedint");
        $("#saved1").addClass("activeSavedint");
        console.log(document.getElementById("saved0").classList)
    }
}

function toTop() {
    window.scrollTo(0,0);
}