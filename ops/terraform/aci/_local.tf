locals {
  name = "${var.project}-${var.environment}"
  tags = {
    project     = var.project
    environment = var.environment
    owner       = var.owner
    workspace   = terraform.workspace
  }
}
