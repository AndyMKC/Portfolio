terraform {
  backend "azurerm" {
    resource_group_name  = "StorySparkResourceGroup"
    storage_account_name = "bootstrapbackend"
    container_name       = "tfstate"
    key                  = "storyspark/main.tfstate"
  }
}
