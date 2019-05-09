### Training

Steps:

  1. Generate box files

     * **Input**:

       * data/ground-truth/\*.tif 
       * data/ground-truth/\*.gt.txt

     * **Output**: data/ground-truth/*.box files

     * **Command**: 
       
       ```bash
       python generate_box_files.py -i "data/ground-truth/???.tif" -t "data/ground-truth/???.gt.txt" > "data/ground-truth/???.box"
       ```

  2. Generate "data/all-boxes" file

     * **Input**: data/ground-truth/*.box files

     * **Output**: data/ground-truth/all-boxes

     * **Comand**

       ```bash
       find ground-truth -name 'data/ground-truth/*.box' -exec cat {} \; > data/all_boxes
       ```

  3. Generate unicharset

     * **Input**: data/ground-truth/all-boxes

     * **Output**: data/unicharset

     * **Command**:

       ```bash
       unicharset_extractor --output_unicharset "data/unicharset" --norm_mode 1 "data/all-boxes"
       ```

  4. Generate all lstmf files

     * **Input**: 'data/ground-truth/???.tif' 'data/ground-truth/???.box' 

     * **Output**: 'data/ground-truth/???.lstmf'

     * **Comand**:

       ```bash
       tesseract data/ground-truth/???.tif data/ground-truth/??? --psm 7 lstm.train
       ```

  5. Generate "data/all-lstmf" file

     * **Input**: data/ground-truth/*.lstmf

     * **Output**: data/all-lstmf

     * **Command**:

       ```bash
       find data/ground-truth -name '*.lstmf' -exec echo {} \; | sort -R -o data/all-lstmf
       ```

  6. Split into list.train and list.eval

     * **Input**: data/all-lstmf
     * **Output**: 
       * data/list.train 
       * data/list.eval

  7. Generate protomodel

     * **Input**:

       *  data/unicharset 
       * data/radical-stroke.txt

     * **Output**:

     * **Command**:

       ```bash
       wget -O data2/radical-stroke.txt 'https://github.com/tesseract-ocr/langdata_lstm/raw/master/radical-stroke.txt'
       mkdir data/model
       combine_lang_model --input_unicharset data/unicharset  --script_dir data/ --output_dir data/ --lang model
       ```

  8. train the model 

     * **Input**: 

       * data/model_tess/model_tess.traineddata
       * data/list.train
       * data/list.eval

     * **Output**: checkpoints/model_tess_checkpoint

     * **Command**:

       ```bash
       mkdir -p data/checkpoints
       lstmtraining \
       	  --traineddata data/model_tess/model_tess.traineddata\
       	  --net_spec "[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c`head -n1 data/unicharset`]" \
       	  --model_output data/checkpoints/model \
       	  --learning_rate 20e-4 \
       	  --train_listfile data/list.train \
       	  --eval_listfile data/list.eval \
       	  --max_iterations 10000
       ```

       

### Continue Training



### Evaluation

* **Input**

* **Output**

* **Command**

  ```bash
  lstmeval --model data/checkpoint/model_checkpoint \
  				 --traineddata data/model/model.traineddata \
  				 --eval_listfile data/list.eval
  ```

  