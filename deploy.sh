#!/bin/bash
# Deployment script for Berliner Luft infrastructure and function code

set -euo pipefail  # Exit immediately on error, unset variables, and handle pipe failures

# Configurable variables
PROJECT_ID="berliner-luft-dez"
REGION="europe-west3"
TF_DIR="terraform"
SRC_DIR="src"
ZIP_FILE="function.zip"

# Helper function for error messages
error_exit() {
    echo "Error: $1" 1>&2
    exit 1
}

# Validate prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    command -v gcloud >/dev/null 2>&1 || error_exit "gcloud not found. Please install Google Cloud SDK."
    command -v gsutil >/dev/null 2>&1 || error_exit "gsutil not found. Please install Google Cloud SDK."
    command -v terraform >/dev/null 2>&1 || error_exit "terraform not found. Please install Terraform."
    command -v zip >/dev/null 2>&1 || error_exit "zip not found. Please install zip utility."
}

# Validate GCP authentication
check_auth() {
    echo "Checking GCP authentication..."
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null; then
        error_exit "Not authenticated. Run 'gcloud auth login'."
    fi
}

# Package source code
package_function() {
    echo "Packaging source code..."
    [ -d "$SRC_DIR" ] || error_exit "Source directory $SRC_DIR not found"
    
    # Clean previous build if it exists
    [ -f "$ZIP_FILE" ] && rm "$ZIP_FILE"
    
    # Create zip with proper directory structure
    (cd "$SRC_DIR" && zip -q -r "../$ZIP_FILE" ./*)
    [ $? -eq 0 ] || error_exit "Failed to create zip file"
}

# Upload function code
upload_function() {
    echo "Uploading function code..."
    gsutil cp "$ZIP_FILE" "gs://berliner-luft/functions/" || error_exit "Failed to upload function code"
}

# Apply Terraform configuration
apply_infrastructure() {
    echo "Applying Terraform configuration..."
    (
       cd "$TF_DIR" || error_exit "Terraform directory $TF_DIR not found"
       
       # Check if Terraform is already initialized
       if [ ! -d ".terraform" ]; then
           echo "Initializing Terraform..."
           terraform init || error_exit "Terraform init failed"
       else
           echo "Terraform is already initialized. Skipping init."
       fi

       terraform apply -auto-approve \
           -var="project_id=$PROJECT_ID" \
           -var="region=$REGION" || error_exit "Terraform apply failed"
    )
}

# Main deployment flow
main() {
    check_prerequisites
    check_auth
    package_function
    upload_function
    apply_infrastructure
    echo "Deployment completed successfully"
}

# Execute main
main
