for filepath in doc/*; do
    filename=$(basename -- "$filepath")
    extension="${filename##*.}"
    #fname="${filename%.*}"
    outpath="txt/${fname}.txt"
    textutil -convert txt "$filepath" -output "$outpath"
    echo "converted $filename."
done
echo "done."
