storage "raft" {
  path    = "./vault/file"
  node_id = "node1"
}

listener "tcp" {
  address     = "127.0.0.1:8200"
  tls_disable = "true"
}

cluster_addr = "https://127.0.0.1:8201"
api_addr = "http://127.0.0.1:8200"
ui = true