import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
from typing import List, Dict, Optional, AsyncGenerator
import asyncio
import logging
from threading import Thread
from queue import Queue
import json

from utils.config import Settings

logger = logging.getLogger(__name__)

class ModelService:
    """Service for managing the Qwen2.5-Coder model"""
    
    def __init__(self):
        self.settings = Settings()
        self.model = None
        self.tokenizer = None
        self.device = None
        self._ready = False
        
    async def initialize(self):
        """Initialize the model and tokenizer"""
        try:
            logger.info(f"Loading model: {self.settings.model_name}")
            
            # Determine device
            if self.settings.model_device == "cuda" and torch.cuda.is_available():
                self.device = "cuda"
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                logger.info("Using CPU device")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.settings.model_name,
                cache_dir=self.settings.model_cache_dir,
                trust_remote_code=True
            )
            
            # Load model with appropriate settings
            model_kwargs = {
                "cache_dir": self.settings.model_cache_dir,
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "device_map": "auto" if self.device == "cuda" else None,
                "trust_remote_code": True
            }
            
            # Add quantization if enabled
            if self.settings.use_quantization:
                model_kwargs["load_in_8bit"] = True
                logger.info("Loading model with 8-bit quantization")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.settings.model_name,
                **model_kwargs
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            self._ready = True
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if model is ready"""
        return self._ready
    
    async def generate_response(
        self,
        prompt: str,
        context: List[Dict] = None,
        stream: bool = True,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """Generate response from the model"""
        
        if not self._ready:
            raise RuntimeError("Model not initialized")
        
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful coding assistant."}
            ]
            
            # Add context if provided
            if context:
                messages.extend(context)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Apply chat template
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Tokenize input
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
            
            if stream:
                # Stream response
                response = ""
                streamer = TextStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
                
                # Run generation in thread for async streaming
                generation_kwargs = {
                    **model_inputs,
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": True,
                    "streamer": streamer
                }
                
                # Use asyncio to run in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.model.generate(**generation_kwargs)
                )
                
                return response
            else:
                # Generate without streaming
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True
                )
                
                # Decode response
                generated_ids = [
                    output_ids[len(input_ids):] 
                    for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
                ]
                
                response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
                return response
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def get_code_completions(
        self,
        code: str,
        position: Dict[str, int],
        num_suggestions: int = 3
    ) -> List[str]:
        """Get code completion suggestions"""
        
        if not self._ready:
            raise RuntimeError("Model not initialized")
        
        try:
            # Extract context around cursor position
            lines = code.split('\n')
            line_num = position.get('line', 0)
            col_num = position.get('column', 0)
            
            # Get code up to cursor
            code_before = '\n'.join(lines[:line_num])
            if line_num < len(lines):
                code_before += '\n' + lines[line_num][:col_num]
            
            # Create prompt for completion
            prompt = f"Complete the following code:\n\n```python\n{code_before}"
            
            # Generate multiple completions
            suggestions = []
            for _ in range(num_suggestions):
                response = await self.generate_response(
                    prompt=prompt,
                    max_new_tokens=50,
                    temperature=0.8,
                    stream=False
                )
                
                # Extract just the completion part
                if '```' in response:
                    completion = response.split('```')[0].strip()
                else:
                    completion = response.strip()
                
                if completion and completion not in suggestions:
                    suggestions.append(completion)
            
            return suggestions[:num_suggestions]
            
        except Exception as e:
            logger.error(f"Error getting code completions: {e}")
            return []
    
    async def analyze_code(
        self,
        code: str,
        analysis_type: str = "review"
    ) -> Dict:
        """Analyze code for issues, improvements, or explanations"""
        
        if not self._ready:
            raise RuntimeError("Model not initialized")
        
        prompts = {
            "review": f"Review this code and provide feedback on improvements:\n\n```\n{code}\n```",
            "explain": f"Explain what this code does:\n\n```\n{code}\n```",
            "optimize": f"Suggest optimizations for this code:\n\n```\n{code}\n```",
            "debug": f"Find potential bugs in this code:\n\n```\n{code}\n```"
        }
        
        prompt = prompts.get(analysis_type, prompts["review"])
        
        try:
            response = await self.generate_response(
                prompt=prompt,
                max_new_tokens=1024,
                temperature=0.7,
                stream=False
            )
            
            return {
                "type": analysis_type,
                "analysis": response,
                "code": code
            }
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.model:
            del self.model
            torch.cuda.empty_cache() if self.device == "cuda" else None
        if self.tokenizer:
            del self.tokenizer
        self._ready = False
        logger.info("Model service cleaned up")