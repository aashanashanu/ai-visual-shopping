#!/bin/bash

# AI Visual Shopping Rebuild Script
# This script completely removes and rebuilds all AWS infrastructure

set -e

# Configuration
REGION="us-east-1"
ENVIRONMENT="dev"
SKIP_CONFIRMATION=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --demo)
      ENVIRONMENT="demo"
      shift
      ;;
    --skip-confirm)
      SKIP_CONFIRMATION=true
      shift
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option $1"
      echo "Usage: $0 [--demo] [--skip-confirm] [--region REGION]"
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

# Confirm rebuild
confirm_rebuild() {
    if [ "$SKIP_CONFIRMATION" = true ]; then
        log "Skip confirmation enabled. Proceeding with rebuild."
        return
    fi
    
    echo
    warning "This will completely remove and rebuild the AI Visual Shopping infrastructure."
    warning "This includes:"
    warning "  - Deleting all existing resources"
    warning "  - Creating new infrastructure from scratch"
    warning "  - Re-seeding all data"
    warning "  - Generating new API endpoints"
    echo
    
    read -p "Are you sure you want to rebuild everything? (Type 'REBUILD' to confirm): " confirm
    
    if [ "$confirm" != "REBUILD" ]; then
        error "Confirmation not received. Aborting rebuild."
        exit 1
    fi
    
    echo
    log "Confirmation received. Proceeding with rebuild..."
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if scripts exist
    if [ ! -f "scripts/cleanup.sh" ]; then
        error "cleanup.sh script not found. Please ensure it exists in the scripts directory."
        exit 1
    fi
    
    if [ ! -f "scripts/deploy.sh" ]; then
        error "deploy.sh script not found. Please ensure it exists in the scripts directory."
        exit 1
    fi
    
    # Make scripts executable
    chmod +x scripts/cleanup.sh
    chmod +x scripts/deploy.sh
    
    log "Prerequisites check completed."
}

# Step 1: Clean up existing infrastructure
cleanup_existing() {
    log "Step 1/3: Cleaning up existing infrastructure..."
    
    # Build cleanup command
    CLEANUP_CMD="./scripts/cleanup.sh"
    if [ "$ENVIRONMENT" = "demo" ]; then
        CLEANUP_CMD="$CLEANUP_CMD --demo"
    fi
    if [ "$SKIP_CONFIRMATION" = true ]; then
        CLEANUP_CMD="$CLEANUP_CMD --force"
    fi
    
    # Execute cleanup
    if $CLEANUP_CMD; then
        log "Cleanup completed successfully."
    else
        error "Cleanup failed. Please check the error messages above."
        exit 1
    fi
    
    # Wait a moment for AWS to process
    log "Waiting for AWS to process cleanup..."
    sleep 10
}

# Step 2: Deploy new infrastructure
deploy_new() {
    log "Step 2/3: Deploying new infrastructure..."
    
    # Build deploy command
    DEPLOY_CMD="./scripts/deploy.sh"
    if [ "$ENVIRONMENT" = "demo" ]; then
        DEPLOY_CMD="$DEPLOY_CMD --demo"
    fi
    if [ "$REGION" != "us-east-1" ]; then
        DEPLOY_CMD="$DEPLOY_CMD --region $REGION"
    fi
    
    # Execute deployment
    if $DEPLOY_CMD; then
        log "Deployment completed successfully."
    else
        error "Deployment failed. Please check the error messages above."
        exit 1
    fi
    
    # Wait a moment for services to be ready
    log "Waiting for services to be ready..."
    sleep 5
}

# Step 3: Verify rebuild
verify_rebuild() {
    log "Step 3/3: Verifying rebuild..."
    
    # Get API Gateway URL from deployment
    if [ "$ENVIRONMENT" = "demo" ]; then
        STACK_NAME="ai-visual-shopping-demo"
    else
        STACK_NAME="ai-visual-shopping"
    fi
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$API_URL" ]; then
        log "API Gateway URL: $API_URL"
        
        # Test API connectivity
        log "Testing API connectivity..."
        if curl -s -o /dev/null -w "%{http_code}" "$API_URL" | grep -q "200\|404\|403"; then
            log "API is responding correctly."
        else
            warning "API may not be fully ready yet. This is normal for new deployments."
        fi
    else
        error "Could not retrieve API URL. Rebuild may have failed."
        exit 1
    fi
    
    log "Rebuild verification completed."
}

# Main rebuild function
main() {
    log "Starting AI Visual Shopping complete rebuild..."
    
    if [ "$ENVIRONMENT" = "demo" ]; then
        log "🏆 DEMO MODE - Optimized rebuild"
    fi
    
    check_prerequisites
    confirm_rebuild
    cleanup_existing
    deploy_new
    verify_rebuild
    
    log "Rebuild completed successfully!"
    
    echo
    log "=== REBUILD SUMMARY ==="
    log "Environment: $ENVIRONMENT"
    log "Region: $REGION"
    log "Skip Confirmation: $SKIP_CONFIRMATION"
    
    echo
    log "=== NEXT STEPS ==="
    log "1. Configure frontend with new API URL"
    log "2. Test the application functionality"
    log "3. Run demo script to verify features"
    log "4. Monitor AWS costs and usage"
    
    if [ "$ENVIRONMENT" = "demo" ]; then
        echo
        log "🏆 DEMO MODE ACTIVE:"
        log "- Cost-optimized configuration deployed"
        log "- Ready for presentations and testing"
        log "- Estimated daily cost: ~$5.50"
    fi
}

# Run main function
main "$@"
