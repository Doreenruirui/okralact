## Github Page

https://github.com/Calamari-OCR/calamari



## Installation using pip

The suggested method is to install calamari into a virtual environment using pip:

```shell
$ virtualenv -p python3 PATH_TO_VENV_DIR (e. g. virtualenv calamari_venv)
$ source PATH_TO_VENV_DIR/bin/activate
$ pip install calamari_ocr
$ pip install tensorflow   # or pip install tensorflow_gpu for GPU support
```


which will install calamari and all of its dependencies.

To install the package without a virtual environment simply run

```shell
$ pip install calamari_ocr
$ pip install tensorflow   # or pip install tensorflow_gpu for GPU support
```


To install the package from its source, download the source code

```shell
$ wget https://github.com/Calamari-OCR/calamari/archive/master.zip
```

 and run

```shell
$ python setup.py install
```



## Installation using Conda

Run

```shell
$ wget https://raw.githubusercontent.com/Calamari-OCR/calamari/master/environment_master_gpu.yml
$ conda env create -f environment_master_gpu.yml
```

Alternatively you can install the cpu versions or the current dev version instead of the stable master.

```shell
$ wget https://raw.githubusercontent.com/Calamari-OCR/calamari/master/environment_master_cpu.yml
$ conda env create -f environment_master_cpu.yml
```
