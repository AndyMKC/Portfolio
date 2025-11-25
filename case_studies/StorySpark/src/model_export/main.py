# export_with_pooling.py
import torch
from pathlib import Path
from transformers import AutoModel, AutoTokenizer

class EncoderWithPooling(torch.nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.base = base_model

    def forward(self, input_ids, attention_mask):
        # base model returns last_hidden_state as first output for most HF encoders
        outputs = self.base(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
        token_embeddings = outputs.last_hidden_state  # [batch, seq, hidden]
        # compute mean pooling with attention mask
        mask = attention_mask.unsqueeze(-1).to(dtype=token_embeddings.dtype)  # [batch, seq, 1]
        summed = (token_embeddings * mask).sum(dim=1)  # [batch, hidden]
        counts = mask.sum(dim=1).clamp(min=1e-9)       # [batch, 1]
        pooled = summed / counts                      # [batch, hidden]
        # optional: L2 normalize (sentence-transformers does this by default for many models)
        norm = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return norm  # [batch, hidden]

if __name__ == "__main__":
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    out_dir = Path("models")
    out_dir.mkdir(parents=True, exist_ok=True) 
    export_path = out_dir / "all-MiniLM-L6-v2.onnx"

    # load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    base_model = AutoModel.from_pretrained(model_name)
    wrapper = EncoderWithPooling(base_model)
    wrapper.eval()

    # ensure CPU for export (simpler and more portable)
    wrapper.to("cpu")

    # prepare a dummy input (batch size 1, short sequence)
    dummy = tokenizer("Hello world", return_tensors="pt")
    input_ids = dummy["input_ids"].to("cpu")
    attention_mask = dummy["attention_mask"].to("cpu")

    # dynamic axes: batch and sequence are dynamic
    dynamic_shapes = {
        "input_ids": {0: None, 1: None},        # batch and seq dynamic
        "attention_mask": {0: None, 1: None}
        }

    # Export with opset 18
    torch.onnx.export(
        wrapper,
        (input_ids, attention_mask),
        export_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["output"],
        opset_version=18,
        dynamo=True,
        dynamic_shapes=dynamic_shapes,
        do_constant_folding=True
    )

    print(f"Model exported to {export_path}")
