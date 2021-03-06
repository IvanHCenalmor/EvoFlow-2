"""
This is a use case of EvoFlow

In this instance, we handle a classification problem, which is to be solved by two DNNs combined in a sequential layout.
The problem is the same as the one solved in Sequential.py, only that here a CNN is evolved as the first component of the model.
"""
import sys
sys.path.append('..')

import tensorflow as tf
import numpy as np

from deatf.network import MLPDescriptor, CNNDescriptor, CNN
from deatf.metrics import accuracy_error
from deatf.data import load_fashion
from deatf import evolution

from tensorflow.keras.layers import Input, Dense, Flatten, Conv2D, AveragePooling2D, MaxPooling2D, Concatenate, UpSampling2D
from tensorflow.keras.models import Model
import tensorflow.keras.optimizers as opt
from sklearn.preprocessing import OneHotEncoder


class SkipCNN(CNN):
    def building(self, x, skip):
        """
        Using the filters defined in the initialization function, create the CNN
        :param layer: Input of the network
        :param skip: Example of how to implement a skip connection
        :return: Output of the network
        """
        skip = (self.descriptor.number_hidden_layers % (skip-2)) + 2
        for lay_indx in range(self.descriptor.number_hidden_layers):
            
            if lay_indx == 0:
                skip_layer = x
                skip_kernel_size = x.shape[1]
            
            if skip == lay_indx:
                actual_kernel_size = x.shape[1]
                x = UpSampling2D((skip_kernel_size,skip_kernel_size))(x)
                x = MaxPooling2D((actual_kernel_size, actual_kernel_size))(x)
                x = Concatenate(axis=-1)([x, skip_layer])
                
            if self.descriptor.layers[lay_indx] == 2:  # If the layer is convolutional
                
                x = Conv2D(self.descriptor.filters[lay_indx][2],
                           [self.descriptor.filters[lay_indx][0],self.descriptor.filters[lay_indx][1]],
                           strides=[self.descriptor.strides[lay_indx][0], self.descriptor.strides[lay_indx][1]],
                           padding="valid",
                           activation=self.descriptor.act_functions[lay_indx],
                           kernel_initializer=self.descriptor.init_functions[lay_indx])(x)

            elif self.descriptor.layers[lay_indx] == 0:  # If the layer is average pooling
                x = AveragePooling2D(pool_size=[self.descriptor.filters[lay_indx][0], self.descriptor.filters[lay_indx][1]],
                                           strides=[self.descriptor.strides[lay_indx][0], self.descriptor.strides[lay_indx][1]],
                                           padding="valid")(x)
            else:
                x = MaxPooling2D(pool_size=[self.descriptor.filters[lay_indx][0], self.descriptor.filters[lay_indx][1]],
                                       strides=[self.descriptor.strides[lay_indx][0], self.descriptor.strides[lay_indx][1]],
                                       padding="valid")(x)
                
        return x

evolution.descs["CNNDescriptor"] = SkipCNN

optimizers = [opt.Adadelta, opt.Adagrad, opt.Adam]

def eval_cnn(nets, train_inputs, train_outputs, batch_size, iters, test_inputs, test_outputs, hypers):
    """
    
    :param nets:
    :param train_inputs:
    :param train_outputs:
    :param batch_size:
    :param iters:
    :param test_inputs:
    :param test_outputs:
    :param hypers:
    """
  
    models = {}
    
    inp = Input(shape=train_inputs["i0"].shape[1:])
    out = nets["n0"].building(inp, hypers["skip"])
    out = Flatten()(out)
    out = Dense(20)(out)
    out = nets["n1"].building(out)
    
    model = Model(inputs=inp, outputs=out)
    #model.summary()
    opt = optimizers[hypers["optimizer"]](learning_rate=hypers["lrate"])
    model.compile(loss=tf.nn.softmax_cross_entropy_with_logits, optimizer=opt, metrics=[])
    
    model.fit(train_inputs['i0'], train_outputs['o0'], epochs=iters, batch_size=batch_size, verbose=0)
            
    models["n0"] = model
    
    preds = models["n0"].predict(test_inputs["i0"])
    
    res = tf.nn.softmax(preds)

    return accuracy_error(test_outputs["o0"], res),


if __name__ == "__main__":

    x_train, y_train, x_test, y_test, x_val, y_val = load_fashion()
    
    x_train = x_train[:500]
    y_train = y_train[:500]
    x_test = x_test[:100]
    y_test = y_test[:100]
    x_val = x_val[:100]
    y_val = y_val[:100]
    
    
    # We fake a 3 channel dataset by copying the grayscale channel three times.
    x_train = np.expand_dims(x_train, axis=3)/255
    x_train = np.concatenate((x_train, x_train, x_train), axis=3)

    x_test = np.expand_dims(x_test, axis=3)/255
    x_test = np.concatenate((x_test, x_test, x_test), axis=3)

    x_val = np.expand_dims(x_val, axis=3)/255
    x_val = np.concatenate((x_val, x_val, x_val), axis=3)
    
    OHEnc = OneHotEncoder()

    y_train = OHEnc.fit_transform(np.reshape(y_train, (-1, 1))).toarray()
    y_test = OHEnc.fit_transform(np.reshape(y_test, (-1, 1))).toarray()
    y_val = OHEnc.fit_transform(np.reshape(y_val, (-1, 1))).toarray()    

    # Here we indicate that we want a CNN as the first network of the model
    e = evolution.Evolving(evaluation=eval_cnn, desc_list=[CNNDescriptor, MLPDescriptor], 
                           x_trains=[x_train], y_trains=[y_train], x_tests=[x_val], y_tests=[y_val],
                           batch_size=150, population=5, generations=3, iters=10, 
                           n_inputs=[[28, 28, 3], [20]], n_outputs=[[7, 7, 1], [10]], cxp=0.5, mtp=0.5, 
                           hyperparameters={"lrate": [0.1, 0.5, 1], "optimizer": [0, 1, 2], "skip": range(3, 10)}, 
                           batch_norm=True, dropout=True)
    a = e.evolve()

    print(a[-1])
