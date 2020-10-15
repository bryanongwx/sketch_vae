def load_model():
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

    model.load_weights('model_truss.h5')

    return model
