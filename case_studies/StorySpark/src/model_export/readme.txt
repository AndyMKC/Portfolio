-pip install -r requirements.txt
The one in this folder and not the top level one

-python ./main.py
This will generate the ONNX model

-gcloud artifacts generic upload all-MiniLM-L6-v2.onnx --repository=models --location=us-west1 --package=exported_models --version=1.0.0 --file=all-MiniLM-L6-v2.onnx
-gcloud artifacts generic upload all-MiniLM-L6-v2.onnx --repository=models --location=us-west1 --package=exported_models --file=all-MiniLM-L6-v2.onnx
-gcloud artifacts generic upload --repository=models --location=us-west1 --package=exported_models --version=1.0.0 --source-directory=./models --destination-path=models
