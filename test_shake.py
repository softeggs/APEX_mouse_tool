"""
test_shake.py — 鼠标轨迹实时可视化工具

原理：每 8ms 主动轮询 GetCursorPos（而非依赖 WM_MOUSEMOVE），
     因此不受 GDI 消息合并影响，能准确反映抖动效果。

用法：
    1. 运行 main.py 开启宏（启用 + 调试模式 + 关进程监控）
    2. 运行本脚本
    3. 在黑色画布内按住左键拖动 → 若出现锯齿轨迹则抖动生效
    4. 右键单击清空轨迹
"""

import tkinter as tk
from pynput.mouse import Controller

CANVAS_W = 700
CANVAS_H = 500
POLL_MS = 8       # 轮询间隔，远低于 5ms 抖动周期，确保不漏点
TRAIL_COLOR = "#89b4fa"
BG_COLOR = "#1e1e2e"


def main() -> None:
    mouse = Controller()
    last: list = [None, None]  # 上一个画布内坐标

    root = tk.Tk()
    root.title("鼠标抖动轨迹测试")
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)

    tk.Label(
        root,
        text="在下方黑色区域内 按住左键拖动 → 查看是否出现锯齿轨迹（右键清空）",
        bg=BG_COLOR, fg="#cdd6f4", font=("Segoe UI", 9),
    ).pack(pady=(10, 4))

    canvas = tk.Canvas(root, bg="black", width=CANVAS_W, height=CANVAS_H,
                       highlightthickness=0)
    canvas.pack(padx=14, pady=(0, 6))

    tk.Label(
        root,
        text="锯齿 = 抖动生效 ✅    直线 = 未生效 ❌",
        bg=BG_COLOR, fg="#585b70", font=("Segoe UI", 8),
    ).pack(pady=(0, 10))

    def update() -> None:
        # 主动轮询光标绝对坐标，转换为画布本地坐标
        cx = root.winfo_pointerx() - canvas.winfo_rootx()
        cy = root.winfo_pointery() - canvas.winfo_rooty()

        if 0 <= cx <= CANVAS_W and 0 <= cy <= CANVAS_H:
            if last[0] is not None:
                canvas.create_line(
                    last[0], last[1], cx, cy,
                    fill=TRAIL_COLOR, width=2,
                )
            last[0] = cx
            last[1] = cy
        else:
            # 光标离开画布时重置，避免跨区域连线
            last[0] = None
            last[1] = None

        root.after(POLL_MS, update)

    def clear(_event=None) -> None:
        canvas.delete("all")
        last[0] = None
        last[1] = None

    canvas.bind("<Button-3>", clear)

    update()
    root.mainloop()


if __name__ == "__main__":
    main()
