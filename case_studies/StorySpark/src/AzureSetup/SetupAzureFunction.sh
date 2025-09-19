#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration Settings ---
# Update these variables with your specific information if needed.
subscriptionId="5ab40d90-e237-422e-a575-b5b73033077c"
resourceGroupName="StorySparkResourceGroup"
functionAppName="StorySparkAPIGateway"
storageAccountName="storysparkstorageaccount"
planName="StorySparkPlanName"
appInsightsName="StorySparkAPIGatewayApplicationInsights"
region="westus2"
pythonVersion="3.12"

# GitHub Continuous Deployment settings
githubOrg="AndyMKC"
githubRepo="Portfolio"
githubBranch="deploy"
# -----------------------------


#echo "--- Logging in to Azure ---"
#az login

echo "--- Setting the subscription ---"
az account set --subscription "$subscriptionId"

#echo "--- Creating or updating Resource Group '$resourceGroupName' ---"
#az group create --name "$resourceGroupName" --location "$region"

#echo "--- Creating Storage Account '$storageAccountName' ---"
# StorageV2 is required for Function Apps and supports both blobs and files.
#az storage account create \
#  --name "$storageAccountName" \
#  --resource-group "$resourceGroupName" \
#  --location "$region" \
#  --sku Standard_LRS \
#  --kind StorageV2

#echo "--- Creating Application Insights instance '$appInsightsName' ---"
#az monitor app-insights component create \
#  --app "$appInsightsName" \
#  --resource-group "$resourceGroupName" \
#  --location "$region" \
#  --application-type web

#echo "--- Creating App Service Plan ---"
#az functionapp plan create \
#  --name StorySparkFunctionAppPlan \
#  --resource-group StorySparkResourceGroup \
#  --location westus2 \
#  --sku F1 \
#  --is-linux

echo "--- Creating Function App '$functionAppName' with Python 3.12 ---"
# Note: The "Secure unique default hostname (preview)" is handled automatically by Azure.
az functionapp create \
  --name "$functionAppName" \
  --resource-group "$resourceGroupName" \
  --consumption-plan-location "$region" \
  --runtime python \
  --runtime-version "$pythonVersion" \
  --os-type linux \
  --storage-account "$storageAccountName" \
  --app-insights "$appInsightsName" \
  --functions-version 4
#  --cnl true

echo "--- Creating User-Assigned Managed Identity 'StorySparkAPIGateway-uami' ---"
managedIdentityName="StorySparkAPIGateway-uami"
identity=$(az identity create \
    --name "$managedIdentityName" \
    --resource-group "$resourceGroupName" \
    --location "$region" \
    --query "principalId" -o tsv)

echo "--- Assigning Managed Identity to Function App ---"
az functionapp identity assign \
  --name "$functionAppName" \
  --resource-group "$resourceGroupName" \
  --identities "$managedIdentityName"

echo "--- Assigning 'Storage Blob Data Owner' role to the Managed Identity ---"
storageId=$(az storage account show \
    --name "$storageAccountName" \
    --resource-group "$resourceGroupName" \
    --query "id" -o tsv)

az role assignment create \
  --assignee "$identity" \
  --role "Storage Blob Data Owner" \
  --scope "$storageId"

echo "--- Assigning 'Monitoring Metrics Publisher' role to the Managed Identity ---"
appInsightsId=$(az monitor app-insights component show \
    --app "$appInsightsName" \
    --resource-group "$resourceGroupName" \
    --query "id" -o tsv)

az role assignment create \
  --assignee "$identity" \
  --role "Monitoring Metrics Publisher" \
  --scope "$appInsightsId"

echo "--- Configuring Continuous Deployment from GitHub ---"
# The --login-with-github parameter will prompt a browser login if not already authenticated.
az functionapp deployment github config \
  --name "$functionAppName" \
  --resource-group "$resourceGroupName" \
  --repo "$githubOrg/$githubRepo" \
  --branch "$githubBranch" \
  --login-with-github

echo "--- Deployment script finished successfully! ---"
echo "Your Azure Function App and associated resources have been created and configured."
echo "Continuous deployment from your GitHub repository is now active."
