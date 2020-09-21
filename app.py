import streamlit as st
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import tensorflow.keras.backend as K
from tensorflow.keras.models import model_from_json
from tensorflow.keras.models import load_model
from tensorflow.keras import layers
from streamlit_drawable_canvas import st_canvas
import matplotlib.pyplot as plt
from matplotlib import cm
from PIL import Image
import numpy as np
from skimage.transform import resize



# Specify canvas parameters in application
stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)
stroke_color = st.sidebar.beta_color_picker("Stroke color hex: ")
bg_color = st.sidebar.beta_color_picker("Background color hex: ", "#eee")
bg_image = st.sidebar.file_uploader("Background image:", type=["png", "jpg"])
drawing_mode = st.sidebar.selectbox(
    "Drawing tool:", ("freedraw", "line", "rect", "circle", "transform")
)
realtime_update = st.sidebar.checkbox("Update in realtime?", True)
update_button = True
if not realtime_update:
    update_button = st.sidebar.button('Send data to Streamlit')


# Create a canvas component
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color="" if bg_image else bg_color,
    background_image=Image.open(bg_image) if bg_image else None,
    update_streamlit=realtime_update or update_button,
    height=300,
    width = 300,
    drawing_mode=drawing_mode,
    key="canvas",
)

#Do something interesting with the image data
# if canvas_result.image_data is not None:
#     st.image(canvas_result.image_data)
#     st.dataframe(pd.json_normalize(canvas_result.json_data["objects"]))


@st.cache(allow_output_mutation=True)
def load_model():
    #model = tf.keras.models.load_model('saved_encoder/my_encoder')
    #model = load_model('test_encoder.h5',custom_objects={'Sampling':Sampling})
    img_rows, img_cols = 72, 72
    num_channels = 3
    latent_dim = 8

    class Sampling(layers.Layer):
        def call(self, inputs):
            z_mean, z_log_var = inputs
            batch = tf.shape(z_mean)[0]
            dim = tf.shape(z_mean)[1]
            epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
            return z_mean + tf.exp(0.5 * z_log_var) * epsilon

    encoder_inputs = keras.Input(shape=(img_rows, img_cols, num_channels))
    x = layers.Conv2D(16, 3, activation="relu", strides=2, padding="same")(encoder_inputs)
    #x = layers.Conv2D(32, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Conv2D(64, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Conv2D(128, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Flatten()(x)
    x = layers.Dense(20, activation="relu")(x)
    z_mean = layers.Dense(latent_dim, name="z_mean")(x)
    z_log_var = layers.Dense(latent_dim, name="z_log_var")(x)
    z = Sampling()([z_mean, z_log_var])
    encoder = keras.Model(encoder_inputs, [z_mean, z_log_var, z], name="encoder")

    latent_inputs = keras.Input(shape=(latent_dim,))
    x = layers.Dense(9 * 9 * 128, activation="relu")(latent_inputs)
    x = layers.Reshape((9, 9, 128))(x)
    x = layers.Conv2DTranspose(128, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Conv2DTranspose(64, 3, activation="relu", strides=2, padding="same")(x)
    #x = layers.Conv2DTranspose(32, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Conv2DTranspose(16, 3, activation="relu", strides=2, padding="same")(x)
    decoder_outputs = layers.Conv2DTranspose(num_channels, 3, activation="sigmoid", padding="same")(x)
    decoder = keras.Model(latent_inputs, decoder_outputs, name="decoder")


    encoder.load_weights('encoder_truss.h5')
    decoder.load_weights('decoder_truss.h5')

    return encoder, decoder


if canvas_result.image_data is not None:
    input_image = canvas_result.image_data
    # st.dataframe(pd.json_normalize(canvas_result.json_data["objects"]))

    def rgba2rgb( rgba, background=(255,255,255) ):
        row, col, ch = rgba.shape
        if ch == 3:
            return rgba
        assert ch == 4, 'RGBA image has 4 channels.'
        rgb = np.zeros( (row, col, 3), dtype='float32' )
        r, g, b, a = rgba[:,:,0], rgba[:,:,1], rgba[:,:,2], rgba[:,:,3]
        a = np.asarray( a, dtype='float32' ) / 255.0

        R, G, B = background
        rgb[:,:,0] = r * a + (1.0 - a) * R
        rgb[:,:,1] = g * a + (1.0 - a) * G
        rgb[:,:,2] = b * a + (1.0 - a) * B
        return np.asarray( rgb, dtype='uint8' )

    output_image = rgba2rgb(input_image)
    output_resized = resize(output_image, (72, 72))

    img_array = output_resized.reshape(1, output_resized.shape[0], output_resized.shape[1], output_resized.shape[2])
    #st.write('numpy result is', img_array/255)
    # st.write('shape is', img_array.shape)
    encoder,decoder = load_model()
    result,_,_ = encoder.predict(img_array)
    # st.write('Encoder prediction is', result)

    reconstruction = decoder.predict(result)

    reconstruction = reconstruction.reshape(reconstruction.shape[1], reconstruction.shape[2], reconstruction.shape[3])
    # st.write('Decoder results is')
    # st.image(reconstruction, width = 300)








img_file_buffer = st.file_uploader('Upload a PNG image', type='png')
# st.set_option('deprecation.showfileUploaderEncoding', False)

if img_file_buffer is not None:
    image = Image.open(img_file_buffer)
    img_array = np.array(image)
    img_array = img_array.reshape(1, img_array.shape[0], img_array.shape[1], img_array.shape[2])
    #st.write('numpy result is', img_array/255)
    st.write('shape is', img_array.shape)
    encoder,decoder = load_model()
    result,_,_ = encoder.predict(img_array/255)
    st.write('Encoder prediction is', result)

    reconstruction = decoder.predict(result)


    with open("style.css") as f:
        st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)

    reconstruction = reconstruction.reshape(reconstruction.shape[1], reconstruction.shape[2], reconstruction.shape[3])
    # st.write('Decoder results is')
    # st.image(reconstruction, width = 300)


st.components.v1.html(
    """
    <head>
    <meta charset="utf-8">
    <title>Sketch Canvas</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <meta name="viewport" content="width=device-width initial-scale=1">
    <meta name="description" content="Sketch Canvas, an MIT Project">

    <style>
        /* .w3-row-padding img {margin-bottom: 12px}
        #main {margin-left: 170px}
        .w3-p {font-size: 100px}
        @media only screen and (max-width: 600px) {#main {margin-left: 0}} */

        /* #canvas-container {
            border: 2px dashed pink;
        }
        #canvas-box, #gap-box {
            border: orange 2px solid;
        }
        #plot-container {
            border: 2px dashed greenyellow;
        } */


        /* MINE */
        :root {
            --teal-color: rgb(44, 196, 188);
            --nav-height: 70px;
        }


        html,body{
            font-family: 'DM Sans',serif;
            font-size:15px;line-height:1; 
            background-color: #2C2C2C;
            margin:0;
        }
        html{overflow-x:hidden}
        h1{font-size:36px}
        h2{font-size:30px}
        /*h3 menus*/
        h3{font-size:24p; color:white;}
        h4{font-size:20px; color:white}
        h5{font-size:18px; color:white}
        h6{font-size:16px; color:white}
        .loading-cursor {
            cursor: progress;
        }
        #top {position: absolute;top: 0;z-index: 0;}
        #main-container {
            /* background-color:rgb(190, 92, 26); */
            padding-top: 20px;
            margin-top: var(--nav-height);
        }
        #nav {
            background-color: black;
            width: 100%;
            height: var(--nav-height);
            margin: 0;
            padding:0;
            position:fixed;
            top: 0;
            color: white;
            vertical-align: top;
            z-index: 2;
        }
        #nav-left, #nav-right, #nav-middle {
            height: 100%;
            width: 32.5%;
            display: inline-block;
            margin: 0;
            padding: 0;
            vertical-align: middle;
            color: white;

        }
        #nav-middle {
            text-align: center;
            font-weight: 500;
            font-size: 30px;
            margin-top: -25px;
        }
        #nav-right {
            text-align: right;
        }
        #title {
            font-weight: 700;
            font-style: normal;
            font-size: 43px;
            height: 100%;
            display: inline-block;
            margin: 0;
            padding: 12px 20px 0;
        }

        .menu-item{
            /* font-size: 22px; */
            text-decoration: none;
            height: 100%;
            font-size: 23px;
            display: inline-block;
            margin: 0 -2px;
            padding: 0 15px;
            color: white;
        }
        .menu-hover:hover{background-color:#2C2C2C}

        #canvas-container {
            text-align: center;
            margin: 20px 0;
            height: 366px;
        }
        #canvas-box, #gap-box {
            height: 100%;
            display: inline-block;
            margin: 0;
        }
        #gap-box {
            width: 27px;
        }
        #plot-container {
            display: inline-block;
            width: 336px;
            height: 100%;
            margin: 0;
            padding: 0;
            /* position: relative;
            top: -126px; */
        }
        .canvas {
            display: inline-block;
            margin: 0;
            padding: 0;
        }
        #myCanvas {
            background-color: white;
            
        }
        #predCanvas {
            background-color: white;

        }
        .loading-div {
            color: white;
            text-align: center;
            font-style: italic;
            font-size: 30px;
            transition: .3s;
        }
        .invisible {
            display: none;
        }
        #button-box {
            display: block;
            width: 100%;
            height: 30px;
            margin: 0;
        }
        .button, .notbutton {
            background-color: #cccccc;
            border: none;
            /* font-family: 'DM Sans'; */
            color: black;
            text-align: center;
            text-decoration: none;
            width: 168px;
            height: 100%;
            font-size: 18px;
            font-weight: bold;
            margin: -2.5px -2px;
            /* padding: 3px 0; */
            /* border-radius: 2px; */
            /* display: inline-block;
            font-size: 16px;
            margin: 4px 2px;*/
            cursor: pointer; 
        }
        .button:hover{background-color: rgb(128, 128, 128);  }
        .notbutton {
            margin: -2.5px 0;
            cursor: auto; 
        }
        .button3{
        background-color: rgb(155, 155, 155);      
        }
        .button3:hover{background-color: rgb(231, 61, 61);  
        }

        #plot {
            background-color: #5F5F5F;
            margin: 0;
            text-align: center;
            width: 336px;
            display: block;
            top: 0;
        }
        #plot2 {
            background-color: #5F5F5F;
            margin: 0;
            text-align: center;
            width: 332px;
            height: 168px;
            padding-left: 4px;
            display: block;
            position: relative;
        }
        .slider {
            -webkit-appearance: none;
            /* appearance: none; */
            height: 8px;
            width: 135px;
            outline: none;
            border-radius: 4px;
            background-color: #888888;
            /* opacity: 0.7; */
            /* -webkit-transition: .2s; */
            /* transition: opacity .2s; */
            transform: rotate(270deg);
            padding: none;
            margin: 72px -51.4px 0;
            vertical-align: middle; 
            /* color: hotpink; */
        }
        #plot2-text{
            /* display: block; */
            width: 332px;
            padding-left: 4px;
            /* background-color: turquoise; */
            /* margin-bottom: -500px; */
            /* vertical-align: bottom; */
            font-size: 12px;
            position: absolute;
            bottom: 0;
            left: 0;
            
        }
        .slider-text {
            color: white;
            height: 100%;
            vertical-align: baseline;
            display: inline-block;
            /* background-color: yellowgreen; */
            width: 21px;
            margin: 0 6px 5px;
        }
        #images-container {
            background-color: #3A3A3A;
            margin-top: 25px;
            width: 100%;
            /* height: 300px; */
            text-align: center;
            padding: 25px 0;
        }
        .saved {
            background-color: white;
            height: 200px;
            width: 200px;
            margin: 7px;


        }


        /* MAIN TEXT SECTION */
        #main-text {
            /* background-color: rgb(63, 92, 20); */
            padding: 10px 100px;
            color: white;
        }
























        .sidebar {
            height:100%;
            width:180px;
            background-color:black;
            position:fixed!important;
            z-index:1;
            overflow:auto;
            text-align: center;
        }
        .canvas-sidebar {
            max-height: 750px;
            margin-top: 0px;
            margin-left:auto;
            margin-right:auto;
            padding-top:0px!important;
            padding-bottom:0px!important;
            padding-left: 0px;
            padding-right: 0px;
            width: 825px;
            min-height:100px;
            background-color: rgb(200, 200, 200);
            /* position:relative;bottom:456px;left:700px; */
        }


        #main-wrapper {
            width: 100%;
            height: 600px;
            margin: 0 auto;
            text-align: center;
            /* border: 2px solid pink; */
            padding-top: 32px;
        }
        .main-box {
            width: 50%;
            height: 550px;
            display: inline-block;
            margin: -2px;
            padding: 20px 0px;
        }

        #box-left {
            /* background: rgb(139, 187, 209); */
        }
        #box-right {
            /* background: rgb(201, 134, 159) */
        }

        #interpolation-box {
            float: left;
            height: 470px;
            width: 632px;
            background-color: rgb(185, 185, 185);

        }

        .interpolation-img {
            height: 77.5px;
            width: 102.6px;
            margin:0px -2px 0px -2px;
            /* border: blue solid 1px; */
        }

        .sketch-img {
            /* background-color: rgba(0,0,0,0.12); */
        }

        .predict-img {
            /* height: 407.5px;
            width: 600.6px; */
            /* border: 2px solid rgb(218, 34, 141); */
            background-color: rgba(255,255,255,.5);
        }

        img {
            border: 0;
        }

        .overlay-box {
            text-align: center;
            height: 100vh;
            margin: 0 auto;
            width: 100%;
            /* border: green 5px solid; */
            position: absolute;
            top: 0px;
            left: 0px;
        }
        .overlay {
            display: inline-block;
            /* border: rgb(248, 238, 91) 1px solid; */


        }
        #enlarged-img {
            vertical-align: middle;
        }


        .text-grey {
            color: rgb(184, 17, 17);
        }
        /* The slider itself */

        input {
            padding: none;
            margin: 0px -100px;

        }
        .slidecontainer {
            margin: 20px 0px;
            width: 100%;
            height: 300px;
            /* background-color: pink; */
        }
    </style>

    <link href="https://fonts.googleapis.com/css?family=DM+Sans:Thin,Extra-Light,Light,Regular,Medium,Semibold,Bold" rel="stylesheet" >
    <link rel="blank-img" href="https://i.ya-webdesign.com/images/blank-png-1.png">
    </head>
    

    <!-- NAVIGATION BAR -->
    <navigation id="nav">
    <div id="nav-left">
        <p id="title">Sketch Canvas</p> 
    </div> 
    <div id="nav-middle">
        <!-- <a href="interpolation.html" class="menu-item menu-hover">&lt;</a> -->
        <p>&lt; Prediction &gt;</p>
        <!-- <a href="interpolation.html" class="menu-item menu-hover">&gt;</a> -->
        
    </div> 
    <div id="nav-right">
        <a href="#top" class="menu-item menu-hover">
        <p>Home</p>
        </a>
        <a href="#about" class="menu-item menu-hover">
        <p>About</p>
        </a>
        <a href="#contact" class="menu-item menu-hover">
        <p>Contact</p>
        </a>
    </div> 
    </navigation>


    <div id="top"></div>
    <!-- MAIN CONTENT -->
    <body id="home" onload="init()" class="loading-cursor">
    <div id="main-container">
        <div id="loading-div" class="loading-div">
        <p>Waiting for models to load...</p>
        </div>


        <div id="canvas-container">
        <div id="canvas-box">
            <canvas id="myCanvas" class="canvas" width="336" height="336"></canvas>
            <div id="button-box">
            <!-- <button class="button" id="predictBtn" onclick="BOTHpredict()">Predict</button> -->
            <button class="button" id="predictBtn" onclick="randomSliders()">Predict</button>
            <button class="button" id="clearBtn" onclick="erase()">Clear</button>
            <!-- <button class="button" id="addBtn" onclick="addSketch()">Add</button> -->
            <!-- <button class="button button3" id="clearallBtn" onclick="eraseAll()">Clear All</button> -->
            <!-- <button class="button" id="saveBtn" onclick="savePNG()">download png</button> -->
            <!-- <button class="button" id="saveBtn" onclick="saveRel()">download relVector</button> -->
            </div>
        </div>
        
        <div id="gap-box">
            <p style="color:white; font-size: 33px;">
            <!-- ⮕ <br><br><br><br><br>⮕ <br><br><br><br> -->
            </p>
        </div>
        
        <div id="plot-container">   
            <!-- PARALLEL PLOT COORDINATES -->    
            <!-- <div id="plot"></div>
            
            <style>
            .axis {
                opacity: 0.4;
            }
            .axis:hover {
                opacity: 1;
            }
            </style> -->
            <!-- INTERACTIVE PARALLEL PLOT COORDINATES -->      
            <div id="plot2">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider1">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider2">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider3">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider4">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider5">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider6">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider7">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider8">
            <input type="range" min="-2.000" max="2.000" value="0.000" step='.01' class="slider" id="slider9">
            <div id="plot2-text">
                <p id="sliderValue1" class="slider-text">0</p>
                <p id="sliderValue2" class="slider-text">0</p>
                <p id="sliderValue3" class="slider-text">0</p>
                <p id="sliderValue4" class="slider-text">0</p>
                <p id="sliderValue5" class="slider-text">0</p>
                <p id="sliderValue6" class="slider-text">0</p>
                <p id="sliderValue7" class="slider-text">0</p>
                <p id="sliderValue8" class="slider-text">0</p>
                <p id="sliderValue9" class="slider-text">0</p>
            </div>           
            </div>
            <div id="button-box">
            <button class="button" id="clearBtn" style="width: 168px;" onclick="sliderPredict()">Predict</button>
            <button class="button" id="predictBtn" style="width: 168px;" onclick="resetSliders()">Reset</button>
            </div>
        </div>
        
        <div id="gap-box">
        </div>

        <div id="canvas-box">
            <canvas id="predCanvas" class="canvas" width="336" height="336"></canvas>
            
            <div id="button-box">
            <p class="notbutton" style="width: 100%;">
                <span style="color:black; font-weight: 600;">CNN: </span>
                <span id="prediction" style="color:black; font-weight: 500; font-size: 20px;"> </span>
            </p>
            </div>
        </div>
    
        <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@1.5.2/dist/tf.min.js"></script>
        <script src="/js/jquery-3.5.1.min.js"></script>
        <script>
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
    var encoder;
    var decoder;
    var model;

    // class Functional extends tf.LayersModel("0831encoder2/encoder.json").Functional {
    //     static className = 'MyCustomLayer';
    
    //     constructor(config) {
    //       super(config);
    //     }
    //  }
    //  tf.serialization.registerClass(Functional);
    // const mdl = await tf.loadModel("0831encoder2/encoder.json");
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


    // var teste = [[-0.03005229 , 0.02860937 , 0.06479363 ,-0.00289215 ,-0.0616348 ,  0.02338343,
    //     -0.03934336 ,-0.08602308 , 0.18989778 ]]

        
    // predicts performance (integer)    
    function CNNpredict() {
        
        $("body").addClass("loading-cursor");
        resetResults();
        var pred = new Image();
        pred.onload = function() {
            ctx.drawImage(pred, 0, 0, 224, 224);
            data = ctx.getImageData(0, 0, 224, 224).data;
            document.getElementById("predict-img").src = canvas.toDataURL();
            var input = [];
            for(var i = 0; i < data.length; i += 4) {
                input.push(data[i + 0] / 255);
                input.push(data[i + 1] / 255);
                input.push(data[i + 2] / 255);
                // console.log("0: "+data[i + 0]);
                // console.log("1: "+data[i + 1]);
                // console.log("2: "+data[i + 2]);
                // console.log("3: "+data[i + 3]);
            }
            // console.log("onload inp: "+input);
            // console.log("onload len: "+input.length);
            CNNpredict2(input);
        };
        pred.src = canvas.toDataURL('image/png');
    }   


    function CNNpredict2(input) {
        // console.log("ID: "+ count);

        // console.log("predict inp: "+input);
        reshaped_input = tf.reshape(input, [1,224,224,3]);
        // console.log("reshape inp: "+reshaped_input);
        
        var outPred = model.predict(reshaped_input);

        var tensorData = outPred.dataSync();
        // console.log("tensor data "+tensorData)
        var predictDisplay = tensorData[0].toFixed(2);

        var output = document.getElementById("prediction");
        output.innerHTML = predictDisplay;
        
        erase();
        $("body").removeClass("loading-cursor");
    }



    // makes prediction from added Sketch
    function VAEpredict() { 
        resetResults();
        var pred = new Image();
        pred.onload = function() {
            ctx.drawImage(pred, 0, 0, 224, 224);
            data = ctx.getImageData(0, 0, 224, 224).data;
            document.getElementById("predict-img").src = canvas.toDataURL();
            var input = [];
            for(var i = 0; i < data.length; i += 4) {
                input.push(data[i + 0] / 255);
                input.push(data[i + 1] / 255);
                input.push(data[i + 2] / 255);
            }
            // add input to this when encoder works
            VAEpredict2();
        };
        pred.src = canvas.toDataURL('image/png');
    }   

    function VAEpredict2(input) {
        input = input || 0;
        // teste = tf.tensor([[-0.03005229 , 0.02860937 , 0.06479363 ,-0.00289215 ,-0.0616348 ,  0.02338343,
        //     -0.03934336 ,-0.08602308 , 0.18989778 ]], [1,9])
        
        teste = [-0.36047292,  0.80789363,  0.48131144, -1.02407718,  2.40988064, -0.88771844,
            0.247859,   -0.55779624, -0.47024077];

        teste = [-2.08542681, -0.47914732,  1.53509092, -0.97853041, -1.57959282, -1.188151, -0.55057764, -1.55801702, -0.54232752];
        
        if (input != 0){
            teste = input;
            console.log('inputed this: '+ teste);
        }
        teste = tf.tensor([teste], [1,9]);
        
        teste.reshape = [1,9];

        var testd = decoder.predict(teste);
        // var output = document.getElementById("predictionVAE");

        // output.innerHTML = testd;
        console.log(testd.shape);
        
        TensorToImage(testd);
        erase();
    }

    function TensorToImage(tensor) {
        var values = tensor.dataSync();
        var rgbdata = Array.from(values);
        rgbdata_reshaped = reshapeArray(rgbdata, 72, 3);
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
        VAEpredict2(sliderArray);
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

        </script>
        </div>
        
        <div id="images-container">
        <img id="saved0" class="saved">
        <img id="saved1" class="saved">
        <img id="saved2" class="saved">
        <img id="saved3" class="saved">
        <img id="saved4" class="saved">
        <img id="saved5" class="saved">
        <img id="saved6" class="saved">
        <img id="saved7" class="saved">
        <img id="saved8" class="saved">
        <img id="saved9" class="saved">
        <br>
        <div style="margin-top:20px;">
            <button class="button" id="saveBtn" onclick="savePNG()">Download Selected</button>
        </div>
        </div>

    <img style="display: none" src="https://i.ya-webdesign.com/images/blank-png-1.png" width="224" height="224" id="predict-img" class="predict-img sketch-img"></img>


    </div>

    <div id="main-text">
        <!-- About Section -->
        <div class="w3-content w3-justify w3-text-grey w3-padding-64" id="about">
        <h2 class="w3-text-light-grey">What is this project about?</h2>
        <hr style="width:200px" class="w3-opacity">
        <p>Some text about this project. Lorem ipsum consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip
            ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum consectetur
            adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
        </p>

        <button class="w3-button w3-light-grey w3-padding-large w3-section">
            <i class="fa fa-download"></i> Download Research Paper
        </button>

        <!-- Testimonials -->
        <h3 class="w3-padding-24 w3-text-light-grey">Team</h3>
        <img src="" alt="Avatar" class="w3-left w3-circle w3-margin-right" style="width:80px">
        <p><span class="w3-large w3-margin-right">Bryan Ong.</span> Masters Researcher.</p>
        <p>I am a....</p><br>

        <img src="" alt="Avatar" class="w3-left w3-circle w3-margin-right" style="width:80px">
        <p><span class="w3-large w3-margin-right">Caitlin Mueller.</span> Advisor.</p>
        <p>I am a...</p>
        <!-- End About Section -->
        </div>


        <!-- Contact Section -->
        <div class="w3-padding-64 w3-content w3-text-grey" id="contact">
        <h2 class="w3-text-light-grey">Contact Us</h2>
        <hr style="width:200px" class="w3-opacity">

        <div class="w3-section">
            <p><i class="fa fa-map-marker fa-fw w3-text-white w3-xxlarge w3-margin-right"></i> Massachusetts, US</p>
            <p><i class="fa fa-phone fa-fw w3-text-white w3-xxlarge w3-margin-right"></i> Phone: +00 151515</p>
            <p><i class="fa fa-envelope fa-fw w3-text-white w3-xxlarge w3-margin-right"> </i> Email: mail@mail.com</p>
        </div><br>
        <p>Lets get in touch. Send me a message:</p>

        <form action="/action_page.php" target="_blank">
            <p><input class="w3-input w3-padding-16" type="text" placeholder="Name" required name="Name"></p>
            <p><input class="w3-input w3-padding-16" type="text" placeholder="Email" required name="Email"></p>
            <p><input class="w3-input w3-padding-16" type="text" placeholder="Subject" required name="Subject"></p>
            <p><input class="w3-input w3-padding-16" type="text" placeholder="Message" required name="Message"></p>
            <p>
            <button class="w3-button w3-light-grey w3-padding-large" type="submit">
                <i class="fa fa-paper-plane"></i> SEND MESSAGE
            </button>
            </p>
        </form>
        <!-- End Contact Section -->
        </div>

        <!-- Footer -->
        <footer class="w3-content w3-padding-64 w3-text-grey w3-xlarge">
        <i class="fa fa-facebook-official w3-hover-opacity"></i>
        <i class="fa fa-instagram w3-hover-opacity"></i>
        <i class="fa fa-snapchat w3-hover-opacity"></i>
        <i class="fa fa-pinterest-p w3-hover-opacity"></i>
        <i class="fa fa-twitter w3-hover-opacity"></i>
        <i class="fa fa-linkedin w3-hover-opacity"></i>
        <!-- End footer -->
        </footer>

    <!-- END MAIN TEXT -->
    </div>
    
    <!-- Load d3.js -->
    <script src="https://d3js.org/d3.v4.js"></script>
    <script src="/js/parallel.js"></script>

    </body>
        
    <script>
        console.log("script b rungin");
    </script>
    """,
    width=1200, 
    height=1500, 
    scrolling=True)
