#!/bin/bash

# AI Visual Shopping Deployment Script
# This script deploys the complete infrastructure and application

set -e

# Configuration
STACK_NAME="ai-visual-shopping"
REGION="us-east-1"
ENVIRONMENT="dev"
USE_DEMO_CONFIG=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --demo)
      ENVIRONMENT="demo"
      USE_DEMO_CONFIG=true
      STACK_NAME="ai-visual-shopping-demo"
      shift
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials are not configured. Please run 'aws configure' first."
    fi
    
    # Check SAM CLI (optional, for easier deployment)
    if ! command -v sam &> /dev/null; then
        warning "AWS SAM CLI is not installed. Using CloudFormation directly."
    fi
    
    log "Prerequisites check completed."
}

# Deploy infrastructure
deploy_infrastructure() {
    log "Deploying CloudFormation infrastructure..."
    
    # Choose template based on configuration
    if [ "$USE_DEMO_CONFIG" = true ]; then
        if [ "$ENVIRONMENT" = "demo" ]; then
            TEMPLATE_FILE="backend/cloudformation-demo.yaml"
            log "Using demo-optimized configuration"
        else
            TEMPLATE_FILE="backend/cloudformation.yaml"
            log "Using standard production configuration"
        fi
    else
        TEMPLATE_FILE="backend/cloudformation.yaml"
        log "Using standard production configuration"
    fi
    
    # Validate CloudFormation template
    aws cloudformation validate-template \
        --template-body file://$TEMPLATE_FILE \
        --region $REGION
    
    # Deploy or update stack
    aws cloudformation deploy \
        --template-file $TEMPLATE_FILE \
        --stack-name $STACK_NAME \
        --parameter-overrides Environment=$ENVIRONMENT \
        --capabilities CAPABILITY_IAM \
        --region $REGION
    
    log "Infrastructure deployment completed."
}

# Get stack outputs
get_stack_outputs() {
    log "Retrieving stack outputs..."
    
    PRODUCT_IMAGES_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ProductImagesBucketName`].OutputValue' \
        --output text)
    
    USER_UPLOADS_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`UserUploadsBucketName`].OutputValue' \
        --output text)
    
    OPENSEARCH_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchDomainEndpoint`].OutputValue' \
        --output text)
    
    API_GATEWAY_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text)
    
    IMAGE_SEARCH_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ImageSearchFunctionName`].OutputValue' \
        --output text)
    
    GENERATE_EXPLANATION_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`GenerateExplanationFunctionName`].OutputValue' \
        --output text)
    
    log "Stack outputs retrieved successfully."
}

# Package and deploy Lambda functions
deploy_lambda_functions() {
    log "Packaging and deploying Lambda functions..."
    
    # Create deployment package for image search function
    cd backend/lambdas
    zip -r image_search.zip image_search.py bedrock_client.py opensearch_client.py requirements.txt
    
    # Update image search function
    aws lambda update-function-code \
        --function-name $IMAGE_SEARCH_FUNCTION \
        --zip-file fileb://image_search.zip \
        --region $REGION
    
    # Create deployment package for generate explanation function
    zip -r generate_explanation.zip generate_explanation.py bedrock_client.py requirements.txt
    
    # Update generate explanation function
    aws lambda update-function-code \
        --function-name $GENERATE_EXPLANATION_FUNCTION \
        --zip-file fileb://generate_explanation.zip \
        --region $REGION
    
    # Create deployment package for seed data function
    zip -r seed_data.zip seed_data.py bedrock_client.py opensearch_client.py requirements.txt ../sample_catalog.json
    
    # Update seed data function
    aws lambda update-function-code \
        --function-name ${STACK_NAME}-seed-data-${ENVIRONMENT} \
        --zip-file fileb://seed_data.zip \
        --region $REGION
    
    # Clean up
    rm -f *.zip
    cd ../..
    
    log "Lambda functions deployed successfully."
}

# Wait for OpenSearch to be available
wait_for_opensearch() {
    log "Waiting for OpenSearch domain to be available..."
    
    # Wait for up to 15 minutes
    for i in {1..30}; do
        STATUS=$(aws opensearch describe-domain \
            --domain-name ai-shopping-opensearch \
            --region $REGION \
            --query 'DomainStatus.Processing' \
            --output text)
        
        if [ "$STATUS" = "false" ]; then
            log "OpenSearch domain is now available."
            break
        fi
        
        log "Waiting for OpenSearch... ($i/30)"
        sleep 30
    done
}

# Seed data
seed_data() {
    log "Seeding data..."
    
    # Invoke seed data Lambda function
    aws lambda invoke \
        --function-name ${STACK_NAME}-seed-data-${ENVIRONMENT} \
        --region $REGION \
        --payload '{}' \
        seed_response.json
    
    # Check response
    if grep -q "completed successfully" seed_response.json; then
        log "Data seeding completed successfully."
    else
        error "Data seeding failed. Check seed_response.json for details."
    fi
    
    # Clean up
    rm -f seed_response.json
}

# Configure frontend
configure_frontend() {
    log "Configuring frontend..."
    
    # Create .env file for frontend
    cat > frontend/.env << EOF
REACT_APP_API_URL=${API_GATEWAY_URL}
REACT_APP_REGION=${REGION}
EOF
    
    log "Frontend configuration completed."
}

# Build and deploy frontend (optional)
deploy_frontend() {
    log "Building frontend..."
    
    cd frontend
    
    # Install dependencies (if node_modules doesn't exist)
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Build the application
    npm run build
    
    # Deploy to S3 (optional - you can use any hosting service)
    if command -v aws s3 sync &> /dev/null; then
        log "Deploying frontend to S3..."
        
        # Create a bucket for frontend hosting
        FRONTEND_BUCKET="${STACK_NAME}-frontend-${ENVIRONMENT}"
        aws s3 mb s3://$FRONTEND_BUCKET --region $REGION || true
        
        # Enable static website hosting
        aws s3 website s3://$FRONTEND_BUCKET --index-document index.html
        
        # Upload build files
        aws s3 sync build/ s3://$FRONTEND_BUCKET --delete
        
        # Make bucket public
        aws s3api put-bucket-policy \
            --bucket $FRONTEND_BUCKET \
            --policy '{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": "arn:aws:s3:::'$FRONTEND_BUCKET'/*"
                    }
                ]
            }'
        
        log "Frontend deployed to: http://$FRONTEND_BUCKET.s3-website-$REGION.amazonaws.com"
    else
        warning "Frontend build completed. Deploy manually to your hosting service."
    fi
    
    cd ..
}

# Main deployment function
main() {
    log "Starting AI Visual Shopping deployment..."
    
    if [ "$USE_DEMO_CONFIG" = true ]; then
        log "🏆 DEMO MODE - Cost-optimized deployment"
    fi
    
    check_prerequisites
    deploy_infrastructure
    get_stack_outputs
    deploy_lambda_functions
    wait_for_opensearch
    seed_data
    configure_frontend
    
    # Optional: deploy frontend to S3
    read -p "Do you want to deploy frontend to S3? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy_frontend
    fi
    
    log "Deployment completed successfully!"
    
    echo
    log "=== DEPLOYMENT SUMMARY ==="
    log "Environment: $ENVIRONMENT"
    log "Configuration: $([ "$USE_DEMO_CONFIG" = true ] && echo "Demo-Optimized" || echo "Standard Production")"
    log "Product Images Bucket: $PRODUCT_IMAGES_BUCKET"
    log "User Uploads Bucket: $USER_UPLOADS_BUCKET"
    log "OpenSearch Endpoint: $OPENSEARCH_ENDPOINT"
    log "API Gateway URL: $API_GATEWAY_URL"
    log "Image Search Function: $IMAGE_SEARCH_FUNCTION"
    log "Generate Explanation Function: $GENERATE_EXPLANATION_FUNCTION"
    
    echo
    log "=== NEXT STEPS ==="
    log "1. Configure Bedrock model access for Nova models"
    log "2. Test API endpoints"
    log "3. Deploy frontend to your hosting service"
    log "4. Run demo script to test functionality"
    log "5. Use './scripts/rebuild.sh' to clean and rebuild when needed"
    log "6. Use './scripts/cleanup.sh' to remove all resources"
    
    if [ "$USE_DEMO_CONFIG" = true ]; then
        echo
        log "🏆 DEMO COST SAVINGS:"
        log "- OpenSearch: t3.small vs t3.medium (save ~$0.25/day)"
        log "- Lambda: 512MB vs 1024MB (save 50%)"
        log "- Storage: 20GB vs 100GB (save 80%)"
        log "- Estimated daily cost: ~$5.50 vs $22.83"
    fi
}

# Run main function
main "$@"
