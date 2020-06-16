local transformer_model = 'bert-large-cased';

local epochs = 3;
local batch_size = 8;

{
  "dataset_reader": {
      "type": "commonsenseqa",
      "transformer_model_name": transformer_model,
      //"max_instances": 200  // debug setting
  },
  "train_data_path": "https://s3.amazonaws.com/commensenseqa/train_rand_split.jsonl",
  "validation_data_path": "https://s3.amazonaws.com/commensenseqa/dev_rand_split.jsonl",
  //"test_data_path": "https://s3.amazonaws.com/commensenseqa/test_rand_split_no_answers.jsonl"
  "model": {
      "type": "transformer_mc",
      "transformer_model_name": transformer_model,
  },
  "data_loader": {
    "sampler": "random",
    "batch_size": batch_size
  },
  "trainer": {
    "optimizer": {
      "type": "huggingface_adamw",
      "weight_decay": 0.0,
      "parameter_groups": [[["bias", "LayerNorm\\.weight", "layer_norm\\.weight"], {"weight_decay": 0}]],
      "lr": 5e-5,
      "eps": 1e-8
    },
    "learning_rate_scheduler": {
      "type": "slanted_triangular",
      "cut_frac": 0.00,
    },
    "grad_norm": 1.0,
    "num_epochs": epochs,
    "cuda_device": -1
  },
  "random_seed": 42,
  "numpy_seed": 42,
  "pytorch_seed": 42,
}
