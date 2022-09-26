S=$1
T=$2
DATADIR=bin/$S-$T
MODELDIR=model/$S-$T

ARGS=(
    $DATADIR
    --path $MODELDIR/checkpoint_best.pt
    --gen-subset test
    --batch-size 128 
	--beam 5 
	--scoring bleu
	#--scoring wer
	#--scoring chrf
	#--remove-bpe

)

fairseq-generate "${ARGS[@]}"