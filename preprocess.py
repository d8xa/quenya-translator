import argparse, logging, os, sys
from pathlib import Path
import parsing.pipes as pipes
from parsing.structs import Pipeline
from parsing.tools import stratify_wordcount, read_txts
from argparse import Namespace


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=os.environ.get("LOGLEVEL", "INFO").upper(),
    stream=sys.stdout,
)
logger = logging.getLogger("quenya_tranlation.preprocess")


def preprocess(args):
    # Read files
    txtfiles = [file for file in args.sourcedir.iterdir() if file.suffix==".txt"]
    texts = read_txts(txtfiles)
    logger.info(f"Read text from {len(txtfiles)} files.")
    
    # Build and run pipeline
    components = build_components(args)
    pipeline = Pipeline(components)    
    processed = pipeline.process(texts)
    logger.info("Preprocessing done.")
    
    # Save result
    save_corpora(processed, args)
    logger.info("Preprocessed files saved to output directory.")


def save_corpora(target, args):
    """Save preprocessed data to files."""
    
    if args.split is not None:
        save_params = zip(target,["train", "test", "val"])
    else:
        save_params = zip(target, ["corpus"])
        
    for data,name in save_params:
        for i,lang in enumerate(["en", "qy"]):
            path = Path(args.outdir, f"{name}.{lang}")
            with path.open("w", encoding="utf-8") as f:
                f.write("\n".join(list(data.iloc[:,i])))


def build_components(args):
    """Arrange necessary pipeline components."""

    components = [
        ("create documents", pipes.DocumentMatcher()),
        ("extract paragraphs", pipes.ParagraphMatcher()),
        ("extract verses", pipes.VerseMatcher()),
        ("language tag paragraphs", pipes.ParagraphLanguageTagger()),
        ("language tag verses", pipes.VerseLanguageTagger()),
        ("extract verses to DataFrame", pipes.DataframeTransformer()),
        ("replace annotation", pipes.CleanupStep())
    ]
    
    if args.punct != "keep":
        components += [("pad punctuation", pipes.PunctuationPreprocessing(method=args.punct))]
    if args.uncase: 
        components += [("uncase", pipes.Uncase())]
    components += [("to parallel corpora", pipes.ParallelCorpusTransformer())]
    
    if args.split is not None:
        stratify_function = None
        if args.stratify:
            stratify_function = stratify_wordcount
        splitter = pipes.TrainTestValSplitter(*args.split, stratify_function=stratify_function, random_state=args.seed)
        components += [("split dataset", splitter)]
        
    return components
 

def digest_args(args):
    """Validate arguments or any args are ignored/overridden."""
    
    ## stratifying when splitting is disabled 
    if args.split is None and args.stratify:
        logger.info("splitting is not enabled. Ignoring flag -stratify.")
        
    # check if source path exists, is directory, and not empty.
    args.sourcedir = args.sourcedir.expanduser()
    message = None
    if not args.sourcedir.exists():
        message = "does not exist"
    elif not args.sourcedir.is_dir():
        message = "is not a directory"
    elif not any([x for x in args.sourcedir.iterdir() if x.suffix==".txt"]):
        message = "does not contain any text files to use."
    
    if message is not None:
        raise ValueError(f"Path {args.sourcedir} {message}. Aborting.")

    # check if target path was supplied. If not, the source folder with suffix "-preprocessed" will be used.
    if args.outdir is None:
        args.outdir = Path(args.sourcedir.absolute().parent, args.sourcedir.absolute().stem+'-preprocessed')
    # Check if target path is directory.
    if not args.outdir.exists() and not args.outdir.suffix=='':
        raise ValueError(f"Path {args.outdir} is not a directory. Aborting.")
    # Create target dir if not existing.
    args.outdir.mkdir(parents=True, exist_ok=True)
    
    # Check if split ratios are valid numbers.
    if args.split is not None and ((any([x<0 for x in args.split]) or sum(args.split)==0)):
        raise ValueError("Split ratios are invalid. Only positive numbers are allowed and at least one value has to be non-zero. Aborting.")
    
    # Rescale ratios if sum is not exactly 1.
    if args.split is not None and sum(args.split)!=1:
        args.split = [x/sum(args.split) for x in args.split]
    
    return True



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Preprocess the Quenya-English translations of the New Testament.')

    # Mandatory args
    parser.add_argument('sourcedir', type=Path, nargs='?', metavar='PATH',
                        help='the path of the directory containing the files to preprocess.')
    
    # Optional args
    parser.add_argument('--outdir', dest='outdir', metavar='PATH', type=Path, 
                        help='the directory where the preprocessed files should be placed. If not specified, the source directory with suffix \'-preprocessed\' will be used.')
    parser.add_argument('--punct', choices=['keep', 'pad', 'remove'], default='keep', dest='punct', 
                        help='action to apply to punctuation in the data. \n\'pad\' ensures whitespace around all punctuation; \'remove\' removes all punctuation; \'keep\' (default) leaves punctuation unchanged.')
    parser.add_argument('--split', nargs=3, type=float, metavar=('N', "N", "N"), dest='split', default=None,
                        help='split the dataset into train/test/validation sets with the supplied proportions. Each set will be a separate file.')
    parser.add_argument('--seed', metavar="N", help='define a random seed to be used when splitting the dataset.', dest='seed', type=int)
    #parser.add_argument('--extract', choices=['verses', "phrases", "sentences"], default='verses', dest='extract', 
    #                    help='what to extract from the text.') # TODO
    
    # Flag args
    parser.add_argument('-uncase', action='store_true', help='convert all text to lowercase.')
    parser.add_argument('-stratify', action='store_true', help='stratify the train/test/validation split by wordcount.')
    
    # Parse
    args, unknown = parser.parse_known_args()
    if len(unknown)>0:
        logger.info(f"Options {unknown} were not recognized and will be ignored.")
    
    try: 
        digest_args(args)
    except ValueError as error:
        logger.error(error)
        #raise

    preprocess(args)

