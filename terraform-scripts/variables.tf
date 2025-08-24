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