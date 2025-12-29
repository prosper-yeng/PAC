package compliance.authz

default allow = false

# Control IDs (examples)
control_log = "ID-LOG-01"
control_purpose = "ID-PUR-01"
control_min = "ID-MIN-01"
control_ret = "ID-RET-01"
control_acc = "ID-ACC-01"

# Required log schema fields (simulated)
required_log_fields = {"control_id","policy_bundle_digest","release_id","environment_id","decision_id","timestamp"}

# Allowed purposes
allowed_purposes = {"onboarding","wallet_presentation"}

# Allowed roles by endpoint
allowed_roles = {
  "onboarding/process": {"onboarding_service","compliance_service"},
  "wallet/verify": {"verifier_service","compliance_service"}
}

# Minimization profile (default; overridden by complexity variants)
min_allowed_claims = {"given_name","family_name","birthdate","age_over_18","ageOver18","ageOver"}

# Retention limit days (can be changed for drift tests)
retention_limit_days = 30

allow {
  input.request.endpoint == "onboarding/process"
  purpose_ok
  role_ok
  retention_ok
  logging_ok
}

allow {
  input.request.endpoint == "wallet/verify"
  purpose_ok
  role_ok
  protocol_ok
  minimization_ok
  logging_ok
}

purpose_ok {
  p := input.request.purpose
  allowed_purposes[p]
}

role_ok {
  ep := input.request.endpoint
  r := input.request.requester_role
  allowed_roles[ep][r]
}

minimization_ok {
  requested := {c | c := input.request.requested_claims[_]}
  diff := requested - min_allowed_claims
  count(diff) == 0
}

retention_ok {
  input.request.retention_days <= retention_limit_days
}

logging_ok {
  fields := {f | f := input.request.log_fields[_]}
  missing := required_log_fields - fields
  count(missing) == 0
}


protocol_ok {
  input.request.endpoint == "wallet/verify"
  input.request.protocol == "openid4vp"
  input.request.vc_dm_version == "2.0"
}
