# OCRD
A repository for online OCRD training infrastructure.

## Setup

```sh
sudo apt-get install redis
pip install -r requirements.txt
```

## Install
### Installation of the Engines
The instructions for installing the engines (Tesseract, kraken, OCRopus, Calamari) are in the folder [install](https://github.com/Doreenruirui/okralact/tree/master/install).

### Installaton of the Training System
```
$ wget https://github.com/Doreenruirui/okralact/archive/master.zip
```

### Deploy the system on a server

Coming soon.

## System Structure

<center>
    <img src="docs/Framework.png" style="zoom:20%"/> 
</center>

**Okralact** is both a set of specifications and a prototype implementation for harmonizing the input data, parameterization and provenance tracking of training different OCR engines. It is a client/server architecture application. The interactions between the client nodes and the server are implementeqd using **Flask**, a lightweight web application framework for Python. All the training or evaluation jobs submitted to the server are handled in the background by task queues implemented wth **Redis Queue** (**RQ**).  

The folder *app* contains the code for the web-application and task queues. The folder *app/templates* defined a set of web interfaces that the users directly interacted with.  Through these webpages, the user can 

 *	upload 
   	*	a dataset
   	*	a configuration file for training a specific engine
 *	submit 
   	*	a job for training an OCR model by selecting a uploaded model and a configuration file
   	*	a job for generating the report of validating all the intermediately models saved during training (can be used to pick the best model)
   	*	a job for evaluating a trained model by selecting a evaluation dataset

The file *app/route.py* contains the code for handling the users' HTTP requests and responses with Flask,  and the code for processing the users' jobs with Redis Queue. There are three task queues running in the backend,  i.e., the training queue, the validation queue and the evaluation queue. Each type of job submitted by the user would be put into its corresponding task queue, where it will wait to be excuted. 

When a job gets opportunity to run, it will call the common API for training, validation or evaluation defined in the folder *engines*. The jobs in training task queue, validating task queue and evaluating task queue will call the API defined in the file *train.py*, *valid.py* and *eval.py* respectively. 

 The unifie specifications for all the OCR engines are defined in the folder *engines/schemas* with **jsonschema**. The file *engine/schemas/common.schema* defined a set of unifed parameters for each engine, the files *engine_[engine name].scheam* has defined the parameter set for each engine. The folder *engines/schemas/models* contains the schemas for the neural network structure for all the engines.  The files *model_[engine name].schema* are the defintion of the neural netwrk layers, e.g., input, cnn, pooling, dropout, rnn, output allowed by each engine. The files *layer_all_[engine name].schema* define the parameters allowed in each layer for each engine. The files *layer_[layer name].schema* define the set of parameters allowed by each neural network layer.

In the folder *engine*, we can also find the code *validating parameters.py*, which is used to validate whether the configuration file that the users uploaded are valid, and *translate_parameters.py*, which is used to translate the user-specific configuration files into the original set parameters that can recognized by each engine. 