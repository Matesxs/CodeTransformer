import sys
import toml

try:
  toml_dict: dict = toml.load("config.toml", _dict=dict)
except:
  print("Cant find config.toml, trying to load config.template.toml")
  try:
    toml_dict: dict = toml.load("config.template.toml", _dict=dict)
  except:
    print("Failed to load config")
    sys.exit(1)

def get_attr(section: str, attr_key: str):
  try:
    return toml_dict[section][attr_key]
  except KeyError:
    print(f"Cant find {attr_key} in {section} section of config, check if your config is not corrupted!")
    sys.exit(1)

class Config:
  error_delay_seconds = get_attr("general", "error_delay_seconds")

  github_token = get_attr("github", "github_app_token")
  github_req_delay = get_attr("github", "github_req_delay")
  clone_timeout_seconds = get_attr("github", "clone_timeout_seconds")

  vocabulary_size = get_attr("tokenizer", "vocabulary_size")
  new_line_tag = get_attr("tokenizer", "new_line_tag")

  n_positions = get_attr("model", "n_positions")
  n_ctx = get_attr("model", "n_ctx")
  n_embd = get_attr("model", "n_embd")
  n_layer = get_attr("model", "n_layer")
  n_head = get_attr("model", "n_head")

  batch_size = get_attr("training", "batch_size")
  epochs = get_attr("training", "epochs")
  save_steps = get_attr("training", "save_steps")

  prediction_size = get_attr("generate", "prediction_size")
  beam_count = get_attr("generate", "beam_count")
  num_return_sequences = get_attr("generate", "num_return_sequences")