"""
This is a use case of EvoFlow

We face here a multiobjective problem. We create two MLP, one of which is intended for classifyin MNIST and the other one for
Fashion-MNIST. They don't interact in any moment in the model.
"""
import sys
sys.path.append('..')

import tensorflow as tf
import numpy as np

from deatf.data import load_fashion, load_mnist
from deatf.network import MLPDescriptor
from deatf.metrics import accuracy_error
from deatf.evolution import Evolving

from sklearn.preprocessing import OneHotEncoder
from tensorflow.keras.layers import Input, Flatten
from tensorflow.keras.models import Model

def evaluation(nets, train_inputs, train_outputs, batch_size, iters, test_inputs, test_outputs, _):
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
    
    inp_0 = Input(shape=train_inputs["i0"].shape[1:])
    out_0 = Flatten()(inp_0)
    out_0 = nets["n0"].building(out_0)
    
    inp_1 = Input(shape=train_inputs["i1"].shape[1:])
    out_1 = Flatten()(inp_1)
    out_1 = nets["n1"].building(out_1)
    
    model = Model(inputs=[inp_0, inp_1], outputs=[out_0, out_1])
    
    opt = tf.keras.optimizers.Adam(learning_rate=0.01)
    model.compile(loss=[tf.nn.softmax_cross_entropy_with_logits, tf.nn.softmax_cross_entropy_with_logits], optimizer=opt, metrics=[])
    
    # As the output has to be the same as the input, the input is passed twice
    model.fit([train_inputs['i0'], train_inputs['i1']],
              [train_outputs['o0'], train_outputs['o1']],
               epochs=iters, batch_size=batch_size, verbose=0)
    
    #tf.keras.utils.plot_model(model, "multi_input_and_output_model.png", show_shapes=True)
    
    models["n0"] = model
    
    pred_0, pred_1 = models['n0'].predict([test_inputs['i0'], test_inputs['i1']])
        
    res_0 = tf.nn.softmax(pred_0)
    res_1 = tf.nn.softmax(pred_1)

    # Return both accuracies
    return accuracy_error(res_0, test_outputs["o0"]), accuracy_error(res_1, test_outputs["o1"])


if __name__ == "__main__":

    fashion_x_train, fashion_y_train, fashion_x_test, fashion_y_test, fashion_x_val, fashion_y_val = load_fashion()
    mnist_x_train, mnist_y_train, mnist_x_test, mnist_y_test, mnist_x_val, mnist_y_val = load_mnist()

    OHEnc = OneHotEncoder()

    fashion_y_train = OHEnc.fit_transform(np.reshape(fashion_y_train, (-1, 1))).toarray()
    fashion_y_test = OHEnc.fit_transform(np.reshape(fashion_y_test, (-1, 1))).toarray()
    fashion_y_val = OHEnc.fit_transform(np.reshape(fashion_y_val, (-1, 1))).toarray()

    mnist_y_train = OHEnc.fit_transform(np.reshape(mnist_y_train, (-1, 1))).toarray()
    mnist_y_test = OHEnc.fit_transform(np.reshape(mnist_y_test, (-1, 1))).toarray()
    mnist_y_val = OHEnc.fit_transform(np.reshape(mnist_y_val, (-1, 1))).toarray()

    # In this case, we provide two data inputs and outputs
    e = Evolving(desc_list=[MLPDescriptor, MLPDescriptor], 
                 x_trains=[fashion_x_train, mnist_x_train], y_trains=[fashion_y_train, mnist_y_train], 
                 x_tests=[fashion_x_val, mnist_x_val], y_tests=[fashion_y_val, mnist_y_val], 
                 evaluation=evaluation, batch_size=150, population=10, generations=10, iters=10, 
                 n_inputs=[[28, 28], [28, 28]], n_outputs=[[10], [10]], sel='best')
    res = e.evolve()

    print(res[0])
