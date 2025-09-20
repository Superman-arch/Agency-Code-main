#!/usr/bin/env python3
"""
Optimize Qwen2.5-Coder model for Jetson Orin Nano deployment
Supports TensorRT optimization and INT8 quantization
"""

import torch
import argparse
import os
import sys
import logging
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_jetson_environment():
    """Check if running on Jetson and verify environment"""
    is_jetson = os.path.exists("/etc/nv_tegra_release")
    
    if is_jetson:
        logger.info("Detected Jetson platform")
        
        # Check for TensorRT
        try:
            import tensorrt as trt
            logger.info(f"TensorRT version: {trt.__version__}")
        except ImportError:
            logger.warning("TensorRT not found. Install with: sudo pip3 install nvidia-tensorrt")
            
        # Check CUDA
        if torch.cuda.is_available():
            logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA version: {torch.version.cuda}")
        else:
            logger.warning("CUDA not available")
    else:
        logger.info("Not running on Jetson platform")
    
    return is_jetson

def quantize_model_int8(model_path: str, output_path: str):
    """Quantize model to INT8 for reduced memory usage"""
    logger.info("Starting INT8 quantization...")
    
    try:
        from transformers import BitsAndBytesConfig
        
        # Configure 8-bit quantization
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            bnb_8bit_compute_dtype=torch.float16,
            bnb_8bit_use_double_quant=True,
            bnb_8bit_quant_type="nf4"
        )
        
        # Load model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Save quantized model
        model.save_pretrained(output_path)
        logger.info(f"Quantized model saved to {output_path}")
        
        # Calculate size reduction
        original_size = sum(p.element_size() * p.nelement() for p in model.parameters())
        quantized_size = sum(p.element_size() * p.nelement() for p in model.parameters() if p.dtype == torch.int8)
        reduction = (1 - quantized_size / original_size) * 100
        logger.info(f"Model size reduced by {reduction:.1f}%")
        
    except ImportError:
        logger.error("bitsandbytes not installed. Install with: pip install bitsandbytes")
        sys.exit(1)

def optimize_for_tensorrt(model_path: str, output_path: str):
    """Optimize model for TensorRT acceleration on Jetson"""
    logger.info("Starting TensorRT optimization...")
    
    try:
        import tensorrt as trt
        import torch2trt
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="cuda",
            trust_remote_code=True
        )
        model.eval()
        
        # Create dummy input
        dummy_input = torch.randint(0, 1000, (1, 512)).cuda()
        
        # Convert to TensorRT
        logger.info("Converting to TensorRT...")
        model_trt = torch2trt.torch2trt(
            model,
            [dummy_input],
            fp16_mode=True,
            max_workspace_size=1 << 30  # 1GB workspace
        )
        
        # Save TensorRT model
        torch.save(model_trt.state_dict(), f"{output_path}/model_trt.pth")
        logger.info(f"TensorRT model saved to {output_path}")
        
    except ImportError as e:
        logger.error(f"Required package not found: {e}")
        logger.info("Install torch2trt: pip install torch2trt")
        sys.exit(1)

def optimize_model_loading(model_path: str):
    """Optimize model loading for faster startup"""
    logger.info("Optimizing model loading...")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    
    # Load model with optimizations
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Enable memory efficient attention
    if hasattr(model, 'enable_mem_efficient_attention'):
        model.enable_mem_efficient_attention()
        logger.info("Enabled memory efficient attention")
    
    # Compile model with torch.compile for faster inference
    if torch.__version__ >= "2.0":
        model = torch.compile(model, mode="reduce-overhead")
        logger.info("Model compiled with torch.compile")
    
    return model, tokenizer

def benchmark_model(model, tokenizer, num_iterations=10):
    """Benchmark model inference speed"""
    import time
    
    logger.info("Running benchmark...")
    
    # Prepare test input
    test_prompt = "def fibonacci(n):"
    inputs = tokenizer(test_prompt, return_tensors="pt").to(model.device)
    
    # Warmup
    for _ in range(3):
        with torch.no_grad():
            _ = model.generate(**inputs, max_new_tokens=50)
    
    # Benchmark
    times = []
    for i in range(num_iterations):
        start = time.time()
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=100)
        end = time.time()
        times.append(end - start)
        logger.info(f"Iteration {i+1}: {end-start:.3f}s")
    
    avg_time = sum(times) / len(times)
    tokens_per_second = 100 / avg_time
    
    logger.info(f"Average inference time: {avg_time:.3f}s")
    logger.info(f"Tokens per second: {tokens_per_second:.1f}")
    
    return avg_time, tokens_per_second

def main():
    parser = argparse.ArgumentParser(description="Optimize Qwen2.5-Coder for Jetson deployment")
    parser.add_argument("--model-path", default="Qwen/Qwen2.5-Coder-7B-Instruct", help="Model path or HuggingFace ID")
    parser.add_argument("--output-path", default="./optimized_model", help="Output path for optimized model")
    parser.add_argument("--quantize", action="store_true", help="Apply INT8 quantization")
    parser.add_argument("--tensorrt", action="store_true", help="Optimize for TensorRT")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark after optimization")
    
    args = parser.parse_args()
    
    # Check environment
    is_jetson = check_jetson_environment()
    
    # Create output directory
    Path(args.output_path).mkdir(parents=True, exist_ok=True)
    
    # Apply optimizations
    if args.quantize:
        quantize_model_int8(args.model_path, args.output_path)
        args.model_path = args.output_path
    
    if args.tensorrt and is_jetson:
        optimize_for_tensorrt(args.model_path, args.output_path)
    
    # Load optimized model
    model, tokenizer = optimize_model_loading(args.model_path)
    
    # Run benchmark if requested
    if args.benchmark:
        benchmark_model(model, tokenizer)
    
    # Save configuration
    config = {
        "model_path": args.model_path,
        "optimizations": {
            "quantized": args.quantize,
            "tensorrt": args.tensorrt and is_jetson,
            "torch_compile": torch.__version__ >= "2.0"
        }
    }
    
    import json
    with open(f"{args.output_path}/optimization_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info("Optimization complete!")

if __name__ == "__main__":
    main()