from transformers import PreTrainedTokenizerFast, GPT2Config, GPT2LMHeadModel, DataCollatorForLanguageModeling, Trainer, TrainingArguments
from datasets import load_dataset
from config_loader import Config
import os
import sys

assert len(sys.argv) == 2, "Enter input tokenizer name as first argument (.json)"
TOKENIZER = sys.argv[1]

PATHS = [os.path.join("github_data", f) for f in os.listdir("github_data")]

EPOCHS = Config.epochs
BATCH_SIZE = Config.batch_size

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

mod_config = GPT2Config(vocab_size=tokenizer.vocab_size, bos_token_id=tokenizer.bos_token_id, eos_token_id=tokenizer.eos_token_id,
                        n_positions=Config.n_positions, n_ctx=Config.n_ctx, n_embd=Config.n_embd, n_layer=Config.n_layer, n_head=Config.n_head)
model = GPT2LMHeadModel(mod_config)

def encode(lines):
  return tokenizer(lines["text"], add_special_tokens=True, truncation=True, max_length=Config.n_positions)

dataset = load_dataset("text", data_files=PATHS)
dataset.set_transform(encode)
dataset = dataset["train"]

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=True, mlm_probability=0.15)

if not os.path.exists("GPyT"): os.mkdir("GPyT")

training_args = TrainingArguments(
  output_dir="./GPyT",
  overwrite_output_dir=True,
  num_train_epochs=EPOCHS,
  per_device_train_batch_size=BATCH_SIZE,
  save_steps=Config.save_steps,
  save_total_limit=2,
  prediction_loss_only=True,
  remove_unused_columns=False,
  dataloader_num_workers=2
)

trainer = Trainer(
  model=model,
  args=training_args,
  data_collator=data_collator,
  train_dataset=dataset
)

trainer.train()
trainer.save_model("GPyT")