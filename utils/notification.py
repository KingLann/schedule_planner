import winsound
from winotify import Notification


def send_toast(title, msg, app_name="DayFlow"):
    """发送 Windows Toast 通知 + 系统提示音"""
    # 先播放系统提示音，确保用户能感知到通知
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

    try:
        toast = Notification(
            app_id=app_name,
            title=title,
            msg=msg,
            duration="long",
        )
        toast.show()
    except Exception:
        pass
