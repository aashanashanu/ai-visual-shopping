#!/bin/bash

# AI Visual Shopping Deployment Script
# This script deploys the complete infrastructure and application

set -e

# Configuration
STACK_NAME="ai-visual-shopping"
REGION="us-east-1"
ENVIRONMENT="dev"
USE_DEMO_CONFIG=false
AUTO_CONFIRM=false
NON_INTERACTIVE=false

# Script and project root directories (absolute)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --demo)
      ENVIRONMENT="demo"
      USE_DEMO_CONFIG=true
      STACK_NAME="ai-visual-shopping-demo"
      shift
      ;;
        --yes|-y)
            AUTO_CONFIRM=true
            shift
            ;;
        --non-interactive)
            NON_INTERACTIVE=true
            shift
            ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--demo] [--region REGION]"
      echo "  --demo    Deploy in demo mode with cost optimizations"
      echo "  --region  AWS region (default: us-east-1)"
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
    
    # Check AWS credentials with better error handling
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials are not configured or invalid. Please run 'aws configure' to set up your credentials, or ensure your IAM role/environment has proper permissions."
    fi
    
    # Verify region is valid (use a simpler check that doesn't require EC2 permissions)
    if ! [[ "$REGION" =~ ^(us|eu|ap|ca|sa)-(east|west|north|south|central|northeast|southeast)-[1-2]$ ]] && ! [[ "$REGION" =~ ^(af|me)-(south|central)-1$ ]]; then
        warning "Region '$REGION' does not match standard AWS region format. Proceeding anyway..."
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
            log "Using demo-optimized configuration with S3 vector storage"
        else
            TEMPLATE_FILE="backend/cloudformation.yaml"
            log "Using standard production configuration"
        fi
    else
        TEMPLATE_FILE="backend/cloudformation.yaml"
        log "Using standard production configuration"
    fi
    
    # Check if template file exists
    if [ ! -f "$TEMPLATE_FILE" ]; then
        error "CloudFormation template file '$TEMPLATE_FILE' not found."
    fi
    
    # Validate CloudFormation template
    if ! aws cloudformation validate-template \
        --template-body file://$TEMPLATE_FILE \
        --region $REGION 2>/dev/null; then
        error "CloudFormation template validation failed. Please check the template syntax."
    fi
    
    # Deploy or update stack
    aws cloudformation deploy \
        --template-file $TEMPLATE_FILE \
        --stack-name $STACK_NAME \
        --parameter-overrides Environment=$ENVIRONMENT \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
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
    
    LAMBDA_ROLE_ARN=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`LambdaExecutionRole`].OutputValue' \
        --output text)
    
    log "Stack outputs retrieved successfully."
}

# Deploy Lambda function code (CloudFormation only creates placeholder functions)
deploy_lambda_code() {
    log "Deploying Lambda function code..."
    
    # Get the script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BACKEND_DIR="$(dirname "$SCRIPT_DIR")/backend"
    LAMBDAS_DIR="$BACKEND_DIR/lambdas"
    
    # Function to package and deploy a Lambda
    deploy_single_lambda() {
        local function_name=$1
        local files=$2
        local zip_name=$3
        
        log "Packaging $function_name..."
        
        # Create zip in backend directory
        cd "$LAMBDAS_DIR"
        
        # Create clean zip with specified files
        if [[ "$files" == *"seed_data"* ]]; then
            # Seed data needs sample_catalog.json and products folder
            zip -j "$BACKEND_DIR/$zip_name" $files 2>/dev/null || true
            
            # Add products folder and sample_catalog.json from project root
            ROOT_DIR="$(dirname "$SCRIPT_DIR")"
            cd "$ROOT_DIR"
            zip -r "$BACKEND_DIR/$zip_name" sample_catalog.json products/ 2>/dev/null || true
        else
            # Regular Lambda functions
            zip -j "$BACKEND_DIR/$zip_name" $files 2>/dev/null || true
        fi
        
        # Deploy to Lambda
        log "Deploying $function_name to AWS Lambda..."

        # Helper to get file size (works on macOS and Linux)
        file_size() {
            local f="$1"
            if command -v stat >/dev/null 2>&1; then
                # Mac stat uses -f, GNU stat uses -c
                if stat -f%z "$f" >/dev/null 2>&1; then
                    stat -f%z "$f"
                else
                    stat -c%s "$f"
                fi
            else
                # Fallback to wc
                wc -c <"$f" | awk '{print $1}'
            fi
        }

        ZIP_PATH="$BACKEND_DIR/$zip_name"
        SIZE_BYTES=$(file_size "$ZIP_PATH" || echo 0)
        MAX_DIRECT_UPLOAD=70167211

        if [ "$SIZE_BYTES" -gt "$MAX_DIRECT_UPLOAD" ]; then
            if [ -n "$PRODUCT_IMAGES_BUCKET" ]; then
                S3_KEY="deployments/$zip_name"
                log "Zip is large ($SIZE_BYTES bytes). Uploading to s3://$PRODUCT_IMAGES_BUCKET/$S3_KEY and using S3-based Lambda deployment..."
                aws s3 cp "$ZIP_PATH" "s3://$PRODUCT_IMAGES_BUCKET/$S3_KEY" --region "$REGION" || {
                    warning "Failed to upload $ZIP_PATH to s3://$PRODUCT_IMAGES_BUCKET/$S3_KEY"
                    return 1
                }

                aws lambda update-function-code \
                    --function-name "$function_name" \
                    --s3-bucket "$PRODUCT_IMAGES_BUCKET" \
                    --s3-key "$S3_KEY" \
                    --region "$REGION" \
                    --output text \
                    --query 'State' || {
                    warning "Failed to deploy $function_name via S3"
                    return 1
                }
            else
                warning "Zip is large ($SIZE_BYTES bytes) but PRODUCT_IMAGES_BUCKET is not set; attempting direct upload (likely to fail)"
                aws lambda update-function-code \
                    --function-name "$function_name" \
                    --zip-file "fileb://$ZIP_PATH" \
                    --region "$REGION" \
                    --output text \
                    --query 'State' || {
                    warning "Failed to deploy $function_name"
                    return 1
                }
            fi
        else
            aws lambda update-function-code \
                --function-name "$function_name" \
                --zip-file "fileb://$ZIP_PATH" \
                --region "$REGION" \
                --output text \
                --query 'State' || {
                warning "Failed to deploy $function_name"
                return 1
            }
        fi
        
        log "✅ $function_name deployed successfully"
        cd "$SCRIPT_DIR"
        return 0
    }
    
    # Deploy Image Search Lambda
    if [ -n "$IMAGE_SEARCH_FUNCTION" ]; then
        deploy_single_lambda "$IMAGE_SEARCH_FUNCTION" \
            "image_search.py bedrock_client.py s3_vector_store.py" \
            "image_search.zip"
    fi
    
    # Deploy Generate Explanation Lambda
    if [ -n "$GENERATE_EXPLANATION_FUNCTION" ]; then
        deploy_single_lambda "$GENERATE_EXPLANATION_FUNCTION" \
            "generate_explanation.py bedrock_client.py" \
            "generate_explanation.zip"
    fi
    
    # Deploy Seed Data Lambda
    local seed_function_name="${STACK_NAME}-seed-data-${ENVIRONMENT}"
    deploy_single_lambda "$seed_function_name" \
        "seed_data.py bedrock_client.py s3_vector_store.py" \
        "seed_data.zip"
    
    log "Lambda code deployment completed"
}

# Deploy Lambda functions (CloudFormation creates them, we deploy code and set permissions)
deploy_lambda_functions() {
    log "Setting up Lambda functions..."
    
    # Deploy Lambda code
    deploy_lambda_code
    
    # Set up API Gateway permissions for Lambda functions
    setup_api_gateway_permissions
    
    log "Lambda functions setup completed."
}

# Clean up function for failed deployments
cleanup_on_failure() {
    log "Cleaning up after deployment failure..."
    
    # Get the script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BACKEND_DIR="$(dirname "$SCRIPT_DIR")/backend/lambdas"
    
    if [ -d "$BACKEND_DIR" ]; then
        cd "$BACKEND_DIR"
        if [ -d "package" ]; then
            rm -rf package
        fi
        rm -f *.zip
        find . -name "requests*" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "idna*" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "certifi*" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "numpy*" -type d -exec rm -rf {} + 2>/dev/null || true
        cd - > /dev/null
    fi
    log "Cleanup completed."
}

# Seed data
seed_data() {
    log "Seeding data..."
    
    aws lambda invoke \
        --function-name ${STACK_NAME}-seed-data-${ENVIRONMENT} \
        --region $REGION \
        --payload '{}' \
        --cli-read-timeout 300 \
        --cli-connect-timeout 30 \
        seed_response.json 2>&1 || true
    
    # Check response - handle both success and FunctionError cases
    if [ -f seed_response.json ]; then
        if grep -q "completed successfully\|\"status\": \"success\"\|FunctionError" seed_response.json; then
            log "Data seeding invocation completed."
        else
            warning "Data seeding may have issues. Check seed_response.json for details."
        fi
    else
        warning "Seed response file not found. Data seeding status unknown."
    fi
    
    # Clean up
    rm -f seed_response.json
}

# Configure frontend
configure_frontend() {
    log "Configuring frontend..."
    
    # Use global ROOT_DIR (project root) defined at script top

    # Create .env file for frontend in the project root
    mkdir -p "$ROOT_DIR/frontend"
    cat > "$ROOT_DIR/frontend/.env" << EOF
REACT_APP_API_URL=${API_GATEWAY_URL}
REACT_APP_REGION=${REGION}
EOF

    log "Frontend configuration completed."
}

# Build and deploy frontend (optional)
deploy_frontend() {
    log "Building frontend..."
    # Use global ROOT_DIR (project root) to ensure correct paths
    cd "$ROOT_DIR/frontend"
    
    # Install dependencies (if node_modules doesn't exist)
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Build the application
    npm run build
    
    # Deploy to S3 (optional - you can use any hosting service)
    if command -v aws &> /dev/null; then
        log "Deploying frontend to S3..."
        
        # Create a bucket for frontend hosting
        FRONTEND_BUCKET="${STACK_NAME}-frontend-${ENVIRONMENT}"
        aws s3 mb s3://$FRONTEND_BUCKET --region $REGION || true
        
        # Disable block public access first
        aws s3api put-public-access-block \
            --bucket $FRONTEND_BUCKET \
            --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false \
            --region $REGION || true
        
        # Enable static website hosting
        aws s3 website s3://$FRONTEND_BUCKET --index-document index.html --error-document index.html --region $REGION
        
        # Upload build files
        aws s3 sync build/ s3://$FRONTEND_BUCKET --delete --region $REGION
        
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
            }' \
            --region $REGION
        
        log "Frontend deployed to: http://$FRONTEND_BUCKET.s3-website-$REGION.amazonaws.com"
    else
        warning "Frontend build completed. Deploy manually to your hosting service."
    fi
    
    cd ..
}

# Fix API Gateway CORS and enable Nova model explanations
# Configure API Gateway with CORS and Nova model support (if not already configured by CloudFormation)
configure_api_gateway() {
    log "Checking API Gateway configuration..."
    
    # Get API Gateway ID from stack outputs
    API_GATEWAY_ID=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text | cut -d'.' -f1)
    
    if [ -n "$API_GATEWAY_ID" ]; then
        # Get actual resource IDs dynamically
        log "Discovering API Gateway resource IDs..."
        SEARCH_RESOURCE_ID=$(aws apigateway get-resources \
            --rest-api-id $API_GATEWAY_ID \
            --region $REGION \
            --query 'items[?pathPart==`search`].id' \
            --output text 2>/dev/null || echo "")
            
        EXPLAIN_RESOURCE_ID=$(aws apigateway get-resources \
            --rest-api-id $API_GATEWAY_ID \
            --region $REGION \
            --query 'items[?pathPart==`explain`].id' \
            --output text 2>/dev/null || echo "")
        
        if [ -z "$SEARCH_RESOURCE_ID" ] || [ -z "$EXPLAIN_RESOURCE_ID" ]; then
            log "API Gateway resources not found. They should be created by CloudFormation."
            return
        fi
        
        log "Found search resource ID: $SEARCH_RESOURCE_ID"
        log "Found explain resource ID: $EXPLAIN_RESOURCE_ID"
        
        # Check if OPTIONS methods already exist
        SEARCH_OPTIONS=$(aws apigateway get-method --rest-api-id $API_GATEWAY_ID --resource-id $SEARCH_RESOURCE_ID --http-method OPTIONS --region $REGION 2>/dev/null || echo "")
        EXPLAIN_OPTIONS=$(aws apigateway get-method --rest-api-id $API_GATEWAY_ID --resource-id $EXPLAIN_RESOURCE_ID --http-method OPTIONS --region $REGION 2>/dev/null || echo "")
        
        if [[ -n "$SEARCH_OPTIONS" && -n "$EXPLAIN_OPTIONS" ]]; then
            log "✅ API Gateway CORS already configured by CloudFormation"
        else
            log "Configuring API Gateway CORS manually..."
            # Add OPTIONS method to search endpoint
            aws apigateway put-method \
                --rest-api-id $API_GATEWAY_ID \
                --resource-id $SEARCH_RESOURCE_ID \
                --http-method OPTIONS \
                --authorization-type "NONE" \
                --region $REGION 2>/dev/null || log "OPTIONS method already exists for search"
            
            # Add OPTIONS method response to search endpoint
            aws apigateway put-method-response \
                --rest-api-id $API_GATEWAY_ID \
                --resource-id $SEARCH_RESOURCE_ID \
                --http-method OPTIONS \
                --status-code 200 \
                --response-parameters '{"method.response.header.Access-Control-Allow-Origin": true, "method.response.header.Access-Control-Allow-Headers": true, "method.response.header.Access-Control-Allow-Methods": true}' \
                --region $REGION 2>/dev/null || log "OPTIONS response already configured for search"
            
            # Add OPTIONS method to explain endpoint
            aws apigateway put-method \
                --rest-api-id $API_GATEWAY_ID \
                --resource-id $EXPLAIN_RESOURCE_ID \
                --http-method OPTIONS \
                --authorization-type "NONE" \
                --region $REGION 2>/dev/null || log "OPTIONS method already exists for explain"
            
            # Add OPTIONS method response to explain endpoint
            aws apigateway put-method-response \
                --rest-api-id $API_GATEWAY_ID \
                --resource-id $EXPLAIN_RESOURCE_ID \
                --http-method OPTIONS \
                --status-code 200 \
                --response-parameters '{"method.response.header.Access-Control-Allow-Origin": true, "method.response.header.Access-Control-Allow-Headers": true, "method.response.header.Access-Control-Allow-Methods": true}' \
                --region $REGION 2>/dev/null || log "OPTIONS response already configured for explain"
            
            # Add MOCK integration for OPTIONS search endpoint
            aws apigateway put-integration \
                --rest-api-id $API_GATEWAY_ID \
                --resource-id $SEARCH_RESOURCE_ID \
                --http-method OPTIONS \
                --type MOCK \
                --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
                --region $REGION 2>/dev/null || log "OPTIONS integration already exists for search"
            
            # Add integration response for OPTIONS search endpoint
            aws apigateway put-integration-response \
                --rest-api-id $API_GATEWAY_ID \
                --resource-id $SEARCH_RESOURCE_ID \
                --http-method OPTIONS \
                --status-code 200 \
                --selection-pattern "" \
                --response-templates '{"application/json": ""}' \
                --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "'\''*'\''", "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent'\''", "method.response.header.Access-Control-Allow-Methods": "'\''POST,OPTIONS'\''"}' \
                --region $REGION 2>/dev/null || log "OPTIONS integration response already exists for search"
            
            # Add MOCK integration for OPTIONS explain endpoint
            aws apigateway put-integration \
                --rest-api-id $API_GATEWAY_ID \
                --resource-id $EXPLAIN_RESOURCE_ID \
                --type MOCK \
                --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
                --region $REGION 2>/dev/null || log "OPTIONS integration already exists for explain"
            
            # Add integration response for OPTIONS explain endpoint
            aws apigateway put-integration-response \
                --rest-api-id $API_GATEWAY_ID \
                --resource-id $EXPLAIN_RESOURCE_ID \
                --status-code 200 \
                --selection-pattern "" \
                --response-templates '{"application/json": ""}' \
                --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "'\''*'\''", "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent'\''", "method.response.header.Access-Control-Allow-Methods": "'\''POST,OPTIONS'\''"}' \
                --region $REGION 2>/dev/null || log "OPTIONS integration response already exists for explain"
            
            # Deploy API Gateway changes
            aws apigateway create-deployment \
                --rest-api-id $API_GATEWAY_ID \
                --stage-name $ENVIRONMENT \
                --description "Add CORS headers and OPTIONS methods" \
                --region $REGION 2>/dev/null || log "Deployment already exists"
            
            log "✅ API Gateway CORS configuration completed"
        fi
    else
        warning "Could not determine API Gateway ID"
    fi
}

# Configure product images bucket for public access (if not already configured by CloudFormation)
configure_product_images_bucket() {
    log "Checking product images bucket configuration..."
    
    if [ -n "$PRODUCT_IMAGES_BUCKET" ]; then
        # Check if bucket already has public access configured
        BUCKET_POLICY=$(aws s3api get-bucket-policy --bucket $PRODUCT_IMAGES_BUCKET --region $REGION 2>/dev/null || echo "")
        
        if [[ $BUCKET_POLICY == *"PublicReadGetObject"* ]]; then
            log "✅ Product images bucket already configured for public access"
        else
            log "Configuring product images bucket for public access..."
            # Disable block public access
            aws s3api put-public-access-block \
                --bucket $PRODUCT_IMAGES_BUCKET \
                --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false \
                --region $REGION || log "Public access block already configured"
            
            # Add public bucket policy for images
            aws s3api put-bucket-policy --bucket $PRODUCT_IMAGES_BUCKET --policy '{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": "arn:aws:s3:::'$PRODUCT_IMAGES_BUCKET'/*"
                    }
                ]
            }' --region $REGION || log "Bucket policy already exists"
            
            log "✅ Product images bucket configured for public access"
        fi
    else
        warning "Product images bucket not found"
    fi
}

# Set up API Gateway permissions for Lambda functions
setup_api_gateway_permissions() {
    log "Setting up API Gateway permissions for Lambda functions..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Get API Gateway ID from stack outputs
    API_GATEWAY_ID=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text | cut -d'.' -f1)
    
    if [ -n "$API_GATEWAY_ID" ] && [ -n "$AWS_ACCOUNT_ID" ]; then
        # Add permission for image search function
        aws lambda add-permission \
            --function-name $IMAGE_SEARCH_FUNCTION \
            --statement-id apigateway-invoke-search \
            --action lambda:InvokeFunction \
            --principal apigateway.amazonaws.com \
            --source-arn "arn:aws:execute-api:${REGION}:${AWS_ACCOUNT_ID}:${API_GATEWAY_ID}/*/POST/search" \
            --region $REGION 2>/dev/null || log "Search permission already exists"
        
        # Add permission for generate explanation function
        aws lambda add-permission \
            --function-name $GENERATE_EXPLANATION_FUNCTION \
            --statement-id apigateway-invoke-explain \
            --action lambda:InvokeFunction \
            --principal apigateway.amazonaws.com \
            --source-arn "arn:aws:execute-api:${REGION}:${AWS_ACCOUNT_ID}:${API_GATEWAY_ID}/*/POST/explain" \
            --region $REGION 2>/dev/null || log "Explain permission already exists"
        
        log "✅ API Gateway permissions configured"
    else
        warning "Could not determine API Gateway ID or AWS Account ID"
    fi
}

# Main deployment function
main() {
    log "Starting AI Visual Shopping deployment..."
    
    if [ "$USE_DEMO_CONFIG" = true ]; then
        log "🏆 DEMO MODE - Cost-optimized deployment"
    fi
    
    # Set up error handling
    set -e
    trap 'cleanup_on_failure' ERR
    
    check_prerequisites
    deploy_infrastructure
    get_stack_outputs
    configure_product_images_bucket
    deploy_lambda_functions
    seed_data
    configure_frontend
    
    # Configure API Gateway with CORS and Nova model support
    configure_api_gateway
    
    # Auto-deploy frontend in demo mode, optional in production
    if [ "$USE_DEMO_CONFIG" = true ]; then
        log "🌐 Auto-deploying frontend in demo mode..."
        deploy_frontend
    else
        # Optional: deploy frontend to S3
        if [ "$NON_INTERACTIVE" = true ]; then
            log "Non-interactive mode: skipping frontend deployment."
        else
            if [ "$AUTO_CONFIRM" = true ]; then
                log "Auto-confirm enabled: deploying frontend..."
                deploy_frontend
            else
                read -p "Do you want to deploy frontend to S3? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    deploy_frontend
                fi
            fi
        fi
    fi
    
    log "Deployment completed successfully!"
    
    echo
    log "=== DEPLOYMENT SUMMARY ==="
    log "Environment: $ENVIRONMENT"
    log "Configuration: $([ "$USE_DEMO_CONFIG" = true ] && echo "Demo-Optimized" || echo "Standard Production")"
    log "Product Images Bucket: $PRODUCT_IMAGES_BUCKET"
    log "User Uploads Bucket: $USER_UPLOADS_BUCKET"
    log "Vector Storage: S3-backed (cost-optimized)"
    log "API Gateway URL: $API_GATEWAY_URL"
    log "Image Search Function: $IMAGE_SEARCH_FUNCTION"
    log "Generate Explanation Function: $GENERATE_EXPLANATION_FUNCTION"
    
    # Add frontend URL if deployed
    if [ "$USE_DEMO_CONFIG" = true ] || [[ $REPLY =~ ^[Yy]$ ]]; then
        FRONTEND_BUCKET="${STACK_NAME}-frontend-${ENVIRONMENT}"
        log "Frontend URL: http://$FRONTEND_BUCKET.s3-website-$REGION.amazonaws.com"
    fi
    
    echo
    log "=== NEXT STEPS ==="
    log "1. Configure Bedrock model access for Nova models"
    log "2. Test API endpoints"
    if [ "$USE_DEMO_CONFIG" = false ] && [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "3. Deploy frontend to your hosting service"
    else
        log "3. Visit your frontend URL to test the application"
    fi
    log "4. Run demo script to test functionality"
    log "5. Use './scripts/rebuild.sh' to clean and rebuild when needed"
    log "6. Use './scripts/cleanup.sh' to remove all resources"
    
    if [ "$USE_DEMO_CONFIG" = true ]; then
        echo
        log "🏆 DEMO COST SAVINGS:"
        log "- OpenSearch: Removed entirely (save ~$540/month)"
        log "- Lambda: 512MB vs 1024MB (save 50%)"
        log "- Storage: S3 vector storage vs OpenSearch EBS (save 95%)"
        log "- Estimated monthly cost: ~$15 vs $540+ (save 97%)"
    fi
}

# Run main function
main "$@"
