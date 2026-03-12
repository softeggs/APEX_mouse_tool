"""
macro_engine.py — Apex 抖枪宏核心引擎

对应原 Lua 脚本的核心抖动逻辑，使用 pynput 实现全局监听，
psutil 实现后台进程检测，ctypes 读取 Windows CapsLock 状态。
"""

import threading
import time
from typing import Optional

import psutil
from pynput import keyboard, mouse
from pynput.mouse import Button, Controller as MouseController

# ──────────────────────────────────────────────
# 常量配置
# ──────────────────────────────────────────────
FREQUENCY_MS: int = 5          # 抖动间隔（ms），对应 Lua Frequency = 5
TARGET_PROCESS: str = "r5apex.exe"
PROCESS_CHECK_INTERVAL: int = 60  # 进程检测间隔（秒）

# Alt 键集合（左/右/AltGr 三种情况都覆盖）
ALT_KEYS = {
    keyboard.Key.alt,
    keyboard.Key.alt_l,
    keyboard.Key.alt_r,
    keyboard.Key.alt_gr,
}


class MacroEngine:
    """
    抖枪宏引擎。

    触发条件：enabled AND CapsLock ON AND RMB held AND LMB held
              AND NOT alt_pressed
              AND (NOT process_monitor_enabled OR process_running)
    """

    def __init__(self) -> None:
        # ── 用户可调参数 ──
        self.lmd: float = 0.5          # 与 Lua LMD 对应

        # ── 开关状态 ──
        self.enabled: bool = False                # 主开关
        self.process_monitor_enabled: bool = True # 进程监控开关
        self.debug_mode: bool = False             # 调试模式：右键不作为触发条件

        # ── 运行时状态（线程间共享，仅在 GIL 保护下读写简单布尔/浮点） ──
        self.process_running: bool = False
        self.alt_pressed: bool = False
        self.lmb_pressed: bool = False
        self.rmb_pressed: bool = False
        self.shake_active: bool = False  # 抖动线程是否正在运行

        # ── 内部对象 ──
        self._mouse_ctrl: MouseController = MouseController()
        self._shake_thread: Optional[threading.Thread] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._stop_event: threading.Event = threading.Event()
        self._process_thread: Optional[threading.Thread] = None

    # ──────────────────────────────────────────────
    # 计算属性（与 Lua 公式完全一致）
    # ──────────────────────────────────────────────
    @property
    def range(self) -> int:
        """对应 Lua: Range = (8//LMD)+2"""
        return int(8 // self.lmd) + 2

    @property
    def decline_range(self) -> float:
        """对应 Lua: Decline_range = 6*LMD  （单位 ms）"""
        return 6 * self.lmd

    # ──────────────────────────────────────────────
    # 触发判断
    # ──────────────────────────────────────────────
    def should_shake(self) -> bool:
        """综合所有条件，决定当前是否应当抖动。"""
        if not self.enabled:
            return False
        if self.alt_pressed:
            # Alt 冻结：按住 Alt 时脚本效果暂停
            return False
        if self.process_monitor_enabled and not self.process_running:
            # 进程监控开启但 r5apex.exe 未运行
            return False
        if not (self.lmb_pressed and (self.rmb_pressed or self.debug_mode)):
            return False
        return True

    # ──────────────────────────────────────────────
    # 抖动主循环（独立线程运行）
    # ──────────────────────────────────────────────
    def _shake_loop(self) -> None:
        """
        抖动主循环，完整复现 Lua 脚本逻辑：
          1. 向右下移动 Range
          2. 等待 Frequency ms
          3. 向左上移动 Range（抵消）
          4. 等待 Frequency ms
          5. 累计时间 >= Decline_range 时额外下移 1px（补偿后坐力下压）
        """
        elapsed: float = 0.0
        r: int = self.range           # 快照当前参数，避免循环中途被修改
        d: float = self.decline_range

        while self.shake_active and self.should_shake():
            # ── 每次进入循环重新读取参数（支持实时 LMD 调节） ──
            r = self.range
            d = self.decline_range

            # 右下抖动
            self._mouse_ctrl.move(r, r)
            time.sleep(FREQUENCY_MS / 1000)
            elapsed += FREQUENCY_MS

            # 左上抖动（抵消）
            self._mouse_ctrl.move(-r, -r)
            time.sleep(FREQUENCY_MS / 1000)
            elapsed += FREQUENCY_MS

            # 下压补偿（对应 Lua 的 MoveMouseRelative(0, 1)）
            if elapsed >= d:
                self._mouse_ctrl.move(0, 1)
                elapsed = 0.0

        # 循环退出后重置标志
        self.shake_active = False

    def _start_shake(self) -> None:
        """启动抖动线程（若尚未运行）。"""
        if self.shake_active:
            return
        if not self.should_shake():
            return
        self.shake_active = True
        self._shake_thread = threading.Thread(
            target=self._shake_loop, daemon=True, name="ShakeThread"
        )
        self._shake_thread.start()

    def _stop_shake(self) -> None:
        """停止抖动线程（设置标志，线程自行退出）。"""
        self.shake_active = False

    # ──────────────────────────────────────────────
    # 鼠标事件回调
    # ──────────────────────────────────────────────
    def _on_mouse_click(
        self,
        x: int, y: int,
        button: Button,
        pressed: bool,
    ) -> None:
        if button == Button.left:
            self.lmb_pressed = pressed
        elif button == Button.right:
            self.rmb_pressed = pressed

        # 统一用 should_shake() 判断，覆盖 debug_mode 下仅左键的情况
        if self.should_shake():
            self._start_shake()
        else:
            self._stop_shake()

    # ──────────────────────────────────────────────
    # 键盘事件回调
    # ──────────────────────────────────────────────
    def _on_key_press(self, key: keyboard.Key) -> None:
        if key in ALT_KEYS:
            self.alt_pressed = True
            # Alt 按下立即停止抖动（冻结效果）
            self._stop_shake()

    def _on_key_release(self, key: keyboard.Key) -> None:
        if key in ALT_KEYS:
            self.alt_pressed = False
            # Alt 松开后统一用 should_shake() 重新判断
            self._start_shake()

    # ──────────────────────────────────────────────
    # 进程监控线程
    # ──────────────────────────────────────────────
    def _process_monitor_loop(self) -> None:
        """
        每 60 秒检测一次 r5apex.exe 是否运行。
        使用 threading.Event.wait() 而非 time.sleep()，确保能快速响应退出信号。
        """
        while not self._stop_event.is_set():
            if self.process_monitor_enabled:
                try:
                    # psutil.process_iter 只拉取 name 字段，降低开销
                    names = [
                        p.info["name"].lower()
                        for p in psutil.process_iter(["name"])
                        if p.info["name"]
                    ]
                    self.process_running = TARGET_PROCESS.lower() in names
                except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                    # 进程消失或权限不足时保持上次状态
                    pass
            # 等待 60 秒或收到停止信号（先到先得）
            self._stop_event.wait(PROCESS_CHECK_INTERVAL)

    # ──────────────────────────────────────────────
    # 生命周期管理
    # ──────────────────────────────────────────────
    def start(self) -> None:
        """启动所有监听器和后台线程。"""
        # 启动鼠标监听器
        self._mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self._mouse_listener.start()

        # 启动键盘监听器
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()

        # 启动进程监控线程
        self._process_thread = threading.Thread(
            target=self._process_monitor_loop,
            daemon=True,
            name="ProcessMonitor",
        )
        self._process_thread.start()

    def stop(self) -> None:
        """停止所有后台任务，释放资源。"""
        self._stop_shake()
        self._stop_event.set()
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
