import pytest
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import torch

MODEL_NAME = "Qwen/Qwen-2.5-7B"
LORA_R = 8
LORA_ALPHA = 32
LORA_DROPOUT = 0.1
LORA_TARGETS = ["q_proj", "v_proj"]

def load_model():
    """Load Qwen 2.5 7B with QLoRA."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    logger.info(f"📦 Loading: {MODEL_NAME}")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        padding_side="right",
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 4-bit quantization
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    torch.cuda.empty_cache()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quant_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    # Prepare for training
    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable()

    # Apply LoRA
    logger.info(f"🔧 LoRA: r={LORA_R}, alpha={LORA_ALPHA}")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGETS,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)

    trainable, total = model.get_nb_trainable_parameters()
    logger.info(f"📊 Params: {trainable:,} trainable / {total:,} total ({100*trainable/total:.2f}%)")

    return model, tokenizer

@pytest.fixture
def load_model_fixture():
    return load_model()

def test_load_model(happy_path):
    """Test the happy path of load_model function."""
    model, tokenizer = load_model_fixture()
    assert isinstance(model, AutoModelForCausalLM)
    assert isinstance(tokenizer, AutoTokenizer)

def test_load_model_edge_case_empty_model_name():
    """Test edge case with empty model name."""
    global MODEL_NAME
    original_model_name = MODEL_NAME
    MODEL_NAME = ""
    model, tokenizer = load_model_fixture()
    assert model is None and tokenizer is None
    MODEL_NAME = original_model_name

def test_load_model_edge_case_none_model_name():
    """Test edge case with None model name."""
    global MODEL_NAME
    original_model_name = MODEL_NAME
    MODEL_NAME = None
    model, tokenizer = load_model_fixture()
    assert model is None and tokenizer is None
    MODEL_NAME = original_model_name

def test_load_model_error_case_invalid_model_name():
    """Test error case with invalid model name."""
    global MODEL_NAME
    original_model_name = MODEL_NAME
    MODEL_NAME = "non_existent_model"
    try:
        load_model_fixture()
    except Exception as e:
        assert str(e) == "Model 'non_existent_model' not found"
    finally:
        MODEL_NAME = original_model_name

def test_load_model_async_behavior():
    """Test async behavior of load_model function."""
    pass  # This function is synchronous, no need for async testing here