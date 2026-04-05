"""
部署模块
Deployment Module

实现模型量化、ONNX导出、实时推理服务
"""

import os
import json
import time
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import logging

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    model_path: str = "models/defense_agent.pt"
    quantization: str = "dynamic"
    precision: str = "fp16"
    max_batch_size: int = 1000
    max_latency_ms: float = 5.0
    warmup_iterations: int = 10
    enable_cache: bool = True
    cache_ttl_seconds: int = 60


class ModelQuantizer:
    
    def __init__(self, model: nn.Module, config: Optional[DeploymentConfig] = None):
        self.model = model
        self.config = config or DeploymentConfig()
        self.quantized_model = None
    
    def quantize_dynamic(self) -> nn.Module:
        self.quantized_model = torch.quantization.quantize_dynamic(
            self.model,
            {nn.Linear, nn.LSTM, nn.GRU},
            dtype=torch.qint8
        )
        return self.quantized_model
    
    def quantize_static(self, calibration_data: List[torch.Tensor]) -> nn.Module:
        self.model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
        torch.quantization.prepare(self.model, inplace=True)
        
        with torch.no_grad():
            for data in calibration_data:
                self.model(data)
        
        torch.quantization.convert(self.model, inplace=True)
        self.quantized_model = self.model
        return self.quantized_model
    
    def quantize_to_fp16(self) -> nn.Module:
        self.quantized_model = self.model.half()
        return self.quantized_model
    
    def quantize_to_int8(self, calibration_data: List[torch.Tensor]) -> nn.Module:
        return self.quantize_static(calibration_data)
    
    def get_model_size(self, model: Optional[nn.Module] = None) -> Dict:
        model = model or self.model
        param_size = sum(p.numel() * p.element_size() for p in model.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
        total_size = param_size + buffer_size
        
        return {
            "param_size_mb": param_size / (1024 * 1024),
            "buffer_size_mb": buffer_size / (1024 * 1024),
            "total_size_mb": total_size / (1024 * 1024)
        }


class ONNXExporter:
    
    def __init__(self, model: nn.Module, config: Optional[DeploymentConfig] = None):
        self.model = model
        self.config = config or DeploymentConfig()
    
    def export(
        self,
        output_path: str,
        input_shape: Tuple[int, ...],
        opset_version: int = 14,
        dynamic_batch: bool = True
    ) -> Dict:
        self.model.eval()
        
        dummy_input = torch.randn(*input_shape)
        
        dynamic_axes = None
        if dynamic_batch:
            dynamic_axes = {
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        
        torch.onnx.export(
            self.model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=opset_version,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes=dynamic_axes
        )
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        
        return {
            "output_path": output_path,
            "file_size_mb": file_size,
            "input_shape": input_shape,
            "opset_version": opset_version,
            "dynamic_batch": dynamic_batch
        }
    
    def verify(self, onnx_path: str, test_input: torch.Tensor) -> Dict:
        try:
            import onnx
            import onnxruntime as ort
            
            onnx_model = onnx.load(onnx_path)
            onnx.checker.check_model(onnx_model)
            
            session = ort.InferenceSession(onnx_path)
            
            input_name = session.get_inputs()[0].name
            
            with torch.no_grad():
                torch_output = self.model(test_input).numpy()
            
            onnx_output = session.run(None, {input_name: test_input.numpy()})[0]
            
            max_diff = np.max(np.abs(torch_output - onnx_output))
            mean_diff = np.mean(np.abs(torch_output - onnx_output))
            
            return {
                "valid": True,
                "max_diff": float(max_diff),
                "mean_diff": float(mean_diff),
                "torch_output_shape": torch_output.shape,
                "onnx_output_shape": onnx_output.shape
            }
        except ImportError:
            return {"valid": False, "error": "onnx or onnxruntime not installed"}
        except Exception as e:
            return {"valid": False, "error": str(e)}


class TorchScriptExporter:
    
    def __init__(self, model: nn.Module):
        self.model = model
    
    def export_trace(self, output_path: str, example_input: torch.Tensor) -> Dict:
        self.model.eval()
        
        traced_model = torch.jit.trace(self.model, example_input)
        traced_model.save(output_path)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        
        return {
            "output_path": output_path,
            "file_size_mb": file_size,
            "method": "trace"
        }
    
    def export_script(self, output_path: str) -> Dict:
        self.model.eval()
        
        scripted_model = torch.jit.script(self.model)
        scripted_model.save(output_path)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        
        return {
            "output_path": output_path,
            "file_size_mb": file_size,
            "method": "script"
        }


class InferenceCache:
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 60):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
    
    def _hash_state(self, state: np.ndarray) -> str:
        return hash(state.tobytes()).__str__()
    
    def get(self, state: np.ndarray) -> Optional[Any]:
        key = self._hash_state(state)
        
        with self._lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    return value
                else:
                    del self.cache[key]
        
        return None
    
    def put(self, state: np.ndarray, result: Any):
        key = self._hash_state(state)
        
        with self._lock:
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[key] = (result, time.time())
    
    def clear(self):
        with self._lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds
            }


class AsyncInferenceService:
    
    def __init__(
        self,
        model: nn.Module,
        config: Optional[DeploymentConfig] = None,
        device: str = "cpu"
    ):
        self.model = model
        self.config = config or DeploymentConfig()
        self.device = device
        
        self.model.to(device)
        self.model.eval()
        
        self.cache = InferenceCache() if self.config.enable_cache else None
        
        self.request_queue = queue.Queue(maxsize=10000)
        self.result_queues: Dict[str, queue.Queue] = {}
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False
        self._worker_thread = None
        
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "total_latency_ms": 0.0,
            "max_latency_ms": 0.0
        }
        self._stats_lock = threading.Lock()
        
        self._warmup()
    
    def _warmup(self):
        logger.info(f"Warming up model with {self.config.warmup_iterations} iterations...")
        
        for _ in range(self.config.warmup_iterations):
            dummy_input = torch.randn(1, 13).to(self.device)
            with torch.no_grad():
                _ = self.model(dummy_input)
        
        logger.info("Warmup complete")
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self._worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Inference service started")
    
    def stop(self):
        self.running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("Inference service stopped")
    
    def _process_loop(self):
        while self.running:
            try:
                request = self.request_queue.get(timeout=0.1)
                self._process_request(request)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}")
    
    def _process_request(self, request: Dict):
        request_id = request["request_id"]
        state = request["state"]
        result_queue = request["result_queue"]
        
        start_time = time.time()
        
        if self.cache:
            cached_result = self.cache.get(state)
            if cached_result is not None:
                with self._stats_lock:
                    self.stats["cache_hits"] += 1
                
                result_queue.put({
                    "request_id": request_id,
                    "result": cached_result,
                    "latency_ms": 0.0,
                    "cached": True
                })
                return
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            if hasattr(self.model, 'get_action'):
                action_logits, value = self.model.get_action(state_tensor)
            else:
                output = self.model(state_tensor)
                if isinstance(output, tuple):
                    action_logits, value = output[0], output[1]
                else:
                    action_logits = output
                    value = torch.tensor(0.0)
        
        action = torch.argmax(action_logits, dim=-1).item()
        
        result = {
            "action": action,
            "action_logits": action_logits.cpu().numpy().tolist(),
            "value": value.item()
        }
        
        if self.cache:
            self.cache.put(state, result)
        
        latency_ms = (time.time() - start_time) * 1000
        
        with self._stats_lock:
            self.stats["total_requests"] += 1
            self.stats["total_latency_ms"] += latency_ms
            self.stats["max_latency_ms"] = max(self.stats["max_latency_ms"], latency_ms)
        
        result_queue.put({
            "request_id": request_id,
            "result": result,
            "latency_ms": latency_ms,
            "cached": False
        })
    
    async def infer(self, state: np.ndarray, timeout: float = 1.0) -> Dict:
        request_id = f"req_{time.time_ns()}"
        result_queue = queue.Queue()
        
        self.request_queue.put({
            "request_id": request_id,
            "state": state,
            "result_queue": result_queue
        })
        
        loop = asyncio.get_event_loop()
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, result_queue.get),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return {"error": "timeout", "request_id": request_id}
    
    def infer_sync(self, state: np.ndarray) -> Dict:
        start_time = time.time()
        
        if self.cache:
            cached_result = self.cache.get(state)
            if cached_result is not None:
                return {
                    "result": cached_result,
                    "latency_ms": 0.0,
                    "cached": True
                }
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            if hasattr(self.model, 'get_action'):
                action_logits, value = self.model.get_action(state_tensor)
            else:
                output = self.model(state_tensor)
                if isinstance(output, tuple):
                    action_logits, value = output[0], output[1]
                else:
                    action_logits = output
                    value = torch.tensor(0.0)
        
        action = torch.argmax(action_logits, dim=-1).item()
        
        result = {
            "action": action,
            "action_logits": action_logits.cpu().numpy().tolist(),
            "value": value.item()
        }
        
        if self.cache:
            self.cache.put(state, result)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "result": result,
            "latency_ms": latency_ms,
            "cached": False
        }
    
    def batch_infer(self, states: List[np.ndarray]) -> List[Dict]:
        start_time = time.time()
        
        batch_tensor = torch.FloatTensor(np.array(states)).to(self.device)
        
        with torch.no_grad():
            if hasattr(self.model, 'get_action'):
                action_logits, values = self.model.get_action(batch_tensor)
            else:
                output = self.model(batch_tensor)
                if isinstance(output, tuple):
                    action_logits, values = output[0], output[1]
                else:
                    action_logits = output
                    values = torch.zeros(len(states))
        
        actions = torch.argmax(action_logits, dim=-1).cpu().numpy()
        
        results = []
        for i, (action, logits, value) in enumerate(zip(actions, action_logits, values)):
            results.append({
                "action": int(action),
                "action_logits": logits.cpu().numpy().tolist(),
                "value": value.item() if hasattr(value, 'item') else float(value)
            })
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "results": results,
            "batch_size": len(states),
            "latency_ms": latency_ms,
            "per_sample_latency_ms": latency_ms / len(states)
        }
    
    def get_stats(self) -> Dict:
        with self._stats_lock:
            stats = self.stats.copy()
        
        if stats["total_requests"] > 0:
            stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["total_requests"]
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_requests"]
        else:
            stats["avg_latency_ms"] = 0.0
            stats["cache_hit_rate"] = 0.0
        
        if self.cache:
            stats["cache_stats"] = self.cache.get_stats()
        
        stats["queue_size"] = self.request_queue.qsize()
        stats["running"] = self.running
        
        return stats


class DeploymentModule:
    
    def __init__(
        self,
        model: nn.Module,
        config: Optional[DeploymentConfig] = None,
        device: str = "cpu"
    ):
        self.model = model
        self.config = config or DeploymentConfig()
        self.device = device
        
        self.quantizer = ModelQuantizer(model, config)
        self.inference_service: Optional[AsyncInferenceService] = None
        
        self.deployment_history: List[Dict] = []
    
    def deploy(
        self,
        quantize: bool = True,
        export_onnx: bool = True,
        export_torchscript: bool = True,
        output_dir: str = "models/deployed"
    ) -> Dict:
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "quantization": {},
            "onnx": {},
            "torchscript": {},
            "inference_service": None
        }
        
        deployed_model = self.model
        
        if quantize:
            logger.info("Quantizing model...")
            
            if self.config.quantization == "dynamic":
                deployed_model = self.quantizer.quantize_dynamic()
            elif self.config.quantization == "fp16":
                deployed_model = self.quantizer.quantize_to_fp16()
            
            original_size = self.quantizer.get_model_size(self.model)
            quantized_size = self.quantizer.get_model_size(deployed_model)
            
            results["quantization"] = {
                "method": self.config.quantization,
                "original_size_mb": original_size["total_size_mb"],
                "quantized_size_mb": quantized_size["total_size_mb"],
                "compression_ratio": original_size["total_size_mb"] / max(quantized_size["total_size_mb"], 0.001)
            }
        
        if export_onnx:
            logger.info("Exporting to ONNX...")
            exporter = ONNXExporter(deployed_model, self.config)
            onnx_path = os.path.join(output_dir, "defense_agent.onnx")
            
            export_result = exporter.export(
                onnx_path,
                input_shape=(1, 13),
                opset_version=14,
                dynamic_batch=True
            )
            
            verify_result = exporter.verify(onnx_path, torch.randn(1, 13))
            
            results["onnx"] = {
                "export": export_result,
                "verification": verify_result
            }
        
        if export_torchscript:
            logger.info("Exporting to TorchScript...")
            exporter = TorchScriptExporter(deployed_model)
            ts_path = os.path.join(output_dir, "defense_agent.pt")
            
            ts_result = exporter.export_trace(ts_path, torch.randn(1, 13))
            results["torchscript"] = ts_result
        
        self.inference_service = AsyncInferenceService(
            deployed_model,
            self.config,
            self.device
        )
        
        results["inference_service"] = "initialized"
        
        self.deployment_history.append(results)
        
        return results
    
    def start_service(self):
        if self.inference_service:
            self.inference_service.start()
    
    def stop_service(self):
        if self.inference_service:
            self.inference_service.stop()
    
    async def infer(self, state: np.ndarray) -> Dict:
        if self.inference_service:
            return await self.inference_service.infer(state)
        return {"error": "service not started"}
    
    def infer_sync(self, state: np.ndarray) -> Dict:
        if self.inference_service:
            return self.inference_service.infer_sync(state)
        return {"error": "service not started"}
    
    def benchmark(
        self,
        n_requests: int = 1000,
        batch_sizes: List[int] = [1, 10, 100, 1000]
    ) -> Dict:
        results = {}
        
        for batch_size in batch_sizes:
            latencies = []
            
            for _ in range(n_requests):
                states = [np.random.randn(13).astype(np.float32) for _ in range(batch_size)]
                
                start_time = time.time()
                
                if batch_size == 1:
                    result = self.infer_sync(states[0])
                    latency = result.get("latency_ms", 0)
                else:
                    result = self.inference_service.batch_infer(states)
                    latency = result.get("latency_ms", 0)
                
                latencies.append(latency)
            
            latencies = np.array(latencies)
            
            results[f"batch_{batch_size}"] = {
                "mean_latency_ms": float(np.mean(latencies)),
                "std_latency_ms": float(np.std(latencies)),
                "p50_latency_ms": float(np.percentile(latencies, 50)),
                "p95_latency_ms": float(np.percentile(latencies, 95)),
                "p99_latency_ms": float(np.percentile(latencies, 99)),
                "max_latency_ms": float(np.max(latencies)),
                "throughput_qps": float(batch_size * n_requests / (sum(latencies) / 1000))
            }
        
        return results
    
    def get_status(self) -> Dict:
        return {
            "config": {
                "quantization": self.config.quantization,
                "precision": self.config.precision,
                "max_latency_ms": self.config.max_latency_ms
            },
            "service_running": self.inference_service is not None and self.inference_service.running,
            "service_stats": self.inference_service.get_stats() if self.inference_service else None,
            "deployment_history_count": len(self.deployment_history)
        }
