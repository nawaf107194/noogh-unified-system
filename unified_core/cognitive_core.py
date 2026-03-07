"""
Cognitive Core - Custom Transformer Architecture
The neural backbone for reasoning and generation
"""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

logger = logging.getLogger("unified_core.neural.cognitive_core")


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
    initializer_range: float = 0.02
    use_rotary_embeddings: bool = True
    use_flash_attention: bool = False
    use_memory_efficient: bool = True


class RotaryEmbedding(nn.Module):
    """Rotary Position Embedding (RoPE)."""
    
    def __init__(self, dim: int, max_seq_len: int = 2048, base: int = 10000):
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)
        self.max_seq_len = max_seq_len
        self._cos_cached = None
        self._sin_cached = None
    
    def _compute_cos_sin(self, seq_len: int, device: torch.device):
        if self._cos_cached is not None and seq_len <= self._cos_cached.size(0):
            return
        
        t = torch.arange(seq_len, device=device, dtype=self.inv_freq.dtype)
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self._cos_cached = emb.cos().unsqueeze(0).unsqueeze(0)
        self._sin_cached = emb.sin().unsqueeze(0).unsqueeze(0)
    
    def forward(self, x: Tensor, seq_len: int) -> Tuple[Tensor, Tensor]:
        self._compute_cos_sin(seq_len, x.device)
        return (
            self._cos_cached[:, :, :seq_len, :].to(x.dtype),
            self._sin_cached[:, :, :seq_len, :].to(x.dtype)
        )


def rotate_half(x: Tensor) -> Tensor:
    """Rotate half the hidden dims of the input."""
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q: Tensor, k: Tensor, cos: Tensor, sin: Tensor) -> Tuple[Tensor, Tensor]:
    """Apply rotary position embeddings to query and key."""
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class CognitiveAttention(nn.Module):
    """Multi-Head Attention with optional RoPE and Flash Attention."""
    
    def __init__(self, config: CognitiveConfig):
        super().__init__()
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = config.hidden_size // config.num_attention_heads
        self.use_rotary = config.use_rotary_embeddings
        self.use_flash = config.use_flash_attention
        
        self.q_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=False)
        self.k_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=False)
        self.v_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=False)
        self.o_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=False)
        
        if self.use_rotary:
            self.rotary_emb = RotaryEmbedding(self.head_dim, config.max_position_embeddings)
        
        self.attention_dropout = nn.Dropout(config.attention_dropout)
    
    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Optional[Tensor] = None,
        past_key_value: Optional[Tuple[Tensor, Tensor]] = None,
        use_cache: bool = False
    ) -> Tuple[Tensor, Optional[Tuple[Tensor, Tensor]]]:
        batch_size, seq_len, _ = hidden_states.size()
        
        # Projections
        q = self.q_proj(hidden_states)
        k = self.k_proj(hidden_states)
        v = self.v_proj(hidden_states)
        
        # Reshape to (batch, heads, seq, head_dim)
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Handle KV cache
        kv_seq_len = seq_len
        if past_key_value is not None:
            kv_seq_len += past_key_value[0].size(2)
            k = torch.cat([past_key_value[0], k], dim=2)
            v = torch.cat([past_key_value[1], v], dim=2)
        
        past_key_value = (k, v) if use_cache else None
        
        # Rotary embeddings
        if self.use_rotary:
            cos, sin = self.rotary_emb(q, kv_seq_len)
            q, k = apply_rotary_pos_emb(q, k, cos, sin)
        
        # Attention computation
        if self.use_flash and hasattr(F, 'scaled_dot_product_attention'):
            attn_output = F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=attention_mask,
                dropout_p=self.attention_dropout.p if self.training else 0.0,
                is_causal=attention_mask is None
            )
        else:
            # Standard attention
            scale = 1.0 / math.sqrt(self.head_dim)
            attn_weights = torch.matmul(q, k.transpose(-2, -1)) * scale
            
            if attention_mask is not None:
                attn_weights = attn_weights + attention_mask
            
            attn_weights = F.softmax(attn_weights, dim=-1)
            attn_weights = self.attention_dropout(attn_weights)
            attn_output = torch.matmul(attn_weights, v)
        
        # Reshape and project
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, -1)
        attn_output = self.o_proj(attn_output)
        
        return attn_output, past_key_value


class CognitiveMLP(nn.Module):
    """Feed-Forward Network with SwiGLU activation."""
    
    def __init__(self, config: CognitiveConfig):
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.up_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.down_proj = nn.Linear(config.intermediate_size, config.hidden_size, bias=False)
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(self, x: Tensor) -> Tensor:
        # SwiGLU: gate * silu(up)
        gate = self.gate_proj(x)
        up = self.up_proj(x)
        hidden = F.silu(gate) * up
        return self.dropout(self.down_proj(hidden))


class CognitiveLayer(nn.Module):
    """Single Transformer layer with pre-norm architecture."""
    
    def __init__(self, config: CognitiveConfig):
        super().__init__()
        self.attention = CognitiveAttention(config)
        self.mlp = CognitiveMLP(config)
        self.input_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.post_attention_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
    
    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Optional[Tensor] = None,
        past_key_value: Optional[Tuple[Tensor, Tensor]] = None,
        use_cache: bool = False
    ) -> Tuple[Tensor, Optional[Tuple[Tensor, Tensor]]]:
        # Pre-norm attention
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        attn_output, present_key_value = self.attention(
            hidden_states, attention_mask, past_key_value, use_cache
        )
        hidden_states = residual + attn_output
        
        # Pre-norm MLP
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = residual + self.mlp(hidden_states)
        
        return hidden_states, present_key_value


class CognitiveCore(nn.Module):
    """
    The Cognitive Core - Main Transformer Model
    Custom architecture optimized for reasoning tasks
    """
    
    def __init__(self, config: CognitiveConfig):
        super().__init__()
        self.config = config
        
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.embed_dropout = nn.Dropout(config.dropout)
        
        self.layers = nn.ModuleList([
            CognitiveLayer(config) for _ in range(config.num_layers)
        ])
        
        self.final_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        
        # Tie weights
        self.lm_head.weight = self.embed_tokens.weight
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module: nn.Module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
    
    def _make_causal_mask(self, seq_len: int, device: torch.device) -> Tensor:
        """Create causal attention mask."""
        mask = torch.triu(
            torch.full((seq_len, seq_len), float('-inf'), device=device),
            diagonal=1
        )
        return mask.unsqueeze(0).unsqueeze(0)
    
    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Optional[Tensor] = None,
        past_key_values: Optional[List[Tuple[Tensor, Tensor]]] = None,
        use_cache: bool = False,
        return_hidden_states: bool = False
    ) -> Dict[str, Any]:
        batch_size, seq_len = input_ids.size()
        
        # Embeddings
        hidden_states = self.embed_tokens(input_ids)
        hidden_states = self.embed_dropout(hidden_states)
        
        # Prepare attention mask
        if attention_mask is None:
            attention_mask = self._make_causal_mask(seq_len, input_ids.device)
        
        # Process layers
        all_hidden_states = [] if return_hidden_states else None
        present_key_values = [] if use_cache else None
        
        for i, layer in enumerate(self.layers):
            if return_hidden_states:
                all_hidden_states.append(hidden_states)
            
            past_kv = past_key_values[i] if past_key_values is not None else None
            hidden_states, present_kv = layer(hidden_states, attention_mask, past_kv, use_cache)
            
            if use_cache:
                present_key_values.append(present_kv)
        
        hidden_states = self.final_layernorm(hidden_states)
        
        # Language modeling head
        logits = self.lm_head(hidden_states)
        
        return {
            "logits": logits,
            "hidden_states": all_hidden_states,
            "past_key_values": present_key_values
        }
    
    def generate(
        self,
        input_ids: Tensor,
        max_new_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        do_sample: bool = True,
        stop_token_id: Optional[int] = None
    ) -> Tensor:
        """Generate tokens autoregressively."""
        self.eval()
        generated = input_ids
        past_key_values = None
        
        with torch.no_grad():
            for _ in range(max_new_tokens):
                # Forward pass
                outputs = self.forward(
                    generated[:, -1:] if past_key_values else generated,
                    past_key_values=past_key_values,
                    use_cache=True
                )
                
                logits = outputs["logits"][:, -1, :]
                past_key_values = outputs["past_key_values"]
                
                # Temperature scaling
                if temperature > 0:
                    logits = logits / temperature
                
                # Top-K filtering
                if top_k > 0:
                    indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
                    logits[indices_to_remove] = float('-inf')
                
                # Top-P (nucleus) filtering
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                    logits[indices_to_remove] = float('-inf')
                
                probs = F.softmax(logits, dim=-1)
                
                if do_sample:
                    next_token = torch.multinomial(probs, num_samples=1)
                else:
                    next_token = torch.argmax(probs, dim=-1, keepdim=True)
                
                generated = torch.cat([generated, next_token], dim=1)
                
                if stop_token_id is not None and next_token.item() == stop_token_id:
                    break
        
        return generated
    
    @classmethod
    def from_pretrained(cls, path: str) -> "CognitiveCore":
        """Load model from checkpoint."""
        checkpoint = torch.load(path, map_location="cpu")
        config = CognitiveConfig(**checkpoint.get("config", {}))
        model = cls(config)
        model.load_state_dict(checkpoint["model_state_dict"])
        return model
    
    def save_pretrained(self, path: str):
        """Save model checkpoint."""
        torch.save({
            "config": {
                "vocab_size": self.config.vocab_size,
                "hidden_size": self.config.hidden_size,
                "num_layers": self.config.num_layers,
                "num_attention_heads": self.config.num_attention_heads,
                "intermediate_size": self.config.intermediate_size,
                "max_position_embeddings": self.config.max_position_embeddings,
            },
            "model_state_dict": self.state_dict()
        }, path)
    
    def count_parameters(self) -> int:
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
