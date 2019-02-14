import argparse


parser = argparse.ArgumentParser(description='Parameters')
parser.add_argument('--engine', type=str, default="kraken",
                    help="choose the OCR engine from tesseract, kraken, ocropus, calamari")
parser.add_argument('--data_dir', type=str, default="",
                    help='the directory of the training data')
parser.add_argument('--model_dir', type=str, default="",
                    help="the directory to store the trained OCR model")
parser.add_argument('--prefix', type=str, default="model",
                    help="the prefix of the model file")
parser.add_argument('--nepoch', type=int, default=20,
                    help="number of epoches to train before stopping")
parser.add_argument('--ratio', type=float, default=0.9,
                    help="ratio of training and validation data")

configs = parser.parse_args()

