"""
Training API Routes
Expose intelligent training capabilities via REST API
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from gateway.app.core.auth import AuthContext, require_admin
from gateway.app.ml.intelligent_training import TrainingConfig, get_training_engine

router = APIRouter(prefix="/training", tags=["training"])


class TrainingRequest(BaseModel):
    """Training request model"""

    model_name: str = "distilgpt2"
    dataset_name: str = "wikitext"
    output_dir: str = "./models/custom-model"
    num_epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 2e-5
    use_gpu: bool = True
    auto_optimize: bool = True


class TrainingStatusResponse(BaseModel):
    """Training status response"""

    status: str
    message: str
    training_id: Optional[str] = None


# Background training jobs
active_trainings: dict = {}


@router.post("/start", response_model=TrainingStatusResponse)
async def start_training(
    request: TrainingRequest, background_tasks: BackgroundTasks, auth: AuthContext = Depends(require_admin)
):
    """
    Start intelligent model training.

    Features:
    - Hardware-aware optimization
    - Auto-tuning hyperparameters
    - Parallel data preprocessing
    - Real-time monitoring
    """
    import uuid

    training_id = str(uuid.uuid4())[:8]

    # Create config
    config = TrainingConfig(
        model_name=request.model_name,
        dataset_name=request.dataset_name,
        output_dir=request.output_dir,
        num_epochs=request.num_epochs,
        batch_size=request.batch_size,
        learning_rate=request.learning_rate,
        use_gpu=request.use_gpu,
        auto_optimize=request.auto_optimize,
    )

    # Start training in background
    async def train_task():
        try:
            active_trainings[training_id] = {"status": "running", "started": datetime.now()}

            engine = get_training_engine()
            result = await engine.train_model(config)

            active_trainings[training_id] = {
                "status": "completed",
                "result": result,
                "started": active_trainings[training_id]["started"],
                "completed": datetime.now(),
            }
        except Exception as e:
            active_trainings[training_id] = {
                "status": "failed",
                "error": str(e),
                "started": active_trainings[training_id]["started"],
                "completed": datetime.now(),
            }

    background_tasks.add_task(train_task)

    return TrainingStatusResponse(
        status="started", message="Training started with intelligent optimization", training_id=training_id
    )


@router.get("/status/{training_id}")
async def get_training_status(training_id: str, auth: AuthContext = Depends(require_admin)):
    """Get status of training job"""
    if training_id not in active_trainings:
        raise HTTPException(status_code=404, detail="Training not found")

    training = active_trainings[training_id]

    response = {"training_id": training_id, "status": training["status"], "started": str(training.get("started"))}

    if training["status"] == "completed":
        result = training["result"]
        response["completed"] = str(training.get("completed"))
        response["training_time"] = result.training_time
        response["metrics"] = result.metrics
        response["model_path"] = result.model_path
        response["improvements"] = result.improvements

    elif training["status"] == "failed":
        response["error"] = training.get("error")
        response["completed"] = str(training.get("completed"))

    return response


@router.get("/history")
async def get_training_history(auth: AuthContext = Depends(require_admin)):
    """Get training history"""
    engine = get_training_engine()

    history = []
    for result in engine.training_history:
        history.append(
            {
                "model_path": result.model_path,
                "metrics": result.metrics,
                "training_time": result.training_time,
                "improvements": result.improvements,
                "timestamp": result.timestamp,
            }
        )

    return {"total_trainings": len(history), "history": history}


@router.get("/hardware-capability")
async def get_hardware_capability(auth: AuthContext = Depends(require_admin)):
    """
    Get hardware capability for training.

    Shows:
    - GPU availability
    - Optimal batch size
    - Memory constraints
    """
    from neural_engine.autonomic_system.hardware_awareness import get_hardware_consciousness

    hw = get_hardware_consciousness()
    state = hw.full_introspection()

    capability = {
        "cpu_cores": state["cpu"]["physical_cores"],
        "gpu_available": state["gpu"]["available"],
        "recommended_device": "cuda" if state["gpu"]["available"] else "cpu",
    }

    if state["gpu"]["available"]:
        gpu = state["gpu"]["gpus"][0]
        vram_gb = gpu["memory_total_mb"] / 1024
        available_gb = vram_gb - (gpu["memory_used_mb"] / 1024)

        # Estimate batch size
        optimal_batch = int(available_gb * 2)
        optimal_batch = min(optimal_batch, 32)
        optimal_batch = max(optimal_batch, 2)

        capability.update(
            {
                "gpu_name": gpu["name"],
                "vram_total_gb": round(vram_gb, 1),
                "vram_available_gb": round(available_gb, 1),
                "recommended_batch_size": optimal_batch,
                "fp16_recommended": vram_gb < 12,
            }
        )

    return capability


@router.post("/quick-finetune")
async def quick_finetune(
    model_name: str = "distilgpt2",
    dataset_name: str = "wikitext",
    background_tasks: BackgroundTasks = None,
    auth: AuthContext = Depends(require_admin),
):
    """
    Quick fine-tune with smart defaults.

    Uses NOOGH intelligence to:
    - Detect best hardware setup
    - Auto-optimize all parameters
    - Train efficiently
    """
    request = TrainingRequest(
        model_name=model_name,
        dataset_name=dataset_name,
        output_dir=f"./models/{model_name.replace('/', '-')}-finetuned",
        num_epochs=1,  # Quick!
        batch_size=8,
        use_gpu=True,
        auto_optimize=True,  # Let NOOGH optimize!
    )

    return await start_training(request, background_tasks, auth)
