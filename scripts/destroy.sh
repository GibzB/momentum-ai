#!/bin/bash
set -euo pipefail

# Destroy Momentum AI infrastructure
# Usage: ./scripts/destroy.sh [dev|prod] [profile]

ENVIRONMENT="${1:-dev}"
PROFILE="${2:-K1-Kitstek-Billy}"

echo "⚠️  Destroying Momentum AI ($ENVIRONMENT) with profile: $PROFILE"
echo "This will DELETE all resources including databases."
read -p "Type 'destroy' to confirm: " CONFIRM

if [ "$CONFIRM" != "destroy" ]; then
  echo "Aborted."
  exit 1
fi

cd infrastructure/terraform
export AWS_PROFILE="$PROFILE"
terraform destroy -var-file="environments/${ENVIRONMENT}/terraform.tfvars" -auto-approve

echo "✅ Infrastructure destroyed."
