"""
装配式知识架构引擎 (Composition Knowledge Architecture Engine)

四层组合模型:
  Skill(91) ──提供能力──→ Feature(21) ──能力封装──→ Module ──子系统──→ Product(70)
    ↑              ↑              ↑
    └── composition_recipe.yaml ──┘

纯标准库依赖，零外部依赖。
"""

import os
import re
import yaml
import json
import fnmatch
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from collections import defaultdict, deque


# =============================================================================
# 数据类
# =============================================================================

@dataclass
class Module:
    """组合单元——由 skills + features + atoms 装配而成的功能模块"""
    name: str
    skills: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    atoms: list[str] = field(default_factory=list)
    composition_rules: dict[str, Any] = field(default_factory=dict)


@dataclass
class Composition:
    """完整的装配结构，包含依赖图"""
    modules: list[Module] = field(default_factory=list)
    graph: dict[str, list[str]] = field(default_factory=dict)  # name -> [dependency_names]


@dataclass
class CompositionRecipe:
    """组合配方——定义如何将下层资产装配成上层资产"""
    name: str
    skills_needed: list[str] = field(default_factory=list)
    atoms_needed: list[str] = field(default_factory=list)
    features_depends_on: list[str] = field(default_factory=list)
    builds_into: str = ""  # 装配后生成的目标（product/module name）


# =============================================================================
# 路径配置
# =============================================================================

# 自动检测 Windows 用户主目录
_HOME = os.path.expanduser("~")
_USER = os.path.basename(_HOME) if _HOME else "56867"

# 根路径——AI数智名片项目
_PROJECT_ROOT = "D:\\AI数智名片"

# 知识库路径
_KNOWLEDGE_BASE = "D:\\向海容的知识库\\wiki\\wiki\\记忆宫殿\\L5孵化室"

# 各项资产的默认扫描路径
_DEFAULT_SKILLS_DIR = os.path.join(_HOME, ".hermes", "skills")
_DEFAULT_FEATURES_DIR = os.path.join(_KNOWLEDGE_BASE, "Feature库")
_DEFAULT_ATOMS_DIR = os.path.join(_KNOWLEDGE_BASE, "Feature库", "atoms")
_DEFAULT_PRODUCTS_DIR = os.path.join(_KNOWLEDGE_BASE, "产品开发")
_DEFAULT_FEATURES_REGISTRY_DIR = os.path.join(_KNOWLEDGE_BASE, "产品开发", "_features")
_DEFAULT_REGISTRY_FILE = os.path.join(_KNOWLEDGE_BASE, "_系统", "composition_registry.yaml")


# =============================================================================
# CompositionEngine
# =============================================================================

class CompositionEngine:
    """装配式知识架构引擎——负责扫描、组合、分析、可视化知识资产"""

    def __init__(
        self,
        skills_dir: str | None = None,
        features_dir: str | None = None,
        atoms_dir: str | None = None,
        products_dir: str | None = None,
        features_registry_dir: str | None = None,
        registry_file: str | None = None,
    ):
        self.skills_dir = skills_dir or _DEFAULT_SKILLS_DIR
        self.features_dir = features_dir or _DEFAULT_FEATURES_DIR
        self.atoms_dir = atoms_dir or _DEFAULT_ATOMS_DIR
        self.products_dir = products_dir or _DEFAULT_PRODUCTS_DIR
        self.features_registry_dir = features_registry_dir or _DEFAULT_FEATURES_REGISTRY_DIR
        self.registry_file = registry_file or _DEFAULT_REGISTRY_FILE

        # 缓存
        self._skills_cache: list[dict] | None = None
        self._atoms_cache: list[dict] | None = None
        self._features_cache: list[dict] | None = None
        self._products_cache: list[dict] | None = None

        # 初始化注册表
        self.registry = CompositionRegistry()
        self._load_registry()

    # ------------------------------------------------------------------
    # 扫描方法
    # ------------------------------------------------------------------

    def scan_skills(self) -> list[dict]:
        """扫描 skills/ 获取所有 SKILL.md 的能力标签"""
        if self._skills_cache is not None:
            return self._skills_cache

        results = []
        skills_root = self.skills_dir
        if not os.path.isdir(skills_root):
            self._skills_cache = results
            return results

        for root, dirs, files in os.walk(skills_root):
            for fname in files:
                if fname.upper() == "SKILL.MD":
                    fpath = os.path.join(root, fname)
                    skill_info = self._parse_skill_md(fpath)
                    if skill_info:
                        results.append(skill_info)

        results.sort(key=lambda x: x.get("name", ""))
        self._skills_cache = results
        return results

    def _parse_skill_md(self, fpath: str) -> dict | None:
        """解析单个 SKILL.md 文件为结构化数据"""
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return None

        # 提取 YAML frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return None

        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return None

        if not isinstance(meta, dict):
            return None

        # 提取 tags / dependencies / description
        tags = []
        deps = []
        description = meta.get("description", "")

        # 从 metadata.hermes.tags 提取
        hermes_meta = meta.get("metadata", {})
        if isinstance(hermes_meta, dict):
            hermes = hermes_meta.get("hermes", {})
            if isinstance(hermes, dict):
                raw_tags = hermes.get("tags", [])
                if isinstance(raw_tags, list):
                    tags = [str(t) for t in raw_tags]

        # 从 dependencies 提取
        raw_deps = meta.get("dependencies", [])
        if isinstance(raw_deps, list):
            deps = [str(d) for d in raw_deps if isinstance(d, str)]

        # 相对路径作为 skill 唯一标识
        rel_path = os.path.relpath(os.path.dirname(fpath), self.skills_dir)
        skill_name = meta.get("name", os.path.basename(os.path.dirname(fpath)))

        return {
            "name": str(skill_name),
            "path": rel_path.replace("\\", "/"),
            "tags": tags,
            "dependencies": deps,
            "description": str(description)[:200] if description else "",
            "version": str(meta.get("version", "")),
            "author": str(meta.get("author", "")),
        }

    def scan_atoms(self) -> list[dict]:
        """扫描 atoms/ 获取所有原子认知单元"""
        if self._atoms_cache is not None:
            return self._atoms_cache

        results = []
        atoms_root = self.atoms_dir
        if not os.path.isdir(atoms_root):
            self._atoms_cache = results
            return results

        for entry in sorted(os.listdir(atoms_root)):
            atom_dir = os.path.join(atoms_root, entry)
            if not os.path.isdir(atom_dir):
                continue

            readme_path = os.path.join(atom_dir, "README.md")
            if not os.path.isfile(readme_path):
                results.append({
                    "name": entry,
                    "path": entry,
                    "skills": [],
                    "tags": [],
                    "description": "",
                })
                continue

            # 解析 README.md 中引用的技能
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                content = ""

            skills_refs = re.findall(r"\*\*([^*]+)\*\*", content)
            description = content.split("\n")[0] if content else ""
            if description.startswith("#"):
                description = description.lstrip("#").strip()

            results.append({
                "name": entry,
                "path": entry,
                "skills": [s.strip() for s in skills_refs if s.strip()],
                "tags": [],
                "description": description,
            })

        self._atoms_cache = results
        return results

    def scan_features(self) -> list[dict]:
        """扫描 Feature库/ 获取所有 feature 文件 (yaml)"""
        if self._features_cache is not None:
            return self._features_cache

        results = []
        features_root = self.features_dir
        if not os.path.isdir(features_root):
            self._features_cache = results
            return results

        for fname in os.listdir(features_root):
            if not fname.endswith(".yaml"):
                continue
            fpath = os.path.join(features_root, fname)
            if not os.path.isfile(fpath):
                continue

            feat = self._parse_feature_yaml(fpath)
            if feat:
                results.append(feat)

        # 同时也扫描 _features/ 注册目录
        if os.path.isdir(self.features_registry_dir):
            for fname in os.listdir(self.features_registry_dir):
                if not fname.endswith(".yaml") or fname.startswith("_"):
                    continue
                fpath = os.path.join(self.features_registry_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                feat = self._parse_feature_yaml(fpath, registry_mode=True)
                if feat:
                    results.append(feat)

        results.sort(key=lambda x: x.get("name", ""))
        self._features_cache = results
        return results

    def _parse_feature_yaml(self, fpath: str, registry_mode: bool = False) -> dict | None:
        """解析单个 feature yaml 文件"""
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            return None

        if not isinstance(data, dict):
            return None

        feat_id = data.get("id") or data.get("name") or os.path.splitext(os.path.basename(fpath))[0]
        raw_atoms = data.get("atoms", [])
        if isinstance(raw_atoms, list):
            atoms = [str(a) for a in raw_atoms]
        else:
            atoms = []

        raw_skills = data.get("skills", [])
        if isinstance(raw_skills, list):
            skills = [str(s) for s in raw_skills]
        else:
            skills = []

        raw_products = data.get("products", [])
        if isinstance(raw_products, list):
            products = [str(p) for p in raw_products]
        else:
            products = []

        return {
            "id": str(feat_id),
            "name": str(data.get("name", feat_id)),
            "domain": str(data.get("domain", "")),
            "type": str(data.get("type", "feature")),
            "description": str(data.get("description", ""))[:300],
            "atoms": atoms,
            "skills": skills,
            "products": products,
            "version": str(data.get("version", "")),
            "status": str(data.get("status", "active")),
            "source_file": os.path.basename(fpath),
        }

    def scan_products(self) -> list[dict]:
        """扫描产品目录，获取所有已注册产品"""
        if self._products_cache is not None:
            return self._products_cache

        results = []
        products_root = self.products_dir
        if not os.path.isdir(products_root):
            self._products_cache = results
            return results

        for entry in sorted(os.listdir(products_root)):
            product_dir = os.path.join(products_root, entry)
            if not os.path.isdir(product_dir):
                continue
            if entry.startswith("_") or entry.startswith("."):
                continue

            # 查找 product 元数据
            meta = self._detect_product_meta(product_dir, entry)
            results.append(meta)

        results.sort(key=lambda x: x.get("name", ""))
        self._products_cache = results
        return results

    def _detect_product_meta(self, product_dir: str, entry_name: str) -> dict:
        """探测产品目录的元数据"""
        # 查找 feature_roadmap.md, PRD, 或描述文件
        desc = ""
        atoms_dirs = []
        features_list = []

        for fname in os.listdir(product_dir):
            fpath = os.path.join(product_dir, fname)
            lower = fname.lower()
            if os.path.isfile(fpath):
                if lower in ("feature_roadmap.md", "prd.md", "readme.md"):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            first_line = f.readline().strip()
                            if first_line:
                                desc = first_line.lstrip("#").strip()[:200]
                    except (OSError, UnicodeDecodeError):
                        pass
            elif os.path.isdir(fpath) and lower == "atoms":
                atoms_dirs = os.listdir(fpath)

        return {
            "name": entry_name,
            "path": entry_name,
            "description": desc,
            "atoms_count": len(atoms_dirs),
            "features": features_list,
        }

    # ------------------------------------------------------------------
    # 核心组合方法
    # ------------------------------------------------------------------

    def compose(self, skills: list[dict], atoms: list[dict]) -> dict:
        """组合 skill + atom 生成新 feature 提案

        Args:
            skills: scan_skills() 输出的 skill 列表
            atoms: scan_atoms() 输出的 atom 列表

        Returns:
            包含组合提案的 dict
        """
        # 建立 skill name -> skill 的索引
        skill_map = {s["name"]: s for s in skills}

        # 建立 atom name -> atom 的索引
        atom_map = {a["name"]: a for a in atoms}

        # 聚类：按能力域聚合
        clusters: dict[str, dict] = {}

        # 对每个 atom，查找其引用的 skill
        for atom_name, atom in atom_map.items():
            referenced_skills = [s for s in atom.get("skills", []) if s in skill_map]
            if not referenced_skills:
                continue

            # 用 skill 的 tags 推断 domain
            domains = set()
            for sk_name in referenced_skills:
                sk = skill_map.get(sk_name, {})
                domains.update(sk.get("tags", []))

            domain_key = "|".join(sorted(domains)) if domains else "uncategorized"
            if domain_key not in clusters:
                clusters[domain_key] = {
                    "domain": domain_key,
                    "skills": [],
                    "atoms": [],
                    "confidence": 0.0,
                }

            clusters[domain_key]["skills"].extend(referenced_skills)
            clusters[domain_key]["atoms"].append(atom_name)

        # 为每个 cluster 生成 feature 提案
        proposals = []
        for domain, cluster in clusters.items():
            unique_skills = list(set(cluster["skills"]))
            unique_atoms = list(set(cluster["atoms"]))
            confidence = min(1.0, (len(unique_skills) + len(unique_atoms)) / 10.0)

            proposals.append({
                "proposed_name": f"composed_{domain.replace('|', '_').replace(' ', '_').lower()}",
                "domain": domain,
                "skills": unique_skills,
                "atoms": unique_atoms,
                "confidence": round(confidence, 2),
                "type": "composed_feature",
            })

        proposals.sort(key=lambda x: x["confidence"], reverse=True)
        return {
            "proposals": proposals,
            "total_skills_used": len(skill_map),
            "total_atoms_used": len(atom_map),
            "clusters_found": len(clusters),
        }

    def analyze_dependencies(self) -> dict:
        """分析所有层级之间的依赖关系"""
        skills = self.scan_skills()
        atoms = self.scan_atoms()
        features = self.scan_features()
        products = self.scan_products()

        # Skill -> Feature 映射
        skill_to_feature = defaultdict(list)
        for feat in features:
            for sk in feat.get("skills", []):
                skill_to_feature[sk].append(feat["name"])

        # Atom -> Feature 映射
        atom_to_feature = defaultdict(list)
        for feat in features:
            for a in feat.get("atoms", []):
                atom_to_feature[a].append(feat["name"])

        # Feature -> Product 映射
        feature_to_product = defaultdict(list)
        for feat in features:
            for p in feat.get("products", []):
                feature_to_product[feat["name"]].append(p)

        # 统计
        all_skill_names = {s["name"] for s in skills}
        all_atom_names = {a["name"] for a in atoms}
        all_feature_names = {f["name"] for f in features}
        all_product_names = {p["name"] for p in products}

        # 孤儿分析：定义了 skill 但未被任何 feature 引用
        orphan_skills = all_skill_names - set(skill_to_feature.keys())
        # 孤儿分析：定义了 atom 但未被任何 feature 引用
        orphan_atoms = all_atom_names - set(atom_to_feature.keys())
        # 孤儿分析：定义了 feature 但未关联任何 product
        orphan_features = all_feature_names - set(feature_to_product.keys())

        return {
            "summary": {
                "skills": len(skills),
                "atoms": len(atoms),
                "features": len(features),
                "products": len(products),
            },
            "skill_to_feature": dict(skill_to_feature),
            "atom_to_feature": dict(atom_to_feature),
            "feature_to_product": dict(feature_to_product),
            "orphans": {
                "skills": sorted(orphan_skills),
                "atoms": sorted(orphan_atoms)[:50],  # 只显示前50
                "features": sorted(orphan_features),
            },
        }

    def find_gaps(self) -> list[dict]:
        """找出哪些 feature 缺少必要的 skill 或 atom 支撑"""
        skills = self.scan_skills()
        atoms = self.scan_atoms()
        features = self.scan_features()

        skill_names = {s["name"] for s in skills}
        atom_names = {a["name"] for a in atoms}

        gaps = []
        for feat in features:
            missing_skills = [s for s in feat.get("skills", []) if s not in skill_names]
            missing_atoms = [a for a in feat.get("atoms", []) if a not in atom_names]

            if missing_skills or missing_atoms:
                gaps.append({
                    "feature": feat["name"],
                    "missing_skills": missing_skills,
                    "missing_atoms": missing_atoms,
                    "severity": len(missing_skills) + len(missing_atoms),
                })

        gaps.sort(key=lambda x: x["severity"], reverse=True)
        return gaps

    def suggest_compositions(self, goal: str) -> list[dict]:
        """根据目标推荐组合方案

        Args:
            goal: 目标描述，可以是产品名、功能名称或关键词

        Returns:
            推荐的 Module 组合方案列表
        """
        skills = self.scan_skills()
        atoms = self.scan_atoms()
        features = self.scan_features()
        products = self.scan_products()

        goal_lower = goal.lower()
        candidates = []

        # 1. 精确匹配产品名 -> 找到关联的feature -> 反向找需要的skill/atom
        for prod in products:
            if goal_lower in prod["name"].lower():
                # 找到与此产品关联的 feature
                relevant_features = [
                    f for f in features
                    if goal_lower in " ".join(f.get("products", [])).lower()
                ]
                for feat in relevant_features:
                    candidates.append({
                        "name": f"Module: {feat['name']}",
                        "type": "module",
                        "features": [feat["name"]],
                        "skills": feat.get("skills", []),
                        "atoms": feat.get("atoms", []),
                        "confidence": 0.9,
                    })

        # 2. 关键词匹配 feature
        if not candidates:
            for feat in features:
                if goal_lower in feat["name"].lower() or goal_lower in feat.get("description", "").lower():
                    candidates.append({
                        "name": f"Module: {feat['name']}",
                        "type": "module",
                        "features": [feat["name"]],
                        "skills": feat.get("skills", []),
                        "atoms": feat.get("atoms", []),
                        "confidence": 0.8,
                    })

        # 3. 关键词匹配 skill
        if not candidates:
            for sk in skills:
                if goal_lower in sk["name"].lower():
                    # 找到使用此 skill 的 feature
                    used_in = [
                        f["name"] for f in features
                        if sk["name"] in f.get("skills", [])
                    ]
                    candidates.append({
                        "name": f"SkillBundle: {sk['name']}",
                        "type": "skill_bundle",
                        "features": used_in,
                        "skills": [sk["name"]],
                        "atoms": [],
                        "confidence": 0.6,
                    })

        # 4. 宽泛匹配 — atom 级别
        if not candidates:
            for a in atoms:
                if goal_lower in a["name"].lower():
                    used_in = [
                        f["name"] for f in features
                        if a["name"] in f.get("atoms", [])
                    ]
                    candidates.append({
                        "name": f"Atom: {a['name']}",
                        "type": "atom",
                        "features": used_in,
                        "skills": a.get("skills", []),
                        "atoms": [a["name"]],
                        "confidence": 0.4,
                    })

        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        return candidates[:10]  # 最多返回10条

    def visualize(self) -> str:
        """生成 ASCII 依赖图"""
        deps = self.analyze_dependencies()
        summary = deps["summary"]

        lines = []
        lines.append("=" * 72)
        lines.append("  装配式知识架构 — 四层依赖图")
        lines.append("=" * 72)
        lines.append(f"  Skills: {summary['skills']}  →  Features: {summary['features']}  →  Products: {summary['products']}")
        lines.append(f"  Atoms:  {summary['atoms']}")
        lines.append("")

        # 第一层: Products
        products = self.scan_products()
        product_features = deps["feature_to_product"]

        for prod in products[:20]:  # 最多显示20个
            name = prod["name"]
            # 找出与此产品关联的所有 features
            related_features = [
                f for f_name, f_products in product_features.items()
                if name in f_products
                for f in [next((x for x in self.scan_features() if x["name"] == f_name), None)]
                if f
            ]

            icon = "📦"
            lines.append(f"  {icon} {name}")
            for feat in related_features[:5]:  # 最多5个feature
                lines.append(f"     ├─ 📐 {feat['name']}")
                for sk in feat.get("skills", [])[:3]:
                    lines.append(f"     │    ├─ 🔧 {sk}")
                for a in feat.get("atoms", [])[:3]:
                    lines.append(f"     │    └─ ⚛ {a}")
            if len(related_features) > 5:
                lines.append(f"     └─ ... (+{len(related_features) - 5} more)")

        # 孤儿节点
        orphans = deps["orphans"]
        if orphans["skills"]:
            lines.append("")
            lines.append(f"  ⚠️ 孤儿 Skills (未关联任何Feature): {len(orphans['skills'])}")
            for s in orphans["skills"][:10]:
                lines.append(f"     - {s}")
            if len(orphans["skills"]) > 10:
                lines.append(f"     ... (+{len(orphans['skills']) - 10} more)")

        if orphans["features"]:
            lines.append("")
            lines.append(f"  ⚠️ 孤儿 Features (未关联任何Product): {len(orphans['features'])}")
            for f in orphans["features"][:10]:
                lines.append(f"     - {f}")
            if len(orphans["features"]) > 10:
                lines.append(f"     ... (+{len(orphans['features']) - 10} more)")

        lines.append("")
        lines.append("=" * 72)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _load_registry(self):
        """从 YAML 文件加载注册表"""
        if os.path.isfile(self.registry_file):
            try:
                self.registry.load(self.registry_file)
            except (OSError, yaml.YAMLError) as e:
                print(f"[composition_engine] 加载注册表失败: {e}")

    def refresh(self):
        """清除缓存，下次扫描重新读取"""
        self._skills_cache = None
        self._atoms_cache = None
        self._features_cache = None
        self._products_cache = None

    def summary(self) -> dict:
        """返回当前所有资产的概要统计"""
        skills = self.scan_skills()
        atoms = self.scan_atoms()
        features = self.scan_features()
        products = self.scan_products()

        gaps = self.find_gaps()

        # Features 按 domain 分布
        domain_dist = defaultdict(int)
        for f in features:
            domain_dist[f.get("domain", "unknown")] += 1

        return {
            "assets": {
                "skills": len(skills),
                "atoms": len(atoms),
                "features": len(features),
                "products": len(products),
            },
            "registry_recipes": len(self.registry.recipes),
            "domain_distribution": dict(domain_dist),
            "gaps_found": len(gaps),
            "orphan_skills": len([s for s in skills if not any(s["name"] in f.get("skills", []) for f in features)]),
        }


# =============================================================================
# CompositionRegistry
# =============================================================================

class CompositionRegistry:
    """装配注册表——管理组合配方及其依赖解析"""

    def __init__(self):
        self.recipes: dict[str, CompositionRecipe] = {}
        self._dirty = False

    def register(self, recipe: CompositionRecipe):
        """注册一个组合配方"""
        self.recipes[recipe.name] = recipe
        self._dirty = True

    def lookup(self, name: str) -> CompositionRecipe | None:
        """按名称查找配方"""
        return self.recipes.get(name)

    def resolve_dependencies(self, name: str) -> list[CompositionRecipe]:
        """解析指定配方的所有依赖（拓扑排序）

        Args:
            name: 配方名称

        Returns:
            按拓扑序排列的依赖配方列表（从依赖者到被依赖者）
        """
        if name not in self.recipes:
            return []

        # 构建依赖图
        graph: dict[str, list[str]] = {}
        in_degree: dict[str, int] = {}

        for r_name, recipe in self.recipes.items():
            if r_name not in graph:
                graph[r_name] = []
                in_degree[r_name] = 0

            for dep in recipe.features_depends_on:
                if dep in self.recipes:
                    if dep not in graph:
                        graph[dep] = []
                        in_degree[dep] = 0
                    graph[r_name].append(dep)
                    in_degree[r_name] = in_degree.get(r_name, 0) + 1

        # Kahn 拓扑排序（寻找从 name 出发的反向依赖链）
        # 实际上我们想要 "name 依赖了谁" — 即依赖链
        visited = set()
        result = []

        def dfs(current: str):
            if current in visited:
                return
            visited.add(current)
            recipe = self.recipes.get(current)
            if recipe:
                for dep in recipe.features_depends_on:
                    if dep in self.recipes:
                        dfs(dep)
                result.append(current)

        dfs(name)
        return [self.recipes[r] for r in result]

    def available_for(self, product: str) -> list[CompositionRecipe]:
        """为指定产品推荐可组合的配方

        Args:
            product: 产品名称

        Returns:
            匹配的配方列表
        """
        matches = []
        product_lower = product.lower()
        for recipe in self.recipes.values():
            if product_lower in recipe.builds_into.lower():
                matches.append(recipe)
        return matches

    def load(self, filepath: str):
        """从 YAML 文件加载注册表"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("注册表 YAML 格式错误: 顶层不是 dict")

        recipes_raw = data.get("recipes", [])
        if not isinstance(recipes_raw, list):
            raise ValueError("注册表格式错误: recipes 不是列表")

        for entry in recipes_raw:
            if not isinstance(entry, dict):
                continue
            recipe = CompositionRecipe(
                name=str(entry.get("name", "")),
                skills_needed=[str(s) for s in entry.get("skills_needed", []) if s],
                atoms_needed=[str(a) for a in entry.get("atoms_needed", []) if a],
                features_depends_on=[str(f) for f in entry.get("features_depends_on", []) if f],
                builds_into=str(entry.get("builds_into", "")),
            )
            self.register(recipe)

        self._dirty = False

    def save(self, filepath: str):
        """将注册表保存到 YAML 文件"""
        recipes_data = []
        for recipe in self.recipes.values():
            recipes_data.append(asdict(recipe))

        data = {
            "_meta": {
                "version": "1.0.0",
                "description": "装配式知识架构组合注册表",
                "generated_by": "composition_engine.CompositionRegistry",
            },
            "recipes": recipes_data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        self._dirty = False


# =============================================================================
# 全局单例
# =============================================================================

_engine_instance: CompositionEngine | None = None


def get_engine(**kwargs) -> CompositionEngine:
    """获取全局 CompositionEngine 单例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = CompositionEngine(**kwargs)
    return _engine_instance


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    """CLI 入口——快速查看知识架构概览"""
    engine = get_engine()
    s = engine.summary()

    print()
    print("=" * 54)
    print("  装配式知识架构引擎 — 资产概览")
    print("=" * 54)
    print(f"  Skills:     {s['assets']['skills']}")
    print(f"  Atoms:      {s['assets']['atoms']}")
    print(f"  Features:   {s['assets']['features']}")
    print(f"  Products:   {s['assets']['products']}")
    print(f"  Recipes:    {s['registry_recipes']}")
    print(f"  Gaps:       {s['gaps_found']}")
    print(f"  Orphan Sk:  {s['orphan_skills']}")
    print()

    # layers
    print("  Domain Distribution:")
    for domain, count in sorted(s["domain_distribution"].items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 40)
        print(f"    {domain:20s} {bar} {count}")
    print()
    print(engine.visualize())


if __name__ == "__main__":
    main()
