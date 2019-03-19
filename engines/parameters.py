import argparse

##ToDo 1. Add automatically splitting the training and evaluation data
##ToDO 2. Unify the early stop parameters

parser = argparse.ArgumentParser(description='Parameters')
# parser.add_argument('--engine', type=str, default="kraken",
#                     help="choose the OCR engine from tesseract, kraken, ocropus, calamari")
parser.add_argument('--data_dir', type=str, default="",
                    help="The directory of the training data")
parser.add_argument('--model_dir', type=str, default="",
                    help="The directory to store the trained OCR model")
parser.add_argument('--prefix', type=str, default="model",
                    help="The prefix of the model file.")
parser.add_argument('--nepoch', type=int, default=20,
                    help="Number of epoches to train before stopping.")

subparsers = parser.add_subparsers()

kraken = subparsers.add_parser('kraken')
kraken.add_argument('--ratio', type=float, default=0.9,
                    help="ratio of training and validation data")
kraken.add_argument('--model_spec', type=str, default='[1,48,0,1 Cr3,3,32 Do0.1,2 Mp2,2 Cr3,3,64 Do0.1,2 Mp2,2 S1(1x12)1,3 Lbx100 Do]', help='The network structure.')
kraken.add_argument('--append', type=int, default=0, help='Removes layers before argument and then appends spec. Only works when loading an existing model.')
kraken.add_argument('--continue_from', type=str, default=None, help='Loading existing file to continue training.')
kraken.add_argument('--learning_rate', type=float, default=0.001, help='learning rate')
kraken.add_argument('--optimizer', type=str, default='Adam', help='Select optimizer (Adam, SGD, RMSprop)')
kraken.add_argument('--momentum', type=float, default=0.9, help='Momentum used with SGD optimizer. Ignored otherwise.')
kraken.add_argument('--weight_decay', type=float, default=0.0,
                    help='Weight decay, penalize the large weight, similar to regularization.')
kraken.add_argument('--save_freq', type=float, default=1, help='The frequency of how often to save the model paratmeters during training. The unit is in epoches.')

tesseract = subparsers.add_parser('tesseract')
tesseract.add_argument('--model_spec', type=str, default='[1,48,0,1 Cr3,3,32 Do0.1,2 Mp2,2 Cr3,3,64 Do0.1,2 Mp2,2 S1(1x12)1,3 Lbx100 Do]', help='The network structure.')
tesseract.add_argument('--append', type=int, default=0, help='Removes layers before argument and then appends spec. Only works when loading an existing model')
tesseract.add_argument('--continue_from', type=str, default=None, help='Loading existing file to continue training.')
tesseract.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate')
tesseract.add_argument('--learning_rate_sep', type=bool, default=0.001, help='Enable layer-specific learning rates')
tesseract.add_argument('--optimizer', type=str, default='Adam', help='Select optimizer (Adam, Momentum)')
tesseract.add_argument('--adam_beta', type=float, default=0.999, help='smoothing factor squared in Adam algorithm')
tesseract.add_argument('--momentum', type=float, default=0.5, help='Momentum for alpha smoothing gradients.')
tesseract.add_argument('--weight_range', type=float, default=0.1, help='The range of randomly initialized weights.')
ocropus = subparsers.add_parser('ocropus')
ocropus.add_argument('--hidden_size', type=int, default=100, help='LSTM state units')
ocropus.add_argument('--learning_rate', type=float, default=0.001, help='learning rate')
ocropus.add_argument('--save_freq', type=float, default=1, help='The frequency of how often to save the model paratmeters during training. The unit is in epoches.')
ocropus.add_argument('--start', type=int, default=-1, help='Manually set the number of already trained lines, which influences the naming and stopping condition.')

calamari = subparsers.add_parser('calamari')
calamari.add_argument('--model_spec', type=str, default='cnn=40:3x3,pool=2x2,cnn=60:3x3,pool=2x2,lstm=200,dropout=0.5', help='The network structure.')


# parser.add_argument('--partition', type=float, default=0.9, help='Ratio of the training and test data')
# parser.add_argument('--validation', type=str, default=None, help='Path to the validation files.')
# parser.add_argument('--save_freq', type=float, default=1,
#                     help='The frequency of how often to save the model paratmeters during training. The unit is in epoches.')
# parser.add_argument('--early_stop', type=bool, default=False, help='Whether to stop training early according to evaluation results.')
# parser.add_argument('--preload', type=bool, default=False, help='Whether to preload all the training set into memory for accelerating training.')
configs = parser.parse_args()

