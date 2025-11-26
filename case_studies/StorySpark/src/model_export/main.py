# export_with_pooling.py
import torch
import onnx
from onnx import shape_inference, checker
import onnxruntime as ort
from pathlib import Path
from transformers import AutoModel, AutoTokenizer
import numpy as np

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
    
def export_model(model_name: str, out_dir: Path, opset: int = 18):
    out_dir.mkdir(parents=True, exist_ok=True)
    export_path = out_dir / "all-MiniLM-L6-v2.onnx"

    # load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    base_model = AutoModel.from_pretrained(model_name)
    wrapper = EncoderWithPooling(base_model)
    wrapper.eval()
    wrapper.to("cpu")

    # Prepare a multi-example dummy (batch size 2) to avoid batch=1 baking
    texts = ["Hello world", "This is a second example"]
    dummy = tokenizer(texts, padding="longest", truncation=True, return_tensors="pt")
    input_ids = dummy["input_ids"].to("cpu")
    attention_mask = dummy["attention_mask"].to("cpu")

    # dynamic_axes: use the same symbolic name "batch" for all batch dims
    dynamic_axes = {
        "input_ids": {0: "batch", 1: "seq"},
        "attention_mask": {0: "batch", 1: "seq"},
        "output": {0: "batch"},
    }

    # Export
    torch.onnx.export(
        wrapper,
        (input_ids, attention_mask),
        str(export_path),
        input_names=["input_ids", "attention_mask"],
        output_names=["output"],
        opset_version=opset,
        do_constant_folding=True,
        dynamic_axes=dynamic_axes,
        verbose=False,
    )

    # Save tokenizer and config next to the ONNX model
    tokenizer.save_pretrained(out_dir)
    try:
        base_model.config.save_pretrained(out_dir)
    except Exception:
        pass

    print(f"Exported ONNX model to: {export_path}")

    # Post-export validation: ONNX checker + shape inference
    m = onnx.load(str(export_path))
    try:
        m_inf = shape_inference.infer_shapes(m)
        checker.check_model(m_inf)
        onnx.save(m_inf, str(export_path))  # overwrite with inferred shapes (optional)
        print("ONNX shape inference and checker passed.")
    except Exception as e:
        print("ONNX shape inference/checker failed:", e)
        # still continue to runtime smoke test; but you should inspect the model

    # Runtime smoke test with different batch sizes
    sess = ort.InferenceSession(str(export_path), providers=["CPUExecutionProvider"])
    print("ONNX Runtime inputs:", [(i.name, i.shape, i.type) for i in sess.get_inputs()])

    def run_smoke(batch_texts):
        toks = tokenizer(batch_texts, padding="longest", truncation=True, return_tensors="np")
        input_ids_np = toks["input_ids"].astype(np.int64)
        attention_mask_np = toks["attention_mask"].astype(np.int64)
        out = sess.run([sess.get_outputs()[0].name], {"input_ids": input_ids_np, "attention_mask": attention_mask_np})
        print(f"Ran batch size {input_ids_np.shape[0]} -> output shape {np.asarray(out[0]).shape}")

    # test batch sizes 1 and 3 (3 will exercise different batch)
    run_smoke(["one example"])
    run_smoke(["a", "b", "c"])

if __name__ == "__main__":
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    out_dir = Path("../models")

    export_model(model_name=model_name, out_dir=out_dir)
