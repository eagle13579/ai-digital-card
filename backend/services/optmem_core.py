"""optmem_core.py — OptMem 原子化封装库（零依赖，纯标准库）

将 VictorTaelin/OptMem 的永久记忆方案封装为可 import 的 Python 库。
存储格式与官方 CLI `memo` 完全兼容（同一 MEMORY_DIR 可混用）。

核心哲学：
  - 文件系统就是数据库：LOG.txt append-only + 固定宽度记录（位置即身份，O(1) seek）
  - 正则搜索就是检索引擎：recall 逐字匹配，无向量库、无嵌入模型
  - 280 字节纯文本就是最可靠的记忆格式：换模型、换厂商，文件还在记忆就在
  - 二叉树摘要：相邻记忆合并为一行摘要，TREE/ 是缓存，可随时从 LOG 重建

用法：
    from optmem_core import OptMemStore
    m = OptMemStore()                      # 读 $MEMORY_DIR 或 ~/.optmem/memory
    m.init()                               # 首次创建
    r = m.note("一句话记忆（≤280字节）")    # 返回 {id, pending}
    ctx = m.wake(limit=96)                 # 唤醒上下文（树渲染）
    hits = m.recall("正则")                # 搜索
    m.nap("0-1", "合并摘要")               # 提交压缩
"""

import datetime
import os
import re
import sys
from collections import deque

__version__ = "1.0.0"

# ─────────────────────────────── 旋钮 ───────────────────────────────
KNOBS = {
    "WAKE_LINES": (96, "the memory context: how many lines wake prints"),
    "ENTRY_CHARS": (280, "the longest one memory may be, in bytes"),
    "PART_CHARS": (20000, "output paging: largest part, in bytes"),
    "PART_LINES": (500, "output paging: largest part, in lines"),
}
LOG_REC = 320   # 固定宽度：记忆记录（位置即身份）
TREE_REC = 288  # 固定宽度：树摘要记录
RAW_MAX = 16    # 不超过此规模的块直接从原始 LOG 压缩


class OptMemError(Exception):
    """OptMem 操作失败（对应 CLI 的 die()）。"""


# ─────────────────────────────── 工具 ───────────────────────────────
def _die(msg: str):
    raise OptMemError(msg)


def _count(path: str, rec: int) -> int:
    try:
        return os.path.getsize(path) // rec
    except FileNotFoundError:
        return 0


def _repair(path: str, rec: int):
    """丢弃崩溃留下的不完整尾记录（防错位）。"""
    try:
        n = os.path.getsize(path)
    except FileNotFoundError:
        return
    if n % rec:
        with open(path, "r+b") as f:
            f.truncate(n - n % rec)


def _parse(line: str):
    head, _, rest = line.partition(" ")
    date, _, text = rest.partition(" ")
    return int(head[1:]), date, text


def _records(buf: bytes):
    return [_parse(buf[i * LOG_REC:(i + 1) * LOG_REC].decode().rstrip())
            for i in range(len(buf) // LOG_REC)]


def _pad(text: str, rec: int) -> bytes:
    b = text.encode()
    if len(b) > rec - 1:
        _die("Too long: %d bytes. The record holds %d." % (len(b), rec - 1))
    return b + b" " * (rec - 1 - len(b)) + b"\n"


def _check(text: str, entry_chars: int) -> str:
    text = text.strip()
    if not text:
        _die("Empty. A memory is one line of text.")
    if "\n" in text or "\r" in text:
        _die("%d lines. A memory is one line: merge them, or note them "
             "separately." % (text.count("\n") + 1))
    n = len(text.encode())
    if n > entry_chars:
        _die("Too long: %d bytes, limit %d. Compress it further." % (n, entry_chars))
    return text


def _block_id(s: str) -> tuple:
    """解析 `<lo>-<hi>`（两端闭合），并校验为对齐的 2 幂块。"""
    m = re.fullmatch(r"(\d+)-(\d+)", s)
    if not m:
        _die("'%s' is not a block id." % s)
    lo, hi = int(m.group(1)), int(m.group(2)) + 1
    n = hi - lo
    if n < 2 or n & (n - 1) or lo % n:
        _die("%s is not a block. Copy the id printed by wake." % s)
    return lo, hi


def _plural(n: int, word: str) -> str:
    if n == 1:
        return "1 " + word
    if word.endswith("y"):
        word = word[:-1] + "ie"
    elif word.endswith(("s", "h", "x")):
        word += "e"
    return "%d %ss" % (n, word)


# ─────────────────────────────── 主类 ───────────────────────────────
class OptMemStore:
    """OptMem 记忆库。同一目录 = 同一身份，跨会话/模型/厂商永久。"""

    def __init__(self, memory_dir: str | None = None):
        self.dir = os.path.expanduser(
            memory_dir or os.environ.get("MEMORY_DIR") or "~/.optmem/memory"
        )
        self.knobs = dict(KNOBS)

    # ---- 存储路径 ----
    def log_path(self) -> str:
        return os.path.join(self.dir, "LOG.txt")

    def tree_path(self, size: int) -> str:
        return os.path.join(self.dir, "TREE", str(size))

    def config_path(self) -> str:
        return os.path.join(self.dir, "config")

    # ---- 配置 ----
    def _overrides(self) -> dict:
        out = {}
        p = self.config_path()
        if not os.path.exists(p):
            return out
        for n, line in enumerate(open(p, encoding="utf-8"), 1):
            line = line.split("#")[0].strip()
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip().upper(), v.strip()
            if k not in KNOBS:
                _die("config line %d: %s is not a size." % (n, k))
            if not v.isdigit() or int(v) < 1:
                _die("config line %d: %s must be a positive whole number." % (n, k))
            out[k] = int(v)
        return out

    def config_get(self) -> dict:
        """返回当前生效的旋钮值 {NAME: int}。"""
        over = self._overrides()
        return {k: over.get(k, default) for k, (default, _) in KNOBS.items()}

    def config_set(self, overrides: dict[str, int | None]) -> dict:
        """设置旋钮；值传 None 恢复默认。返回完整配置。"""
        if not os.path.isdir(self.dir):
            _die("No memory at %s. Run init() first." % self.dir)
        cur = self._overrides()
        for k, v in overrides.items():
            k = k.strip().upper()
            if k not in KNOBS:
                _die("%s is not a size. One of: %s." % (k, ", ".join(KNOBS)))
            if v is None:
                cur.pop(k, None)
            else:
                if int(v) < 1:
                    _die("%s must be a positive whole number." % k)
                cur[k] = int(v)
        lines = ["# OptMem sizes for this memory. A commented line means: follow the",
                 "# tool's default.", ""]
        for k, (default, what) in KNOBS.items():
            lines.append("%-2s%-12s = %-6d # %s"
                         % ("" if k in cur else "# ", k, cur.get(k, default), what))
        os.makedirs(self.dir, exist_ok=True)
        with open(self.config_path(), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return self.config_get()

    # ---- 日志 ----
    def log_len(self) -> int:
        return _count(self.log_path(), LOG_REC)

    def log_get(self, i: int):
        return self.log_slice(i, i + 1)[0]

    def log_slice(self, lo: int, hi: int):
        with open(self.log_path(), "rb") as f:
            f.seek(lo * LOG_REC)
            return _records(f.read((hi - lo) * LOG_REC))

    def log_scan(self):
        """流式读取全部记忆（百万条也不占内存）。"""
        with open(self.log_path(), "rb") as f:
            while True:
                buf = f.read(LOG_REC * 4096)
                if not buf:
                    return
                for e in _records(buf):
                    yield e

    def _locked(self):
        lock = open(os.path.join(self.dir, ".lock"), "a")
        try:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        except ImportError:
            pass  # 非 POSIX：退化为无锁（官方 CLI 有 Windows 锁，这里不重复）
        return lock

    def log_append(self, items: list[tuple[str, str]]) -> int:
        """追加记忆（唯一写入口）。返回首个 id。"""
        os.makedirs(self.dir, exist_ok=True)
        os.makedirs(os.path.join(self.dir, "TREE"), exist_ok=True)
        lock = self._locked()
        try:
            _repair(self.log_path(), LOG_REC)
            base = self.log_len()
            with open(self.log_path(), "ab") as f:
                for k, (date, text) in enumerate(items):
                    f.write(_pad("#%d %s %s" % (base + k, date, text), LOG_REC))
                f.flush()
                os.fsync(f.fileno())
            return base
        finally:
            lock.close()

    # ---- 树 ----
    def tree_get(self, lo: int, hi: int) -> str | None:
        size = hi - lo
        try:
            with open(self.tree_path(size), "rb") as f:
                f.seek((lo // size) * TREE_REC)
                rec = f.read(TREE_REC)
        except FileNotFoundError:
            return None
        try:
            return rec.decode().rstrip() or None
        except UnicodeDecodeError:
            _die("The summary of #%d-%d is corrupt. forget %d-%d" % (lo, hi - 1, lo, hi - 1))

    def tree_put(self, lo: int, hi: int, text: str) -> bool:
        size = hi - lo
        lock = self._locked()
        try:
            p = self.tree_path(size)
            _repair(p, TREE_REC)
            if _count(p, TREE_REC) != lo // size:
                return False
            with open(p, "ab") as f:
                f.write(_pad(text, TREE_REC))
                f.flush()
                os.fsync(f.fileno())
            return True
        finally:
            lock.close()

    def tree_drop(self, lo: int, hi: int) -> list:
        """删除块及其上层（LOG 不动，可重建）。返回被删块列表。"""
        gone, size = [], hi - lo
        lock = self._locked()
        try:
            while size <= self.log_len():
                p, k = self.tree_path(size), lo // size
                n = _count(p, TREE_REC)
                if n > k:
                    gone += [(i * size, (i + 1) * size) for i in range(k, n)]
                    with open(p, "r+b") as f:
                        f.truncate(k * TREE_REC)
                size *= 2
            return gone
        finally:
            lock.close()

    # ---- 覆盖（wake 渲染）----
    @staticmethod
    def _cover(T: int, alpha: float):
        root = 1
        while root < T:
            root *= 2
        out, stack = [], [(0, root)]
        while stack:
            lo, hi = stack.pop()
            if lo >= T:
                continue
            size = hi - lo
            if size > 1 and (hi > T or size > alpha * (T - lo)):
                mid = (lo + hi) // 2
                stack.append((mid, hi))
                stack.append((lo, mid))
            else:
                out.append((lo, hi))
        out.sort()
        return out

    def cover(self, T: int, budget: int):
        """唤醒要打印的块：至多 budget 个，近期更细，远期收敛为摘要。"""
        if T <= 0:
            return []
        if T <= budget:
            return [(i, i + 1) for i in range(T)]
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if len(self._cover(T, mid)) > budget:
                lo = mid
            else:
                hi = mid
        out = self._cover(T, hi)
        while len(out) < budget:
            i = max((i for i, b in enumerate(out) if b[1] - b[0] > 1), default=None)
            if i is None:
                break
            lo_, hi_ = out[i]
            mid = (lo_ + hi_) // 2
            out[i:i + 1] = [(lo_, mid), (mid, hi_)]
        return out

    # ---- 压缩（nap）----
    def pending(self, limit: int | None = None) -> list:
        T = self.log_len()
        todo, size = [], 2
        while size <= T:
            have = _count(self.tree_path(size), TREE_REC)
            for k in range(have, T // size):
                todo.append((k * size, (k + 1) * size))
                if limit and len(todo) >= limit:
                    return todo
            size *= 2
        return todo

    def pending_count(self) -> int:
        T = self.log_len()
        n, size = 0, 2
        while size <= T:
            n += max(0, T // size - _count(self.tree_path(size), TREE_REC))
            size *= 2
        return n

    def nap_prompt(self, lo: int, hi: int) -> str:
        """生成压缩提示（交给 LLM 产出摘要行）。"""
        chars = self.config_get()["ENTRY_CHARS"]
        if hi - lo <= RAW_MAX:
            body = "\n".join("  #%d %s %s" % e for e in self.log_slice(lo, hi))
        else:
            mid, halves = (lo + hi) // 2, []
            for a, b in ((lo, mid), (mid, hi)):
                s = self.tree_get(a, b)
                if s is None:
                    _die("The summary of #%d-%d is blank. forget %d-%d" % (a, b - 1, a, b - 1))
                halves.append("  #%d-%d %s" % (a, b - 1, s))
            body = "\n".join(halves)
        left = self.pending_count() - 1
        tail = "" if not left else "\n%s after this one." % (
            "1 compression remains" if left == 1 else
            "%d compressions remain" % left)
        return ("Compress memories #%d-%d into one line of at most %d bytes.\n"
                "Keep what has lasting effect, drop what does not. Invent "
                "nothing.\n\n"
                "%s\n%s\n"
                "Run: nap %d-%d \"<your line>\""
                % (lo, hi - 1, chars, body, tail, lo, hi - 1))

    def next_nap(self) -> str | None:
        todo = self.pending(limit=1)
        if not todo:
            return None
        lo, hi = todo[0]
        return self.nap_prompt(lo, hi)

    # ---- 业务命令（结构化返回）----
    def init(self) -> dict:
        """创建记忆库（幂等）。"""
        os.makedirs(os.path.join(self.dir, "TREE"), exist_ok=True)
        open(self.log_path(), "a").close()
        if not os.path.exists(self.config_path()):
            self.config_set({})
        return {"dir": self.dir, "memories": self.log_len(),
                "created": os.path.isdir(self.dir)}

    def note(self, text: str) -> dict:
        """记一条记忆。返回 {id, pending, nap_prompt}。"""
        cfg = self.config_get()
        text = _check(text, cfg["ENTRY_CHARS"])
        i = self.log_append([(datetime.date.today().isoformat(), text)])
        r = {"id": i, "pending": self.pending_count(),
             "nap_prompt": self.next_nap()}
        return r

    def wake(self, limit: int | None = None) -> dict:
        """唤醒：读记忆上下文（树渲染）。返回 {lines, parts, pending}。"""
        cfg = self.config_get()
        T = self.log_len()
        budget = limit or cfg["WAKE_LINES"]
        lines = []
        for lo, hi in self.cover(T, budget):
            if hi - lo == 1:
                lines.append("#%d %s %s" % self.log_get(lo))
            else:
                s = self.tree_get(lo, hi)
                if s is None:
                    nap = self.next_nap()
                    if nap:
                        return {"lines": lines, "blocked": True,
                                "nap_prompt": nap, "message":
                                "memory context needs #%d-%d, not compressed yet" % (lo, hi - 1)}
                    _die("The summary of #%d-%d is blank. forget %d-%d" % (lo, hi - 1, lo, hi - 1))
                lines.append("#%d-%d %s" % (lo, hi - 1, s))
        return {"lines": lines, "blocked": False,
                "pending": self.pending_count(),
                "nap_prompt": self.next_nap()}

    def nap(self, block: str, summary: str) -> dict:
        """提交压缩摘要。block 形如 '0-1'。返回 {ok, saved, pending, next}。"""
        cfg = self.config_get()
        lo, hi = _block_id(block)
        summary = _check(summary, cfg["ENTRY_CHARS"])
        todo = self.pending(limit=1)
        if not todo:
            return {"ok": False, "message": "Nothing left to compress."}
        if (lo, hi) != todo[0]:
            if self.tree_get(lo, hi) is not None:
                return {"ok": False, "message": "%d-%d is already settled." % (lo, hi - 1)}
            _die("Wrong block: %s. The next is %d-%d." % (block, todo[0][0], todo[0][1] - 1))
        ok = self.tree_put(lo, hi, summary)
        if not ok:
            return {"ok": False, "message": "%d-%d was settled or forgotten meanwhile." % (lo, hi - 1)}
        return {"ok": True, "saved": "%d-%d" % (lo, hi - 1),
                "pending": self.pending_count(),
                "next": self.next_nap()}

    def recall(self, regex: str, newest: int = 20000) -> dict:
        """正则搜索全部记忆。返回 {matches, hits, truncated}。"""
        try:
            pat = re.compile(regex, re.I)
        except re.error as e:
            _die("bad regex: %s" % e)
        hits, out, size = 0, deque(), 0
        for e in self.log_scan():
            line = "#%d %s %s" % e
            if not pat.search(line):
                continue
            hits += 1
            out.append(line)
            size += len(line.encode()) + 1
            while size > newest:
                size -= len(out.popleft().encode()) + 1
        return {"matches": list(out), "hits": hits,
                "truncated": len(out) < hits}

    def zoom(self, block: str) -> dict:
        """展开一个树节点，返回其两半。"""
        lo, hi = _block_id(block)
        T = self.log_len()
        if lo >= T:
            _die("#%s is beyond the memory: it holds %s." % (block, _plural(T, "memory")))
        mid = (lo + hi) // 2
        halves = []
        for a, b in ((lo, mid), (mid, hi)):
            if a >= T:
                continue
            if b - a == 1:
                halves.append({"block": "%d" % a, "line": "#%d %s %s" % self.log_get(a)})
            else:
                halves.append({"block": "%d-%d" % (a, b - 1),
                               "line": "#%d-%d %s" % (a, b - 1, self.tree_get(a, b)
                                                      or "not compressed yet")})
        return {"block": block, "halves": halves}

    def forget(self, block: str) -> dict:
        """删除坏摘要（及上层），LOG 不动可重建。"""
        lo, hi = _block_id(block)
        gone = self.tree_drop(lo, hi)
        if not gone:
            _die("No summary at %s." % block)
        return {"forgotten": ["%d-%d" % (a, b - 1) for a, b in gone],
                "message": "forgot %d-%d up; run nap to rebuild" % (gone[0][0], gone[0][1] - 1)}

    def import_lines(self, lines: list[tuple[str, str]]) -> dict:
        """批量导入 [(YYYY-MM-DD, text), ...]（引导历史身份用一次）。"""
        cfg = self.config_get()
        chars = cfg["ENTRY_CHARS"]
        last = self.log_get(self.log_len() - 1)[1] if self.log_len() else "0000-00-00"
        out = []
        for date, text in lines:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                _die("expected 'YYYY-MM-DD', got: %s" % date)
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                _die("%s is not a real date." % date)
            if date < last:
                _die("date %s precedes the previous memory (%s)." % (date, last))
            text = text.strip()
            if not text or len(text.encode()) > chars:
                _die("%d bytes, limit %d." % (len(text.encode()), chars))
            out.append((date, text))
            last = date
        if not out:
            _die("no memories.")
        base = self.log_append(out)
        return {"first": base, "count": len(out),
                "pending": self.pending_count()}


# ─────────────────────────────── 便捷函数 ───────────────────────────────
def open_memory(memory_dir: str | None = None) -> OptMemStore:
    """打开（必要时创建）记忆库。"""
    m = OptMemStore(memory_dir)
    if not os.path.isdir(m.dir):
        m.init()
    return m
