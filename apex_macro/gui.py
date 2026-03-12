"""
gui.py — Apex 抖枪宏 tkinter 界面

提供：主开关、LMD 参数调节滑块、进程监控开关、实时状态显示。
界面每 300ms 轮询一次引擎状态并更新标签颜色。
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from apex_macro.macro_engine import MacroEngine, TARGET_PROCESS

if TYPE_CHECKING:
    pass


class MacroGUI:
    """tkinter 主窗口，持有 MacroEngine 引用并展示实时状态。"""

    def __init__(self, engine: MacroEngine) -> None:
        self.engine = engine

        # ── 根窗口配置 ──
        self.root = tk.Tk()
        self.root.title("Apex 抖枪宏")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")  # 深色背景

        # ── Tkinter 变量（与 UI 控件双向绑定） ──
        self.enabled_var = tk.BooleanVar(value=False)
        self.monitor_var = tk.BooleanVar(value=True)
        self.lmd_var = tk.DoubleVar(value=0.5)

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_status_update()

    # ──────────────────────────────────────────────
    # UI 构建
    # ──────────────────────────────────────────────
    def _build_ui(self) -> None:
        BG = "#1e1e2e"
        FG = "#cdd6f4"
        ACCENT = "#89b4fa"
        GREEN = "#a6e3a1"
        RED = "#f38ba8"
        YELLOW = "#f9e2af"
        PANEL = "#313244"
        FONT_TITLE = ("Segoe UI", 13, "bold")
        FONT_LABEL = ("Segoe UI", 9)
        FONT_VAL = ("Segoe UI", 9, "bold")

        pad = {"padx": 14, "pady": 4}

        # ── 标题 ──
        tk.Label(
            self.root, text="🎮  Apex 抖枪宏",
            bg=BG, fg=ACCENT, font=FONT_TITLE,
        ).pack(fill="x", padx=14, pady=(14, 6))

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10)

        # ── 主开关 ──
        frame_switch = tk.Frame(self.root, bg=BG)
        frame_switch.pack(fill="x", **pad)
        tk.Label(frame_switch, text="启用宏", bg=BG, fg=FG, font=FONT_LABEL).pack(side="left")
        self.btn_enable = tk.Button(
            frame_switch, text="● 未启用",
            bg=PANEL, fg=RED, relief="flat", font=FONT_VAL,
            activebackground=PANEL, cursor="hand2",
            command=self._toggle_enabled,
        )
        self.btn_enable.pack(side="right")

        # ── LMD 滑块 ──
        frame_lmd = tk.Frame(self.root, bg=PANEL, bd=0, relief="flat")
        frame_lmd.pack(fill="x", padx=14, pady=6)

        header = tk.Frame(frame_lmd, bg=PANEL)
        header.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(header, text="LMD（灵敏度倍数）", bg=PANEL, fg=FG, font=FONT_LABEL).pack(side="left")
        self.lbl_lmd_val = tk.Label(header, text="0.50", bg=PANEL, fg=ACCENT, font=FONT_VAL)
        self.lbl_lmd_val.pack(side="right")

        self.scale_lmd = tk.Scale(
            frame_lmd, from_=0.1, to=3.0, resolution=0.05,
            orient="horizontal", variable=self.lmd_var,
            bg=PANEL, fg=FG, troughcolor="#45475a",
            highlightthickness=0, showvalue=False,
            command=self._on_lmd_change,
        )
        self.scale_lmd.pack(fill="x", padx=10, pady=(0, 4))

        # 实时参数预览
        frame_params = tk.Frame(frame_lmd, bg=PANEL)
        frame_params.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(frame_params, text="Range:", bg=PANEL, fg=FG, font=FONT_LABEL).pack(side="left")
        self.lbl_range = tk.Label(frame_params, text="18", bg=PANEL, fg=YELLOW, font=FONT_VAL)
        self.lbl_range.pack(side="left", padx=(2, 12))
        tk.Label(frame_params, text="Decline:", bg=PANEL, fg=FG, font=FONT_LABEL).pack(side="left")
        self.lbl_decline = tk.Label(frame_params, text="3.00 ms", bg=PANEL, fg=YELLOW, font=FONT_VAL)
        self.lbl_decline.pack(side="left", padx=(2, 0))

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10, pady=2)

        # ── 进程监控开关 ──
        frame_proc = tk.Frame(self.root, bg=BG)
        frame_proc.pack(fill="x", **pad)
        tk.Label(
            frame_proc, text=f"进程监控  ({TARGET_PROCESS})",
            bg=BG, fg=FG, font=FONT_LABEL,
        ).pack(side="left")
        self.btn_monitor = tk.Button(
            frame_proc, text="● 已开启",
            bg=PANEL, fg=GREEN, relief="flat", font=FONT_VAL,
            activebackground=PANEL, cursor="hand2",
            command=self._toggle_monitor,
        )
        self.btn_monitor.pack(side="right")

        # ── 调试模式按钮 ──
        frame_debug = tk.Frame(self.root, bg=BG)
        frame_debug.pack(fill="x", **pad)
        tk.Label(
            frame_debug, text="调试模式  (仅左键触发，无需右键)",
            bg=BG, fg="#fab387", font=FONT_LABEL,
        ).pack(side="left")
        self.btn_debug = tk.Button(
            frame_debug, text="● 已关闭",
            bg=PANEL, fg="#585b70", relief="flat", font=FONT_VAL,
            activebackground=PANEL, cursor="hand2",
            command=self._toggle_debug,
        )
        self.btn_debug.pack(side="right")

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10, pady=2)

        # ── 状态面板 ──
        frame_status = tk.Frame(self.root, bg=PANEL)
        frame_status.pack(fill="x", padx=14, pady=6)
        tk.Label(frame_status, text="运行状态", bg=PANEL, fg=FG, font=FONT_LABEL).pack(
            anchor="w", padx=10, pady=(6, 2)
        )

        row1 = tk.Frame(frame_status, bg=PANEL)
        row1.pack(fill="x", padx=10, pady=1)
        tk.Label(row1, text="宏状态：", bg=PANEL, fg=FG, font=FONT_LABEL).pack(side="left")
        self.lbl_status = tk.Label(row1, text="未启用", bg=PANEL, fg=RED, font=FONT_VAL)
        self.lbl_status.pack(side="left")

        row2 = tk.Frame(frame_status, bg=PANEL)
        row2.pack(fill="x", padx=10, pady=1)
        tk.Label(row2, text="进程状态：", bg=PANEL, fg=FG, font=FONT_LABEL).pack(side="left")
        self.lbl_proc = tk.Label(row2, text="监控中…", bg=PANEL, fg=YELLOW, font=FONT_VAL)
        self.lbl_proc.pack(side="left")

        row3 = tk.Frame(frame_status, bg=PANEL)
        row3.pack(fill="x", padx=10, pady=(1, 8))
        tk.Label(row3, text="Alt 冻结：", bg=PANEL, fg=FG, font=FONT_LABEL).pack(side="left")
        self.lbl_alt = tk.Label(row3, text="否", bg=PANEL, fg=GREEN, font=FONT_VAL)
        self.lbl_alt.pack(side="left")

        # ── 底部提示 ──
        tk.Label(
            self.root,
            text="触发：右键 + 左键  │  Alt = 冻结",
            bg=BG, fg="#585b70", font=("Segoe UI", 8),
        ).pack(pady=(2, 10))

    # ──────────────────────────────────────────────
    # 控件回调
    # ──────────────────────────────────────────────
    def _toggle_enabled(self) -> None:
        self.engine.enabled = not self.engine.enabled
        enabled = self.engine.enabled
        self.btn_enable.config(
            text="● 已启用" if enabled else "● 未启用",
            fg="#a6e3a1" if enabled else "#f38ba8",
        )

    def _toggle_monitor(self) -> None:
        self.engine.process_monitor_enabled = not self.engine.process_monitor_enabled
        on = self.engine.process_monitor_enabled
        self.btn_monitor.config(
            text="● 已开启" if on else "● 已关闭",
            fg="#a6e3a1" if on else "#f38ba8",
        )

    def _toggle_debug(self) -> None:
        self.engine.debug_mode = not self.engine.debug_mode
        on = self.engine.debug_mode
        self.btn_debug.config(
            text="● 已开启" if on else "● 已关闭",
            fg="#fab387" if on else "#585b70",  # 橙色=开启，灰色=关闭
        )

    def _on_lmd_change(self, val: str) -> None:
        """LMD 滑块拖动时实时同步引擎参数并刷新显示。"""
        lmd = float(val)
        self.engine.lmd = lmd
        self.lbl_lmd_val.config(text=f"{lmd:.2f}")
        self.lbl_range.config(text=str(self.engine.range))
        self.lbl_decline.config(text=f"{self.engine.decline_range:.2f} ms")

    # ──────────────────────────────────────────────
    # 状态轮询（300ms 刷新）
    # ──────────────────────────────────────────────
    def _schedule_status_update(self) -> None:
        self._update_status()
        self.root.after(300, self._schedule_status_update)

    def _update_status(self) -> None:
        """更新运行状态标签。"""
        GREEN = "#a6e3a1"
        RED = "#f38ba8"
        YELLOW = "#f9e2af"
        BLUE = "#89dceb"

        # 宏状态
        if self.engine.shake_active:
            self.lbl_status.config(text="抖动中 ●", fg=GREEN)
        elif self.engine.enabled:
            self.lbl_status.config(text="已启用（等待触发）", fg=BLUE)
        else:
            self.lbl_status.config(text="未启用", fg=RED)

        # 进程状态
        if not self.engine.process_monitor_enabled:
            self.lbl_proc.config(text="监控已关闭", fg="#585b70")
        elif self.engine.process_running:
            self.lbl_proc.config(text=f"{TARGET_PROCESS} 运行中", fg=GREEN)
        else:
            self.lbl_proc.config(text=f"{TARGET_PROCESS} 未检测到", fg=RED)

        # Alt 冻结
        if self.engine.alt_pressed:
            self.lbl_alt.config(text="是 ❄", fg=YELLOW)
        else:
            self.lbl_alt.config(text="否", fg=GREEN)

    # ──────────────────────────────────────────────
    # 生命周期
    # ──────────────────────────────────────────────
    def _on_close(self) -> None:
        """窗口关闭时停止引擎，清理所有后台线程。"""
        self.engine.stop()
        self.root.destroy()

    def run(self) -> None:
        """阻塞运行 tkinter 主循环。"""
        self.root.mainloop()
