#!/bin/bash
set -euo pipefail

# Deploy Momentum AI infrastructure and application
# Usage: ./scripts/deploy.sh [dev|prod] [profile]

ENVIRONMENT="${1:-dev}"
PROFILE="${2:-K1-Kitstek-Billy}"
REGION="us-east-1"

echo "🚀 Deploying Momentum AI ($ENVIRONMENT) with profile: $PROFILE"
echo "---"

# 1. Terraform
echo "📦 Provisioning infrastructure..."
cd infrastructure/terraform
export AWS_PROFILE="$PROFILE"
terraform init -input=false
terraform apply -var-file="environments/${ENVIRONMENT}/terraform.tfvars" -auto-approve

API_ENDPOINT=$(terraform output -raw api_endpoint)
LAMBDA_NAME=$(terraform output -raw lambda_function_name)
echo "✅ Infrastructure deployed. API: $API_ENDPOINT"

# 2. Lambda
echo "📦 Packaging backend..."
cd ../../backend
rm -rf package lambda.zip
pip install -r requirements.txt -t package/ --platform manylinux2014_aarch64 --only-binary=:all: --quiet
cp -r app package/
cd package
zip -r ../lambda.zip . -x "*.pyc" "__pycache__/*" > /dev/null
cd ..

echo "🚀 Deploying Lambda..."
aws lambda update-function-code \
  --function-name "$LAMBDA_NAME" \
  --zip-file fileb://lambda.zip \
  --publish \
  --region "$REGION" \
  --profile "$PROFILE" > /dev/null

aws lambda wait function-updated \
  --function-name "$LAMBDA_NAME" \
  --region "$REGION" \
  --profile "$PROFILE"
echo "✅ Lambda deployed."

# 3. Frontend
echo "📦 Building frontend..."
cd ../frontend
VITE_API_URL="$API_ENDPOINT" npm run build
echo "✅ Frontend built. Deploy to Amplify via console or CI/CD."

echo "---"
echo "🎉 Deployment complete!"
echo "API: $API_ENDPOINT"
echo "Lambda: $LAMBDA_NAME"
