#!/bin/bash

# Deployment script for Jetson Orin Nano
# This script sets up the Qwen Coder Interface on Jetson hardware

set -e

echo "======================================"
echo "Qwen Coder Interface - Jetson Deployment"
echo "======================================"

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "Warning: Not running on Jetson hardware"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# System information
echo "System Information:"
if [ -f /etc/nv_tegra_release ]; then
    cat /etc/nv_tegra_release
fi
echo "Python version: $(python3 --version)"
echo "CUDA available: $(python3 -c 'import torch; print(torch.cuda.is_available())')"
echo ""

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    curl \
    docker.io \
    docker-compose \
    nginx \
    build-essential \
    cmake

# Install Jetson-specific packages
if [ -f /etc/nv_tegra_release ]; then
    echo "Installing Jetson-specific packages..."
    
    # Install JetPack dependencies
    sudo apt-get install -y \
        cuda-toolkit-11-4 \
        libcudnn8 \
        tensorrt \
        python3-libnvinfer-dev
    
    # Set CUDA paths
    export PATH=/usr/local/cuda/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
    
    # Add to bashrc for persistence
    echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install PyTorch for Jetson
if [ -f /etc/nv_tegra_release ]; then
    echo "Installing PyTorch for Jetson..."
    # Install PyTorch with CUDA support for Jetson
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    echo "Installing standard PyTorch..."
    pip install torch torchvision torchaudio
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install additional Jetson optimizations
if [ -f /etc/nv_tegra_release ]; then
    echo "Installing Jetson optimization packages..."
    pip install pycuda
    
    # Install torch2trt for TensorRT optimization
    git clone https://github.com/NVIDIA-AI-IOT/torch2trt
    cd torch2trt
    python setup.py install
    cd ..
fi

# Download and optimize model
echo "Downloading and optimizing Qwen2.5-Coder model..."
python jetson_deployment/optimize_model.py \
    --model-path "Qwen/Qwen2.5-Coder-7B-Instruct" \
    --output-path "./optimized_model" \
    --quantize \
    $([ -f /etc/nv_tegra_release ] && echo "--tensorrt") \
    --benchmark

# Setup Docker
echo "Setting up Docker containers..."
sudo usermod -aG docker $USER

# Build Docker images
docker-compose -f docker/docker-compose.yml build

# Create necessary directories
mkdir -p data logs model_cache workspace

# Setup systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/qwen-coder.service > /dev/null <<EOF
[Unit]
Description=Qwen Coder Interface
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose -f docker/docker-compose.yml up
ExecStop=/usr/bin/docker-compose -f docker/docker-compose.yml down

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable qwen-coder.service

# Setup nginx reverse proxy
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/qwen-coder > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/qwen-coder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Performance tuning for Jetson
if [ -f /etc/nv_tegra_release ]; then
    echo "Applying Jetson performance optimizations..."
    
    # Set to max performance mode
    sudo nvpmodel -m 0
    sudo jetson_clocks
    
    # Create performance script
    cat > set_performance.sh <<EOF
#!/bin/bash
# Set Jetson to maximum performance
sudo nvpmodel -m 0
sudo jetson_clocks
EOF
    chmod +x set_performance.sh
    
    # Add to crontab for startup
    (crontab -l 2>/dev/null; echo "@reboot $(pwd)/set_performance.sh") | crontab -
fi

# Create .env file
echo "Creating environment configuration..."
cat > .env <<EOF
MODEL_NAME=Qwen/Qwen2.5-Coder-7B-Instruct
MODEL_DEVICE=cuda
USE_QUANTIZATION=true
USE_TENSORRT=$([ -f /etc/nv_tegra_release ] && echo "true" || echo "false")
MODEL_CACHE_DIR=./model_cache
SECRET_KEY=$(openssl rand -hex 32)
EOF

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "To start the service:"
echo "  sudo systemctl start qwen-coder.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u qwen-coder.service -f"
echo ""
echo "Access the interface at:"
echo "  http://localhost"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop qwen-coder.service"
echo ""

# Optionally start the service
read -p "Start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl start qwen-coder.service
    echo "Service started! Opening browser..."
    sleep 5
    xdg-open http://localhost 2>/dev/null || echo "Please open http://localhost in your browser"
fi