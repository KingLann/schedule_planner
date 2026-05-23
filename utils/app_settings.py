import json
import os
import sys
import winreg

_APP_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SchedulePlanner')
_CONFIG_DIR = os.path.join(_APP_DIR, 'config')
_CONFIG_FILE = os.path.join(_CONFIG_DIR, 'app_settings.json')
_APP_NAME = "SchedulePlanner"

_DEFAULTS = {
    "auto_start": False,
    "minimize_to_tray": False,
    "silent_start": False,
    "notification_enabled": False,
    "reminder_minutes": 15,
    "checkin_reminder_time": "21:00",
    "daily_task_reminder_time": "08:00",
    "reminder_repeat_interval": 5,
    "reminder_max_count": 0,
}


def _ensure_config_dir():
    os.makedirs(_CONFIG_DIR, exist_ok=True)


def _load():
    _ensure_config_dir()
    if not os.path.exists(_CONFIG_FILE):
        return dict(_DEFAULTS)
    try:
        with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 补齐缺失的默认值
        for k, v in _DEFAULTS.items():
            data.setdefault(k, v)
        return data
    except (json.JSONDecodeError, IOError):
        return dict(_DEFAULTS)


def _save(data):
    _ensure_config_dir()
    tmp_file = _CONFIG_FILE + ".tmp"
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, _CONFIG_FILE)


def get_setting(key, default=None):
    data = _load()
    return data.get(key, default)


def set_setting(key, value):
    data = _load()
    data[key] = value
    _save(data)


# --- 开机自启 (Windows 注册表) ---

def _get_exe_path():
    """获取当前可执行文件路径（支持 PyInstaller 打包后运行）"""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


def set_auto_start(enabled):
    """写入或删除注册表开机自启项"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            exe_path = _get_exe_path()
            # 如果是 .py 脚本，用 pythonw 运行避免弹出控制台
            if exe_path.endswith('.py'):
                cmd = f'pythonw "{exe_path}"'
            else:
                cmd = f'"{exe_path}"'
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, _APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def is_auto_start():
    """从注册表读取是否已设置开机自启"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, _APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False
