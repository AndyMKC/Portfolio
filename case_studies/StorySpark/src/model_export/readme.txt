-pip install -r requirements.txt
The one in this folder and not the top level one

-python ./main.py
This will generate the ONNX model.  Run it with the working directory to be one level above (/StorySpark/src) so that when we run dockerfile from the src directory, it will just find a folder called models without having to go into the model_export file first.  We do that because we are using GitHub actions to download the ONNX models to the model folder for the dockerfile to pick up.

Model files are uploaded to this location via GitHub's CI/CD pipelines -- https://console.cloud.google.com/storage/browser/storyspark-5555555-models?pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22))&project=storyspark-5555555