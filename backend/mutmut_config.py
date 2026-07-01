"""
mutmut 变异测试配置文件

运行方式:
  mutmut run --paths-to-mutate app/services/ app/utils/  --tests-dir tests/
  mutmut results
  mutmut html
"""

from mutmut import Config

config = Config(
    # 需要变异的核心模块路径
    paths_to_mutate=[
        "app/services/matching_engine.py",
        "app/services/tag_service.py",
        "app/services/brochure.py",
        "app/services/trust_service.py",
        "app/utils/formatting.py",
    ],
    # 测试目录
    tests_dir="tests",
    # 测试文件模式
    test_pattern="test_*.py",
    # 按文件名筛选测试（可选，不指定则运行全部）
    test_function="test_mutation_core",
    # 变异后超时时间（秒）
    mutant_timeout=30,
    # 字典变异开关（字符串字面量替换）
    dict_synonyms=True,
    # 数据库后端（默认 SQLite）
    backup_source=False,
    # 变异数量上限（0=不限制）
    max_mutations=0,
    # 使用 pytest 运行测试
    pytest_cmd="python -m pytest -x --timeout=30",
)
