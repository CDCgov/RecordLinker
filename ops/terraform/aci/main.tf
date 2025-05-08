provider "random" {}
provider "azurerm" {
  features {}
}

resource "random_password" "secret_key" {
  length  = 32
  special = false
}

# 1. Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-aci-${local.name}"
  location = "eastus"

  tags = local.tags
}

# 2. Azure storage account
resource "azurerm_storage_account" "storage" {
  name                     = lower("${var.owner}-${local.name}")
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = local.tags
}

# 3. Azure File Share
resource "azurerm_storage_share" "db_file_share" {
  name                 = "db-fileshare-${local.name}"
  storage_account_name = azurerm_storage_account.storage.name
  quota                = 100

  tags = local.tags
}


# 4. Azure Container Instance
resource "azurerm_container_group" "aci" {
  name                = "aci-${local.name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"

  tags = local.tags

  depends_on = [
    azurerm_storage_account.storage,
    azurerm_storage_share.db_file_share
  ]

  container {
    name   = "recordlinker"
    image  = "ghcr.io/cdcgov/recordlinker/demo:latest"
    cpu    = 1
    memory = "1.5Gi"

    environment_variables = {
      DB_URI = "sqlite:////mnt/sqlite-db/recordlinker.db"
    }

    secure_environment_variables = {
      SECRET_KEY = "${random_password.secret_key.result}"
    }

    volume {
      name       = "sqlite-volume"
      mount_path = "/mnt/sqlite-db"
    }
  }

  volume {
    name = "sqlite-volume"
    azure_file {
      share_name           = azurerm_storage_share.db_file_share.name
      storage_account_name = azurerm_storage_account.storage.name
      storage_account_key  = azurerm_storage_account.storage.primary_access_key
    }
  }

  ip_address_type = "public"
  dns_name_label  = "recordlinker-${local.name}"
}
