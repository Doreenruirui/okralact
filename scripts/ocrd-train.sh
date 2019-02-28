#!/bin/bash

ENGINE="Kraken"
TEST="0"
DATA_FOLDER=""
MODEL_FOLDER=""

usage()
{
    echo "Parameters for train an OCR engine"
    echo "optinal arguments"
    echo "      -h --help"
    echo "      --engine=$ENGINE, the engine used to train the model: ocropus/tesseract/kraken/calamari, default: kraken"
    echo "      --data_dir,  the direcctory of training data"
    echo "      --model_dir, the directory of model file"
    echo "      --prefix,   the prefix of model file, default[engine name]"
    echo "      --lr,   learning rate, default[0.001]"
    echo "      --num_epoches, number of epoches to train before stop"
}

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        --engine)
            ENGINE=$VALUE
            if [[ $ENGINE != 'ocropus' && $ENGINE != 'kraken' && $ENGINE != 'calamari' && $ENGINE != 'tesseract' ]]; then
                echo 'Please choose an engine from: ocropus, kraken, calamari or tesseract'
                exit 1
            fi
            ;;
        --data_dir)
            DATA_FOLDER=$VALUE
            ;;
        --model_dir)
            MODEL_FOLDER=$VALUE
            ;;
        --prefix)
            MODEL_FOLDER=$VALUE
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done


echo "ENGINE is $ENGINE";
if [[ $ENGINE == 'kraken' ]]; then
    echo "Load Engine $ENGINE"
    source activate kraken
        echo "$DATA_FOLDER/*.png"
        ketos train $DATA_FOLDER/*.png --output $MODEL_FOLDER/model
    source deactivate
fi