# a11y 可访问性指南

## 门禁规则
- CI自动运行 axe-core 扫描4个核心页面
- critical/serious violations=0 阻断合并
- 违反时CI红色, 修复后绿色

## 本地运行
```bash
cd frontend && npm run test:a11y
```

## 参考
- WCAG 2.1 AA 标准
- axe-core 规则集
