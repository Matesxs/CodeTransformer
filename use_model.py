from transformers import PreTrainedTokenizerFast, GPT2LMHeadModel
import config
import os
import sys

TOKENIZER = "BLTokenizer.json"
MODEL_PATH = "GPyT/checkpoint-44000"

if not os.path.exists("tokenizers"): os.mkdir("tokenizers")
TOKENIZER = os.path.join("tokenizers", TOKENIZER)

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

model = GPT2LMHeadModel.from_pretrained(MODEL_PATH).to("cuda")

while True:
  inp = input(">>> ")
  input_ids = tokenizer.encode(inp, return_tensors="pt").to("cuda")
  beam_output = model.generate(input_ids, max_length=config.n_positions, num_beams=10, temperature=0.7, no_repeat_ngram_size=5, num_return_sequences=1)

  for beam in beam_output:
    out = tokenizer.decode(beam)
    fout = out.replace("<newl>", "\n")
    print(str(fout))