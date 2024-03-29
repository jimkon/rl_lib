import numpy as np
import tensorflow as tf


class RBFNet:
    def __init__(self, samplers=None, constant_samplers=True, constant_gammas=True, gamma_scaler=0.1):
        self.samplers = samplers
        self.samplers_num = -1
        self.constant_samplers = constant_samplers
        self.constant_gammas = constant_gammas
        self.gamma_scaler = gamma_scaler
        self.initialized = False

    def create_net(self, X_shape, y_shape):
        # tf.compat.v1.reset_default_graph()

        self.input_dimensions = X_shape
        self.output_dimensions = y_shape

        if self.samplers is not None:
            # if samplers parameter is set
            if isinstance(self.samplers, int):
                # if samplers parameter is integer
                if self.samplers == -1:
                    self.samplers_num = self.input_dimensions
                else:
                    self.samplers_num = self.samplers

                self.samplers = np.random.random((self.samplers_num, self.input_dimensions)) * 2 - 1
            else:
                # if samplers parameter is array
                self.samplers = np.array(self.samplers)
                self.samplers_num = self.samplers.shape[0]
        else:
            self.samplers_num = self.input_dimensions
            self.samplers = np.random.random((self.samplers_num, self.input_dimensions)) * 2 - 1

        assert self.output_dimensions == 1, 'Not tested for more than 1 output dimensions'
        assert self.input_dimensions == self.samplers.shape[1], 'Samplers dimensions don\'t match with input dimensions'

        print('RBF net init in({}) samplers({}) out({})'.format(self.input_dimensions, self.samplers_num,
                                                                self.output_dimensions))

        assert self.samplers_num != 1, 'samplers must be a positive integer. took {} instead'.format(self.samplers)

        self.input_shape = tuple([self.input_dimensions])
        self.output_shape = tuple([self.output_dimensions])

        # variables
        if self.constant_samplers:
            self.centers = tf.constant(self.samplers)
        else:
            self.centers = tf.Variable(self.samplers)

        gammas = np.random.normal(size=(self.samplers_num), loc=.2, scale=self.gamma_scaler)
        if self.constant_gammas:
            self.gammas = tf.constant(gammas)
        else:
            self.gammas = tf.Variable(gammas)

        self.weights = tf.Variable(
                np.random.random((self.samplers_num, self.output_dimensions)) * (1 / self.samplers_num))

        # placeholders
        self.x = tf.compat.v1.placeholder(tf.float64, (self.input_dimensions))
        self.y = tf.compat.v1.placeholder(tf.float64, (self.output_dimensions))

        # internal computations
        self.dists = tf.sqrt(tf.reduce_sum(tf.square(self.x - self.centers), axis=1))
        self.mul_gamma = tf.reshape(tf.multiply(self.dists, self.gammas), shape=(1, self.samplers_num))
        self.output = tf.matmul(self.mul_gamma, self.weights)

        # training computations
        cost = tf.abs(self.output - self.y)
        self.train = tf.compat.v1.train.GradientDescentOptimizer(10e-3).minimize(cost)

        # init
        self.init_op = tf.compat.v1.global_variables_initializer()

        self.sess = tf.compat.v1.Session()
        self.sess.run(self.init_op)

        self.initialized = True

    def predict(self, X):
        assert self.initialized, 'must call fit before predict'
        assert X.shape == self.input_shape, 'X.shape = {}, it should be {}'.format(X.shape, self.input_shape)

        res = self.sess.run(self.output, feed_dict={
                self.x: X
        })[0]
        assert res.shape == self.output_shape, 'predict.shape = {}, it should be {}'.format(res.shape,
                                                                                                   self.output_shape)

        return res

    def partial_fit(self, X, y):
        if not self.initialized:
            self.create_net(X.shape[0], y.shape[0])

        assert X.shape == self.input_shape, 'X.shape = {}, it should be {}'.format(X.shape, self.input_shape)
        assert y.shape == self.output_shape, 'y.shape = {}, it should be {}'.format(y.shape, self.output_shape)

        self.sess.run(self.train, feed_dict={
                self.x: X,
                self.y: y
        })

    def info(self):
        centers = self.sess.run(self.centers)
        gammas = self.sess.run(self.gammas)
        weights = self.sess.run(self.weights)

        return centers, gammas, weights


def nn_layer(x, size, activation=tf.nn.relu, drop_out=0.3, use_bias=True, return_vars=True):
    # x*W+b
    if drop_out:
        x = tf.nn.dropout(x, rate=drop_out)

    W = tf.Variable(np.random.random((x.shape[1], size)) * (1. / (int(x.shape[1]) * size)))

    if use_bias:
        b = tf.Variable(np.random.random((1, size)) * (1. / size))
        line = tf.matmul(x, W) + b
    else:
        b = None
        line = tf.matmul(x, W)

    if activation is None:
        y = line
    else:
        y = activation(line)

    if return_vars:
        return y, W, b
    else:
        return y


class FullyConnectedDNN:

    def __init__(self, input_dims, output_dims, hidden_layers=[200, 100], activations=[tf.nn.relu, tf.nn.relu], use_biases=[True, True],
                 drop_out=.3, output_activation=None, output_use_bias=False, lr=1e-2):

        self.input_dims = input_dims
        self.output_dims = output_dims

        self.input_shape = tuple([self.input_dims])
        self.output_shape = tuple([self.output_dims])

        layers = np.append(hidden_layers, output_dims).astype(np.int) if hidden_layers is not None else np.array([output_dims])
        all_activations = activations.copy() if activations is not None else []
        all_activations.append(output_activation)
        all_use_biases = use_biases.copy() if use_biases is not None else []
        all_use_biases.append(output_use_bias)

        print("NN: layers:{}, activations:{}".format(layers, all_activations, all_use_biases))

        self.ys, self.Ws, self.bs = [], [], []

        # tf.compat.v1.reset_default_graph()
        self.x = tf.compat.v1.placeholder(tf.float64, shape=(None, input_dims))
        x = self.x
        for i, layer in enumerate(layers):
            y, W, b = nn_layer(x, layer, all_activations[i], drop_out=drop_out if i > 0 else 0., use_bias=all_use_biases[i], return_vars=True)

            self.ys.append(y)
            self.Ws.append(W)
            self.bs.append(b)

            x = y

        self.y = y

        self.y_ = tf.compat.v1.placeholder(tf.float64, shape=(None, output_dims))

        self.loss = tf.compat.v1.losses.mean_squared_error(self.y_, self.y)
        # self.loss = tf.reduce_mean(tf.squared_difference(self.y_, self.y))

        self.train = tf.compat.v1.train.AdamOptimizer(lr).minimize(self.loss)

        self.init_op = tf.compat.v1.global_variables_initializer()

        self.sess = tf.compat.v1.Session()
        self.sess.run(self.init_op)

    def predict(self, X):

        X = np.atleast_2d(X)

        result = self.sess.run(self.y, feed_dict={
                self.x: X
        })

        return result

    def fit(self, X, y):

        assert X.shape[0] == y.shape[0],\
            'X.shape[0] != y.shape[0], {} != {}'.format(X.shape[0], y.shape[0])

        assert X.shape[1] == self.input_shape[0],\
            'X.shape[1] = {}, it should be {}'.format(X.shape, self.input_shape)
        assert y.shape[1] == self.output_shape[0],\
            'y.shape[1] = {}, it should be {}'.format(y.shape, self.output_shape)

        self.sess.run(self.train, feed_dict={
                self.x : X,
                self.y_: y
        })

    def partial_fit(self, X, y):
        self.fit(np.atleast_2d(X), np.atleast_2d(y))
