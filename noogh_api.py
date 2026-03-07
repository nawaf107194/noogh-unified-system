import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from gateway.app.core.agent_kernel import AgentKernel, KernelConfig, AuthContext
import uvicorn
import logging

# إعداد الـ logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("noogh_api")

app = FastAPI(title="NOOGH API for Integromat")

# إعداد التهيئة
config = KernelConfig(
    max_iterations=5,
    enable_learning=False,
    enable_dream_mode=False
)

# تهيئة النواة (Kernel) كمتغير عالمي
kernel: AgentKernel | None = None

# إصلاح AuthContext: إضافة الـ token المطلوب
# سنستخدم "NOOGH_MASTER_TOKEN" كقيمة افتراضية للربط
try:
    auth = AuthContext(
        user_id="make_integration",
        token="NOOGH_MASTER_TOKEN",  # هذا هو البارامتر الذي كان ناقصاً
        scopes=["*"]
    )
except TypeError:
    # في حال كان ترتيب البارامترات مختلفاً في ملفك
    auth = AuthContext("make_integration", "NOOGH_MASTER_TOKEN", ["*"])


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize AgentKernel once on startup."""
    global kernel
    try:
        kernel = AgentKernel(config=config)
        logger.info("✅ NOOGH Kernel initialized and ready for Integromat")
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"❌ Failed to initialize Kernel: {e}")
        kernel = None


class QueryRequest(BaseModel):
    task: str


@app.post("/process")
async def process_task(request: QueryRequest):
    """Proxy endpoint: يمرر الطلب مباشرة إلى AgentKernel.process_task."""
    if kernel is None:
        raise HTTPException(status_code=503, detail="Kernel not initialized")

    try:
        logger.info(f"📥 Received task: {request.task}")

        # AgentKernel يوفر واجهة async باسم process_task ترجع dict جاهز للإرسال.
        result = await kernel.process_task(request.task, auth=auth)
        # لا نعيد تغليف النتيجة هنا، فقط نمررها كما هي للحفاظ على مرونة الـ Kernel.
        return result
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"❌ Error during processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    uvicorn.run(app, host="0.0.0.0", port=8000)
