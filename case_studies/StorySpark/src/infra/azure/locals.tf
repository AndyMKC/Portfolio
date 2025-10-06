locals {
  prefix        = var.project_prefix
  location      = var.location
  tags = {
    project = "StorySpark"
    env     = var.environment
  }

  resource_group_name = "${local.prefix}ResourceGroup"
  app_service_plan_name = "${local.prefix}AppServicePlan"
  log_analytics_workspace_name = "${local.prefix}LogAnalyticsWorkspace"
  application_insights_name = "${local.prefix}APIGatewayApplicationInsights"
  storage_account_name = "storysparkstorageacct2"
  acr_name = length(trim(var.acr_name)) > 0 ? var.acr_name : lower("${local.prefix}acr")
  acr_repo = var.acr_repo
  function_app_name = local.prefix
  search_service_name = "storyspark-ai-search2"
  backend_key = "StorySpark2.tfstate"
}
