S=$1
T=$2

ARGS=(
    --sys gens/$S-$T.out.sys 
    --ref gens/$S-$T.out.ref
)

fairseq-score "${ARGS[@]}" 