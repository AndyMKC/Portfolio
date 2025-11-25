-pip install -r requirements.txt
The one in this folder and not the top level one

-python ./main.py
This will generate the ONNX model.  Run it from the model_export folder since it will generate a folder one level up.  We do this so that when we run dockerfile from the src directory, it will just find a folder called models without having to go into the model_export file first.  We do that because we are using GitHub actions to download the ONNX models to the model folder for the dockerfile to pick up.

-gcloud artifacts generic upload --repository=models --location=us-west1 --package=exported_models --version=1.0.0 --source-directory=../models --destination-path=models
This will upload the artifacts

-Downloading

# Works to download entire folder
gcloud artifacts generic download --project=storyspark-5555555 --location=us-west1 --repository=models --package=exported_models --version=1.0.0 --destination=.

# Individual file
gcloud artifacts generic download --project=storyspark-5555555 --location=us-west1 --repository=models --package=exported_models --version=1.0.0 --name=models/all-MiniLM-L6-v2.onnx --destination=.

