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

# Enable public traffic to the storage account
# az storage account update \
#   --name storysparkresourcega52f \
#   --resource-group StorySparkResourceGroup \
#   --set networkRuleSet.defaultAction=Allow \
#   --public-network-access Enabled

# Enable Shared Key Access
# az storage account update \
#   --resource-group StorySparkResourceGroup \
#   --name storysparkstorageaccount \
#   --allow-shared-key-access true

# Create the Function App
# az functionapp create \
#   --name StorySparkAPIGateway \
#   --resource-group StorySparkResourceGroup \
#   --consumption-plan-location westus2 \
#   --runtime python \
#   --runtime-version 3.12 \
#   --os-type Linux \
#   --storage-account storysparkstorageaccount \
#   --app-insights StorySparkAPIGatewayApplicationInsights \
#   --functions-version 4

# Deploy code from GitHub
# az functionapp deployment source config \
#   --name StorySparkAPIGateway \
#   --resource-group StorySparkResourceGroup \
#   --repo-url https://github.com/AndyMKC/Portfolio \
#   --branch deploy

# az functionapp deployment source delete \
#   --name StorySparkAPIGateway \
#   --resource-group StorySparkResourceGroup

# az functionapp deployment source config \
#   --name StorySparkAPIGateway \
#   --resource-group StorySparkResourceGroup \
#   --repo-url https://github.com/AndyMKC/Portfolio \
#   --branch deploy

# az functionapp deployment source show \
#   --name StorySparkAPIGateway \
#   --resource-group StorySparkResourceGroup \
#   --query "{ repo: repoUrl, branch: branch, type: type, manual: isManualIntegration }" \
#   -o table

# Enabling logs
az webapp log tail \
  --name StorySparkAPIGateway \
  --resource-group StorySparkResourceGroup

SUB_ID=$(az account show --query id -o tsv)
# az rest \
#   --method PUT \
#   --uri "/subscriptions/$SUB_ID/resourceGroups/StorySparkResourceGroup/providers/Microsoft.Web/sites/StorySparkAPIGateway/sourcecontrols/web?api-version=2024-11-01" \
#   --body '{
#     "properties": {
#       "repoUrl": "https://github.com/AndyMKC/Portfolio",
#       "branch": "deploy",
#       "isManualIntegration": false
#     }
#   }'

#   az functionapp deployment github-actions add \
#   --name StorySparkAPIGateway \
#   --resource-group StorySparkResourceGroup \
#   --repo AndyMKC/Portfolio \
#   --branch deploy \
#   --login-with-github


# az functionapp deployment source show \
#   --name StorySparkAPIGateway \
#   --resource-group StorySparkResourceGroup \
#   --query "{repo:repoUrl, branch:branch, manual:isManualIntegration}" \
#   -o table




