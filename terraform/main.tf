# This file sets up: EKS cluster, ALB, ECR, CloudWatch
# FOCUS: Understand what each resource does, don't memorize syntax

provider "aws" {
  region = var.aws_region
}

# EKS Cluster
resource "aws_eks_cluster" "iris_cluster" {
  name     = "iris-mlops-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.24"

  vpc_config {
    subnet_ids = aws_subnet.public[*].id
  }
}

# Node Group
resource "aws_eks_node_group" "iris_nodes" {
  cluster_name    = aws_eks_cluster.iris_cluster.name
  node_group_name = "iris-nodes"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = aws_subnet.public[*].id

  scaling_config {
    desired_size = 2
    max_size     = 4
    min_size     = 1
  }

  instance_types = ["t3.nano"]
}

# ECR Repository
resource "aws_ecr_repository" "iris_ecr" {
  name = "iris-bentoml"
}

# ALB for EKS
resource "aws_lb" "iris_alb" {
  name               = "iris-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "iris_logs" {
  name              = "/aws/eks/iris-cluster/logs"
  retention_in_days = 7
}

# VPC and networking resources (standard EKS setup)
# ... (VPC, subnets, security groups, IAM roles)