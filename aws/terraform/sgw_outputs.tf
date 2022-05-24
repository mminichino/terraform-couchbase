output "node-public" {
  value = var.use_public_ip ? [
    for instance in aws_instance.sgw_nodes:
    instance.public_ip
  ] : null
}

output "node-private" {
  value = [
    for instance in aws_instance.sgw_nodes:
    instance.private_ip
  ]
}
