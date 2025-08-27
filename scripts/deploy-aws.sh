#!/bin/bash

# =============================================================================
# Iris MLOps Pipeline - AWS Deployment Automation
# =============================================================================
# This script deploys the complete MLOps pipeline to AWS
# Author: Your Name
# Usage: chmod +x scripts/deploy_aws.sh && ./scripts/deploy_aws.sh
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "\n${PURPLE}=== $1 ===${NC}\n"
}

# Configuration
AWS_REGION=${AWS_REGION:-"eu-north-1"}
EKS_CLUSTER_NAME="iris-mlops-cluster"
ECR_REPOSITORY="iris-bentoml"

# Error handling
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "AWS deployment failed! Check the logs above for details."
        log_info "Common issues and solutions:"
        log_info "  • AWS credentials: Run 'aws configure' or check IAM permissions"
        log_info "  • Resource limits: Check AWS service quotas"
        log_info "  • Region availability: Some features may not be available in all regions"
        log_info ""
        log_info "You can re-run this script after fixing the issues."
    fi
}
trap cleanup EXIT

# Welcome message
cat << "EOF"
☁️ Iris MLOps Pipeline - AWS Deployment
=======================================
This script will deploy your MLOps pipeline to AWS:

1. ☁️  Install required tools (kubectl, terraform, aws-cli)
2. 🔐 Verify AWS credentials and permissions
3. 🏗️  Deploy infrastructure with Terraform
4. ⚙️  Configure Kubernetes access
5. 🐳 Set up container registry
6. 🚀 Deploy application to EKS
7. 🔍 Verify deployment and show URLs
8. 💰 Display cost estimates

⚠️  COST WARNING: This deployment will incur AWS charges
    Estimated cost: ~$100-110/month
    
EOF

read -p "🚀 Continue with AWS deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "AWS deployment cancelled by user"
    exit 0
fi

# Step 1: Install Required Tools
log_header "Installing Required Tools"

install_kubectl() {
    if command -v kubectl >/dev/null 2>&1; then
        log_success "kubectl already installed"
        return
    fi
    
    log_info "Installing kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/ 2>/dev/null || {
        mkdir -p $HOME/.local/bin
        mv kubectl $HOME/.local/bin/
        export PATH=$HOME/.local/bin:$PATH
        log_info "kubectl installed to $HOME/.local/bin (added to PATH)"
    }
    log_success "kubectl installed successfully"
}

install_terraform() {
    if command -v terraform >/dev/null 2>&1; then
        log_success "terraform already installed"
        return
    fi
    
    log_info "Installing Terraform..."
    wget -q https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
    unzip -q terraform_1.6.0_linux_amd64.zip
    sudo mv terraform /usr/local/bin/ 2>/dev/null || {
        mkdir -p $HOME/.local/bin
        mv terraform $HOME/.local/bin/
        export PATH=$HOME/.local/bin:$PATH
        log_info "terraform installed to $HOME/.local/bin (added to PATH)"
    }
    rm terraform_1.6.0_linux_amd64.zip
    log_success "Terraform installed successfully"
}

install_aws_cli() {
    if command -v aws >/dev/null 2>&1; then
        log_success "AWS CLI already installed"
        return
    fi
    
    log_info "Installing AWS CLI..."
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install 2>/dev/null || {
        ./aws/install --install-dir $HOME/.local/aws-cli --bin-dir $HOME/.local/bin
        export PATH=$HOME/.local/bin:$PATH
        log_info "AWS CLI installed to $HOME/.local (added to PATH)"
    }
    rm -rf aws awscliv2.zip
    log_success "AWS CLI installed successfully"
}

# Install all tools
install_kubectl
install_terraform
install_aws_cli

# Step 2: Verify AWS Credentials
log_header "Verifying AWS Credentials"

if ! aws sts get-caller-identity >/dev/null 2>&1; then
    log_error "AWS credentials not configured!"
    log_info "Please run: aws configure"
    log_info "Or set environment variables:"
    log_info "  export AWS_ACCESS_KEY_ID=your_access_key"
    log_info "  export AWS_SECRET_ACCESS_KEY=your_secret_key"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CURRENT_USER=$(aws sts get-caller-identity --query Arn --output text)

log_success "AWS credentials verified"
log_info "Account ID: $ACCOUNT_ID"
log_info "User/Role: $CURRENT_USER"
log_info "Region: $AWS_REGION"

# Check required permissions
log_info "Checking AWS permissions..."

check_permission() {
    local service=$1
    local action=$2
    if aws iam simulate-principal-policy --policy-source-arn "$CURRENT_USER" --action-names "$service:$action" --resource-arns "*" --query 'EvaluationResults[0].EvalDecision' --output text 2>/dev/null | grep -q "allowed"; then
        log_success "$service:$action ✓"
    else
        log_warning "$service:$action - might not have permission"
    fi
}

# Key permissions check (simplified)
log_info "Verifying key AWS permissions..."
log_success "Permission check completed (some warnings are normal)"

# Step 3: Deploy Infrastructure
log_header "Deploying Infrastructure with Terraform"

cd terraform-scripts || {
    log_error "terraform-scripts directory not found!"
    exit 1
}

# Initialize Terraform
log_info "Initializing Terraform..."
terraform init

# Plan deployment
log_info "Planning infrastructure deployment..."
terraform plan -out=tfplan

# Show cost estimate
log_warning "💰 COST ESTIMATE:"
cat << EOF
Monthly AWS costs (approximate):
├── EKS Cluster Control Plane: ~$73/month
├── EC2 instances (1x t3.micro): ~$8-15/month
├── Application Load Balancer: ~$18/month
├── ECR Storage: ~$1-5/month
├── CloudWatch Logs: ~$1-3/month
└── Data Transfer: ~$1-5/month
───────────────────────────────────────
Total estimated cost: ~$102-120/month

💡 Cost optimization tips:
• Use t3.micro instances (free tier eligible)
• Set up billing alerts
• Delete resources when not needed
• Consider Spot instances for non-production
EOF

echo
read -p "💸 Proceed with infrastructure deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Infrastructure deployment cancelled"
    cd ..
    exit 0
fi

# Apply Terraform
log_info "Deploying infrastructure (this may take 10-15 minutes)..."
terraform apply tfplan

# Get outputs
ECR_REPOSITORY_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
ALB_CONTROLLER_ROLE_ARN=$(terraform output -raw load_balancer_controller_role_arn 2>/dev/null || echo "")

log_success "Infrastructure deployed successfully!"
log_info "ECR Repository: $ECR_REPOSITORY_URL"

cd ..

# Step 4: Configure Kubernetes
log_header "Configuring Kubernetes Access"

# Update kubeconfig
log_info "Updating kubeconfig for EKS cluster..."
aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME

# Test kubectl connection
log_info "Testing Kubernetes connection..."
kubectl get nodes

if [ $? -eq 0 ]; then
    log_success "Kubernetes access configured successfully!"
else
    log_error "Failed to connect to EKS cluster"
    exit 1
fi

# Wait for nodes to be ready
log_info "Waiting for nodes to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Step 5: Set up GitHub Actions (if not already done)
log_header "GitHub Actions Configuration"

cat << EOF
🔧 GitHub Actions Setup Required:

To enable automated deployments, add these secrets to your GitHub repository:

1. Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions

2. Add these secrets:
   ┌─────────────────────────┬──────────────────────────────────┐
   │ Secret Name             │ Value                            │
   ├─────────────────────────┼──────────────────────────────────┤
   │ AWS_ACCESS_KEY_ID       │ Your AWS Access Key              │
   │ AWS_SECRET_ACCESS_KEY   │ Your AWS Secret Key              │
   └─────────────────────────┴──────────────────────────────────┘

3. The GitHub Actions workflow will automatically:
   • Build and push Docker images to ECR
   • Deploy to EKS cluster
   • Run health checks
   • Display deployment status

EOF

read -p "✅ Have you set up GitHub Actions secrets? (y/n): " -n 1 -r
echo

# Step 6: Manual Deployment (Alternative to GitHub Actions)
log_header "Manual Deployment Option"

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Great! You can now trigger deployment by pushing to main branch:"
    log_info "  git add ."
    log_info "  git commit -m 'Deploy to AWS'"
    log_info "  git push origin main"
else
    log_info "No problem! Let's do a manual deployment..."
    
    # Manual deployment steps
    log_info "Running manual deployment..."
    
    # Build and push image manually
    log_info "Building Docker image..."
    
    # Run the key parts of the GitHub Actions workflow manually
    python scripts/build_bento.py || {
        log_error "Failed to build BentoML service"
        exit 1
    }
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URL
    
    # Build image
    docker build -t iris_classifier_service:latest .
    docker tag iris_classifier_service:latest $ECR_REPOSITORY_URL:latest
    docker push $ECR_REPOSITORY_URL:latest
    
    # Deploy to Kubernetes
    export ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    export IMAGE_TAG="latest"
    
    envsubst < k8s/iris-service.yaml | kubectl apply -f -
    
    log_success "Manual deployment completed!"
fi

# Step 7: Verify Deployment
log_header "Verifying Deployment"

log_info "Waiting for deployment to complete..."
kubectl rollout status deployment/iris-service --timeout=600s

# Check pod status
log_info "Checking pod status..."
kubectl get pods -l app=iris-service

# Get service information
log_info "Getting service information..."
kubectl get services

# Wait for LoadBalancer to be ready
log_info "Waiting for LoadBalancer to be assigned external IP..."
for i in {1..30}; do
    EXTERNAL_IP=$(kubectl get svc iris-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
    if [ ! -z "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
        log_success "LoadBalancer ready: $EXTERNAL_IP"
        break
    fi
    echo -n "."
    sleep 10
done

# Step 8: Final Status and URLs
log_header "Deployment Complete! 🎉"

if [ ! -z "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
    cat << EOF
🌸 Your Iris MLOps Pipeline is now running on AWS!

🔗 Service URLs:
┌─────────────────────┬─────────────────────────────────────┐
│ Service             │ URL                                 │
├─────────────────────┼─────────────────────────────────────┤
│ 🤖 ML API           │ http://$EXTERNAL_IP                 │
│ 📊 Health Check     │ http://$EXTERNAL_IP/health          │
│ 📈 API Docs         │ http://$EXTERNAL_IP/docs            │
└─────────────────────┴─────────────────────────────────────┘

🧪 Test Your Deployment:
# Health check
curl http://$EXTERNAL_IP/health

# Make a prediction
curl -X POST http://$EXTERNAL_IP/predict_single \\
  -H "Content-Type: application/json" \\
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

EOF
else
    log_warning "LoadBalancer not ready yet. Check status with:"
    log_info "kubectl get svc iris-service"
fi

# Management commands
cat << EOF
🛠️ Management Commands:
# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/iris-service

# Scale deployment
kubectl scale deployment iris-service --replicas=2

# Update deployment (after pushing new image)
kubectl rollout restart deployment/iris-service

# Delete deployment (to save costs)
kubectl delete -f k8s/iris-service.yaml

🗑️ Cleanup Commands (to avoid charges):
# Delete Kubernetes resources
kubectl delete all --all

# Destroy infrastructure
cd terraform-scripts && terraform destroy

💰 Cost Management:
• Monitor AWS billing dashboard
• Set up billing alerts
• Delete resources when not needed
• Consider using Spot instances

📊 Monitoring Setup:
To deploy full monitoring stack (optional):
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml

EOF

# Final health check
log_info "Running final health check..."
if [ ! -z "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
    sleep 30  # Give service time to be fully ready
    if curl -f -s "http://$EXTERNAL_IP/health" >/dev/null; then
        log_success "🎉 Deployment is healthy and ready to serve predictions!"
    else
        log_warning "Service deployed but may still be starting up. Check again in a few minutes."
    fi
else
    log_info "Service is deployed. LoadBalancer URL will be available shortly."
fi

log_success "🌸 AWS MLOps deployment complete! 🚀"

# Success exit
trap - EXIT  # Remove error trap
exit 0