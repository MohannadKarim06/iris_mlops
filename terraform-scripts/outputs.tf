# terraform-scripts/outputs.tf
output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.iris_cluster.endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.iris_cluster.name
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.iris_ecr.repository_url
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.iris_vpc.id
}

output "subnet_ids" {
  description = "Subnet IDs"
  value       = aws_subnet.public[*].id
}

output "load_balancer_controller_role_arn" {
  description = "ALB Controller IAM Role ARN"
  value       = aws_iam_role.aws_load_balancer_controller_role.arn
}

output "mlflow_bucket_name" {
  description = "MLflow S3 bucket name"
  value       = aws_s3_bucket.mlflow_artifacts.bucket
}
