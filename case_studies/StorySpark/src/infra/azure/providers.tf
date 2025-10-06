terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.47"
    }
  }
  required_version = ">= 1.3.0"
}

provider "azurerm" {
  features {}
}
