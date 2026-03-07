import torch
import logging
import asyncio
import os
from dotenv import load_dotenv

# Bootstrapping for Verification Script
from gateway.app.security.secrets_manager import SecretsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reality_check")

async def verify_environment():
    logger.info("--- REALITY CHECK: ENVIRONMENT ---")
    
    # Bootstrap Secrets
    load_dotenv()
    SecretsManager.load()
    secrets = SecretsManager.get_all()
    data_dir = secrets.get("NOOGH_DATA_DIR", "./data")
    
    logger.info(f"Data Dir: {data_dir}")
    
    # 1. GPU Check
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "N/A"
    logger.info(f"CUDA Available: {cuda_available}")
    logger.info(f"Device Name: {device_name}")
    
    # 2. Hugging Face Connectivity
    # Import here to avoid early failures if imports are broken
    from gateway.app.ml.hf_data_manager import HFDataManager
    from gateway.app.ml.distillation import DistillationService

    logger.info("--- REALITY CHECK: HUB CONNECTIVITY ---")
    manager = HFDataManager(data_dir=data_dir)
    try:
        # Search for a known dataset - using wikitext as requested in objective
        results = manager.search_datasets("wikitext", limit=1)
        logger.info(f"Hub Search Success: {len(results) > 0}")
        if results:
            logger.info(f"First result: {results[0]['id']}")
            # Attempt to load a small slice
            # wikitext usually requires config name, let's try 'wikitext-2-raw-v1' or just rely on search
            ds_id = results[0]['id']
            config_name = "wikitext-2-raw-v1" if "wikitext" in ds_id else None
            
            ds = manager.load_dataset(ds_id, config_name=config_name, split="train", streaming=True)
            sample = next(iter(ds))
            logger.info(f"Dataset Loading Success: {len(sample.get('text', '')) > 0}")
    except Exception as e:
        logger.error(f"Hub Connectivity Failed: {e}")

    # 3. Distillation (Non-Simulated)
    logger.info("--- REALITY CHECK: DISTILLATION PIPELINE ---")
    distiller = DistillationService(secrets=secrets, data_dir=data_dir)
    # This will now return [] if teacher fails, proving reality
    data = distiller.generate_synthetic_data("Boolean Logic", num_examples=2)
    logger.info(f"Teacher Generation Count: {len(data)}")
    if not data:
        logger.warning("Teacher Generation Failed (Reality: Cloud Provider or API Key missing/failed or httpx missing)")

if __name__ == "__main__":
    asyncio.run(verify_environment())
