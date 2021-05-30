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

def decode_newlines(inp):
  return inp.replace(Config.new_line_tag, "\n")

def encode_newlines(inp):
  return inp.replace("\n", Config.new_line_tag)

def auto_complete(inp):
  inp = encode_newlines(inp)
  newline_count = inp.count(Config.new_line_tag)

  input_ids = tokenizer.encode(inp, return_tensors="pt").to("cuda")

  model_output = model.generate(input_ids,
                                max_length=Config.prediction_size, 
                                num_beams=Config.beam_count, 
                                temperature=0.7, 
                                no_repeat_ngram_size=5, 
                                num_return_sequences=Config.num_return_sequences, 
                                return_dict_in_generate=True, 
                                output_scores=True)

  sequence = model_output["sequences"][0]
  decoded = decode_newlines(tokenizer.decode(sequence))

  # print("Debug whole decoded message:")
  # print(40*"-")
  # print(decoded)
  # print(40*"-")

  auto_completed = ""
  split = decoded.split("\n")
  for s in split[:newline_count+1]:
    auto_completed += s + "\n"

  return auto_completed

while True:
  try:
    inp = input(">>> ")
    print("\nAutocomplete:\n" + auto_complete(inp.rstrip()))
  except KeyboardInterrupt:
    break

