from typing import Any, Dict, List

import httpx


def safe_text(r: httpx.Response) -> str:
    try:
        return r.text[:2000]
    except Exception:
        return "<unreadable>"


async def dispatch_execute(settings, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = []
    all_succeeded = True

    # Get internal token for service authentication
    import os

    internal_token = os.getenv("NOOGH_INTERNAL_TOKEN")
    if not internal_token:
        return {
            "ok": False,
            "executed": False,
            "results": [{"status": "failed", "error": "NOOGH_INTERNAL_TOKEN not configured"}],
        }

    headers = {"X-Internal-Token": internal_token}

    async with httpx.AsyncClient(timeout=20.0) as client:
        for a in actions:
            name = a["action"]
            args = a.get("args", {})

            try:
                if name == "dream.start":
                    r = await client.post(
                        f"{settings.NEURAL_URL}/api/v1/system/dream",
                        json={"minutes": args.get("minutes", 1)},
                        headers=headers,  # Forward token
                    )
                    r.raise_for_status()  # Raises on 4xx/5xx
                    results.append({"action": name, "status": "success", "response": r.json()})

                elif name == "memory.store":
                    r = await client.post(f"{settings.NEURAL_URL}/api/v1/memory/store", json=args, headers=headers)
                    r.raise_for_status()
                    results.append({"action": name, "status": "success", "response": r.json()})

                elif name == "vision.process":
                    r = await client.post(f"{settings.NEURAL_URL}/api/v1/vision/process", json=args, headers=headers)
                    r.raise_for_status()
                    results.append({"action": name, "status": "success", "response": r.json()})

                elif name == "system.health":
                    r = await client.get(f"{settings.NEURAL_URL}/health")
                    r.raise_for_status()
                    results.append({"action": name, "status": "success", "response": r.json()})

                else:
                    all_succeeded = False
                    results.append({"action": name, "status": "failed", "error": "unknown action mapping for execute"})

            except httpx.HTTPStatusError as e:
                all_succeeded = False
                results.append(
                    {
                        "action": name,
                        "status": "failed",
                        "http_code": e.response.status_code,
                        "error": e.response.text[:200],
                    }
                )

            except httpx.RequestError as e:
                all_succeeded = False
                results.append({"action": name, "status": "failed", "error": f"Network error: {str(e)}"})

    return {"ok": all_succeeded, "executed": all_succeeded, "results": results}  # DERIVED, not hardcoded
