# -*- coding: utf-8 -*-
"""扫描模型文件, 按ClassDef为单位提取: 表名、列(含comment/pk/unique/index)、table_args索引"""
import ast, os, io, sys, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MODELS_DIR = 'app/models'
EXTRA_FILES = ['app/crm/crm_models.py']
out = {}

def scan_file(path):
    src_text = open(path, encoding='utf-8').read()
    try:
        tree = ast.parse(src_text)
    except Exception as e:
        out[path] = {'error': str(e)}
        return
    classes = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        cls = {'name': node.name, 'tablename': None, 'columns': [], 'index_defs': [], 'doc': None}
        # docstring
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            cls['doc'] = node.body[0].value.value
        for item in node.body:
            # __tablename__
            if isinstance(item, ast.Assign):
                for t in item.targets:
                    if isinstance(t, ast.Name) and t.id == '__tablename__':
                        try: cls['tablename'] = ast.literal_eval(item.value)
                        except Exception: pass
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == '__tablename__':
                try: cls['tablename'] = ast.literal_eval(item.value)
                except Exception: pass
            # __table_args__ 中的 Index 定义
            if isinstance(item, ast.Assign):
                for t in item.targets:
                    if isinstance(t, ast.Name) and t.id == '__table_args__':
                        seg = ast.get_source_segment(src_text, item.value) or ''
                        for m in __import__('re').finditer(r'Index\([^)]*\)', seg):
                            cls['index_defs'].append(m.group(0).replace('\n', ' '))
            # 列: AnnAssign 带 mapped_column
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                col = {'name': item.target.id, 'type': None, 'comment': None, 'pk': False, 'unique': False, 'index': False}
                val = item.value
                if val is not None:
                    seg = ast.get_source_segment(src_text, val) or ''
                    col['raw'] = seg.replace('\n', ' ')[:180]
                    if isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id == 'mapped_column':
                        if val.args:
                            try: col['type'] = ast.unparse(val.args[0])
                            except Exception: col['type'] = ''
                        for kw in val.keywords:
                            if kw.arg == 'comment':
                                try: col['comment'] = ast.literal_eval(kw.value)
                                except Exception: pass
                            elif kw.arg == 'primary_key':
                                try: col['pk'] = bool(ast.literal_eval(kw.value))
                                except Exception: pass
                            elif kw.arg == 'unique':
                                try: col['unique'] = bool(ast.literal_eval(kw.value))
                                except Exception: pass
                            elif kw.arg == 'index':
                                try: col['index'] = bool(ast.literal_eval(kw.value))
                                except Exception: pass
                cls['columns'].append(col)
            # 列: Assign 带 Column(
            if isinstance(item, ast.Assign):
                for t in item.targets:
                    if not isinstance(t, ast.Name):
                        continue
                    if t.id in ('__tablename__', '__table_args__', 'metadata'):
                        continue
                    seg = ast.get_source_segment(src_text, item.value) or ''
                    if 'Column(' not in seg:
                        continue
                    col = {'name': t.id, 'type': None, 'comment': None, 'pk': False, 'unique': False, 'index': False, 'raw': seg.replace('\n',' ')[:180]}
                    if 'primary_key=True' in seg: col['pk'] = True
                    if 'unique=True' in seg: col['unique'] = True
                    if 'index=True' in seg: col['index'] = True
                    m = __import__('re').search(r'comment\s*=\s*["\']([^"\']+)["\']', seg)
                    if m: col['comment'] = m.group(1)
                    cls['columns'].append(col)
        if cls['tablename'] or cls['columns']:
            classes.append(cls)
    out[path] = classes

for f in sorted(os.listdir(MODELS_DIR)):
    if f.endswith('.py') and f != '__init__.py':
        scan_file(os.path.join(MODELS_DIR, f))
for f in EXTRA_FILES:
    if os.path.exists(f):
        scan_file(f)

json.dump(out, open('data/_models_dump.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)

# 汇总: 表名 -> 列数
stat = {}
for path, classes in out.items():
    if isinstance(classes, dict) and 'error' in classes:
        print(f'ERROR {path}: {classes["error"]}')
        continue
    for c in classes:
        if c['tablename']:
            n = len(c['columns'])
            stat.setdefault(c['tablename'], []).append((c['name'], n))
full, stub, dup = [], [], []
for t, lst in sorted(stat.items()):
    names = [x[0] for x in lst]
    n = max(x[1] for x in lst)
    if len(lst) > 1:
        dup.append((t, names, [x[1] for x in lst]))
    if n >= 3:
        full.append((t, names[0], n))
    else:
        stub.append((t, names[0], n))
print(f'=== 完整模型(>=3列): {len(full)} ===')
for t, c, n in full: print(f'  {t} | {c} | {n}列')
print(f'=== 占位/简化模型(<3列): {len(stub)} ===')
for t, c, n in stub: print(f'  {t} | {c} | {n}列')
print(f'=== 同名多类(需复核): {len(dup)} ===')
for t, names, ns in dup: print(f'  {t} | {names} | 列数{ns}')
