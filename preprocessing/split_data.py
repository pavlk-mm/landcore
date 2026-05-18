#!/usr/bin/env python3
"""
Script for splitting documents in a file into multiple sets (train, tuning, dev, etc.).
"""

import argparse
from dataclasses import dataclass
import random
from pathlib import Path
import re

@dataclass
class Document:
    """
    Represents a document with its content and metadata.
    """
    doc_id: str
    word_count: int
    content: str

def load_plaintext_documents(file_path):
    """
    Load plaintext documents from a file. Each document is on a single line,
    tokenized by whitespace. The number of the line is used as the document ID,
    and the word count is calculated.
    
    :param file_path: Path to the input file
    :return: List of Document objects
    """
    documents = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            content = line.strip()
            word_count = len(content.split())
            documents.append(Document(doc_id=f"doc{i}", word_count=word_count, content=content))
    return documents

def load_conllu_documents(file_path):
    """
    Load documents from a CoNLL-U formatted file. Each document starts with a
    comment line # newdoc id = <doc_id>. The document content is the lines
    following the comment until the next # newdoc or the end of the file. The
    word count is calculated based on the number of token lines in the document.
    
    :param file_path: Path to the input CoNLL-U file
    :return: List of Document objects
    """
    documents = []
    doc_id, content_lines, word_count = None, [], 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if match := re.match(r"^#\s*newdoc\s*id\s*=\s*(.*?)\s*$", line):
                if doc_id is not None:
                    documents.append(Document(doc_id=doc_id, word_count=word_count, content="\n".join(content_lines)))
                doc_id, content_lines, word_count = None, [], 0
                doc_id = match.group(1)
            elif re.match(r"^\d+\t", line):
                word_count += 1
            content_lines.append(line)
    # Add the last document if it exists
    if doc_id is not None:
        documents.append(Document(doc_id=doc_id, word_count=word_count, content="\n".join(content_lines)))
    return documents

def split_file(input_file, output_files, format='auto', split_ratio=[0.2, 0.2], upper_bounds=None, shuffle=False, seed=42, allow_empty_splits=False):
    """
    Split lines from input_file into train and tuning sets.
    
    Args:
        input_file: Path to input file
        output_files: List of paths to output files
        format: Format of the input file ('auto', 'plaintext', 'conllu')
        split_ratio: Ratio of data to use for each split (default: [0.2, 0.2]).
        The last split will take the remaining data (1 - sum(split_ratio)).
        upper_bounds: Optional list of upper bounds for each split (default: None)
        shuffle: Whether to shuffle the lines before splitting (default: False)
        seed: Random seed for reproducibility (default: 42)
        allow_empty_splits: Allow splits to be empty if split ratios are small (default: False)
    """
    if not (len(split_ratio) == len(output_files) - 1):
        raise ValueError("Length of split_ratio must be one less than the number of output_files.")
    if upper_bounds and len(upper_bounds) != len(output_files) - 1:
        raise ValueError("Length of upper_bounds must be one less than the number of output_files.")

    if format == 'auto':
        if input_file.endswith('.conllu'):
            format = 'conllu'
        elif input_file.endswith('.txt'):
            format = 'plaintext'
        else:
            raise ValueError("Could not determine file format. Please specify --format.")

    if format == 'plaintext':
        documents = load_plaintext_documents(input_file)
    elif format == 'conllu':
        documents = load_conllu_documents(input_file)
    
    # Shuffle if requested
    if shuffle:
        random.seed(seed)
        random.shuffle(documents)
    
    # Calculate split points
    normalized_ratios = [len(documents) * r for r in split_ratio]
    split_points = [int(sum(normalized_ratios[:i+1])) for i in range(len(normalized_ratios))]

    split_documets = []
    split_word_counts = []
    current_split = 0
    word_count = 0
    docs = []
    for idoc, doc in enumerate(documents):
        if current_split < len(split_points) and (allow_empty_splits or len(docs) > 0) and \
            ((upper_bounds and word_count + doc.word_count > upper_bounds[current_split]) \
            or idoc >= split_points[current_split]):
            split_documets.append(docs)
            split_word_counts.append(word_count)
            docs = []
            word_count = 0
            current_split += 1
        docs.append(doc)
        word_count += doc.word_count

    if docs:
        split_documets.append(docs)
        split_word_counts.append(word_count)
    
    # Write output files
    for split_docs, output_file in zip(split_documets, output_files):
        with open(output_file, 'w', encoding='utf-8') as f:
            for doc in split_docs:
                f.write(doc.content + '\n')
    
    print(f"Split complete:")
    for i, (output_file, split_docs, word_count) in enumerate(zip(output_files, split_documets, split_word_counts)):
        print(f"  Split {i} ({output_file}): {len(split_docs)} documents, {word_count} words")


def main():
    parser = argparse.ArgumentParser(
        description='Split a file into train and tuning sets',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input_file', type=str,
                        help='Path to the input file')
    parser.add_argument('--output-files', '-o', nargs="+",
                        help='Paths to output files for each split (default: auto-generated based on input file name)')
    parser.add_argument('--split-ratio', '-r', type=str, default='0.2,0.2',
                        help='Comma-separated list of ratios for n-1 splits (each must be between 0.0 and 1.0)')
    parser.add_argument('--format', '-f', choices=['auto', 'plaintext', 'conllu'], default='auto',
                        help='Format of the input file (auto-detected by extension)')
    parser.add_argument('--upper-bounds', '-u', type=str, default=None,
                        help='comma-separated list of upper bounds for n-1 splits (in words)')
    parser.add_argument('--shuffle', '-s', action='store_true',
                        help='Shuffle lines before splitting')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for shuffling')
    parser.add_argument('--allow-empty-splits', action='store_true',
                        help='Allow splits to be empty if split ratios are small')
    
    args = parser.parse_args()
    
    # Parse and validate split ratio
    args.split_ratio = [float(r) for r in args.split_ratio.split(',')]
    if not all(0.0 < r < 1.0 for r in args.split_ratio):
        parser.error("Split ratio must be between 0.0 and 1.0")
    
    # Set default output file names if not provided
    input_path = Path(args.input_file)
    input_extension = input_path.suffix
    if args.output_files:
        if len(args.output_files) != len(args.split_ratio) + 1:
            parser.error(f"Number of output files must be {len(args.split_ratio) + 1} (one for each split)")
    else:
        args.output_files = [str(input_path.with_suffix(f".split{i}{input_extension}")) for i in range(len(args.split_ratio) + 1)]

    # Parse upper bounds if provided
    if args.upper_bounds:
        args.upper_bounds = [int(u) for u in args.upper_bounds.split(',')]
        if not all(u > 0 for u in args.upper_bounds):
            parser.error("Upper bounds must be positive integers")
    else:
        args.upper_bounds = None

    # Perform the split
    split_file(
        args.input_file,
        args.output_files,
        args.format,
        args.split_ratio,
        args.upper_bounds,
        args.shuffle,
        args.seed,
        args.allow_empty_splits
    )


if __name__ == '__main__':
    main()
