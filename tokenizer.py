from tokenizers import Tokenizer, models, pre_tokenizers, decoders, processors, trainers
from transformers import PreTrainedTokenizerFast
import os
import sys

TOKENIZER = "BLTokenizer.json"
PATHS = [os.path.join("github_data", f) for f in os.listdir("github_data")]
TRAIN = True

for p in PATHS:
  if not os.path.exists(p) or not os.path.isfile(p):
    print(f"Invalid input file {p}")
    sys.exit(1)

if not os.path.exists("tokenizers"): os.mkdir("tokenizers")
TOKENIZER = os.path.join("tokenizers", TOKENIZER)

if TRAIN:
  tokenizer = Tokenizer(models.BPE())

  tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=True)
  tokenizer.decoder = decoders.ByteLevel()
  tokenizer.post_processor = processors.ByteLevel(trim_offsets=True)

  trainer = trainers.BpeTrainer(vocab_size=52_000, min_frequency=2, special_tokens=[
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