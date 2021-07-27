# quenya-translator

An attempt to use machine translation to translate between the low-resource artificial language (Neo-)Quenya, and English.


## The preprocessing CLI

Usage:
```bash
python preprocess.py [-h] [--outdir PATH] [--punct {keep,pad,remove}] 
                     [--split TRAIN TEST VAL] [--seed SEED] [-uncase]
                     [-stratify]
                     [source directory]
```
Example:
```bash
python preprocess.py data/raw --outdir data/out --punct pad --split 80 10 10 -stratify 
```

To see an explanation of all arguments, use the help option `-h`. 


## The data
[Fauskanger's translation of The New Testament in Neo-Quenya](https://folk.uib.no/hnohf/nqnt.htm) was used and slightly modifed.
The following modifications were performed: 
* The `.doc` files were converted to `.txt` using macOS's `textutil`.
* All document preambles (title, date, etc.) were separated from the body. 
* Unbalanced numbers of paragraphs per document and verses per paragraph were detected (missing newlines or verse numbers) and fixed manually if possible. Chapters or verses with missing translation were either removed or marked as "\[REMOVED\]" to be ignored by the preprocessing pipeline.


## The training

[fairseq](https://github.com/pytorch/fairseq) was used to tokenize, train and evaluate a Transformer model.

The following commands were used:

###### Tokenization
```bash
fairseq-preprocess \
	--source-lang en \
	--target-lang qy \
	--trainpref $TEXTDIR/train \
	--testpref $TEXTDIR/test \
	--validpref $TEXTDIR/val \
	--tokenizer moses \
	--destdir $DATADIR \
	--workers 4
```

###### Training

First phase:
```bash
fairseq-train $DATADIR \
	--save-dir $MODELDIR \
	--log-format json \
	--arch transformer_iwslt_de_en \
	--optimizer adam \
	--adam-betas (0.9,0.98) \
	--clip-norm 0.0 \
	--lr 1e-3 \
	--lr-scheduler inverse_sqrt \
	--warmup-updates 4000 \
	--dropout 0.3 \
	--weight-decay 1e-4 \
	--criterion label_smoothed_cross_entropy \
	--label-smoothing 0.1 \
	--max-tokens 4096 \
	--eval-bleu \
	--eval-bleu-detok moses \
	--eval-bleu-remove-bpe \
	--best-checkpoint-metric bleu \
	--maximize-best-checkpoint-metric \
	--max-epoch 300 \
	--patience 10 \
	--log-interval 100 \
	--no-progress-bar \
	--no-epoch-checkpoints \
	--keep-best-checkpoints 3 \
	--num-workers 0
```

The command for the second phase is the same except for `--lr 1e-5` and `--restore-file $MODELDIR/checkpoint_best.pt`.

Training was performed on an NVIDIA RTX 2080 Ti and took on average 3380s, 142 epochs and 23s/epoch, of which approx. 60% is the first phase.


###### Evaluation
```bash
fairseq-generate $DATADIR \
    --path $MODELDIR/checkpoint_best.pt \
    --gen-subset test \
    --batch-size 128 --beam 5 --remove-bpe
```

## The results

 During testing of different preprocessing options and training parameters, model performance varied between a BLEU score of only 35 up to almost 47, averaging around 44. The best performing model achieved `BLEU4 = 44.99` on the validation set and `BLEU4 = 46.87, 75.3/55.2/41.8/32.2 (BP=0.964, ratio=0.964, syslen=15841, reflen=16428)` on the testset, using the exact commands given in this README.