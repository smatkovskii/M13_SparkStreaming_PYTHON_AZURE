# Setup azurerm as a state backend
terraform {
  backend "azurerm" {
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "bdcc" {
  name = "rg-${var.ENV}-${var.LOCATION}"
  location = var.LOCATION

  tags = {
    region = var.BDCC_REGION
    env = var.ENV
  }
}

resource "azurerm_storage_account" "bdcc" {
  depends_on = [
    azurerm_resource_group.bdcc]

  name = "st${var.ENV}${var.LOCATION}"
  resource_group_name = azurerm_resource_group.bdcc.name
  location = azurerm_resource_group.bdcc.location
  account_tier = "Standard"
  account_replication_type = var.STORAGE_ACCOUNT_REPLICATION_TYPE
  is_hns_enabled = "true"

  tags = {
    region = var.BDCC_REGION
    env = var.ENV
  }
}

resource "azurerm_role_assignment" "role_assignment" {
  depends_on = [
    azurerm_storage_account.bdcc]

  scope                = azurerm_storage_account.bdcc.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "gen2_data" {
  depends_on = [
    azurerm_role_assignment.role_assignment]

  name = "data"
  storage_account_id = azurerm_storage_account.bdcc.id
}

resource "azurerm_databricks_workspace" "bdcc" {
  depends_on = [
    azurerm_resource_group.bdcc
  ]

  name = "dbw-${var.ENV}-${var.LOCATION}"
  resource_group_name = azurerm_resource_group.bdcc.name
  location = azurerm_resource_group.bdcc.location
  sku = "standard"

  tags = {
    region = var.BDCC_REGION
    env = var.ENV
  }
}

output "databricks_url" {
  value = azurerm_databricks_workspace.bdcc.workspace_url
}

output "storage_account_name" {
  value = azurerm_storage_account.bdcc.name
}

output "storage_account_access_key" {
  sensitive = true
  value = azurerm_storage_account.bdcc.primary_access_key
}

output "storage_account_container_name" {
  value = azurerm_storage_data_lake_gen2_filesystem.gen2_data.name
}