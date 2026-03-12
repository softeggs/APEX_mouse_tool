# Apex 抖枪宏（Python 通用版）

> 原始版本基于 Logitech GHub Lua 脚本，**本版本使用 Python 重写，适用于所有鼠标**。

---

## 功能特性

- 🖱️ **核心抖动机制**：完整复现 Lua 原版左右抖动 + 下压补偿逻辑
- ⚙️ **LMD 参数实时调节**：滑块控制抖动幅度，数值实时预览
- 🔛 **主开关**：一键启用 / 禁用整个宏
- ❄️ **Alt 冻结**：按住 `Alt` 时脚本效果暂停，松开自动恢复
- 🔍 **进程监控**：后台检测 `r5apex.exe`（每 60s 一次），未检测到游戏时宏不生效
- 🪲 **调试模式**：去除右键触发条件，仅需左键即可测试抖动效果

---

## 触发条件（正常模式）

```
启用宏（GUI开关） + 鼠标右键按住 + 鼠标左键按住
```

> 进程监控开启时，还需 `r5apex.exe` 正在运行。  
> 按住 `Alt` 时效果临时冻结。

---

## 参数说明

| 参数 | 公式 | 默认值（LMD=0.5） |
|---|---|---|
| LMD | 用户调节（0.1 ~ 3.0） | 0.5 |
| Range（抖动幅度） | `int(8 // LMD) + 2` | 18 px |
| Decline_range（补偿阈值） | `6 × LMD` | 3.0 ms |
| Frequency（抖动间隔） | 固定 | 5 ms |

---

## 项目结构

```
apex----main/
├── main.py                   # 程序入口
├── test_shake.py             # 抖动效果可视化测试工具
├── requirements.txt          # 依赖列表
├── re抖枪宏）.lua            # 原始 Logitech Lua 脚本（参考）
└── apex_macro/
    ├── macro_engine.py       # 核心引擎（监听/抖动/进程监控）
    └── gui.py                # tkinter 界面
```

---

## 安装与运行

```bash
# 1. 安装依赖（使用目标 Python 解释器）
C:/Python313/python.exe -m pip install pynput psutil

# 2. 启动主程序
C:/Python313/python.exe main.py

# 3.（可选）验证抖动效果
C:/Python313/python.exe test_shake.py
```

---

## 验证抖动效果

在 Paint 等应用中，Windows 会合并高频鼠标消息导致锯齿不可见。推荐使用内置测试工具：

1. 运行 `test_shake.py`
2. 启用主程序中的**调试模式**（去除右键条件）
3. 在黑色画布内**按住左键拖动** → 出现锯齿线即为生效

---

## 注意事项

- 部分系统环境下 pynput 全局监听需要**以管理员身份运行**
- `pip install` 须使用与运行脚本**相同的 Python 解释器**（如系统同时安装了 Anaconda 和 Python 3.13，须区分）
- 本工具仅供学习与研究用途
