"""
System Tools for ALLaM
Provides system status, GPU info, and Docker container information.
"""

import logging
import os
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_system_status() -> Dict[str, Any]:
    """
    Get system status including CPU, RAM, and Disk usage.
    
    Returns:
        Dict with system metrics
    """
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        
        # Memory
        memory = psutil.virtual_memory()
        ram_total = memory.total / (1024**3)  # GB
        ram_used = memory.used / (1024**3)
        ram_percent = memory.percent
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024**3)
        disk_used = disk.used / (1024**3)
        disk_percent = disk.percent
        
        return {
            "status": "operational",
            "cpu": {
                "usage_percent": cpu_percent,
                "cores": cpu_count
            },
            "memory": {
                "total_gb": round(ram_total, 2),
                "used_gb": round(ram_used, 2),
                "percent": ram_percent
            },
            "disk": {
                "total_gb": round(disk_total, 2),
                "used_gb": round(disk_used, 2),
                "percent": disk_percent
            },
            "summary_ar": f"النظام يعمل بكفاءة. المعالج: {cpu_percent}%، الذاكرة: {ram_percent}%، القرص: {disk_percent}%"
        }
    except ImportError:
        return {
            "status": "limited",
            "error": "psutil not installed",
            "summary_ar": "لا يمكن قراءة حالة النظام - psutil غير مثبت"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "summary_ar": f"حدث خطأ: {str(e)}"
        }


def get_gpu_status() -> Dict[str, Any]:
    """
    Get GPU status including VRAM and temperature.
    
    Returns:
        Dict with GPU metrics
    """
    try:
        # Try nvidia-smi
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            gpus = []
            
            for i, line in enumerate(lines):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    gpu_info = {
                        "id": i,
                        "name": parts[0],
                        "memory_total_mb": int(parts[1]),
                        "memory_used_mb": int(parts[2]),
                        "memory_free_mb": int(parts[3]),
                        "temperature_c": int(parts[4]) if parts[4] != '[N/A]' else None,
                        "utilization_percent": int(parts[5]) if parts[5] != '[N/A]' else None
                    }
                    gpus.append(gpu_info)
            
            total_free = sum(g["memory_free_mb"] for g in gpus)
            
            return {
                "status": "available",
                "gpus": gpus,
                "count": len(gpus),
                "total_free_mb": total_free,
                "summary_ar": f"GPU متاح: {gpus[0]['name']}، الذاكرة المتاحة: {total_free} MB"
            }
        else:
            return {
                "status": "unavailable",
                "error": "nvidia-smi failed",
                "summary_ar": "GPU غير متاح أو لا يمكن قراءته"
            }
            
    except FileNotFoundError:
        return {
            "status": "no_nvidia",
            "error": "nvidia-smi not found",
            "summary_ar": "لا يوجد GPU من NVIDIA"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "summary_ar": f"خطأ في قراءة GPU: {str(e)}"
        }


def get_docker_status() -> Dict[str, Any]:
    """
    Get Docker container status.
    
    Returns:
        Dict with container information
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Image}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            containers = []
            
            for line in lines:
                if line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        containers.append({
                            "name": parts[0],
                            "status": parts[1],
                            "image": parts[2]
                        })
            
            running = len([c for c in containers if "Up" in c["status"]])
            
            return {
                "status": "available",
                "containers": containers,
                "running": running,
                "total": len(containers),
                "summary_ar": f"Docker يعمل: {running} حاوية نشطة من {len(containers)}"
            }
        else:
            return {
                "status": "error",
                "error": result.stderr,
                "summary_ar": "لا يمكن قراءة حالة Docker"
            }
            
    except FileNotFoundError:
        return {
            "status": "not_installed",
            "error": "docker not found",
            "summary_ar": "Docker غير مثبت"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "summary_ar": f"خطأ: {str(e)}"
        }


def get_current_time() -> Dict[str, Any]:
    """
    Get current date and time.
    
    Returns:
        Dict with current time info
    """
    from datetime import datetime
    import locale
    
    now = datetime.now()
    
    # Arabic day names
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    months_ar = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", 
                 "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    
    day_ar = days_ar[now.weekday()]
    month_ar = months_ar[now.month - 1]
    
    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_name": day_ar,
        "summary_ar": f"اليوم {day_ar}، {now.day} {month_ar} {now.year}، الساعة {now.strftime('%H:%M')}"
    }


def list_processes() -> Dict[str, Any]:
    """
    List running processes with their resource usage.
    
    Returns:
        Dict with process list
    """
    try:
        import psutil
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0 or pinfo['memory_percent'] > 0.1:
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "user": pinfo['username'] or "N/A",
                        "cpu": round(pinfo['cpu_percent'], 1),
                        "memory": round(pinfo['memory_percent'], 1)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU and take top 15
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        top_processes = processes[:15]
        
        return {
            "success": True,
            "count": len(top_processes),
            "processes": top_processes,
            "summary_ar": f"عدد العمليات النشطة: {len(top_processes)}. أعلى عملية CPU: {top_processes[0]['name'] if top_processes else 'لا يوجد'}"
        }
    except ImportError:
        return {"success": False, "error": "psutil غير مثبت", "summary_ar": "لا يمكن قراءة العمليات - psutil غير مثبت"}
    except Exception as e:
        return {"success": False, "error": str(e), "summary_ar": f"خطأ في قراءة العمليات: {str(e)}"}


def read_system_file(path: str = "", lines: int = 0, **kwargs) -> Dict[str, Any]:
    """
    Read any system file.
    
    Args:
        path: Path to the file to read
        lines: Optional max lines to read (0 = all)
        **kwargs: Ignore extra arguments
        
    Returns:
        Dict with file content
    """
    if not path:
        return {"success": False, "error": "يجب تحديد المسار", "summary_ar": "لم يتم تحديد مسار الملف"}
    
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            if lines > 0:
                content = ''.join(f.readlines()[:lines])
            else:
                content = f.read(10000)  # Max 10KB
        
        line_count = content.count('\n') + 1
        
        return {
            "success": True,
            "path": path,
            "content": content,
            "lines": line_count,
            "summary_ar": f"تم قراءة {path}: {line_count} سطر"
        }
    except FileNotFoundError:
        return {"success": False, "error": f"الملف غير موجود: {path}", "summary_ar": f"الملف غير موجود: {path}"}
    except PermissionError:
        return {"success": False, "error": f"لا توجد صلاحية للقراءة: {path}", "summary_ar": f"لا توجد صلاحية للقراءة: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e), "summary_ar": f"خطأ في قراءة الملف: {str(e)}"}


def write_file(path: str = "", content: str = "", **kwargs) -> Dict[str, Any]:
    """
    Write content to a file.
    
    Args:
        path: Path to the file to write
        content: Content to write to the file
        **kwargs: Ignore extra arguments
        
    Returns:
        Dict with write result
    """
    if not path:
        return {"success": False, "error": "يجب تحديد المسار", "summary_ar": "لم يتم تحديد مسار الملف"}
    
    if not content:
        return {"success": False, "error": "يجب تحديد المحتوى", "summary_ar": "لم يتم تحديد المحتوى"}
    
    # Security: block writing to sensitive system paths
    blocked_paths = ["/etc/", "/boot/", "/sys/", "/proc/", "/dev/", "/root/"]
    for blocked in blocked_paths:
        if path.startswith(blocked):
            return {
                "success": False, 
                "error": f"لا يمكن الكتابة في: {blocked}", 
                "summary_ar": f"مسار محظور: {blocked}"
            }
    
    try:
        # Create parent directories if needed
        import os
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "path": path,
            "bytes_written": len(content),
            "summary_ar": f"تم كتابة {len(content)} حرف إلى {path}"
        }
    except PermissionError:
        return {"success": False, "error": f"لا توجد صلاحية للكتابة: {path}", "summary_ar": f"لا توجد صلاحية للكتابة"}
    except Exception as e:
        return {"success": False, "error": str(e), "summary_ar": f"خطأ في كتابة الملف: {str(e)}"}


def exec_python(code: str = "") -> Dict[str, Any]:
    """
    Execute Python code safely using CodeExecutor sandbox.
    
    Args:
        code: Python code to execute
        
    Returns:
        Dict with execution result
    """
    if not code or len(code.strip()) == 0:
        return {"success": False, "error": "يجب تحديد الكود", "summary_ar": "لم يتم تحديد كود Python"}
    
    try:
        # Use secure CodeExecutor with process isolation
        from neural_engine.code_executor import CodeExecutor
        executor = CodeExecutor(timeout=5)
        result = executor.execute(code)
        
        # Check for errors in result
        is_success = not result.startswith("Error") and not result.startswith("Runtime Error")
        
        return {
            "success": is_success,
            "output": result.strip() if result else "تم التنفيذ بدون مخرجات",
            "summary_ar": f"{'✅ نجاح' if is_success else '❌ فشل'}: {result.strip()[:100]}" if result else "تم التنفيذ بدون مخرجات"
        }
    except Exception as e:
        logger.error(f"CodeExecutor failed: {e}")
        return {"success": False, "error": str(e), "summary_ar": f"خطأ في التنفيذ: {str(e)}"}


def system_shell(command: str = "", **kwargs) -> Dict[str, Any]:
    """
    Execute a shell command.
    
    Args:
        command: Shell command to execute
        **kwargs: Ignored extra arguments from model hallucinations
        
    Returns:
        Dict with command output
    """
    if not command:
        return {"success": False, "error": "يجب تحديد الأمر", "summary_ar": "لم يتم تحديد الأمر"}
    
    # Safety: block dangerous commands
    dangerous = ["rm -rf", "mkfs", "dd if=", "> /dev/", "chmod 777", ":(){ :|:", "fork bomb"]
    command_lower = command.lower()
    for d in dangerous:
        if d in command_lower:
            return {"success": False, "error": f"أمر محظور: {d}", "summary_ar": f"هذا الأمر محظور لأسباب أمنية"}
    
    try:
        import shlex
        # SECURITY FIX (HIGH-05): shell=False prevents command injection
        result = subprocess.run(
            shlex.split(command),
            shell=False,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout[:5000] if result.stdout else ""
        error = result.stderr[:1000] if result.stderr else ""
        
        return {
            "success": result.returncode == 0,
            "output": output,
            "error": error,
            "returncode": result.returncode,
            "summary_ar": f"تم تنفيذ الأمر. الحالة: {'نجاح' if result.returncode == 0 else 'فشل'}"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "انتهى الوقت المسموح", "summary_ar": "انتهى وقت تنفيذ الأمر (30 ثانية)"}
    except Exception as e:
        return {"success": False, "error": str(e), "summary_ar": f"خطأ في تنفيذ الأمر: {str(e)}"}


def web_search(query: str = "") -> Dict[str, Any]:
    """
    Search the web for information using DuckDuckGo.
    
    Args:
        query: Search query
        
    Returns:
        Dict with search results
    """
    if not query:
        return {"success": False, "error": "يجب تحديد الاستعلام", "summary_ar": "لم يتم تحديد استعلام البحث"}
    
    try:
        from neural_engine.specialized_systems.web_searcher import WebSearcher
        searcher = WebSearcher()
        results = searcher.search(query, num_results=5)
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "summary_ar": f"تم العثور على {len(results)} نتائج للبحث عن: {query}"
        }
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return {"success": False, "error": str(e), "summary_ar": f"فشل البحث: {str(e)}"}


async def intelligent_analyze(query: str = "") -> Dict[str, Any]:
    """
    Perform deep intelligent analysis of a system query.
    
    This tool uses the UnifiedIntelligentAgent which combines hardware awareness,
    parallel thinking, and self-governance.
    """
    if not query:
        return {"success": False, "error": "يجب تحديد موضوع التحليل", "summary_ar": "لم يتم تحديد موضوع التحليل"}
    
    try:
        from neural_engine.autonomic_system.unified_agent import get_unified_agent
        agent = get_unified_agent()
        result = await agent.intelligent_analyze(query)
        
        return {
            "success": True,
            "recommendation": result.unified_recommendation,
            "confidence": result.confidence_score,
            "execution_time": result.execution_time,
            "summary_ar": f"تحليل ذكي: {result.unified_recommendation[:200]}"
        }
    except Exception as e:
        logger.error(f"Intelligent analysis failed: {e}")
        return {"success": False, "error": str(e), "summary_ar": f"فشل التحليل: {str(e)}"}


def self_report() -> Dict[str, Any]:
    """
    Generate system self-analysis report.
    
    Returns:
        Dict with self-analysis report
    """
    try:
        from neural_engine.autonomic_system.self_governor import get_self_governing_agent
        agent = get_self_governing_agent()
        report = agent.generate_self_report()
        
        return {
            "success": True,
            "report": report,
            "summary_ar": "تم إنشاء تقرير التحليل الذاتي للنظام"
        }
    except Exception as e:
        logger.error(f"Self report failed: {e}")
        return {"success": False, "error": str(e), "summary_ar": f"فشل التقرير: {str(e)}"}


def get_prompt(name: str = "") -> Dict[str, Any]:
    """
    Get a prompt template from the library.
    
    Args:
        name: Prompt template name
        
    Returns:
        Dict with prompt template
    """
    if not name:
        return {"success": False, "error": "يجب تحديد اسم القالب", "summary_ar": "لم يتم تحديد اسم قالب البرومبت"}
    
    try:
        from neural_engine.specialized_systems.library import prompt_library
        prompt = prompt_library.get_prompt(name)
        
        if prompt:
            return {
                "success": True,
                "name": prompt.name,
                "category": prompt.category.value,
                "template": prompt.template,
                "variables": prompt.variables,
                "description": prompt.description,
                "summary_ar": f"قالب {name}: {prompt.description[:100]}"
            }
        else:
            return {"success": False, "error": f"القالب '{name}' غير موجود", "summary_ar": f"لم يتم العثور على قالب: {name}"}
    except Exception as e:
        logger.error(f"Get prompt failed: {e}")
        return {"success": False, "error": str(e), "summary_ar": f"فشل جلب القالب: {str(e)}"}


def search_prompts(keyword: str = "") -> Dict[str, Any]:
    """
    Search prompt library by keyword.
    
    Args:
        keyword: Search keyword
        
    Returns:
        Dict with matching prompts
    """
    if not keyword:
        return {"success": False, "error": "يجب تحديد كلمة البحث", "summary_ar": "لم يتم تحديد كلمة البحث"}
    
    try:
        from neural_engine.specialized_systems.library import prompt_library
        results = prompt_library.search(keyword)
        
        prompts_list = [{"name": p.name, "description": p.description, "category": p.category.value} for p in results]
        
        return {
            "success": True,
            "results": prompts_list,
            "count": len(prompts_list),
            "summary_ar": f"تم العثور على {len(prompts_list)} قالب للبحث عن: {keyword}"
        }
    except Exception as e:
        logger.error(f"Search prompts failed: {e}")
        return {"success": False, "error": str(e), "summary_ar": f"فشل البحث: {str(e)}"}


def list_prompts() -> Dict[str, Any]:
    """
    List all available prompts.
    
    Returns:
        Dict with all prompt names
    """
    try:
        from neural_engine.specialized_systems.library import prompt_library
        stats = prompt_library.get_stats()
        all_names = prompt_library.list_all()
        
        return {
            "success": True,
            "prompts": all_names[:30],  # Limit to 30
            "total": stats["total_prompts"],
            "categories": stats["by_category"],
            "summary_ar": f"المكتبة تحتوي على {stats['total_prompts']} قالب في {len(stats['by_category'])} فئات"
        }
    except Exception as e:
        logger.error(f"List prompts failed: {e}")
        return {"success": False, "error": str(e), "summary_ar": f"فشل القائمة: {str(e)}"}


# Tool registration helper
def register_system_tools(registry=None):
    """NO-OP: Tools are now defined in unified_core.tools.definitions.
    
    This function previously registered tools with the deprecated
    neural_engine.tools.tool_registry. All tools are now managed
    statically via unified_core.tool_registry.
    """
    logger.debug(
        "register_system_tools() is superseded by unified_core.tools.definitions"
    )

