# Use the official Azure Functions base image for Python 3.11
FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# Set working directory to where the Functions host expects your app
WORKDIR /home/site/wwwroot

# Copy all function app files from api_gateway/ into the container
# Assumes you run docker build from Portfolio root
COPY case_studies/StorySpark/src/api_gateway/ /home/site/wwwroot/

# Install Python dependencies if requirements.txt is present
RUN if [ -f requirements.txt ]; then \
      pip install --no-cache-dir -r requirements.txt; \
    fi

# Optional: verify azure.functions is installed
RUN python -c "import azure.functions"

# Expose port 80 (Functions host listens here)
EXPOSE 80
