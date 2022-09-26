S=en
T=qy
DATADIR=bin/$S-$T
MODELDIR=model/$S-$T

ARGS=(
    $DATADIR
    --path $MODELDIR/checkpoint_best.pt
    --gen-subset test
    --batch-size 128 
	--beam 5
)

mkdir -p gens

fairseq-generate "${ARGS[@]}" > gens/$S-$T.out

grep ^H gens/$S-$T.out | cut -f3- > gens/$S-$T.out.sys
grep ^T gens/$S-$T.out | cut -f2- > gens/$S-$T.out.ref