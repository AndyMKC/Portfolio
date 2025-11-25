import torch
import os
from transformers import AutoModel, AutoTokenizer

if __name__ == "__main__":
    model_name = os.environ.get("STORYSPARK_HUGGINGFACE_EMBEDDINGS_MODEL") # sentence-transformers/all-MiniLM-L6-v2
    export_path = os.environ.get("STORYSPARK_EMBEDDINGS_MODEL_PATH") # all-MiniLM-L6-v2.onnx

    model = AutoModel.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Dummy input for tracing
    dummy = tokenizer("Hello world", return_tensors="pt")
    
    # Export to ONNX
    torch.onnx.export(
        model,
        (dummy["input_ids"], dummy["attention_mask"]),
        export_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["output"],
        dynamic_axes={
            "input_ids": {0: "batch"},
            "attention_mask": {0: "batch"},
            "output": {0: "batch"}
        },
        opset_version=14
    )

    print(f"Model exported to {export_path}")