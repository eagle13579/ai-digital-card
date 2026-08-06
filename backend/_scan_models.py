# -*- coding: utf-8 -*-
"""扫描 backend/app/models/*.py 及 crm 模型, 提取模型类、表名、列定义(含comment)、索引定义"""
import ast, os, io, sys, json, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MODELS_DIR = 'app/models'
EXTRA_FILES = ['app/crm/crm_models.py']
out = {}

def scan_file(path):
    try:
        tree = ast.parse(open(path, encoding='utf-8').read())
    except Exception as e:
        out[path] = {'error': str(e)}
        return
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            cls = {'name': node.name, 'tablename': None, 'columns': [], 'table_args': [], 'doc': None}
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                cls['doc'] = node.body[0].value.value
            for item in node.body:
                # __tablename__
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id == '__tablename__':
                            try:
                                cls['tablename'] = ast.literal_eval(item.value)
                            except Exception:
                                pass
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == '__tablename__':
                    try:
                        cls['tablename'] = ast.literal_eval(item.value)
                    except Exception:
                        pass
                # __table_args__
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id == '__table_args__':
                            try:
                                cls['table_args'] = ast.dump(item.value)
                            except Exception:
                                pass
                # 列定义: mapped_column / Column
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    col = {'name': item.target.id, 'type': None, 'comment': None, 'pk': False, 'unique': False, 'index': False}
                    val = item.value
                    if val is not None:
                        src = ast.get_source_segment(open(path, encoding='utf-8').read(), val) or ''
                        col['raw'] = src.replace('\n', ' ')[:160]
                        # 提取类型
                        if isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id == 'mapped_column':
                            if val.args:
                                try:
                                    col['type'] = ast.unparse(val.args[0]) if hasattr(ast, 'unparse') else ''
                                except Exception:
                                    col['type'] = ''
                            for kw in val.keywords:
                                k = kw.arg
                                if k == 'comment':
                                    try: col['comment'] = ast.literal_eval(kw.value)
                                    except Exception: pass
                                if k == 'primary_key':
                                    try: col['pk'] = ast.literal_eval(kw.value)
                                    except Exception: pass
                                if k == 'unique':
                                    try: col['unique'] = ast.literal_eval(kw.value)
                                    except Exception: pass
                                if k == 'index':
                                    try: col['index'] = ast.literal_eval(kw.value)
                                    except Exception: pass
                    cls['columns'].append(col)
                # 旧式 Column 定义
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id not in ('__tablename__', '__table_args__', 'metadata'):
                            src = ast.get_source_segment(open(path, encoding='utf-8').read(), item.value) or ''
                            if 'Column(' in src or 'mapped_column(' in src:
                                col = {'name': t.id, 'type': None, 'comment': None, 'pk': False, 'unique': False, 'index': False, 'raw': src.replace('\n',' ')[:160]}
                                if 'primary_key=True' in src: col['pk'] = True
                                if 'unique=True' in src: col['unique'] = True
                                if 'index=True' in src: col['index'] = True
                                m = re.search(r'comment\s*=\s*["\']([^"\']+)["\']', src)
                                if m: col['comment'] = m.group(1)
                                classes.append(cls)  # placeholder to keep order
                                cls = {'name': node.name, 'tablename': cls['tablename'], 'columns': [], 'table_args': cls['table_args'], 'doc': cls['doc']}
                                cls['columns'].append(col)
                                continue
                            if t.id in ('Index',): pass
            if cls['columns'] or cls['tablename']:
                classes.append(cls)
    out[path] = classes

for f in sorted(os.listdir(MODELS_DIR)):
    if f.endswith('.py') and f != '__init__.py':
        scan_file(os.path.join(MODELS_DIR, f))
for f in EXTRA_FILES:
    if os.path.exists(f):
        scan_file(f)

json.dump(out, open('data/_models_dump.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)

# 统计: 完整模型(>=3列) vs 占位模型(1-2列)
full, stub = [], []
for path, classes in out.items():
    if isinstance(classes, dict) and 'error' in classes:
        print(f'ERROR {path}: {classes["error"]}')
        continue
    for c in classes:
        if c['tablename']:
            n = len(c['columns'])
            if n >= 3:
                full.append((c['tablename'], c['name'], n))
            else:
                stub.append((c['tablename'], c['name'], n))
print(f'=== 完整模型(>=3列): {len(full)} ===')
for t, n_, c in sorted(full): print(f'  {t} | {n_} | {c}列')
print(f'=== 占位/简化模型(<3列): {len(stub)} ===')
for t, n_, c in sorted(stub): print(f'  {t} | {n_} | {c}列')
