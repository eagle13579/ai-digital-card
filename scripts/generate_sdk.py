#!/usr/bin/env python3
"""
AI数字名片 API SDK 生成脚本

基于 openapi.yaml (OpenAPI 3.1) 自动生成 Python + TypeScript SDK。
使用 openapi-generator CLI (需要 Java 17+ 运行环境)。

用法:
    python scripts/generate_sdk.py              # 生成 Python + TypeScript SDK
    python scripts/generate_sdk.py --lang python # 仅生成 Python SDK
    python scripts/generate_sdk.py --lang typescript # 仅生成 TypeScript SDK
    python scripts/generate_sdk.py --validate-only  # 仅校验规范
    python scripts/generate_sdk.py --local          # 使用本地文件（不请求后端）
    python scripts/generate_sdk.py --local --lang python

环境变量:
    OPENAPI_GENERATOR_VERSION: openapi-generator CLI 版本 (默认 7.12.0)
    OPENAPI_GENERATOR_JAR:     自定义 JAR 路径
    API_BASE_URL:              后端实时规范 URL (默认 http://localhost:8201)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import yaml

# ─── 项目路径 ────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENAPI_FILE = os.path.join(PROJECT_ROOT, "openapi.yaml")
PYTHON_SDK_DIR = os.path.join(PROJECT_ROOT, "backend", "app", "sdk")
TYPESCRIPT_SDK_DIR = os.path.join(PROJECT_ROOT, "frontend", "src", "lib", "api-sdk")

# ─── 配置 ─────────────────────────────────────────────────────────────────────
DEFAULT_GENERATOR_VERSION = "7.12.0"
DEFAULT_API_BASE_URL = "http://localhost:8201"

# openapi-generator 生成器的选择
GENERATORS = {
    "python": {
        "generator": "python",
        "output_dir": PYTHON_SDK_DIR,
        "additional_props": [
            "packageName=ai_digital_business_card_sdk",
            "projectName=ai-digital-business-card-sdk",
            "packageVersion=2.0.0",
        ],
    },
    "typescript": {
        "generator": "typescript-fetch",
        "output_dir": TYPESCRIPT_SDK_DIR,
        "additional_props": [
            "npmName=@ai-digital-business-card/sdk",
            "npmVersion=2.0.0",
            "supportsES6=true",
            "modelPropertyNaming=camelCase",
        ],
    },
}


# ─── 工具函数 ─────────────────────────────────────────────────────────────────


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


def error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)


def fatal(msg: str) -> None:
    error(msg)
    sys.exit(1)


def find_openapi_generator() -> str:
    """尝试找到 openapi-generator CLI（优先使用环境变量指定的 JAR）"""
    jar_path = os.environ.get("OPENAPI_GENERATOR_JAR")
    if jar_path and os.path.isfile(jar_path):
        info(f"使用自定义 JAR: {jar_path}")
        return f"java -jar {jar_path}"

    # 检查是否在 PATH 中
    for cmd in ["openapi-generator-cli", "openapi-generator"]:
        if shutil.which(cmd):
            info(f"使用系统命令: {cmd}")
            return cmd

    # 检查本地缓存
    version = os.environ.get("OPENAPI_GENERATOR_VERSION", DEFAULT_GENERATOR_VERSION)
    local_jar = os.path.join(PROJECT_ROOT, f"openapi-generator-cli-{version}.jar")
    if os.path.isfile(local_jar):
        return f"java -jar {local_jar}"

    # 检查 .openapi-generator/ 目录
    cached_jar = os.path.join(
        os.path.expanduser("~"), ".openapi-generator", f"openapi-generator-cli-{version}.jar"
    )
    if os.path.isfile(cached_jar):
        return f"java -jar {cached_jar}"

    # 未找到
    return None


def download_generator_jar(version: str) -> str:
    """下载 openapi-generator CLI JAR 到本地缓存"""
    jar_dir = os.path.join(os.path.expanduser("~"), ".openapi-generator")
    os.makedirs(jar_dir, exist_ok=True)
    jar_path = os.path.join(jar_dir, f"openapi-generator-cli-{version}.jar")

    if os.path.isfile(jar_path):
        info(f"JAR 已缓存: {jar_path}")
        return jar_path

    url = (
        f"https://repo1.maven.org/maven2/org/openapitools/"
        f"openapi-generator-cli/{version}/openapi-generator-cli-{version}.jar"
    )
    info(f"正在下载 openapi-generator CLI v{version}...")
    info(f"  来源: {url}")
    info(f"  目标: {jar_path}")

    try:
        urllib.request.urlretrieve(url, jar_path)
        info("下载完成")
        return jar_path
    except Exception as e:
        fatal(f"下载失败: {e}\n请手动下载并放到 {jar_path}")


def get_openapi_spec(local_only: bool = False) -> str:
    """
    获取 OpenAPI 规范文件路径。
    优先从后端服务获取实时规范，回退到本地文件。
    返回规范文件的路径。
    """
    if local_only:
        info("使用本地文件模式")
        if os.path.isfile(OPENAPI_FILE):
            info(f"  本地规范: {OPENAPI_FILE}")
            return OPENAPI_FILE
        fatal(f"本地 OpenAPI 规范文件不存在: {OPENAPI_FILE}")

    # 尝试从后端获取实时规范
    api_base = os.environ.get("API_BASE_URL", DEFAULT_API_BASE_URL)
    urls_to_try = [
        f"{api_base}/openapi.json",
        f"{api_base}/openapi.yaml",
        f"{api_base}/docs/openapi.json",
    ]

    for url in urls_to_try:
        try:
            info(f"尝试从后端获取规范: {url}")
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                content = resp.read().decode("utf-8")
                # 保存到临时文件
                suffix = ".json" if url.endswith(".json") else ".yaml"
                tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                tmp.write(content.encode("utf-8"))
                tmp.close()
                info(f"  成功获取，保存到临时文件: {tmp.name}")
                return tmp.name
        except Exception as e:
            info(f"  {url} 不可用: {e}")
            continue

    # 回退到本地文件
    info("后端不可用，回退到本地规范文件")
    if os.path.isfile(OPENAPI_FILE):
        info(f"  本地规范: {OPENAPI_FILE}")
        return OPENAPI_FILE

    fatal("无法获取 OpenAPI 规范（后端不可用且本地文件不存在）")


def validate_spec(spec_path: str) -> dict:
    """
    校验 OpenAPI 规范文件的基本完整性。
    返回解析后的规范字典。
    """
    info(f"正在校验 OpenAPI 规范: {spec_path}")

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 尝试解析 JSON 或 YAML
        try:
            spec = json.loads(content)
        except json.JSONDecodeError:
            spec = yaml.safe_load(content)

        if not isinstance(spec, dict):
            fatal("规范文件格式错误：根元素必须是对象")

        # 检查版本
        openapi_version = spec.get("openapi", spec.get("swagger", ""))
        if not openapi_version:
            fatal("规范中缺少 openapi 或 swagger 版本声明")

        info(f"  OpenAPI 版本: {openapi_version}")

        # 检查基本信息
        info(f"  标题: {spec.get('info', {}).get('title', 'N/A')}")
        info(f"  版本: {spec.get('info', {}).get('version', 'N/A')}")

        # 统计端点
        paths = spec.get("paths", {})
        endpoint_count = sum(len(methods) for methods in paths.values() if isinstance(methods, dict))
        info(f"  端点数量: {endpoint_count}")

        # 检查 operationId 唯一性（影响 SDK 方法名）
        operation_ids = []
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method in methods.values():
                if isinstance(method, dict) and "operationId" in method:
                    operation_ids.append(method["operationId"])

        if operation_ids:
            duplicates = {oid for oid in operation_ids if operation_ids.count(oid) > 1}
            if duplicates:
                info(f"  [警告] operationId 有重复: {', '.join(duplicates)}")
            info(f"  operationId 数量: {len(operation_ids)}")

        return spec

    except yaml.YAMLError as e:
        fatal(f"YAML 解析失败: {e}")
    except json.JSONDecodeError as e:
        fatal(f"JSON 解析失败: {e}")
    except Exception as e:
        fatal(f"校验过程出错: {e}")


def ensure_output_dir(directory: str) -> None:
    """确保输出目录存在且为空"""
    if os.path.exists(directory):
        info(f"  清理旧目录: {directory}")
        shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)
    info(f"  创建输出目录: {directory}")


def run_generator(generator_cmd: str, spec_path: str, lang: str, config: dict) -> None:
    """运行 openapi-generator 生成指定语言的 SDK"""
    output_dir = config["output_dir"]

    info(f"\n{'='*60}")
    info(f"生成 {lang.upper()} SDK")
    info(f"  生成器: {config['generator']}")
    info(f"  输出目录: {output_dir}")
    info(f"{'='*60}")

    ensure_output_dir(output_dir)

    # 构建参数
    cmd = [
        generator_cmd,
        "generate",
        "-g", config["generator"],
        "-i", spec_path,
        "-o", output_dir,
        "--skip-validate-spec",  # 避免严格的 spec 校验（已经前置校验过）
    ]

    # 添加附加属性
    for prop in config.get("additional_props", []):
        cmd.extend(["--additional-properties", prop])

    # 执行
    info(f"执行命令: {' '.join(cmd[:4])} ... (参数略)")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            error(f"生成失败 (exit code {result.returncode})")
            # 只打印最后50行错误
            stderr_lines = result.stderr.strip().split("\n")
            for line in stderr_lines[-50:]:
                print(f"  {line}", file=sys.stderr)
            fatal("SDK 生成失败，请检查上面的错误信息")
        info(f"  ✅ {lang} SDK 生成成功: {output_dir}")

        # 打印生成的目录结构概览
        generated_files = []
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), output_dir)
                generated_files.append(rel)

        # 只显示部分文件
        show_count = min(len(generated_files), 20)
        info(f"  生成文件数量: {len(generated_files)} (显示前 {show_count} 个):")
        for f in generated_files[:show_count]:
            print(f"    └── {f}")
        if len(generated_files) > show_count:
            print(f"    ... 还有 {len(generated_files) - show_count} 个文件")

    except subprocess.TimeoutExpired:
        fatal("SDK 生成超时 (120s)")
    except FileNotFoundError:
        fatal("找不到 Java 运行时。请安装 Java 17+ 或使用 --local 模式仅校验规范")


def post_process_python() -> None:
    """对生成的 Python SDK 进行后处理"""
    info("\n后处理 Python SDK...")

    # 创建独立的 pyproject.toml（如果不存在）
    pyproject_path = os.path.join(PYTHON_SDK_DIR, "pyproject.toml")
    if not os.path.isfile(pyproject_path):
        info("  创建 pyproject.toml")
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write("""[build-system]
requires = ["setuptools>=64.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "ai-digital-business-card-sdk"
version = "2.0.0"
description = "AI数字名片 REST API Python SDK"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
""")

    # 创建 README（如果不存在）
    readme_path = os.path.join(PYTHON_SDK_DIR, "README.md")
    if not os.path.isfile(readme_path):
        info("  创建 README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("""# AI数字名片 Python SDK

由 openapi-generator 自动生成。

## 安装

```bash
pip install ai-digital-business-card-sdk
```

## 使用

```python
from ai_digital_business_card_sdk import ApiClient, Configuration
from ai_digital_business_card_sdk.api import AuthApi

config = Configuration(host="https://api.example.com")
config.access_token = "your-token"

with ApiClient(config) as client:
    api = AuthApi(client)
    response = api.login(phone="13800138000", password="***")
    print(response)
```
""")

    info("  后处理完成")


def post_process_typescript() -> None:
    """对生成的 TypeScript SDK 进行后处理"""
    info("\n后处理 TypeScript SDK...")

    # 创建 package.json（如果不存在）
    package_path = os.path.join(TYPESCRIPT_SDK_DIR, "package.json")
    if not os.path.isfile(package_path):
        info("  创建 package.json")
        package = {
            "name": "@ai-digital-business-card/sdk",
            "version": "2.0.0",
            "description": "AI数字名片 REST API TypeScript SDK",
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "build": "tsc",
                "prepublishOnly": "npm run build"
            },
            "license": "MIT",
        }
        with open(package_path, "w", encoding="utf-8") as f:
            json.dump(package, f, indent=2)

    # 创建 tsconfig.json（如果不存在）
    tsconfig_path = os.path.join(TYPESCRIPT_SDK_DIR, "tsconfig.json")
    if not os.path.isfile(tsconfig_path):
        info("  创建 tsconfig.json")
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "ESNext",
                "moduleResolution": "bundler",
                "declaration": True,
                "outDir": "./dist",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
            },
            "include": ["src/**/*"],
        }
        with open(tsconfig_path, "w", encoding="utf-8") as f:
            json.dump(tsconfig, f, indent=2)

    info("  后处理完成")


def clean_generated_sdk(lang: str, output_dir: str) -> None:
    """移除不需要的生成文件"""
    info(f"\n清理 {lang} SDK 中的无用文件...")

    patterns_to_remove = [".openapi-generator", "git_push.sh", ".gitignore"]

    for pattern in patterns_to_remove:
        target = os.path.join(output_dir, pattern)
        if os.path.isfile(target):
            os.remove(target)
            info(f"  删除文件: {target}")
        elif os.path.isdir(target):
            shutil.rmtree(target)
            info(f"  删除目录: {target}")

    info(f"  清理完成")


# ─── 主逻辑 ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="AI数字名片 API SDK 生成脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--lang",
        choices=["python", "typescript", "all"],
        default="all",
        help="要生成的 SDK 语言 (默认: all)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="仅校验 OpenAPI 规范，不生成 SDK",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="使用本地 openapi.yaml 文件（不请求后端）",
    )
    args = parser.parse_args()

    # ── Step 1: 获取规范 ──
    spec_path = get_openapi_spec(local_only=args.local)

    # ── Step 2: 校验规范 ──
    spec = validate_spec(spec_path)

    if args.validate_only:
        info("\n✅ 规范校验通过，未生成 SDK")
        # 清理临时文件
        if spec_path != OPENAPI_FILE:
            os.unlink(spec_path)
        return

    # ── Step 3: 查找/下载 generator ──
    generator_cmd = find_openapi_generator()
    if generator_cmd is None:
        info("\nopenapi-generator CLI 未找到，尝试下载...")
        version = os.environ.get("OPENAPI_GENERATOR_VERSION", DEFAULT_GENERATOR_VERSION)
        jar_path = download_generator_jar(version)
        generator_cmd = f"java -jar {jar_path}"
        info(f"  使用: {generator_cmd}")

    # ── Step 4: 生成 SDK ──
    languages = []
    if args.lang == "all":
        languages = ["python", "typescript"]
    else:
        languages = [args.lang]

    for lang in languages:
        if lang not in GENERATORS:
            info(f"跳过未配置的语言: {lang}")
            continue

        run_generator(generator_cmd, spec_path, lang, GENERATORS[lang])

        # 后处理
        if lang == "python":
            post_process_python()
        elif lang == "typescript":
            post_process_typescript()

        # 清理
        clean_generated_sdk(lang, GENERATORS[lang]["output_dir"])

    # ── Step 5: 完成 ──
    info("\n" + "=" * 60)
    info("✅ SDK 生成完成！")
    info("=" * 60)
    info(f"  Python SDK:     {PYTHON_SDK_DIR}")
    info(f"  TypeScript SDK: {TYPESCRIPT_SDK_DIR}")
    info("")

    # 清理临时文件
    if spec_path != OPENAPI_FILE:
        os.unlink(spec_path)
        info(f"  已清理临时规范文件: {spec_path}")


if __name__ == "__main__":
    main()
