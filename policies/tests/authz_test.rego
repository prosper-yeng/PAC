package compliance.authz

test_allow_onboarding_ok {
  input := {
    "request": {
      "endpoint": "onboarding/process",
      "purpose": "onboarding",
      "requester_role": "onboarding_service",
      "retention_days": 30,
      "risk_tier": "med",
      "requested_claims": ["given_name","family_name"],
      "log_fields": ["control_id","policy_bundle_digest","release_id","environment_id","decision_id","timestamp"]
    }
  }
  data.compliance.authz.allow with input as input
}

test_deny_wallet_excessive_claims {
  input := {
    "request": {
      "endpoint": "wallet/verify",
      "purpose": "wallet_presentation",
      "requester_role": "verifier_service",
      "retention_days": 1,
      "risk_tier": "low",
      "requested_claims": ["given_name","family_name","national_id"],
      "log_fields": ["control_id","policy_bundle_digest","release_id","environment_id","decision_id","timestamp"]
    }
  }
  not data.compliance.authz.allow with input as input
}


test_wallet_protocol_ok {
  input := {"request": {
    "endpoint": "wallet/verify",
    "purpose": "wallet_presentation",
    "requester_role": "verifier_service",
    "retention_days": 1,
    "requested_claims": ["ageOver18"],
    "log_fields": ["control_id","policy_bundle_digest","release_id","environment_id","decision_id","timestamp"],
    "protocol": "openid4vp",
    "vc_dm_version": "2.0"
  }}
  data.compliance.authz.allow with input as input
}

test_wallet_protocol_missing_denied {
  input := {"request": {
    "endpoint": "wallet/verify",
    "purpose": "wallet_presentation",
    "requester_role": "verifier_service",
    "retention_days": 1,
    "requested_claims": ["ageOver18"],
    "log_fields": ["control_id","policy_bundle_digest","release_id","environment_id","decision_id","timestamp"],
    "protocol": "oidc",
    "vc_dm_version": "2.0"
  }}
  not data.compliance.authz.allow with input as input
}
