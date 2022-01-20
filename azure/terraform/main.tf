terraform {
  required_providers {
    aws = {
      source  = "hashicorp/azurerm"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "random_id" "cluster-id" {
  byte_length = 4
}

resource "azurerm_public_ip" "node_external" {
  for_each            = var.cluster_spec
  name                = "${each.key}-pub"
  resource_group_name = var.azure_resource_group
  location            = var.azure_location
  allocation_method   = "Dynamic"
}

resource "azurerm_network_interface" "node_nic" {
  for_each            = var.cluster_spec
  name                = "${each.key}-nic"
  location            = var.azure_location
  resource_group_name = var.azure_resource_group

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.azure_subnet
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.node_external[each.key].id
  }
}

data "azurerm_network_security_group" "cluster_nsg" {
  name                = var.azure_nsg
  resource_group_name = var.azure_resource_group
}

resource "azurerm_network_interface_security_group_association" "node_nsg" {
  for_each                  = var.cluster_spec
  network_interface_id      = azurerm_network_interface.node_nic[each.key].id
  network_security_group_id = data.azurerm_network_security_group.cluster_nsg.id
}

data "azurerm_image" "cb_image" {
  name                = var.azure_image_name
  resource_group_name = var.azure_resource_group
}

resource "azurerm_linux_virtual_machine" "couchbase_nodes" {
  for_each              = var.cluster_spec
  name                  = each.key
  size                  = var.azure_machine_type
  location              = var.azure_location
  resource_group_name   = var.azure_resource_group
  source_image_id       = data.azurerm_image.cb_image.id
  admin_username        = var.azure_admin_user
  network_interface_ids = [
    azurerm_network_interface.node_nic[each.key].id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = var.azure_disk_type
    disk_size_gb         = var.azure_disk_size
  }

  admin_ssh_key {
    username   = var.azure_admin_user
    public_key = file(var.ssh_public_key_file)
  }

  provisioner "remote-exec" {
    inline = [
      "sudo /usr/local/hostprep/bin/refresh.sh",
      "sudo /usr/local/hostprep/bin/clusterinit.sh -m write -i ${self.private_ip_address} -e ${self.public_ip_address} -s ${each.value.node_services} -o ${var.index_memory}",
    ]
    connection {
      host        = self.private_ip_address
      type        = "ssh"
      user        = var.azure_admin_user
      private_key = file(var.ssh_private_key)
    }
  }
}

locals {
  rally_node = element([for node in azurerm_linux_virtual_machine.couchbase_nodes: node.private_ip_address], 0)
}

resource "time_sleep" "pause" {
  depends_on = [azurerm_linux_virtual_machine.couchbase_nodes]
  create_duration = "5s"
}

resource "null_resource" "couchbase-init" {
  for_each = azurerm_linux_virtual_machine.couchbase_nodes
  triggers = {
    cb_nodes = join(",", keys(azurerm_linux_virtual_machine.couchbase_nodes))
  }
  connection {
    host        = each.value.private_ip_address
    type        = "ssh"
    user        = var.azure_admin_user
    private_key = file(var.ssh_private_key)
  }
  provisioner "remote-exec" {
    inline = [
      "sudo /usr/local/hostprep/bin/clusterinit.sh -m config -r ${local.rally_node}",
    ]
  }
  depends_on = [azurerm_linux_virtual_machine.couchbase_nodes, time_sleep.pause]
}

resource "null_resource" "couchbase-rebalance" {
  triggers = {
    cb_nodes = join(",", keys(azurerm_linux_virtual_machine.couchbase_nodes))
  }
  connection {
    host        = local.rally_node
    type        = "ssh"
    user        = var.azure_admin_user
    private_key = file(var.ssh_private_key)
  }
  provisioner "remote-exec" {
    inline = [
      "sudo /usr/local/hostprep/bin/clusterinit.sh -m rebalance -r ${local.rally_node}",
    ]
  }
  depends_on = [null_resource.couchbase-init]
}