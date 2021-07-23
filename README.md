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
python preprocess.py data/raw --outdir data/out --punct pad --split 75 15 10 -stratify 
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

Tokenize:
```bash
fairseq-preprocess --destdir $DATADIR/tokenized.en-qy 
    --source-lang en --target-lang qy \
    --trainpref $TEXTDIR/train --testpref $TEXTDIR/test --validpref $TEXTDIR/val \
    --tokenizer moses \
    --workers 8
```

Train:
```bash
fairseq-train \
    $DATADIR \
    --save-dir $MODELDIR \
    --tensorboard-logdir $LOGDIR \
    --arch transformer_iwslt_de_en \
    --share-decoder-input-output-embed \
    --optimizer adam --adam-betas (0.9,0.98)
    --lr 1e-3 --lr-scheduler inverse_sqrt \
    --warmup-updates 4000 \
    --clip-norm 0.0 --dropout 0.3 --weight-decay 0.0001 \
    --criterion label_smoothed_cross_entropy --label-smoothing 0.1 \
    --max-tokens 4096 \
    --eval-bleu \
    --eval-bleu-detok moses \
    --eval-bleu-remove-bpe \
    --best-checkpoint-metric bleu --maximize-best-checkpoint-metric
    --fixed-validation-seed 7
    --keep-last-epochs 15
    --patience 10
```

Evaluate:
```bash
fairseq-generate $DATADIR \
    --path $MODELDIR/checkpoint_best.pt \
    --gen-subset test
    --batch-size 128 --beam 5 --remove-bpe
```