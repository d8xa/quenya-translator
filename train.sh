S=$1
T=$2
DATADIR=bin/$S-$T
MODELDIR=model/$S-$T

ARGS=(
    $DATADIR
	--save-dir $MODELDIR
	--log-format json
	--arch transformer_iwslt_de_en
	--optimizer adam
	--adam-betas '(0.9,0.98)'
	--clip-norm 0.0
	--lr 1e-3
	--lr-scheduler inverse_sqrt
	--warmup-updates 4000
	--dropout 0.3
	--weight-decay 1e-4
	--criterion label_smoothed_cross_entropy
	--label-smoothing 0.1
	--max-tokens 4096
	--eval-bleu
	--eval-bleu-detok moses
	#--eval-bleu-remove-bpe
	--best-checkpoint-metric bleu
	--maximize-best-checkpoint-metric
	--max-epoch 300
	--patience 10
	--log-interval 100
	--tensorboard-logdir $MODELDIR/logs
	--no-progress-bar
	--no-epoch-checkpoints
	--keep-best-checkpoints 3
	--num-workers 0
	--fp16
	--source-lang $S
)

fairseq-train "${ARGS[@]}"