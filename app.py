from flask import Flask, render_template, request, jsonify, url_for, redirect, send_from_directory
import jinja2 as jinja
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import tensorflow.keras.backend as K
from tensorflow.keras.models import model_from_json
from tensorflow.keras.models import load_model
from tensorflow.keras import layers
import matplotlib.pyplot as plt
from matplotlib import cm
from PIL import Image
import numpy as np
from skimage.transform import resize, rescale
from functools import lru_cache
from scipy.interpolate import griddata


try:
    import simplejson as json
except (ImportError,):
    import json

encoder_link = "static/h5/encoder_curve.h5"
decoder_link = "static/h5/decoder_curve.h5"   
model_link = "static/h5/model_truss.h5"
slider_model_link = "static/h5/model.h5"


def create_app():
    app = Flask(__name__)
    return app
app = create_app()


@lru_cache()
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

    encoder.load_weights(encoder_link)
    decoder.load_weights(decoder_link)
    print(" = = = FINISHED LOADING VAE MODELS AND WEIGHTS = = =")

    cnn_model = load_CNN_model()

    slider_cnn_model = load_slider_CNN_model()
    # cnn_model = load_vector_CNN_model()

    return encoder, decoder, cnn_model, slider_cnn_model

def load_CNN_model():
    #model = tf.keras.models.load_model('saved_encoder/my_encoder')
    #model = load_model('test_encoder.h5',custom_objects={'Sampling':Sampling})
    img_rows, img_cols = 72, 72
    num_channels = 3

    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(32, (3,3), padding='same', activation=tf.nn.relu,
                               input_shape=(72, 72, 3)),
        tf.keras.layers.MaxPooling2D((2, 2), strides=2),

        tf.keras.layers.Conv2D(64, (3,3), padding='same', activation=tf.nn.relu),
        tf.keras.layers.MaxPooling2D((2, 2), strides=2),

        tf.keras.layers.Conv2D(128, (3,3), padding='same', activation=tf.nn.relu),
        tf.keras.layers.MaxPooling2D((2, 2), strides=2),

        tf.keras.layers.Flatten(),

        tf.keras.layers.Dense(128, activation=tf.nn.relu),

        tf.keras.layers.Dense(64, activation=tf.nn.relu),

        tf.keras.layers.Dense(32, activation=tf.nn.relu),

        tf.keras.layers.Dense(1, activation = 'linear')
    ])

    model.load_weights(model_link)
    print(" = = = FINISHED LOADING CNN MODEL WEIGHTS = = =")
    return model


def load_slider_CNN_model():

    # train_data = 8
    # train_data = np.asarray(train_data, dtype='uint8')
    # train_data = train_data.reshape(8)
 
    train_data_shape = 8

    img_rows, img_cols = 72, 72
    num_channels = 3

    model = tf.keras.Sequential([
                             
    tf.keras.layers.Dense(32, activation=tf.nn.relu, 
                       input_shape=(8,)),
    tf.keras.layers.Dense(32, activation=tf.nn.relu),
    tf.keras.layers.Dense(32, activation=tf.nn.relu),
    tf.keras.layers.Dense(1, activation = 'linear')
    
    ])

    model.load_weights(slider_model_link)
    print(" = = = FINISHED LOADING CNN MODEL WEIGHTS = = =")
    return model


@app.route("/")
def index():
    return render_template("index.html")
      

@app.route('/VAEencoder', methods=['GET','POST'])
def VAEencoder():
    JSinput = request.get_json()
    lst = json.loads(JSinput["input"])
    # print("list inputssss: \n", lst[0:200])
    # print("list input len: \n", len(lst))
    
    output_image = np.asarray(lst, dtype='uint8')
    output_image = output_image.reshape(360,360,3)
 
    output_resized = resize(output_image, (72, 72))

    img_array = output_resized.reshape(1, 72, 72, 3)
    # print("IMG ARRAY: ", img_array)
    enc_output,_,_ = encoder.predict(img_array)
    print("encoder out shape:",enc_output.shape)

    result = VAEdecoder(enc_output)
    return result

@app.route('/VAEdecoderHelper', methods=['GET','POST'])
def VAEdecoderHelper():
    JSinput = request.get_json()
    lst = [json.loads(JSinput["input"])]
    print("lst:",lst)

    user_vector = np.asarray(lst)
    print("uservec:",user_vector)
    result = VAEdecoder(user_vector)
    return result


def VAEdecoder(vector):
    print("ENC OUT/DEC INP: ",vector)
    vector_list = vector.tolist()

    reconstruction = decoder.predict(vector)
    reconstruction = reconstruction.reshape(reconstruction.shape[1], reconstruction.shape[2], reconstruction.shape[3])
    reconstruction = reconstruction.tolist()

    return jsonify({"result": reconstruction, "vector": vector_list})


@app.route('/CNNpredict', methods=['GET','POST'])
def CNNpredict():
    print("CNN predict: ")
    JSinput = request.get_json()
    lst = json.loads(JSinput["input"])
    
    output_image = np.asarray(lst, dtype='uint8')
    output_image = output_image.reshape(360,360,3)
    output_resized = resize(output_image, (72, 72))
    output_image = output_resized.reshape(1,72,72,3)


    prediction = cnn_model.predict(output_image)
    prediction = prediction[0][0]
    prediction = float(prediction)
    print("prediction 0 0: ",prediction)

    # // var tensorData = outPred.dataSync();
    # // // console.log("tensor data "+tensorData)
    # // var predictDisplay = tensorData[0].toFixed(2);

    # vector_list = vector.tolist()

    return jsonify({"result": prediction})

@app.route('/CNNpredictVector', methods=['GET','POST'])
def CNNpredictVector():
    JSinput = request.get_json()
    vector = json.loads(JSinput["input"])
    print("vector json: ",vector)

    
    vector = np.asarray(vector, dtype='uint8')
    vector = vector.reshape(1,8)
    print("vector json: ",vector)

    prediction = slider_cnn_model.predict(vector)
    print("prediction: ",prediction)
    prediction = prediction[0][0]
    prediction = float(prediction)
    print("prediction 0 0: ",prediction)


    return jsonify({"result": prediction})

     

@app.route('/interpolation', methods=['GET','POST'])
def interpolation():
    img_width = 72
    img_height = 72
    num_channels = 3
    
    JSinput = request.get_json()
    input1 = json.loads(JSinput["input1"])
    input2 = json.loads(JSinput["input2"])
    num_of_int = json.loads(JSinput["number"])
    print("latent vector: ",input1)

    output_image1 = np.asarray(input1)
    print("nparray: ",output_image1)
    output_image2 = np.asarray(input2)
    
    shape1 = 2
    shape2 = 8
    
    # data = np.zeros([shape1,shape2])
    data = [output_image1,output_image2]

    
    start_int = output_image1
    end_int = output_image2
    num_samples = num_of_int
    dim = shape2 # data doesnt have shape since its transfered from js
    
    # Initialize grid space depending on number of latent space vectors and number of intended samples
    grid_space = np.zeros([dim, num_samples])
    print("grid_space")
    print(grid_space)
    for i in range(dim):
        print("shp1 ",start_int.shape)
        print("shp2 ",end_int.shape)
        grid_space[i] = np.linspace(start_int[i], end_int[i], num=num_samples)
    print("GRID SPACE:\n",grid_space)

    # Plot results
    all_ints = []
    for i in range(num_samples):
        img = np.array([grid_space[:,i]])
        print("img: ", img)
        img_int = decoder.predict(img)
        int_dec = img_int.reshape(img_width, img_height, num_channels)
        int_dec = int_dec.tolist()
        all_ints.append(int_dec)
        
    return jsonify({"int_list": all_ints})



@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))




encoder, decoder, cnn_model, slider_cnn_model = load_model()
if __name__ == '__main__':
    app.run(use_reloader=False, debug=True)
