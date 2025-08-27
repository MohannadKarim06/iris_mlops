#!/bin/bash

# =============================================================================
# Iris MLOps Pipeline - Local Development Setup
# =============================================================================
# This script sets up the complete local development environment
# Author: Your Name
# Usage: chmod +x scripts/setup_local.sh && ./scripts/setup_local.sh
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Error handling
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "Setup failed! Check the logs above for details."
        log_info "You can re-run this script after fixing the issues."
    fi
}
trap cleanup EXIT

# Welcome message
cat << "EOF"
🌸 Iris MLOps Pipeline - Local Setup
====================================
This script will set up your complete local development environment:

1. ✅ Python virtual environment
2. ✅ Install all dependencies  
3. ✅ Initialize DVC pipeline
4. ✅ Run complete ML pipeline
5. ✅ Build BentoML service
6. ✅ Start local services with Docker
7. ✅ Run API tests
8. ✅ Display service URLs

EOF

read -p "🚀 Ready to start? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Setup cancelled by user"
    exit 0
fi

# Check prerequisites
log_header "Checking Prerequisites"

check_command() {
    if command -v $1 >/dev/null 2>&1; then
        log_success "$1 is installed ✓"
        return 0
    else
        log_error "$1 is not installed"
        return 1
    fi
}

# Required tools
missing_tools=()

if ! check_command python3; then
    missing_tools+=("python3")
fi

if ! check_command pip3; then
    missing_tools+=("pip3")
fi

if ! check_command docker; then
    missing_tools+=("docker")
fi

if ! check_command docker-compose; then
    missing_tools+=("docker-compose")
fi

if ! check_command git; then
    missing_tools+=("git")
fi

if [ ${#missing_tools[@]} -ne 0 ]; then
    log_error "Missing required tools: ${missing_tools[*]}"
    log_info "Please install them and re-run this script"
    log_info "Installation guides:"
    log_info "  - Python: https://python.org/downloads"
    log_info "  - Docker: https://docs.docker.com/get-docker"
    log_info "  - Git: https://git-scm.com/downloads"
    exit 1
fi

# Check Docker daemon
if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon is not running. Please start Docker and try again."
    exit 1
fi

log_success "All prerequisites satisfied!"

# Step 1: Python Environment Setup
log_header "Setting up Python Environment"

# Create virtual environment
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip

# Install requirements
log_info "Installing Python dependencies..."
pip install -r requirements.txt

log_success "Python environment ready!"

# Step 2: Initialize DVC
log_header "Initializing DVC"

if [ ! -f ".dvc/config" ]; then
    log_info "Initializing DVC..."
    dvc init --no-scm || log_warning "DVC already initialized"
else
    log_info "DVC already initialized"
fi

# Create necessary directories
log_info "Creating project directories..."
mkdir -p data/raw data/processed models metrics

log_success "DVC initialized!"

# Step 3: Run ML Pipeline
log_header "Running ML Pipeline"

log_info "Starting complete ML pipeline with DVC..."
log_info "This includes: data ingestion → preprocessing → training → evaluation"

# Run the pipeline
dvc repro

# Check if pipeline completed successfully
if [ -f "metrics/eval_metrics.json" ]; then
    accuracy=$(python3 -c "import json; print(json.load(open('metrics/eval_metrics.json'))['accuracy'])")
    log_success "ML Pipeline completed! Model accuracy: ${accuracy}"
else
    log_error "ML Pipeline failed - metrics file not found"
    exit 1
fi

# Step 4: Build BentoML Service
log_header "Building BentoML Service"

log_info "Building BentoML service with trained model..."
python scripts/build_bento.py

if [ $? -eq 0 ]; then
    log_success "BentoML service built successfully!"
else
    log_error "Failed to build BentoML service"
    exit 1
fi

# Step 5: Docker Services
log_header "Starting Local Services"

# Stop any existing containers
log_info "Stopping existing containers..."
docker-compose -f docker-compose.local.yml down --remove-orphans 2>/dev/null || true

# Build and start services
log_info "Building and starting Docker services..."
log_info "This may take a few minutes for the first run..."

docker-compose -f docker-compose.local.yml up -d --build

# Wait for services to be ready
log_info "Waiting for services to start..."
sleep 30

# Check service health
check_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Checking $service_name (port $port)..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$port/health >/dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_warning "$service_name may not be ready yet (will continue anyway)"
    return 1
}

# Check core services
check_service "ML API" 3000

log_success "Docker services started!"

# Step 6: Run Tests
log_header "Running API Tests"

log_info "Testing ML API endpoints..."

# Wait a bit more for services to fully initialize
sleep 10

# Run the test script
python scripts/test_local.py

if [ $? -eq 0 ]; then
    log_success "All API tests passed!"
else
    log_warning "Some API tests failed, but setup continues..."
fi

# Step 7: Display Service Information
log_header "Setup Complete! 🎉"

cat << EOF
🌸 Your Iris MLOps Pipeline is now running locally!

📊 Available Services:
┌─────────────────────┬─────────────────────────┬──────────────────┐
│ Service             │ URL                     │ Description      │
├─────────────────────┼─────────────────────────┼──────────────────┤
│ 🤖 ML API           │ http://localhost:3000   │ Prediction API   │
│ 🎨 Streamlit UI     │ http://localhost:8501   │ Web Interface    │
│ 📈 Prometheus       │ http://localhost:9090   │ Metrics          │
│ 📊 Grafana          │ http://localhost:3001   │ Dashboards       │
└─────────────────────┴─────────────────────────┴──────────────────┘

🔗 Quick Links:
• API Health: http://localhost:3000/health
• API Docs: http://localhost:3000/docs (auto-generated)
• Grafana Login: admin/admin

🧪 Test Commands:
# Test single prediction
curl -X POST http://localhost:3000/predict_single \\
  -H "Content-Type: application/json" \\
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

# Run comprehensive tests
python scripts/test_local.py

📁 Project Structure:
• Models: ./models/
• Data: ./data/
• Metrics: ./metrics/
• Logs: docker-compose logs

🛠️ Management Commands:
# View logs
docker-compose -f docker-compose.local.yml logs -f

# Stop services
docker-compose -f docker-compose.local.yml down

# Restart services
docker-compose -f docker-compose.local.yml restart

# Rebuild after code changes
docker-compose -f docker-compose.local.yml up -d --build

🚀 Next Steps:
1. Open the Streamlit UI to interact with the model
2. Check Grafana dashboards for monitoring
3. Modify code and see changes in real-time
4. Deploy to AWS when ready: ./scripts/deploy_aws.sh

EOF

# Final health check
log_header "Final Health Check"

services_ready=0
total_services=4

# Check each service
check_url() {
    local name=$1
    local url=$2
    if curl -s "$url" >/dev/null 2>&1; then
        log_success "$name: Ready ✓"
        services_ready=$((services_ready + 1))
    else
        log_warning "$name: Not responding ⚠️"
    fi
}

check_url "ML API" "http://localhost:3000/health"
check_url "Streamlit" "http://localhost:8501"
check_url "Prometheus" "http://localhost:9090"
check_url "Grafana" "http://localhost:3001"

echo
if [ $services_ready -eq $total_services ]; then
    log_success "🎉 All services are running perfectly!"
else
    log_warning "⚠️  $services_ready/$total_services services are ready"
    log_info "Some services might need a few more minutes to start"
    log_info "Check service logs: docker-compose -f docker-compose.local.yml logs"
fi

# Deactivate virtual environment message
echo
log_info "Virtual environment is active. To deactivate later, run: deactivate"

log_success "🌸 Local MLOps setup complete! Happy coding! 🚀"

# Success exit
trap - EXIT  # Remove error trap
exit 0