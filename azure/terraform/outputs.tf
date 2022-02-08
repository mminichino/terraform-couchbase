output "node-public" {
  value = var.use_public_ip ? [
    for instance in azurerm_linux_virtual_machine.couchbase_nodes:
    instance.public_ip_address
  ] : null
}

output "node-private" {
  value = [
    for instance in azurerm_linux_virtual_machine.couchbase_nodes:
    instance.private_ip_address
  ]
}
