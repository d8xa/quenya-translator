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