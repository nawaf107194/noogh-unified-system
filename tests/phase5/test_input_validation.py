"""
Model Input Validation Tests

Tests for neural model input validation:
- Input tensor shape validation
- Token ID range validation
- Attention mask validation
- Sequence length limits
- Type checking and sanitization

OWASP References:
- CWE-20: Improper Input Validation
- CWE-129: Improper Validation of Array Index
"""
import pytest
import torch
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


# =============================================================================
# MOCK CLASSES
# =============================================================================

@dataclass
class CognitiveConfig:
    """Configuration for the Cognitive Core model."""
    vocab_size: int = 50257
    hidden_size: int = 1024
    num_layers: int = 12
    num_attention_heads: int = 16
    intermediate_size: int = 4096
    max_position_embeddings: int = 2048
    dropout: float = 0.1
    attention_dropout: float = 0.1
    layer_norm_eps: float = 1e-6


@dataclass
class ValidationResult:
    """Result of input validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class MockInputValidator:
    """Validates inputs to neural models."""
    
    def __init__(self, config: CognitiveConfig):
        self.config = config
        self.validation_count = 0
        self.rejection_count = 0
    
    def validate_input_ids(self, input_ids: torch.Tensor) -> ValidationResult:
        """Validate input token IDs."""
        self.validation_count += 1
        errors = []
        warnings = []
        
        # Check type
        if not isinstance(input_ids, torch.Tensor):
            errors.append(f"Expected torch.Tensor, got {type(input_ids)}")
            self.rejection_count += 1
            return ValidationResult(valid=False, errors=errors)
        
        # Check dtype
        if input_ids.dtype not in (torch.long, torch.int32, torch.int64):
            errors.append(f"Expected integer dtype, got {input_ids.dtype}")
        
        # Check dimensions
        if input_ids.dim() not in (1, 2):
            errors.append(f"Expected 1D or 2D tensor, got {input_ids.dim()}D")
        
        # Check sequence length
        seq_len = input_ids.shape[-1] if input_ids.dim() > 0 else 0
        if seq_len > self.config.max_position_embeddings:
            errors.append(
                f"Sequence length {seq_len} exceeds max {self.config.max_position_embeddings}"
            )
        
        if seq_len == 0:
            errors.append("Empty input sequence")
        
        # Check token range
        if input_ids.numel() > 0:
            min_id = input_ids.min().item()
            max_id = input_ids.max().item()
            
            if min_id < 0:
                errors.append(f"Negative token ID found: {min_id}")
            
            if max_id >= self.config.vocab_size:
                errors.append(
                    f"Token ID {max_id} exceeds vocab size {self.config.vocab_size}"
                )
        
        if errors:
            self.rejection_count += 1
        
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    def validate_attention_mask(
        self, 
        attention_mask: Optional[torch.Tensor],
        input_ids: torch.Tensor
    ) -> ValidationResult:
        """Validate attention mask."""
        self.validation_count += 1
        errors = []
        warnings = []
        
        if attention_mask is None:
            # None is valid - will use default causal mask
            return ValidationResult(valid=True, warnings=["No attention mask provided"])
        
        if not isinstance(attention_mask, torch.Tensor):
            errors.append(f"Expected torch.Tensor, got {type(attention_mask)}")
            self.rejection_count += 1
            return ValidationResult(valid=False, errors=errors)
        
        # Check shape matches input_ids
        if attention_mask.shape != input_ids.shape:
            errors.append(
                f"Attention mask shape {attention_mask.shape} != input shape {input_ids.shape}"
            )
        
        # Check values are 0 or 1
        unique_values = attention_mask.unique()
        valid_values = torch.tensor([0, 1], dtype=attention_mask.dtype, device=attention_mask.device)
        if not all(v in valid_values for v in unique_values):
            warnings.append(f"Attention mask contains non-binary values: {unique_values.tolist()}")
        
        if errors:
            self.rejection_count += 1
        
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    def validate_generation_params(
        self,
        max_length: int,
        temperature: float,
        top_k: int,
        top_p: float
    ) -> ValidationResult:
        """Validate generation parameters."""
        self.validation_count += 1
        errors = []
        warnings = []
        
        # Max length validation
        if max_length <= 0:
            errors.append(f"max_length must be positive, got {max_length}")
        if max_length > self.config.max_position_embeddings:
            errors.append(
                f"max_length {max_length} exceeds max embeddings {self.config.max_position_embeddings}"
            )
        
        # Temperature validation
        if temperature <= 0:
            errors.append(f"temperature must be positive, got {temperature}")
        if temperature > 10.0:
            warnings.append(f"Very high temperature {temperature} may cause unstable output")
        
        # Top-k validation
        if top_k < 0:
            errors.append(f"top_k must be non-negative, got {top_k}")
        if top_k > self.config.vocab_size:
            warnings.append(f"top_k {top_k} >= vocab_size, effectively disabled")
        
        # Top-p validation
        if not 0.0 <= top_p <= 1.0:
            errors.append(f"top_p must be in [0, 1], got {top_p}")
        
        if errors:
            self.rejection_count += 1
        
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def validator():
    """Create input validator."""
    return MockInputValidator(CognitiveConfig())


@pytest.fixture
def small_vocab_validator():
    """Create validator with small vocabulary."""
    return MockInputValidator(CognitiveConfig(vocab_size=1000, max_position_embeddings=512))


# =============================================================================
# INPUT ID VALIDATION TESTS
# =============================================================================

class TestInputIdValidation:
    """Test input ID validation."""
    
    def test_valid_input_ids(self, validator):
        """Test valid input IDs pass validation."""
        input_ids = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
        
        result = validator.validate_input_ids(input_ids)
        
        assert result.valid
        assert len(result.errors) == 0
    
    def test_negative_token_rejected(self, validator):
        """Test negative token IDs are rejected."""
        input_ids = torch.tensor([[1, -5, 3]], dtype=torch.long)
        
        result = validator.validate_input_ids(input_ids)
        
        assert not result.valid
        assert any("egative" in e for e in result.errors)
    
    def test_out_of_vocab_rejected(self, small_vocab_validator):
        """Test out-of-vocabulary tokens are rejected."""
        input_ids = torch.tensor([[1, 2, 99999]], dtype=torch.long)
        
        result = small_vocab_validator.validate_input_ids(input_ids)
        
        assert not result.valid
        assert any("vocab" in e.lower() for e in result.errors)
    
    def test_too_long_sequence_rejected(self, small_vocab_validator):
        """Test sequences exceeding max length are rejected."""
        input_ids = torch.zeros((1, 1000), dtype=torch.long)  # 1000 > 512
        
        result = small_vocab_validator.validate_input_ids(input_ids)
        
        assert not result.valid
        assert any("exceeds" in e.lower() for e in result.errors)
    
    def test_empty_input_rejected(self, validator):
        """Test empty input is rejected."""
        input_ids = torch.tensor([], dtype=torch.long)
        
        result = validator.validate_input_ids(input_ids)
        
        assert not result.valid
    
    def test_wrong_dtype_rejected(self, validator):
        """Test wrong dtype is rejected."""
        input_ids = torch.tensor([[1.0, 2.0, 3.0]])  # Float instead of int
        
        result = validator.validate_input_ids(input_ids)
        
        assert not result.valid
    
    def test_non_tensor_rejected(self, validator):
        """Test non-tensor input is rejected."""
        input_ids = [1, 2, 3]  # List instead of tensor
        
        result = validator.validate_input_ids(input_ids)
        
        assert not result.valid


# =============================================================================
# ATTENTION MASK VALIDATION TESTS
# =============================================================================

class TestAttentionMaskValidation:
    """Test attention mask validation."""
    
    def test_valid_attention_mask(self, validator):
        """Test valid attention mask passes."""
        input_ids = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
        attention_mask = torch.tensor([[1, 1, 1, 1, 0]], dtype=torch.long)
        
        result = validator.validate_attention_mask(attention_mask, input_ids)
        
        assert result.valid
    
    def test_none_mask_allowed(self, validator):
        """Test None attention mask is allowed."""
        input_ids = torch.tensor([[1, 2, 3]], dtype=torch.long)
        
        result = validator.validate_attention_mask(None, input_ids)
        
        assert result.valid
    
    def test_shape_mismatch_rejected(self, validator):
        """Test shape mismatch is rejected."""
        input_ids = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
        attention_mask = torch.tensor([[1, 1, 1]], dtype=torch.long)  # Wrong shape
        
        result = validator.validate_attention_mask(attention_mask, input_ids)
        
        assert not result.valid


# =============================================================================
# GENERATION PARAMETER VALIDATION TESTS
# =============================================================================

class TestGenerationParamValidation:
    """Test generation parameter validation."""
    
    def test_valid_params(self, validator):
        """Test valid generation parameters pass."""
        result = validator.validate_generation_params(
            max_length=100,
            temperature=1.0,
            top_k=50,
            top_p=0.9
        )
        
        assert result.valid
    
    def test_negative_max_length_rejected(self, validator):
        """Test negative max_length is rejected."""
        result = validator.validate_generation_params(
            max_length=-10,
            temperature=1.0,
            top_k=50,
            top_p=0.9
        )
        
        assert not result.valid
    
    def test_zero_temperature_rejected(self, validator):
        """Test zero temperature is rejected."""
        result = validator.validate_generation_params(
            max_length=100,
            temperature=0.0,
            top_k=50,
            top_p=0.9
        )
        
        assert not result.valid
    
    def test_invalid_top_p_rejected(self, validator):
        """Test invalid top_p is rejected."""
        result = validator.validate_generation_params(
            max_length=100,
            temperature=1.0,
            top_k=50,
            top_p=1.5  # > 1.0
        )
        
        assert not result.valid


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestInputValidationAuditSummary:
    """Generate input validation audit summary."""
    
    def test_generate_audit_summary(self, validator):
        """Run input validation tests and generate summary."""
        results = {
            "valid_accepted": 0,
            "invalid_rejected": 0,
            "type_errors_caught": 0,
            "range_errors_caught": 0,
        }
        
        # Test valid inputs
        valid_ids = torch.tensor([[1, 2, 3]], dtype=torch.long)
        if validator.validate_input_ids(valid_ids).valid:
            results["valid_accepted"] += 1
        
        # Test out-of-range
        bad_ids = torch.tensor([[99999]], dtype=torch.long)
        if not validator.validate_input_ids(bad_ids).valid:
            results["range_errors_caught"] += 1
            results["invalid_rejected"] += 1
        
        # Test negative
        negative_ids = torch.tensor([[-1, 2]], dtype=torch.long)
        if not validator.validate_input_ids(negative_ids).valid:
            results["range_errors_caught"] += 1
            results["invalid_rejected"] += 1
        
        # Test type error
        if not validator.validate_input_ids([1, 2, 3]).valid:
            results["type_errors_caught"] += 1
            results["invalid_rejected"] += 1
        
        print(f"\n{'='*60}")
        print("INPUT VALIDATION AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Valid Inputs Accepted: {results['valid_accepted']}")
        print(f"Invalid Inputs Rejected: {results['invalid_rejected']}")
        print(f"Type Errors Caught: {results['type_errors_caught']}")
        print(f"Range Errors Caught: {results['range_errors_caught']}")
        print(f"Total Validations: {validator.validation_count}")
        print(f"Total Rejections: {validator.rejection_count}")
        print(f"{'='*60}\n")
        
        assert results["invalid_rejected"] >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
