'''This script demonstrates how to build a variational autoencoder with Keras.

Reference: "Auto-Encoding Variational Bayes" https://arxiv.org/abs/1312.6114
'''
import numpy as np
import matplotlib.pyplot as plt

from keras.layers import Input, Dense, Lambda
from keras.models import Model
from keras import backend as K
from keras import objectives
from keras.datasets import mnist
from keras.datasets import imdb
from keras.preprocessing import sequence

batch_size = 16
original_dim = 784
latent_dim = 2
intermediate_dim = 128
epsilon_std = 0.01
nb_epoch = 100

x = Input(batch_shape=(batch_size, original_dim))
h = Dense(intermediate_dim, activation='relu')(x)
z_mean = Dense(latent_dim)(h)
z_log_std = Dense(latent_dim)(h)

def sampling(args):
    z_mean, z_log_std = args
    epsilon = K.random_normal(shape=(batch_size, latent_dim),
                              mean=0., std=epsilon_std)
    return z_mean + K.exp(z_log_std) * epsilon

# note that "output_shape" isn't necessary with the TensorFlow backend
# so you could write `Lambda(sampling)([z_mean, z_log_std])`
z = Lambda(sampling, output_shape=(latent_dim,))([z_mean, z_log_std])

# we instantiate these layers separately so as to reuse them later
decoder_h = Dense(intermediate_dim, activation='relu')
decoder_mean = Dense(original_dim, activation='sigmoid')
h_decoded = decoder_h(z)
x_decoded_mean = decoder_mean(h_decoded)

def vae_loss(x, x_decoded_mean):
    xent_loss = objectives.binary_crossentropy(x, x_decoded_mean)
    kl_loss = - 0.5 * K.mean(1 + z_log_std - K.square(z_mean) - K.exp(z_log_std), axis=-1)
    return xent_loss + kl_loss

vae = Model(x, x_decoded_mean)
vae.compile(optimizer='rmsprop', loss=vae_loss)

# train the VAE on MNIST digits
(x_train, y_train), (x_test, y_test) = mnist.load_data()

new_size_train = 20000
new_size_test = 4000
x_train = x_train[0:new_size_train].astype('float32') / 255.
x_test = x_test[0:new_size_test].astype('float32') / 255.

y_train = y_train[0:new_size_train]
y_test = y_test[0:new_size_test]

x_train = x_train.reshape((len(x_train), np.prod(x_train.shape[1:])))
x_test = x_test.reshape((len(x_test), np.prod(x_test.shape[1:])))

print(x_train.shape, y_train.shape)
print(x_test.shape, y_test.shape)

# #########################################################################################################
# # [IOHAVOC] attempts to repurpose the mnist VAE code to IMDB. It became quickly clear that
# # we need to use a LSTM instead of just a Dense
# (x_train_imdb, y_train_imdb), (x_test_imdb, y_test_imdb) = imdb.load_data(nb_words=5000, maxlen=None)
#
# # print('Pad sequences (samples x time)')
# sentence_maxlen = 784
# x_train_imdb = sequence.pad_sequences(x_train_imdb, maxlen=sentence_maxlen)
# x_test_imdb  = sequence.pad_sequences(x_test_imdb, maxlen=sentence_maxlen)
#
# print(x_train_imdb.shape, y_train_imdb.shape)
# print(x_test_imdb.shape, y_test_imdb.shape)
#
# x_train, y_train = x_train_imdb.astype('float32') / 1., y_train_imdb.astype('float32') / 1.
# x_test, y_test = x_test_imdb.astype('float32') / 1., y_test_imdb.astype('float32') / 1.
#
# new_size_train = 20000
# new_size_test = 4000
# x_train = x_train[0:new_size_train].astype('float32') / 255.
# x_test = x_test[0:new_size_test].astype('float32') / 255.
#
# y_train = y_train[0:new_size_train]
# y_test = y_test[0:new_size_test]
#
# # print(x_train.shape, y_train.shape)
# # print(x_test.shape, y_test.shape)
#
# #########################################################################################################

vae.summary()
vae.fit(x_train, x_train,
        shuffle=True,
        nb_epoch=nb_epoch,
        batch_size=batch_size,
        validation_data=(x_test, x_test))

# build a model to project inputs on the latent space
encoder = Model(x, z_mean)

# display a 2D plot of the digit classes in the latent space
x_test_encoded = encoder.predict(x_test, batch_size=batch_size)
plt.figure(figsize=(6, 6))
plt.scatter(x_test_encoded[:, 0], x_test_encoded[:, 1], c=y_test)
plt.colorbar()
plt.show()

# build a digit generator that can sample from the learned distribution
decoder_input = Input(shape=(latent_dim,))
_h_decoded = decoder_h(decoder_input)
_x_decoded_mean = decoder_mean(_h_decoded)
generator = Model(decoder_input, _x_decoded_mean)

# display a 2D manifold of the digits
n = 15  # figure with 15x15 digits
digit_size = 28
figure = np.zeros((digit_size * n, digit_size * n))

# we will sample n points within [-15, 15] standard deviations
grid_x = np.linspace(-15, 15, n)
grid_y = np.linspace(-15, 15, n)

for i, yi in enumerate(grid_x):
    for j, xi in enumerate(grid_y):
        z_sample = np.array([[xi, yi]]) * epsilon_std
        x_decoded = generator.predict(z_sample)
        digit = x_decoded[0].reshape(digit_size, digit_size)
        figure[i * digit_size: (i + 1) * digit_size,
               j * digit_size: (j + 1) * digit_size] = digit

plt.figure(figsize=(10, 10))
plt.imshow(figure)
plt.show()
