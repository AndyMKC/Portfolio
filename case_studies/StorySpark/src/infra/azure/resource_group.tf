terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "tfstate-rg"         # replace with your backend RG
    storage_account_name = "tfstatestorageacct" # replace with your backend storage account
    container_name       = "tfstate"
    key                  = "storyspark.tfstate"
  }
}

provider "azurerm" {
  features {}
}
