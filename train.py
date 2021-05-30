from transformers import PreTrainedTokenizerFast, GPT2Config, GPT2LMHeadModel, DataCollatorForLanguageModeling, Trainer, TrainingArguments
from datasets import load_dataset
from config_loader import Config
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--input_data", "-i", help="Path to training data", required=False, default="github_data", type=str)
parser.add_argument("--tokenizer_path", "-t", help="Path to tokenizer file", required=False, default="tokenizers/BLTokenizer.json", type=str)
parser.add_argument("--output", "-o", help="Output folder path for model", required=False, default="GPyT", type=str)
parser.add_argument("--cache_dir", "-c", help="Path to directory where dataset cache will be stored (best on some ssd)", required=False, default=None, type=str)

args = parser.parse_args()

assert os.path.exists(args.input_data) and os.path.isdir(args.input_data), "Invalid training data path"
assert os.path.exists(args.tokenizer_path) and os.path.isfile(args.tokenizer_path), "Invalid path to tokenizer file"

PATHS = [os.path.join(args.input_data, f) for f in os.listdir(args.input_data)]

EPOCHS = Config.epochs
BATCH_SIZE = Config.batch_size

TOKENIZER = args.tokenizer_path

tokenizer = PreTrainedTokenizerFast(tokenizer_file=TOKENIZER)
tokenizer.add_special_tokens({
  "eos_token": "</s>",
  "bos_token": "<s>",
  "unk_token": "<unk>",
  "pad_token": "<pad>",
  "mask_token": "<mask>"
})

mod_config = GPT2Config(vocab_size=tokenizer.vocab_size, bos_token_id=tokenizer.bos_token_id, eos_token_id=tokenizer.eos_token_id,
                        n_positions=Config.n_positions, n_ctx=Config.n_ctx, n_embd=Config.n_embd, n_layer=Config.n_layer, n_head=Config.n_head)
model = GPT2LMHeadModel(mod_config)

def encode(lines):
  return tokenizer(lines["text"], add_special_tokens=True, truncation=True, max_length=Config.n_positions)

dataset = load_dataset("text", data_files=PATHS, cache_dir=args.cache_dir)
dataset.set_transform(encode)
dataset = dataset["train"]

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=True, mlm_probability=0.15)

if not os.path.exists(args.output): os.mkdir(args.output)

training_args = TrainingArguments(
  output_dir=args.output,
  overwrite_output_dir=True,
  num_train_epochs=EPOCHS,
  per_device_train_batch_size=BATCH_SIZE,
  save_steps=Config.save_steps,
  save_total_limit=2,
  prediction_loss_only=True,
  remove_unused_columns=False
)

trainer = Trainer(
  model=model,
  args=training_args,
  data_collator=data_collator,
  train_dataset=dataset
)

try:
  if any([("checkpoint" in p) for p in os.listdir(args.output)]):
    trainer.train(resume_from_checkpoint=True)
  else:
    trainer.train()
    
  trainer.save_model(args.output)
except KeyboardInterrupt:
  pass