#!/bin/bash
set -e

echo "🚀 Setting up AWS infrastructure..."

# Install required tools
echo "Installing kubectl..."
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/


echo "✅ Tools installed successfully!"

# Deploy infrastructure
echo "🏗️ Deploying Terraform infrastructure..."
cd terraform
terraform init
terraform plan
terraform apply -auto-approve

# Configure kubectl
echo "⚙️ Configuring kubectl..."
aws eks update-kubeconfig --region us-west-2 --name iris-mlops-cluster

# Install AWS Load Balancer Controller
echo "🔧 Installing AWS Load Balancer Controller..."
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller/crds?ref=master"

# Get account ID for ALB controller
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
sed -i "s/ACCOUNT-ID/$ACCOUNT_ID/g" k8s/aws-load-balancer-controller.yaml

echo "✅ AWS setup complete!"
echo "🎯 Ready for deployment!"