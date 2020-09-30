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
from skimage.transform import resize
from functools import lru_cache

try:
    import simplejson as json
except (ImportError,):
    import json


url = 0
def create_app():
    app = Flask(__name__)
    return app
app = create_app()
# app.config['SERVER_NAME']='myapp.dev:5000'

@app.route('/weights')
def get_weights():
    with app.test_request_context():
        encoder_weights = redirect(url_for('static', filename='h5/encoder_truss.h5'))
        # decoder_weights = redirect(url_for('static', filename='h5/decoder_truss.h5'))
    return encoder_weights


# with app.app_context():
#     # app.create_all()
#     url = url_for('static', filename='encoder_truss.h5', _external=True)

# with app.test_request_context('localhost:5432'):
#     url = url_for('static', filename='encoder_truss.h5', _external=True)
# file1 = open('/static/h5/encoder_truss.h5')
# app.config.update(
#     SERVER_NAME='myapp.dev:5000'
# )
# with app.test_request_context():
#     url = url_for('static', filename='encoder_truss.h5')


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

    encoder.load_weights("static/h5/encoder_truss.h5")
    decoder.load_weights("static/h5/decoder_truss.h5")
    print(" = = =  = FINISHED LOADING MODELS AND WEIGHTS !")

    return encoder, decoder



@app.route("/")
def index():
    return render_template("index.html")  
    # app.send_static_file('index.html')
  

@app.route('/VAEpredict/', methods=['GET','POST'])
def predict():
    JSinp = request.get_json()

    lst = json.loads(JSinp["inp"])
    output_image = np.asarray(lst, dtype='uint8')
    output_resized = resize(output_image, (72, 72, 3))

    img_array = output_resized.reshape(1, output_resized.shape[0], output_resized.shape[1], output_resized.shape[2])
    result,_,_ = encoder.predict(img_array)
    reconstruction = decoder.predict(result)
    reconstruction = reconstruction.reshape(reconstruction.shape[1], reconstruction.shape[2], reconstruction.shape[3])
    reconstruction = reconstruction.tolist()

    return jsonify({"result": reconstruction})


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))




encoder,decoder = load_model()
if __name__ == '__main__':
    app.run(use_reloader=True, debug=True)
