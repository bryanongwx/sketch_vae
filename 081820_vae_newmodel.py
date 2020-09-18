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


st.title('VAE Sketch Canvas')

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
    st.dataframe(pd.json_normalize(canvas_result.json_data["objects"]))

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
    st.write('shape is', img_array.shape)
    encoder,decoder = load_model()
    result,_,_ = encoder.predict(img_array)
    st.write('Encoder prediction is', result)

    reconstruction = decoder.predict(result)

    reconstruction = reconstruction.reshape(reconstruction.shape[1], reconstruction.shape[2], reconstruction.shape[3])
    st.write('Decoder results is')
    st.image(reconstruction, width = 300)








img_file_buffer = st.file_uploader('Upload a PNG image', type='png')
st.set_option('deprecation.showfileUploaderEncoding', False)

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
    st.write('Decoder results is')
    st.image(reconstruction, width = 300)
