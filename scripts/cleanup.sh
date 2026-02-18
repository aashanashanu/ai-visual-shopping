#!/bin/bash

# AI Visual Shopping Cleanup Script
# This script removes all AWS infrastructure created by the deployment

set -e

# Configuration
STACK_NAME="ai-visual-shopping"
REGION="us-east-1"
ENVIRONMENT="dev"
FORCE_DELETE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --demo)
      ENVIRONMENT="demo"
      STACK_NAME="ai-visual-shopping-demo"
      shift
      ;;
    --force)
      FORCE_DELETE=true
      shift
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option $1"
      echo "Usage: $0 [--demo] [--force] [--region REGION]"
      exit 1
      ;;
  esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials are not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        warning "jq is not installed. Some features may not work properly."
    fi
    
    log "Prerequisites check completed."
}

# Confirm deletion
confirm_deletion() {
    if [ "$FORCE_DELETE" = true ]; then
        log "Force delete mode enabled. Skipping confirmation."
        return
    fi
    
    echo
    warning "This will permanently delete ALL AWS resources created by the AI Visual Shopping application."
    warning "This includes:"
    warning "  - S3 buckets and all data"
    warning "  - OpenSearch domain and all indices"
    warning "  - Lambda functions"
    warning "  - API Gateway"
    warning "  - IAM roles and policies"
    echo
    
    read -p "Are you absolutely sure you want to delete everything? (Type 'DELETE' to confirm): " confirm
    
    if [ "$confirm" != "DELETE" ]; then
        error "Confirmation not received. Aborting deletion."
        exit 1
    fi
    
    echo
    log "Confirmation received. Proceeding with deletion..."
}

# Get stack outputs
get_stack_outputs() {
    log "Getting stack outputs..."
    
    if ! aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION &> /dev/null; then
        warning "Stack $STACK_NAME not found. Nothing to delete."
        return 1
    fi
    
    # Get stack outputs
    PRODUCT_IMAGES_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ProductImagesBucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    USER_UPLOADS_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`UserUploadsBucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    OPENSEARCH_DOMAIN=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchDomainEndpoint`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    API_GATEWAY=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    log "Stack outputs retrieved successfully."
}

# Empty S3 buckets
empty_s3_buckets() {
    log "Emptying S3 buckets..."
    
    if [ -n "$PRODUCT_IMAGES_BUCKET" ]; then
        log "Emptying product images bucket: $PRODUCT_IMAGES_BUCKET"
        
        # Check if bucket exists and is not empty
        if aws s3 ls "s3://$PRODUCT_IMAGES_BUCKET" --region $REGION &> /dev/null; then
            # Delete all objects
            aws s3 rm "s3://$PRODUCT_IMAGES_BUCKET" --recursive --region $REGION || true
            # Delete all versions
            aws s3api delete-objects --bucket $PRODUCT_IMAGES_BUCKET \
                --delete "$(aws s3api list-object-versions --bucket $PRODUCT_IMAGES_BUCKET \
                --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
                --output json 2>/dev/null | jq -c '. || {}')" 2>/dev/null || true
            # Delete delete markers
            aws s3api delete-objects --bucket $PRODUCT_IMAGES_BUCKET \
                --delete "$(aws s3api list-object-versions --bucket $PRODUCT_IMAGES_BUCKET \
                --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
                --output json 2>/dev/null | jq -c '. || {}')" 2>/dev/null || true
            log "Product images bucket emptied."
        else
            info "Product images bucket not found or already empty."
        fi
    fi
    
    if [ -n "$USER_UPLOADS_BUCKET" ]; then
        log "Emptying user uploads bucket: $USER_UPLOADS_BUCKET"
        
        if aws s3 ls "s3://$USER_UPLOADS_BUCKET" --region $REGION &> /dev/null; then
            aws s3 rm "s3://$USER_UPLOADS_BUCKET" --recursive --region $REGION || true
            aws s3api delete-objects --bucket $USER_UPLOADS_BUCKET \
                --delete "$(aws s3api list-object-versions --bucket $USER_UPLOADS_BUCKET \
                --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
                --output json 2>/dev/null | jq -c '. || {}')" 2>/dev/null || true
            aws s3api delete-objects --bucket $USER_UPLOADS_BUCKET \
                --delete "$(aws s3api list-object-versions --bucket $USER_UPLOADS_BUCKET \
                --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
                --output json 2>/dev/null | jq -c '. || {}')" 2>/dev/null || true
            log "User uploads bucket emptied."
        else
            info "User uploads bucket not found or already empty."
        fi
    fi
    
    log "S3 buckets emptied successfully."
}

# Delete CloudFormation stack
delete_stack() {
    log "Deleting CloudFormation stack: $STACK_NAME"
    
    # Delete stack
    aws cloudformation delete-stack \
        --stack-name $STACK_NAME \
        --region $REGION
    
    # Wait for stack deletion to complete
    log "Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name $STACK_NAME \
        --region $REGION
    
    log "CloudFormation stack deleted successfully."
}

# Clean up orphaned resources
cleanup_orphaned() {
    log "Checking for orphaned resources..."
    
    # Clean up orphaned Lambda functions
    log "Checking for orphaned Lambda functions..."
    LAMBDA_FUNCTIONS=$(aws lambda list-functions \
        --region $REGION \
        --query 'Functions[?contains(FunctionName, `ai-shopping-`)].FunctionName' \
        --output text 2>/dev/null || echo "")
    
    for func in $LAMBDA_FUNCTIONS; do
        if [ -n "$func" ]; then
            log "Deleting orphaned Lambda function: $func"
            aws lambda delete-function \
                --function-name "$func" \
                --region $REGION || true
        fi
    done
    
    # Clean up orphaned API Gateways
    log "Checking for orphaned API Gateways..."
    API_GATEWAYS=$(aws apigateway get-rest-apis \
        --region $REGION \
        --query 'items[?contains(name, `ai-shopping`)].id' \
        --output text 2>/dev/null || echo "")
    
    for api in $API_GATEWAYS; do
        if [ -n "$api" ]; then
            log "Deleting orphaned API Gateway: $api"
            aws apigateway delete-rest-api \
                --rest-api-id "$api" \
                --region $REGION || true
        fi
    done
    
    log "Orphaned resource cleanup completed."
}

# Verify cleanup
verify_cleanup() {
    log "Verifying cleanup..."
    
    # Check if stack still exists
    if aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION &> /dev/null; then
        error "Stack $STACK_NAME still exists. Cleanup may have failed."
        return 1
    fi
    
    # Check for remaining resources
    REMAINING_RESOURCES=""
    
    # Check S3 buckets
    if [ -n "$PRODUCT_IMAGES_BUCKET" ] && aws s3 ls "s3://$PRODUCT_IMAGES_BUCKET" --region $REGION &> /dev/null; then
        REMAINING_RESOURCES="$REMAINING_RESOURCES S3:$PRODUCT_IMAGES_BUCKET"
    fi
    
    if [ -n "$USER_UPLOADS_BUCKET" ] && aws s3 ls "s3://$USER_UPLOADS_BUCKET" --region $REGION &> /dev/null; then
        REMAINING_RESOURCES="$REMAINING_RESOURCES S3:$USER_UPLOADS_BUCKET"
    fi
    
    if [ -n "$REMAINING_RESOURCES" ]; then
        warning "Some resources may still exist: $REMAINING_RESOURCES"
        warning "You may need to clean them up manually."
    else
        log "Cleanup verification successful. All resources have been removed."
    fi
}

# Main cleanup function
main() {
    log "Starting AI Visual Shopping cleanup..."
    
    if [ "$FORCE_DELETE" = true ]; then
        log "🔥 FORCE DELETE MODE ENABLED"
    fi
    
    check_prerequisites
    confirm_deletion
    
    # Get stack information
    if get_stack_outputs; then
        # Empty S3 buckets first (required for CloudFormation deletion)
        empty_s3_buckets
        
        # Delete CloudFormation stack
        delete_stack
    fi
    
    # Clean up any orphaned resources
    cleanup_orphaned
    
    # Verify cleanup
    verify_cleanup
    
    log "Cleanup completed successfully!"
    
    echo
    log "=== CLEANUP SUMMARY ==="
    log "Environment: $ENVIRONMENT"
    log "Stack Name: $STACK_NAME"
    log "Region: $REGION"
    log "Force Delete: $FORCE_DELETE"
    
    echo
    log "=== NEXT STEPS ==="
    log "1. Verify all resources are deleted in AWS Console"
    log "2. Check for any remaining charges"
    log "3. Run './scripts/deploy.sh' to rebuild if needed"
    log "4. Monitor AWS billing for any unexpected charges"
}

# Run main function
main "$@"
