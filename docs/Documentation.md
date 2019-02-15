#Comparison of OCR Engines

Elevators for different engines:

1. [**ocropus**](#ocropus-parameters): [**tutoral**]()
2. [**kraken**](#kraken-parameters):  [**tutorial**](http://kraken.re/training.html)
3. [**calamari**](#calamari-parameters): [**tutorial**](https://github.com/Calamari-OCR/calamari)
4. [**tesseract**](#tesseract-parameters) :  [**tutorial**](https://github.com/tesseract-ocr/tesseract/wiki/TrainingTesseract-4.00#tutorial-guide-to-lstmtraining)


| Model                   |                                             | Tesseract                                                    | Kraken                                                 | Ocropus                                            | Calamari                                                     |
| :---------------------- | ------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------ |
| Input                   |                                             | .tif                                                         | *.png <br />*.gt.txt                                   | .png<br />.gt.txt                                  | .png<br />.gt.txt                                            |
| Output                  |                                             | Prefix                                                       | Prefix                                                 | Prefix                                             | Prefix/Directory                                             |
| Train Command           |                                             | training/lstmtraining --debug_interval 100   --traineddata ~/tesstutorial/engtrain/eng/eng.traineddata    --net_spec '[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c111]'   --model_output ~/tesstutorial/engoutput/base --learning_rate 20e-4 \   --train_listfile ~/tesstutorial/engtrain/eng.training_files.txt   --eval_listfile ~/tesstutorial/engeval/eng.training_files.txt   --max_iterations 5000 &>~/tesstutorial/engoutput/basetrain.log | ketos train output_dir/*.png                           | ocropus-rtrain -o modelname book\*/????/\*.bin.png | calamari-train --files your_images.*.png                     |
| Evaluation Command      |                                             |                                                              | ketos test -m syriac_best.mlmodel lines/*.png          |                                                    | calamari-predict --checkpoint path_to_model.ckpt --files your_images.*.png |
| Fine Tuning             |                                             | training/lstmtraining --model_output /path/to/output [--max_image_MB 6000] \   --continue_from /path/to/existing/model \   --traineddata /path/to/original/traineddata \   [--perfect_sample_delay 0] [--debug_interval 0] \   [--max_iterations 0] [--target_error_rate 0.01] \   --train_listfile /path/to/list/of/filenames.txt | ketos train -i model_best.mlmodel syr/*.png            |                                                    |                                                              |
| Model Structure         | Direction of LSTM                           |                                                              |                                                        | ✔️(bi or single)                                    | :heavy_check_mark:(bi or l2r, r2l)                           |
|                         | Number of Hidden units                      |                                                              |                                                        | :heavy_check_mark:                                 |                                                              |
|                         | Specify Model Layers                        | :heavy_check_mark:                                           | :heavy_check_mark:                                     | ❌                                                  | :heavy_check_mark:                                           |
|                         | Modify top layers                           | :heavy_check_mark:                                           | :heavy_check_mark:                                     | ❌                                                  |                                                              |
|                         | load exisiting model                        | :heavy_check_mark:                                           | :heavy_check_mark:                                     | :heavy_check_mark:                                 | **:heavy_check_mark:**                                       |
|                         | Range of random Initialization of weights   | :heavy_check_mark:                                           | ❌                                                      | ❌                                                  | ❌                                                            |
| Training Specifications | Learning    Rate                            | :heavy_check_mark:                                           | :heavy_check_mark:                                     | ✔️                                                  | ❌                                                            |
|                         | Learning Rate for each layer                | :heavy_check_mark:                                           | ❌                                                      | ❌                                                  |                                                              |
|                         | Learning Rate Scheduler                     | ❌                                                            | :heavy_check_mark:                                     | ❌                                                  | ❌                                                            |
|                         | Momentum                                    | :heavy_check_mark:                                           | :heavy_check_mark:                                     | ❌                                                  | ❌                                                            |
|                         | Weight Decay                                |                                                              | :heavy_check_mark:                                     | ❌                                                  | ❌                                                            |
|                         | Ratio of Train/Valid                        | :heavy_check_mark:(specificy validation lines)​               | :heavy_check_mark:(ratio  or specify validation lines) | ❌                                                  | :heavy_check_mark:(specify the validation lines)             |
|                         | Optimizer                                   | :heavy_check_mark:                                           | :heavy_check_mark:                                     | ❌                                                  | ❌                                                            |
|                         | adam_beta                                   | :heavy_check_mark:                                           | ❌                                                      | ❌                                                  | ❌                                                            |
|                         | batch size                                  |                                                              | ❌                                                      | ❌                                                  | :heavy_check_mark:                                           |
|                         | Save Freq                                   |                                                              | :heavy_check_mark:(iterations)                         | :heavy_check_mark:(epochs)                         | :heavy_check_mark:(checkpoint frequency)                     |
|                         | \#lines before stop                         | :heavy_check_mark:(iterations)​                               | :heavy_check_mark:(epochs)                             | :heavy_check_mark:(lines)                          | :heavy_check_mark:(iterations)                               |
|                         |                                             |                                                              |                                                        |                                                    |                                                              |
|                         | \#number of lines already trained           |                                                              | ❌                                                      | :heavy_check_mark:                                 | ❌                                                            |
|                         | Early stop                                  | :heavy_check_mark:(error below a target)                     | :heavy_check_mark:(number of report frequency)         | ❌                                                  | :heavy_check_mark:                                           |
|                         | Early Stop Iterations after worse           | ❌                                                            | ❌                                                      | ❌                                                  | :heavy_check_mark:                                           |
|                         | Target Error Rate to Stop                   | :heavy_check_mark:                                           | ❌                                                      | ❌                                                  | ❌                                                            |
|                         | Device to Train (cpu/gpu:0, gpu:1)          | ❌                                                            | :heavy_check_mark:                                     | ❌                                                  | ❌                                                            |
|                         | Preload Data into Memory                    | :question:                                                   | :heavy_check_mark:                                     | ❌                                                  | :heavy_check_mark:                                           |
|                         | Number of openMP threads                    | ❌                                                            | :heavy_check_mark:                                     | ❌                                                  | :heavy_check_mark:                                           |
|                         | Skip Invalid Groundtruth or Not             |                                                              | ❌                                                      | ❌                                                  | :heavy_check_mark:                                           |
|                         | Clip the gradient                           | ❌                                                            | ❌                                                      | ❌                                                  | :heavy_check_mark:                                           |
|                         | Maximum amount of memory for caching images | :heavy_check_mark:                                           | ❌                                                      | ❌                                                  | ❌                                                            |
|                         | Perfect sample delay                        | :heavy_check_mark:(choose difficult samples to train)​        |                                                        |                                                    |                                                              |
| Data                    | Pad the lines                               |                                                              | :heavy_check_mark:                                     | :heavy_check_mark:                                 | :heavy_check_mark:                                           |
|                         | Height of Lines                             |                                                              | :heavy_check_mark:                                     | :heavy_check_mark:                                 | :heavy_check_mark:                                           |
|                         | Augmenation                                 |                                                              | ❌                                                      | ❌                                                  | :heavy_check_mark:                                           |
|                         | Normalization                               |                                                              |                                                        |                                                    |                                                              |
|                         | Codec                                       |                                                              |                                                        |                                                    |                                                              |
|                         | Add New Characters                          | :heavy_check_mark:                                           | :question::heavy_check_mark:                           | ❌                                                  | ❌                                                            |
| Info                    | Display output for every n iteration        | :heavy_check_mark:(iteration: 100)                           | :heavy_check_mark:(epochs)                             | :heavy_check_mark:(iterations)                     | :heavy_check_mark:(epochs: could < 1)                        |

[**back to top**](#comparison-of-ocr-engines)



## ocorpus parameters

1. [**kraken**](#kraken-parameters)
2. [**calamari**](#calamari-parameters)
3. [**tesseract**](#tesseract-parameters)
4. [**comparison**](#comparison-of-ocr-engines)



|                 | Parameter                                           | Explanation                                                  |
| --------------- | --------------------------------------------------- | ------------------------------------------------------------ |
|                 | -h, --help                                          | show this help message and exit                              |
| :question:      | -e LINEEST, --lineest LINEEST                       | type of text line estimator, default: center                 |
| :question:      | -E, --nolineest                                     | don't perform line estimation and load .dew.png file         |
| :question:      | -l HEIGHT, --height HEIGHT                          | set the default height for line estimation, default:  48     |
| :question:      | --dewarp                                            | only perform line estimation and output .dew.png file        |
| :question:      | -c [CODEC [CODEC ...]], --codec [CODEC [CODEC ...]] | construct a codec from the input text                        |
|                 | -C, --clstm                                         | use C++ LSTM                                                 |
| Train           | -r LRATE, --lrate LRATE                             | LSTM learning rate, default: 0.0001                          |
| Model           | -S HIDDENSIZE, --hiddensize HIDDENSIZE              | LSTM state units, default: 100                               |
| Output          | -o OUTPUT, --output OUTPUT                          | LSTM model file                                              |
| Train           | -F SAVEFREQ, --savefreq SAVEFREQ                    | LSTM save frequency, default: 1000                           |
| :question:Train | --strip                                             | strip the model before saving                                |
| Train           | -N NTRAIN, --ntrain NTRAIN                          | #lines to train before stopping, default: 1000000            |
| :question:      | -t TESTS, --tests TESTS                             | test cases for error estimation                              |
| Model           | --unidirectional                                    | use only unidirectional LSTM                                 |
| Train           | --updates                                           | verbose LSTM updates                                         |
| Train           | --load LOAD                                         | start training with a previously trained model               |
| :question:Train | --start START                                       | manually set the number of already learned lines, which influences the naming and stoping condition,  default: -1 which will then be overriden by the value  saved in the network |
| :question:      | -X EXECUTE, --exec EXECUTE                          | execute before anything else (usually used for imports)      |
| Info            | -v, --verbose                                       |                                                              |
| Info            | -d DISPLAY, --display DISPLAY                       | display output for every nth iteration, where  n=DISPLAY, default: 0 |
| :question:      | -m MOVIE, --movie MOVIE                             |                                                              |
| :question:      | -M MOVIESAMPLE, --moviesample MOVIESAMPLE           |                                                              |
| :question:      | -q, --quiet                                         |                                                              |
| :question:      | -Q, --nocheck                                       |                                                              |
| :question:      | -p PAD, --pad PAD                                   |                                                              |
| Input           | -f FILE, --file FILE                                | path to file listing input files, one per line               |

 ## Kraken parameters

1. [**ocropus**](#ocropus-parameters)

2. [**calamari**](#calamari-parameters)

3. [**tesseract**](#tesseract-parameters)

4. [**comparison**](#comparison-of-ocr-engines)

   The first block defines the input in order of **[batch, heigh, width, channels]** with **zero-valued dimensions being variable**. Integer valued height or width input specifications will result in the input images being automatically scaled in either dimension.

   When **channels** are set to **1 grayscale** or **B/W inputs** are expected, **3** expects **RGB color images**. Higher values in combination with a **height of 1** result in the network being fed **1 pixel wide grayscale strips scaled to the size of the channel dimension**.

   ```
   [1,48,0,1 Cr3,3,32 Do0.1,2 Mp2,2 Cr3,3,64 Do0.1,2 Mp2,2 S1(1x12)1,3 Lbx100 Do 01c59]
   
   Creating new model [1,48,0,1 Cr3,3,32 Do0.1,2 Mp2,2 Cr3,3,64 Do0.1,2 Mp2,2 S1(1x12)1,3 Lbx100 Do] with 59 outputs
   layer           type    params
   0               conv    kernel 3 x 3 filters 32 activation r
   1               dropout probability 0.1 dims 2
   2               maxpool kernel 2 x 2 stride 2 x 2
   3               conv    kernel 3 x 3 filters 64 activation r
   4               dropout probability 0.1 dims 2
   5               maxpool kernel 2 x 2 stride 2 x 2
   6               reshape from 1 1 x 12 to 1/3
   7               rnn     direction b transposed False summarize False out 100 legacy None
   8               dropout probability 0.5 dims 1
   9               linear  augmented False out 59
   ```

   A model with a small convolutional stack before a recurrent LSTM layer. The extended dropout layer syntax is used to **reduce drop probability on the depth dimension as the default is too high for convolutional layers**. The remainder of the height dimension (12) is reshaped into the depth dimensions before applying the final recurrent and linear layers.

   ```
   [1,0,0,3 Cr3,3,16 Mp3,3 Lfys64 Lbx128 Lbx256 Do 01c59]
   
   Creating new model [1,0,0,3 Cr3,3,16 Mp3,3 Lfys64 Lbx128 Lbx256 Do] with 59 outputs
   layer           type    params
   0               conv    kernel 3 x 3 filters 16 activation r
   1               maxpool kernel 3 x 3 stride 3 x 3
   2               rnn     direction f transposed True summarize True out 64 legacy None
   3               rnn     direction b transposed False summarize False out 128 legacy None
   4               rnn     direction b transposed False summarize False out 256 legacy None
   5               dropout probability 0.5 dims 1
   6               linear  augmented False out 59
   ```

   A model with arbitrary sized color image input, an initial summarizing recurrent layer to squash the height to 64, followed by 2 bi-directional recurrent layers and a linear projection.

   ### Convolutional Layers

   ```
   C[{name}](s|t|r|l|m)[{name}]<y>,<x>,<d>
   s = sigmoid
   t = tanh
   r = relu
   l = linear
   m = softmax
   ```

   Adds a 2D convolution with kernel size (y, x) and d output channels, applying the selected nonlinearity.

   ### Recurrent Layers

   ```
   L[{name}](f|r|b)(x|y)[s][{name}]<n> LSTM cell with n outputs.
   G[{name}](f|r|b)(x|y)[s][{name}]<n> GRU cell with n outputs.
   f runs the RNN forward only.
   r runs the RNN reversed only.
   b runs the RNN bidirectionally.
   s (optional) summarizes the output in the requested dimension, return the last step.
   ```

   Adds either an LSTM or GRU recurrent layer to the network using eiter the x (width) or y (height) dimension as the time axis. Input features are the channel dimension and the non-time-axis dimension (height/width) is treated as another batch dimension. For example, a Lfx25 layer on an 1, 16, 906, 32 input will execute 16 independent forward passes on 906x32 tensors resulting in an output of shape 1, 16, 906, 25. If this isn’t desired either run a summarizing layer in the other direction, e.g. Lfys20 for an input 1, 1, 906, 20, or prepend a reshape layer S1(1x16)1,3 combining the height and channel dimension for an 1, 1, 906, 512 input to the recurrent layer.

   ### Helper and Plumbing Layers

   #### Max Pool

   ```
   Mp[{name}]<y>,<x>[,<y_stride>,<x_stride>]
   ```

   Adds a maximum pooling with (y, x) kernel_size and (y_stride, x_stride) stride.

   ### Reshape

   ```
   S[{name}]<d>(<a>x<b>)<e>,<f> Splits one dimension, moves one part to another
           dimension.
   ```

   The S layer reshapes a source dimension d to a,b and distributes a into dimension e, respectively b into f. Either e or f has to be equal to d. So S1(1, 48)1, 3 on an 1, 48, 1020, 8input will first reshape into 1, 1, 48, 1020, 8, leave the 1 part in the height dimension and distribute the 48 sized tensor into the channel dimension resulting in a 1, 1, 1024, 48*8=384 sized output. S layers are mostly used to remove undesirable non-1 height before a recurrent layer.

   Note

   This S layer is equivalent to the one implemented in the tensorflow implementation of VGSL, i.e. behaves differently from tesseract.

   ### Regularization Layers

   ```
   Do[{name}][<prob>],[<dim>] Insert a 1D or 2D dropout layer
   ```

   Adds an 1D or 2D dropout layer with a given probability. Defaults to 0.5 drop probability and 1D dropout. Set to dim to 2 after convolutional layers.



|  | Parameter | Explanation |
| -------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| :question: | -p, --pad INTEGER                | Left and right  padding around lines  [default: 16]          |
| Output | -o, --output PATH                | Output model file [default: model]                         |
| Model | -s, --spec TEXT                  | [**VGSL spec of the  network to train**](http://kraken.re/vgsl.html#vgsl). CTC  layer will be added  automatically. VGSL spec of the network to train. CTC layer will be added automatically. default: [1,48,0,1 Cr3,3,32 Do0.1,2 Mp2,2 Cr3,3,64 Do0.1,2 Mp2,2 S1(1x12)1,3 Lbx100 Do] |
| Model | -a, --append INTEGER | Removes layers before argument and then  appends spec. Only   works when loading an  existing model |
| Train | -i, --load PATH | Load existing file to continue training |
| Train | -F, --savefreq FLOAT | Model save frequency in epochs during  training  [default: 1.0] |
| :question:Info | -R, --report FLOAT | Report creation  frequency in epochs  [default: 1.0] |
| Train | -q, --quit [early\|dump] | Stop condition for  training. Set to  `early` for early  stooping or `dumb`  for fixed number of epochs  [default:   early] |
| :question:Train | -N, --epochs INTEGER | Number of epochs to train for  [default: -1] |
| Train | --lag INTEGER | Number of evaluations (--report frequence) to wait before stopping training without  improvement  [default: 5] |
| Train | --min-delta FLOAT | Minimum improvement between epochs to reset  early stopping. Default is scales the delta by the best loss |
| Train | -d, --device TEXT | Select device to use (cpu, cuda:0, cuda:1, ...)  [default: cpu] |
| Train | --optimizer [Adam\|SGD\|RMSprop] | Select optimizer  [default: Adam] |
| Train | -r, --lrate FLOAT | Learning rate  [default: 0.002] |
| Train | -m, --momentum FLOAT | Momentum  [default: 0.9] |
| :question:Train | -w, --weight-decay FLOAT | Weight decay  [default: 0.0] |
| :question:Train | --schedule [constant\|1cycle] | Set learning rate scheduler. For 1cycle, cycle length is determined by the `--epoch`option.  [default: constant] |
| Train | -p, --partition FLOAT | Ground truth data partition ratio between  train/validation set  [default: 0.9] |
| :question:Data | -u, --normalization [NFD\|NFKD\|NFC\|NFKC] | Ground truth normalization: Unicode has code points to encode most glyphs encountered in the wild. A lesser known feature is that there usually are multiple ways to encode a glyph. [Unicode normalization](http://www.unicode.org/reports/tr15/) ensures that equal glyphs are encoded in the same way, i.e. that the encoded representation across the training data set is consistent and there is only one way the network can recognize a particular feature on the page. Usually it is sufficient to set the normalization to Normalization Form Decomposed (NFD), as it reduces the the size of the overall script to be recognized slightly. |
| :question: | -n, --normalize-whitespace/--no-normalize-whitespace | Normalizes unicode whitespace  [default: True] |
| :question: | -c, --codec FILENAME | Load a codec JSON definition (invalid if loading existing model) |
| :question: | --resize [add/both/fail] | Codec/output layer resizing option. If set to `add` code points will be added, `both`  will set the layer to match exactly the training data, `fail` will abort if training data and model codec do not match.[default: fail] |
| :question: | --reorder / --no-reorder | Reordering of code points to display order [default: True] |
| :question:Input​ | -t, --training-files FILENAME | File(s) with additional paths to training data |
| Eval | -e, --evaluation-files FILENAME | File(s) with paths to evaluation data. Overrides the `-p` parameter |
| Train | --preload / --no-preload | Hard enable/disable for training data preloading. Enables/disables preloading of the training set into memory for accelerated training. The default setting preloads data sets with less than 2500 lines, explicitly adding `--preload` will preload arbitrary sized sets. `--no-preload` disables preloading in all circumstances. |
| Train | --threads INTEGER | Number of OpenMP threads and workers when  running on CPU.  [default: 1] |
|  | --help | Show this message and exit. |

## Calamari Parameters

1. [**ocropus**](#ocropus-parameters)
2. [**kraken**](#kraken-parameters)
3. [**tesseract**](#tesseract-parameters)
4. [**comparison**](#comparison-of-ocr-engines)

|                    | Parameter                                                    | Explanation                                                  |
| ------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
|                    | -h, --help                                                   | show this help message and exit                              |
|                    | --version                                                    | show program's version number and exit                       |
| Input              | --files FILES [FILES ...]                                    | List all image files that shall be processed. Ground  truth files with the same base name but with '.gt.txt' as extension are required at the same location |
| Input              | --text_files TEXT_FILES [TEXT_FILES ...]                     | Optional list of GT files if they are in other  directory    |
| Data               | --gt_extension GT_EXTENSION                                  | Default extension of the gt files (expected to exist in same dir) |
| :question:         | --dataset                                                    | {RAW,FILE,ABBYY,PAGEXML,EXTENDED_PREDICTION}                 |
| Train              | --train_data_on_the_fly                                      | Instead of preloading all data during the training,  load the data on the fly. This is slower, but might be required for limited RAM or large datasets |
| Train              | --seed SEED                                                  | Seed for random operations. If negative or zero a  'random' seed is used |
| Train              | --backend BACKEND                                            | The backend to use for the neural net computation.  Currently supported only tensorflow |
| Model              | --network NETWORK                                            | `--network=cnn=40:3x3,pool=2x2,cnn=60:3x3,pool=2x2,lstm=200,dropout=0.5` .The network structure Specify the network structure in a simple language. The default network consists of a stack of two CNN- and Pooling-Layers, respectively and a following LSTM layer. The network uses the default CTC-Loss implemented in Tensorflow for training and a dropout-rate of 0.5. The creation string thereto is: `cnn=40:3x3,pool=2x2,cnn=60:3x3,pool=2x2,lstm=200,dropout=0.5`. To add additional layers or remove a single layer just add or remove it in the comma separated list. Note that the order is important! |
| Data               | --line_height LINE_HEIGHT                                    | The line height: The height of each rescaled input file passed to the network. |
| Data               | --pad PAD                                                    | Padding (left right) of the line                             |
| Train              | --num_threads NUM_THREADS                                    | The number of threads to use for all operations              |
| Info               | --display DISPLAY                                            | Frequency of how often an output shall occur during raining. If 0 < display <= 1 the display is in units  of epochs. |
| Train              | --batch_size  BATCH_SIZE                                     | The batch size to use for training                           |
| Train              | --checkpoint_frequency CHECKPOINT_FREQUENCY                  | The frequency how often to write checkpoints during training. If 0 < value <= 1 the unit is in epochs,  thus relative to the number of training examples.If  -1, the early_stopping_frequency will be used. |
| Train              | --max_iters MAX_ITERS                                        | The number of iterations for training. If using early  stopping, this is the maximum number of iterations |
| :question: Train   | --stats_size STATS_SIZE                                      | Average this many iterations for computing an average loss, label error rate and training time |
| :question:Train    | --no_skip_invalid_gt                                         | Do no skip invalid gt, instead raise an exception.           |
| Output             | --output_model_prefix OUTPUT_MODEL_PREFIX                    | Prefix for storing checkpoints and models                    |
| Model              | --bidi_dir {ltr,rtl,auto}                                    | The default text direction when preprocessing bidirectional text. Supported values are 'auto' to  automatically detect the direction, 'ltr' and 'rtl'  for left-to-right and right-to-left, respectively |
| Model              | --weights WEIGHTS                                            | Load network weights from the given file.                    |
| :question:Data     | --no_auto_compute_codec                                      | Do not compute the codec automatically. See also whitelist   |
| :question:         | --whitelist_files WHITELIST_FILES [WHITELIST_FILES ...]      | Whitelist of txt files that may not be removed on restoring a model: Specify either individual characters or a text file listing all white list characters stored as string. |
| :question:         | --whitelist WHITELIST [WHITELIST ...]                        | Whitelist of characters that may not be removed on restoring a model. For large datasets you can use this to skip the automatic codec computation (see --no_auto_compute_codec) |
| Train              | --gradient_clipping_mode GRADIENT_CLIPPING_MODE              | Clipping mode of gradients. Defaults to AUTO, possible values are AUTO, NONE, CONSTANT |
| Train              | --gradient_clipping_const GRADIENT_CLIPPING_CONST            | Clipping constant of gradients in CONSTANT mode.             |
| Input              | --validation VALIDATION [VALIDATION ...]                     | Validation line files used for early stopping                |
| Input              | --validation_text_files VALIDATION_TEXT_FILES [VALIDATION_TEXT_FILES ...] | Optional list of validation GT files if they are in other directory |
| Input              | --validation_extension VALIDATION_EXTENSION                  | Default extension of the gt files (expected to exist  in same dir) |
| :question:Input    | --validation_dataset {RAW,FILE,ABBYY,PAGEXML,EXTENDED_PREDICTION} |                                                              |
| Train              | --validation_data_on_the_fly                                 | Instead of preloading all data during the training,  load the data on the fly. This is slower, but might be required for limited RAM or large datasets |
| :question:Train    | --early_stopping_frequency EARLY_STOPPING_FREQUENCY          | The frequency of early stopping. By default the checkpoint frequency uses the early stopping  frequency. By default (value = 0.5) the early stopping frequency equates to a half epoch. If 0 < value <= 1 the frequency has the unit of an epoch (relative to  number of training data). |
| Train              | --early_stopping_nbest EARLY_STOPPING_NBEST                  | The number of models that must be worse than the  current best model to stop |
| Output             | --early_stopping_best_model_prefix EARLY_STOPPING_BEST_MODEL_PREFIX | The prefix of the best model using early stopping            |
| Output             | --early_stopping_best_model_output_dir EARLY_STOPPING_BEST_MODEL_OUTPUT_DIR | Path where to store the best model. Default is output_dir    |
| Data               | --n_augmentations N_AUGMENTATIONS                            | Amount of data augmentation per line (done before training). If this number is < 1 the amount is relative. |
| Train/Augmentation | --only_train_on_augmented                                    | When training with augmentations usually the model is retrained in a second run with only the non augmented data. This will take longer. Use this flag to disable this behavior. |
| :question:Train    | --fuzzy_ctc_library_path FUZZY_CTC_LIBRARY_PATH              | The fuzzy ctc module is not included in the official tensorflow, you need to compile it yourself. The resulting library (.so) must be loaded explicitly to  make the functions available to calamari |
| :question:         | --num_inter_threads NUM_INTER_THREADS                        | Tensorflow's session inter threads param                     |
| :question:         | --num_intra_threads NUM_INTRA_THREADS                        | Tensorflow's session intra threads param                     |
| :question:         | --text_regularization TEXT_REGULARIZATION [TEXT_REGULARIZATION ...] | Text regularization to apply.                                |
| :question:         | --text_normalization TEXT_NORMALIZATION                      | Unicode text normalization to apply. Defaults to NFC         |

#### Training a n-fold of models

To train n more-or-less individual models given a training set you can use the `calamari-cross-fold-train`-script. The default call is

```
calamari-cross-fold-train --files your_images*.*.png --best_models_dir some_dir
```

By default this will train 5 default models using 80%=(n-1)/n of the provided data for training and 20%=1/n for validation. These independent models can then be used to predict lines using a voting mechanism. There are several important parameters to adjust the training. For a full list type `calamari-cross-fold-train --help`.

- Almost parameters of `calamari-train` can be used to affect the training
- `--n_folds=5`: The number of folds
- `--weights=None`: Specify one or `n_folds` models to use for pretraining.
- `--best_models_dir=REQUIRED`: Directory where to store the best model determined on the validation data set
- `--best_model_label={id}`: The prefix for each of the best model of each fold. A string that will be formatted. `{id}` will be replaced by the number of the fold, i. e. 0, ..., n-1.
- `--temporary_dir=None`: A directory where to store temporary files, e. g. checkpoints of the scripts to train an individual model. By default a temporary dir using pythons `tempfile` modules is used.
- `--max_parallel_models=n_folds`: The number of models that shall be run in parallel. By default all models are trained in parallel.
- `--single_fold=[]`: Use this parameter to train only a subset, e. g. a single fold out of all `n_folds`.

To use all models to predict and then vote for a set of lines you can use the `calamari-predict` script and provide all models as `checkpoint`:

```
calamari-predict --checkpoint best_models_dir/*.ckpt.json --files your_images.*.png
```

### 

Evaluation:

```
calamari-eval --gt *.gt.txt
```

on the ground truth files to compute an evaluation measure including the full confusion matrix. By default the predicted sentences as produced by the `calamari-predict` script end in `.pred.txt`. You can change the default behavior of the validation script by the following parameters

- `--gt=REQUIRED`: The ground truth txt files.
- `--pred=None`: The prediction files. If `None` it is expected that the prediction files have the same base name as the ground truth files but with `--pred_ext` as suffix.
- `--pred_ext=.pred.txt`: The suffix of the prediction files if `--pred` is not specified
- `--n_confusions=-1`: Print only the top `n_confusions` most common errors.

## Tesseract Parameters

1. [**ocropus**](#ocropus-parameters)

2. [**kraken**](#kraken-parameters)

3. [**calamari**](#calamari-parameters)

4. [**comparison**](#comparison-of-ocr-engines)

5. [**tutorial**](https://github.com/tesseract-ocr/tesseract/wiki/TrainingTesseract-4.00#tutorial-guide-to-lstmtraining)

   Instead of a `unicharset` and `script_dir,` `lstmtraining` now takes a `traineddata` file on its command-line, to obtain all the information it needs on the language to be learned. The `traineddata` *must* contain at least an `lstm-unicharset` and `lstm-recoder` component, and may also contain the three dawg files: `lstm-punc-dawg lstm-word-dawg lstm-number-dawg` A `config` file is also optional. The other components, if present, will be ignored and unused.

   `combine_lang_model` 

   -  Input :
     -  `input_unicharset`
     -  `script_dir`(`script_dir` points to the `langdata` directory)
     -  `lang` (`lang` is the language being used) and optional word list files.
   - Output:
     -  It creates the `lstm-recoder` from the `input_unicharset` and creates all the dawgs, if wordlists are provided, putting everything together into a `traineddata`file.

|                 | **Flag**               | **Type** | **Default** | **Explanation**                                              |
| --------------- | ---------------------- | -------- | ----------- | ------------------------------------------------------------ |
| Data            | `traineddata`          | `string` | none        | Path to the starter traineddata file that contains the unicharset, recoder and optional language model. |
| Model           | `net_spec`             | `string` | none        | Specifies the topology of the network.                       |
| Output          | `model_output`         | `string` | none        | Base path of output model files/checkpoints.                 |
| Train           | `max_image_MB`         | `int`    | `6000`      | Maximum amount of memory to use for caching images.          |
| :question:Train | `sequential_training`  | `bool`   | `false`     | Set to true for sequential training. Default is to process all training data in round-robin fashion. |
| Model           | `net_mode`             | `int`    | `192`       | Flags from `NetworkFlags`in `network.h`. Possible values: `128` for Adam optimization instead of momentum; `64` to allow different layers to have their own learning rates, discovered automatically. |
| Train           | `perfect_sample_delay` | `int`    | `0`         | When the network gets good, only backprop a perfect sample after this many imperfect samples have been seen since the last perfect sample was allowed through. |
| Train           | `debug_interval`       | `int`    | `0`         | If non-zero, show visual debugging every this many iterations. |
| Model           | `weight_range`         | `double` | `0.1`       | Range of random values to initialize weights.                |
| Train           | `momentum`             | `double` | `0.5`       | Momentum for alpha smoothing gradients.                      |
| Train           | `adam_beta`            | `double` | `0.999`     | Smoothing factor squared gradients in ADAM algorithm.        |
| Train           | `max_iterations`       | `int`    | `0`         | Stop training after this many iterations.                    |
| Train           | `target_error_rate`    | `double` | `0.01`      | Stop training if the mean percent error rate gets below this value. |
| Train           | `continue_from`        | `string` | none        | Path to previous checkpoint from which to continue training or fine tune (training checkpoint **or** a recognition model) |
| :question:Train | `stop_training`        | `bool`   | `false`     | Convert the training checkpoint in `--continue_from` to a recognition model. |
| Train           | `convert_to_int`       | `bool`   | `false`     | With `stop_training`, convert to 8-bit integer for greater speed, with slightly less accuracy. |
| Model           | `append_index`         | `int`    | `-1`        | Cut the head off the network at the given index and append `--net_spec`network in place of the cut off part. |
| Input           | `train_listfile`       | `string` | none        | Filename of a file listing training data files.              |
| Input           | `eval_listfile`        | `string` | none        | Filename of a file listing evaluation data files to be used in evaluating the model independently of the training data. |

