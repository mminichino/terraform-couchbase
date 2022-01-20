packer {
  required_plugins {
    azure = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/azure"
    }
  }
}

locals {
  timestamp = "${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
}

variable "cb_version" {
  description = "Software version"
  type        = string
}

variable "os_linux_type" {
  description = "Linux type"
  type        = string
}

variable "os_linux_release" {
  description = "Linux release"
  type        = string
}

variable "azure_resource_group" {
  description = "Azure resource group"
  type        = string
}

variable "azure_image_publisher" {
  description = "Azure image publisher"
  type        = string
}

variable "azure_image_offer" {
  description = "Azure image offer"
  type        = string
}

variable "azure_image_sku" {
  description = "Azure image SKU"
  type        = string
}

variable "azure_location" {
  description = "Azure location"
  type        = string
}

source "azure-arm" "cb-node" {
  use_azure_cli_auth = true

  managed_image_resource_group_name = var.azure_resource_group
  managed_image_name = "${var.os_linux_type}-${var.os_linux_release}-couchbase-${local.timestamp}"

  os_type = "Linux"
  image_publisher = var.azure_image_publisher
  image_offer = var.azure_image_offer
  image_sku = var.azure_image_sku

  location = var.azure_location
  vm_size = "Standard_DS2_v2"

  azure_tags = {
    type = "couchbase-server"
    version = var.cb_version
  }
}

build {
  name    = "centos-couchbase-image"
  sources = [
    "source.azure-arm.cb-node"
  ]
  provisioner "shell" {
  environment_vars = [
    "SW_VERSION=${var.cb_version}",
  ]
  inline = [
    "echo Installing Couchbase",
    "sleep 30",
    "sudo yum update -y",
    "sudo yum install -y git",
    "sudo git clone https://github.com/mminichino/hostprep /usr/local/hostprep",
    "sudo /usr/local/hostprep/bin/hostprep.sh -t couchbase -v ${var.cb_version}",
    "/usr/sbin/waagent -force -deprovision+user && export HISTSIZE=0 && sync",
  ]
  }
}