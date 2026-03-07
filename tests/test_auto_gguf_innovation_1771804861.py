import pytest
import os
from pathlib import Path
import sys
import subprocess

from noogh_unified_system.src.auto_gguf import convert_to_gguf, GGUF_OUTPUT_DIR

def test_convert_to_gguf_happy_path(tmpdir):
    model_dir = str(tmpdir / "model")
    output_file = str(tmpdir / "output.gguf")
    
    # Mock the existence of llama.cpp
    llama_cpp_dir = Path("/opt/llama.cpp")
    llama_cpp_dir.mkdir(exist_ok=True)
    (llama_cpp_dir / "convert_hf_to_gguf.py").touch()
    (llama_cpp_dir / "build" / "bin" / "llama-quantize").touch()
    
    # Mock the model directory
    Path(model_dir).mkdir(exist_ok=True)
    
    result = convert_to_gguf(model_dir, output_file=output_file)
    
    assert result["success"] is True
    assert os.path.exists(output_file)
    os.remove(output_file)

def test_convert_to_gguf_no_llama_cpp():
    model_dir = str(Path("/some/fake/model"))
    
    result = convert_to_gguf(model_dir)
    
    assert result["success"] is False
    assert "llama.cpp not found" in result["error"]

def test_convert_to_gguf_invalid_model_dir():
    model_dir = None
    
    with pytest.raises(TypeError):
        convert_to_gguf(model_dir)

def test_convert_to_gguf_no_quantize_bin(tmpdir):
    model_dir = str(tmpdir / "model")
    output_file = str(tmpdir / "output.gguf")
    
    # Mock the existence of llama.cpp
    llama_cpp_dir = Path("/opt/llama.cpp")
    llama_cpp_dir.mkdir(exist_ok=True)
    (llama_cpp_dir / "convert_hf_to_gguf.py").touch()
    
    # Mock the model directory
    Path(model_dir).mkdir(exist_ok=True)
    
    result = convert_to_gguf(model_dir, output_file=output_file, quantize="invalid")
    
    assert result["success"] is False
    assert "Quantize binary not found" in result["error"]