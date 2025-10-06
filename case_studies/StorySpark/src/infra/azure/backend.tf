terraform {
  backend "azurerm" {
    resource_group_name  = "${var.bootstrap_backend_resource_group}"
    storage_account_name = "${var.bootstrap_backend_storage_account}"
    container_name       = "${var.bootstrap_backend_container}"
    key                  = "${var.bootstrap_backend_key}"
  }
}
