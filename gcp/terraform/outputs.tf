output "node-public" {
  value = [
    for instance in google_compute_instance.couchbase_nodes:
    instance.network_interface.0.access_config.0.nat_ip
  ]
}

output "node-private" {
  value = [
    for instance in google_compute_instance.couchbase_nodes:
    instance.network_interface.0.network_ip
  ]
}