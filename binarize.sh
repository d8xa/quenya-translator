S=$1
T=$2

ARGS=(
    --source-lang $S
	--target-lang $T
	--trainpref $TEXTDIR/train
	--testpref $TEXTDIR/test
	--validpref $TEXTDIR/val
	--tokenizer moses
    #--bpe subword_nmt
	--destdir $DATADIR/$S-$T
	--workers 4
)

fairseq-preprocess "${ARGS[@]}"