## Github Page

https://github.com/mittagessen/kraken

## Installtion:



When using a recent version of pip all dependencies will be installed from binary wheel packages, so installing build-essential or your distributions equivalent is often unnecessary. kraken only runs on Linux or Mac OS X. Windows is not supported.

Installation using Conda
Install the latest 1.0 release through conda:

```
$ wget https://raw.githubusercontent.com/mittagessen/kraken/master/environment.yml
$ conda env create -f environment.yml
```
or
```
$ wget https://raw.githubusercontent.com/mittagessen/kraken/master/environment_cuda.yml
$ conda env create -f environment_cuda.yml
```
for CUDA acceleration with the appropriate hardware.

## Installation using Pip

It is also possible to install the same version from pypi:

```
$ pip install kraken
```

Finally you'll have to scrounge up a model to do the actual recognition of characters. To download the default model for printed English text and place it in the kraken directory for the current user:

```
$ kraken get 10.5281/zenodo.2577813
```

A list of libre models available in the central repository can be retrieved by running:

```
$ kraken list
```