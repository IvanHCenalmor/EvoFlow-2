import sys
sys.path.append('../..')

import tensorflow as tf
import time

from evoflow.metrics import accuracy_error
from evoflow.network import ConvDescriptor

from aux_functions_testing import test

import tensorflow.keras.optimizers as opt
from tensorflow.keras.layers import Input, Dense, Flatten
from tensorflow.keras.models import Model

optimizers = [opt.Adadelta, opt.Adagrad, opt.Adam]


def test_CNN_all_datasets(eval_func=None, batch_size=150, population=5, 
                      generations=10, iters=100, n_layers=10, max_layer_size=20):
    
    dataset_collection = ['mnist', 'kmnist', 'cmaterdb', 'fashion_mnist', 'omniglot', 
                          'binary_alpha_digits', 'cifar10', 'rock_paper_scissors']

    for dataset in dataset_collection:
        
        print('\nEvaluating the {} dataset with the following configuration:'.format(dataset),
              '\nBatch size:  {}\nPopulation of networks:  {}\nGenerations:  {}'.format(batch_size, population, generations),
              '\nIterations in each network:  {}\nMaximum number of layers:  {}'.format(iters, n_layers),
              '\nMaximum number of neurons in each layer: {}'.format(max_layer_size))

        init_time = time.time()
        
        try:
            x = test_CNN(dataset, eval_func=eval_func, batch_size=batch_size, 
                 population=population, generations=generations, iters=iters, 
                 n_layers=n_layers, max_layer_size=max_layer_size)
            print(x)
        except Exception as e:
            print('An error ocurred executing the {} dataset.'.format(dataset))    
            print(e)
            
        print('Time: ', time.time() - init_time)
        
def test_CNN(dataset_name, eval_func=None, batch_size=150, population=5, 
             generations=10, iters=100, n_layers=10, max_layer_size=20):
    
    return test(dataset_name, [ConvDescriptor], eval_func, batch_size, 
                population, generations, iters, n_layers, max_layer_size,  
                hyperparameters={"lrate": [0.1, 0.5, 1], "optimizer": [0, 1, 2]})    
        
def eval_cnn(nets, train_inputs, train_outputs, batch_size, test_inputs, test_outputs, hypers):
    models = {}
    
    inp = Input(shape=train_inputs["i0"].shape[1:])
    out = nets["n0"].building(inp)
    out = Flatten()(out)
    out = Dense(train_outputs["o0"].shape[1])(out)
    
    model = Model(inputs=inp, outputs=out)

    opt = optimizers[hypers["optimizer"]](learning_rate=hypers["lrate"])
    model.compile(loss=tf.nn.softmax_cross_entropy_with_logits, optimizer=opt, metrics=[])
    
    model.fit(train_inputs['i0'], train_outputs['o0'], epochs=10, batch_size=batch_size, verbose=0)
    
    models["n0"] = model

    preds = models["n0"].predict(test_inputs["i0"])
    
    res = tf.nn.softmax(preds)

    return accuracy_error(res, test_outputs["o0"]),
    
if __name__ == "__main__":
    #test_CNN('binary_alpha_digits', eval_func=eval_cnn, batch_size=150, population=20, generations=5, iters=10)
    test_CNN_all_datasets(eval_func=eval_cnn, batch_size=150, population=2, generations=2, iters=5)