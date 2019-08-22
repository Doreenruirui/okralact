## Github Page

https://github.com/tmbdev/ocropy

## Installation from the source

To install OCRopus dependencies system-wide:

```shell
$ sudo apt-get install $(cat PACKAGES)
$ wget -nd http://www.tmbdev.net/en-default.pyrnn.gz
$ mv en-default.pyrnn.gz models/
$ sudo python setup.py install
```

## Installtion using Python Virtual Environment

Alternatively, dependencies can be installed into a [Python Virtual Environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/):

```shell
$ virtualenv ocropus_venv/
$ source ocropus_venv/bin/activate
$ pip install -r requirements.txt
$ wget -nd http://www.tmbdev.net/en-default.pyrnn.gz
$ mv en-default.pyrnn.gz models/
$ python setup.py install
```

## Installation using Conda

An additional method using [Conda](http://conda.pydata.org/) is also possible:

```shell
$ conda create -n ocropus_env python=2.7
$ source activate ocropus_env
$ conda install --file requirements.txt
$ wget -nd http://www.tmbdev.net/en-default.pyrnn.gz
$ mv en-default.pyrnn.gz models/
$ python setup.py install
```

To test the recognizer, run:

```shell
$ ./run-test
```