import threading
import pystray
from PIL import Image


_tray_icon = None


def create_tray(icon_path, on_show, on_quit):
    """创建系统托盘图标。

    Args:
        icon_path: .ico 文件路径
        on_show: 点击"显示主窗口"时的回调
        on_quit: 点击"退出"时的回调
    """
    global _tray_icon

    try:
        image = Image.open(icon_path)
    except Exception:
        # 如果图标加载失败，创建一个简单的纯色图标
        image = Image.new('RGB', (64, 64), color=(99, 102, 241))

    menu = pystray.Menu(
        pystray.MenuItem("显示主窗口", lambda icon, item: on_show()),
        pystray.MenuItem("退出", lambda icon, item: on_quit()),
    )

    _tray_icon = pystray.Icon(
        name="SchedulePlanner",
        icon=image,
        title="日程记事本",
        menu=menu,
    )

    # pystray.run() 是阻塞的，放到后台线程
    thread = threading.Thread(target=_tray_icon.run, daemon=True)
    thread.start()


def destroy_tray():
    """销毁系统托盘图标"""
    global _tray_icon
    if _tray_icon:
        try:
            _tray_icon.stop()
        except Exception:
            pass
        _tray_icon = None
