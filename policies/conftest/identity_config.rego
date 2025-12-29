package conftest.identity

deny[msg] {
  input.kind == "ConfigMap"
  input.metadata.name == "identity-api-config"
  to_number(input.data.RETENTION_LIMIT_DAYS) > 30
  msg := sprintf("RETENTION_LIMIT_DAYS too high: %v", [input.data.RETENTION_LIMIT_DAYS])
}
