# Folo设计Token接入说明

## 文件位置
- folo-design-tokens.css 在项目根目录

## 接入方式
在 frontend/src/index.css 或 tailwind.css 中 import:
  @import '../../folo-design-tokens.css';

或者拷贝所需Token到现有的CSS变量定义中。

## 覆盖的Token
- 12个Apple UIKit系统色（red/orange/yellow/green/mint/teal/cyan/blue/indigo/purple/pink/brown）
- 5级填充层（fill-primary 到 fill-quaternary）
- 5级材质层（material-ultra-thick 到 material-ultra-thin）
- 4级文字色（text-primary 到 text-quaternary）
- 6个界面组件色（sidebar/tooltip/menu/popover/titlebar/selection）
- 完整 Dark Mode 支持
