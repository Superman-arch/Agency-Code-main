# Qwen Coder Interface

A powerful web-based interface for Qwen2.5-Coder-7B-Instruct with integrated terminal access, designed for local deployment and optimized for NVIDIA Jetson Orin Nano.

![Qwen Coder Interface](https://img.shields.io/badge/Model-Qwen2.5--Coder--7B-purple)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![React](https://img.shields.io/badge/React-18.3-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed)
![Jetson](https://img.shields.io/badge/Jetson-Optimized-76b900)

## Features

### Core Capabilities
- **AI-Powered Code Assistant**: Leverages Qwen2.5-Coder-7B-Instruct for code generation, completion, and analysis
- **Interactive Terminal**: Secure command execution with real-time output streaming
- **Code Editor**: Monaco-based editor with syntax highlighting and IntelliSense
- **Split-Pane Interface**: Similar to Open WebUI with resizable panels for optimal workflow
- **File Management**: Browse, edit, and manage project files directly in the interface
- **Dark/Light Theme**: Customizable interface with theme persistence

### Technical Features
- **WebSocket Communication**: Real-time bidirectional communication for chat and terminal
- **Session Management**: Persistent conversation context and workspace state
- **Security Sandboxing**: Secure terminal execution with command validation
- **Model Optimization**: INT8 quantization and TensorRT support for Jetson deployment
- **Docker Support**: Containerized deployment with docker-compose
- **Agency Swarm Integration**: Compatible with Agency Swarm framework

## System Requirements

### Minimum Requirements
- **CPU**: 8-core processor
- **RAM**: 16GB (32GB recommended)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for CUDA acceleration)
- **Storage**: 50GB free space
- **OS**: Ubuntu 20.04+ / macOS 12+ / Windows 11 with WSL2

### Jetson Orin Nano Requirements
- **JetPack**: 5.1 or later
- **RAM**: 8GB minimum
- **Storage**: 64GB+ NVMe SSD recommended
- **Power**: 15W or 25W mode

## Quick Start

### Quick Setup for Jetson Nano
```bash
# SSH into Jetson and run these commands:
ssh username@jetson-ip
rm -rf Agency-Code-main  # Remove if exists
git clone https://github.com/Superman-arch/Agency-Code-main.git
cd Agency-Code-main/qwen-coder-interface
./jetson_deployment/deploy.sh
```

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/Superman-arch/Agency-Code-main.git
cd Agency-Code-main/qwen-coder-interface
```

2. **Install backend dependencies**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Install frontend dependencies**
```bash
cd frontend
npm install
cd ..
```

4. **Create environment file**
```bash
cat > .env <<EOF
MODEL_NAME=Qwen/Qwen2.5-Coder-7B-Instruct
MODEL_DEVICE=cuda
SECRET_KEY=your-secret-key-here
EOF
```

5. **Start the backend server**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Start the frontend (new terminal)**
```bash
cd frontend
npm run dev
```

7. **Access the interface**
Open http://localhost:3000 in your browser

### Docker Deployment

```bash
# Build and run with docker-compose
docker-compose -f docker/docker-compose.yml up -d

# Access at http://localhost
```

## Jetson Orin Nano Deployment

### Step-by-Step SSH Setup

#### First-Time Setup
```bash
# 1. SSH into your Jetson
ssh username@jetson-ip

# 2. Remove any existing clone (if present)
rm -rf Agency-Code-main

# 3. Clone the repository
git clone https://github.com/Superman-arch/Agency-Code-main.git

# 4. Navigate to the project
cd Agency-Code-main/qwen-coder-interface

# 5. Make deployment script executable
chmod +x jetson_deployment/deploy.sh

# 6. Run the deployment
./jetson_deployment/deploy.sh
```

#### Quick Reinstall (if already cloned)
```bash
ssh username@jetson-ip
cd ~/Agency-Code-main/qwen-coder-interface
git pull
./jetson_deployment/deploy.sh
```

#### Complete Clean Install (One-Liner)
```bash
ssh username@jetson-ip "cd ~ && rm -rf Agency-Code-main && git clone https://github.com/Superman-arch/Agency-Code-main.git && cd Agency-Code-main/qwen-coder-interface && chmod +x jetson_deployment/deploy.sh && ./jetson_deployment/deploy.sh"
```

### Manual Optimization
```bash
# Optimize model for Jetson
python jetson_deployment/optimize_model.py \
    --model-path "Qwen/Qwen2.5-Coder-7B-Instruct" \
    --output-path "./optimized_model" \
    --quantize \
    --tensorrt \
    --benchmark
```

### Performance Settings
```bash
# Set Jetson to max performance
sudo nvpmodel -m 0
sudo jetson_clocks
```

## Architecture

### Backend Stack
- **FastAPI**: High-performance async web framework
- **Transformers**: Hugging Face library for model inference
- **WebSockets**: Real-time communication
- **SQLAlchemy**: Database ORM for session management
- **Agency Swarm**: Agent framework integration

### Frontend Stack
- **Next.js**: React framework with SSR support
- **Monaco Editor**: VSCode's editor component
- **XTerm.js**: Terminal emulator
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: State management

### Model Optimization
- **INT8 Quantization**: Reduces model size by ~75%
- **TensorRT**: NVIDIA's inference optimization library
- **torch.compile**: PyTorch 2.0 compilation for faster inference
- **Memory Mapping**: Efficient model loading

## API Documentation

### Chat Endpoints
```python
POST /api/chat/generate
{
    "message": "Write a Python function",
    "session_id": "optional-session-id",
    "max_tokens": 512,
    "temperature": 0.7
}

POST /api/chat/analyze-code
{
    "code": "def hello(): pass",
    "analysis_type": "review|explain|optimize|debug"
}
```

### Terminal Endpoints
```python
POST /api/terminal/execute
{
    "command": "ls -la",
    "session_id": "session-id",
    "working_dir": "/path/to/dir"
}

WebSocket /ws/{session_id}
{
    "type": "input|resize|kill",
    "data": "command or terminal data"
}
```

### File Operations
```python
POST /api/files/read
POST /api/files/write
POST /api/files/delete
GET  /api/files/list
```

## Configuration

### Environment Variables
```bash
# Model Settings
MODEL_NAME=Qwen/Qwen2.5-Coder-7B-Instruct
MODEL_DEVICE=cuda|cpu
MODEL_MAX_LENGTH=32768
USE_QUANTIZATION=true|false

# Terminal Settings
TERMINAL_MAX_OUTPUT=10000
TERMINAL_TIMEOUT=30
TERMINAL_ALLOWED_COMMANDS=ls,pwd,cd,cat,echo,grep,python,npm,git

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]

# Jetson Specific
USE_TENSORRT=true|false
IS_JETSON=auto-detected
```

## Security Considerations

### Terminal Sandboxing
- Command validation against whitelist
- Forbidden pattern detection
- Process timeout limits
- Resource usage constraints

### Authentication (Coming Soon)
- JWT-based authentication
- Session management
- Role-based access control

### Best Practices
- Always use HTTPS in production
- Regularly update dependencies
- Monitor resource usage
- Implement rate limiting

## Performance Benchmarks

### Desktop (RTX 3080)
- Model Load Time: ~15 seconds
- Inference Speed: ~45 tokens/second
- Memory Usage: ~14GB

### Jetson Orin Nano (Optimized)
- Model Load Time: ~30 seconds
- Inference Speed: ~15 tokens/second (INT8)
- Memory Usage: ~6GB (quantized)

## Troubleshooting

### Common Jetson Setup Issues

1. **"destination path 'Agency-Code-main' already exists"**
```bash
# Remove the existing directory and re-clone
rm -rf Agency-Code-main
git clone https://github.com/Superman-arch/Agency-Code-main.git
```

2. **"No such file or directory: Agency-Code-main/qwen-coder-interface"**
```bash
# Make sure you're in the right directory
cd ~/Agency-Code-main
ls  # Should show qwen-coder-interface folder
cd qwen-coder-interface
```

3. **Out of memory during model download**
```bash
# Enable larger swap BEFORE running deployment
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Then run deployment
./jetson_deployment/deploy.sh
```

4. **CUDA not available**
```bash
# Check CUDA installation
python3 -c "import torch; print(torch.cuda.is_available())"

# If false, ensure JetPack is properly installed
sudo apt-get update
sudo apt-get install nvidia-jetpack
```

5. **Model download fails or is slow**
```bash
# Use local cache and retry
export HF_HOME=~/huggingface_cache
mkdir -p $HF_HOME

# Or download model manually first
python3 -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-Coder-7B-Instruct', cache_dir='$HF_HOME')"
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black backend/
isort backend/
```

## Roadmap

- [ ] Multi-user authentication
- [ ] Cloud deployment support (AWS, GCP, Azure)
- [ ] Model fine-tuning interface
- [ ] Plugin system for extensions
- [ ] Mobile responsive design
- [ ] Voice input/output support
- [ ] Collaborative editing
- [ ] Integration with VSCode extensions

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Qwen Team** at Alibaba Cloud for the amazing Qwen2.5-Coder model
- **Hugging Face** for the Transformers library
- **NVIDIA** for Jetson platform and TensorRT
- **Agency Swarm** framework for agent capabilities
- **Open WebUI** for interface inspiration

## Support

- **Issues**: [GitHub Issues](https://github.com/Superman-arch/Agency-Code-main/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Superman-arch/Agency-Code-main/discussions)
- **Documentation**: [Wiki](https://github.com/Superman-arch/Agency-Code-main/wiki)

## Citation

If you use this project in your research or work, please cite:

```bibtex
@software{qwen_coder_interface,
  title = {Qwen Coder Interface},
  author = {Superman-arch},
  year = {2024},
  url = {https://github.com/Superman-arch/Agency-Code-main}
}
```

---

Built with ❤️ for the AI coding community