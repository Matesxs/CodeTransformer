from transformers import PreTrainedTokenizerFast, GPT2LMHeadModel
import os
import argparse
from config_loader import Config

parser = argparse.ArgumentParser()
parser.add_argument("--tokenizer_path", "-t", help="Path to tokenizer file", required=False, default="tokenizers/BLTokenizer.json", type=str)
parser.add_argument("--model", "-m", help="Path to valid model folder", required=False, default="GPyT", type=str)

args = parser.parse_args()

assert os.path.exists(args.tokenizer_path) and os.path.isfile(args.tokenizer_path), "Invalid path to tokenizer file"
assert os.path.exists(args.model) and os.path.isdir(args.model), "Invalid path to model folder"

TOKENIZER = args.tokenizer_path
MODEL_PATH = args.model

tokenizer = PreTrainedTokenizerFast(tokenizer_file=TOKENIZER)
tokenizer.add_special_tokens({
  "eos_token": "</s>",
  "bos_token": "<s>",
  "unk_token": "<unk>",
  "pad_token": "<pad>",
  "mask_token": "<mask>"
})

model = GPT2LMHeadModel.from_pretrained(MODEL_PATH).to("cuda")

while True:
  inp = input(">>> ")
  input_ids = tokenizer.encode(inp, return_tensors="pt").to("cuda")
  beam_output = model.generate(input_ids, max_length=Config.n_positions, num_beams=10, temperature=0.7, no_repeat_ngram_size=5, num_return_sequences=1)

  for beam in beam_output:
    out = tokenizer.decode(beam)
    fout = out.replace("<newl>", "\n")
    print(str(fout))