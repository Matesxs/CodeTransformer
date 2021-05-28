from tokenizers import Tokenizer, models, pre_tokenizers, decoders, processors, trainers
from transformers import PreTrainedTokenizerFast
from config_loader import Config
import os
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", help="Path to input data folder", required=False, default="github_data", type=str)
parser.add_argument("--output", "-o", help="Path to output folder", required=False, default="tokenizers", type=str)
parser.add_argument("--name", "-n", help="Name of output file", required=False, default="BLTokenizer.json", type=str)
parser.add_argument("--dont_train", "-T", help="Disable training - only test tokenizer", action="store_false")

args = parser.parse_args()
assert os.path.exists(args.input) and os.path.isdir(args.input), "Invalid input path"

PATHS = [os.path.join(args.input, f) for f in os.listdir(args.input)]

for p in PATHS:
  if not os.path.exists(p) or not os.path.isfile(p):
    print(f"Invalid input file {p}")
    sys.exit(1)

if not os.path.exists(args.output): os.mkdir(args.output)
TOKENIZER = os.path.join(args.output, args.name)

if args.dont_train:
  tokenizer = Tokenizer(models.BPE())

  tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=True)
  tokenizer.decoder = decoders.ByteLevel()
  tokenizer.post_processor = processors.ByteLevel(trim_offsets=True)

  trainer = trainers.BpeTrainer(vocab_size=Config.vocabulary_size, min_frequency=2, special_tokens=[
    "<s>",
    "<pad>",
    "</s>",
    "<unk>",
    "<mask>"
  ])
  tokenizer.train(files=PATHS, trainer=trainer)

  if os.path.exists(TOKENIZER): os.remove(TOKENIZER)

  tokenizer.save(TOKENIZER, pretty=True)

if not os.path.exists(TOKENIZER) or not os.path.isfile(TOKENIZER):
  print("Tokenizer doesnt exist")
  sys.exit(1)

tokenizer = PreTrainedTokenizerFast(tokenizer_file=TOKENIZER)
tokenizer.add_special_tokens({
  "eos_token": "</s>",
  "bos_token": "<s>",
  "unk_token": "<unk>",
  "pad_token": "<pad>",
  "mask_token": "<mask>"
})

print("Tokenizer integrity test")
t = tokenizer.encode("print('Hello world!')")
print(t)
print(tokenizer.decode(t))