"""
LoongArch 架构兼容性检测工具
用于在银河麒麟 + LoongArch 环境下检测系统兼容性
适配：设备检修AI系统
"""

import os
import sys
import platform
import subprocess


def check_architecture():
    """检测 CPU 架构"""
    arch = platform.machine()
    print(f"CPU架构: {arch}")

    if arch == "loongarch64":
        print("  ✓ LoongArch64 架构 - 符合赛题要求")
        return True
    else:
        print(f"  ⚠ 当前架构为 {arch}，非 LoongArch64")
        print("  提示: 开发阶段可在 x86_64 上运行，部署时需适配 LoongArch")
        return False


def check_os():
    """检测操作系统"""
    print(f"操作系统: {platform.platform()}")

    try:
        with open("/etc/os-release", "r") as f:
            content = f.read()
            if "Kylin" in content:
                print("  ✓ 检测到银河麒麟 (Kylin) 操作系统")
                return True
            else:
                print("  ⚠ 未检测到银河麒麟操作系统")
                return False
    except FileNotFoundError:
        print("  ⚠ 无法读取系统信息")
        return False


def check_python():
    """检测 Python 版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 10:
        print("  ✓ Python 版本满足要求 (>=3.10)")
        return True
    else:
        print("  ✗ Python 版本过低，需要 3.10+")
        return False


def check_hardware():
    """检测硬件资源"""
    print("\n硬件资源检测:")

    try:
        cpu_cores = os.cpu_count() or 0
        print(f"  CPU核心数: {cpu_cores} (要求: 四核及以上)")
        if cpu_cores >= 4:
            print("  ✓ CPU 核心数满足要求")
            cpu_ok = True
        else:
            print("  ⚠ CPU 核心数不足")
            cpu_ok = False
    except Exception:
        cpu_ok = False

    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / (1024 * 1024)
                    print(f"  内存: {mem_gb:.1f}GB (要求: 8GB以上)")
                    if mem_gb >= 8:
                        print("  ✓ 内存满足要求")
                        mem_ok = True
                    else:
                        print("  ⚠ 内存不足")
                        mem_ok = False
                    break
            else:
                mem_ok = False
    except Exception:
        mem_ok = False

    return cpu_ok and mem_ok


def check_dependencies():
    """检测关键依赖包"""
    print("\n关键依赖检测:")

    dependencies = {
        "fastapi": "FastAPI 后端框架",
        "uvicorn": "ASGI 服务器",
        "pydantic": "数据验证",
        "openai": "OpenAI 兼容 SDK (支持 LongCat/Ollama)",
        "dotenv": "python-dotenv 环境变量加载",
        "requests": "HTTP 请求库",
    }

    all_ok = True
    for package, desc in dependencies.items():
        # dotenv 导入名是下划线
        import_name = package.replace("-", "_")
        try:
            __import__(import_name)
            print(f"  ✓ {desc} ({package})")
        except ImportError:
            print(f"  ✗ {desc} ({package}) - 未安装")
            all_ok = False

    return all_ok


def check_llm_service():
    """检测 LLM 服务是否可用"""
    print("\nLLM 服务检测:")

    backend = os.environ.get("LLM_BACKEND", "longcat")
    print(f"  配置后端: {backend}")

    if backend == "ollama":
        base_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/v1")
        try:
            import httpx
            resp = httpx.get(f"{base_url.replace('/v1', '')}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                print(f"  ✓ Ollama 服务可达，已加载 {len(models)} 个模型")
                for m in models[:5]:
                    print(f"    - {m.get('name', 'unknown')}")
                return True
            else:
                print("  ⚠ Ollama 服务响应异常")
                return False
        except Exception as e:
            print(f"  ⚠ Ollama 服务不可达: {e}")
            return False
    elif backend == "longcat":
        api_key = os.environ.get("LONGCAT_API_KEY", "")
        if not api_key or api_key == "your_api_key_here":
            print("  ⚠ LONGCAT_API_KEY 未配置")
            return False
        try:
            import httpx
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = httpx.get(
                os.environ.get("LONGCAT_API_URL", "https://api.longcat.chat/openai/v1"),
                headers=headers,
                timeout=5
            )
            if resp.status_code < 500:
                print("  ✓ LongCat API 可达")
                return True
            else:
                print("  ⚠ LongCat API 响应异常")
                return False
        except Exception as e:
            print(f"  ⚠ 网络检测失败: {e}")
            return False
    else:
        print(f"  ⚠ 未知后端类型: {backend}")
        return False


def check_frontend():
    """检测前端构建产物"""
    print("\n前端服务检测:")

    # 检测多个可能的前端产物位置
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist"),
    ]

    for frontend_dist in possible_paths:
        if os.path.isdir(frontend_dist) and os.listdir(frontend_dist):
            print(f"  ✓ Vue 前端构建产物存在: {frontend_dist}")
            return True

    print("  ⚠ Vue 前端未构建，请运行: cd frontend && npm ci && npm run build")
    return False


def run_all_checks():
    """运行所有兼容性检测"""
    print("=" * 50)
    print("  LoongArch 兼容性检测工具")
    print("  设备检修AI系统")
    print("=" * 50)
    print()

    results = {
        "架构检测": check_architecture(),
        "系统检测": check_os(),
        "Python检测": check_python(),
        "硬件检测": check_hardware(),
        "依赖检测": check_dependencies(),
        "LLM服务检测": check_llm_service(),
        "前端检测": check_frontend(),
    }

    print("\n" + "=" * 50)
    print("  检测结果汇总")
    print("=" * 50)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 未通过"
        print(f"  {name}: {status}")

    all_passed = all(results.values())
    print()
    if all_passed:
        print("  🎉 所有检测通过，系统可正常运行")
    else:
        print("  ⚠ 部分检测未通过，请参考上方提示修复")

    return all_passed


if __name__ == "__main__":
    run_all_checks()
