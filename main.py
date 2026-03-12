"""
main.py — Apex 抖枪宏程序入口

用法：
    python main.py

依赖安装：
    pip install -r requirements.txt
"""

from apex_macro.macro_engine import MacroEngine
from apex_macro.gui import MacroGUI


def main() -> None:
    engine = MacroEngine()
    engine.start()          # 启动全局监听器和进程监控线程

    gui = MacroGUI(engine)  # 构建 GUI（窗口关闭时自动调用 engine.stop()）
    gui.run()               # 阻塞直到窗口关闭


if __name__ == "__main__":
    main()
