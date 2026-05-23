import os
import shutil
from datetime import datetime

from database import DB_PATH

_BACKUP_DIR = os.path.join(os.path.dirname(DB_PATH), "Backup")
_MAX_BACKUPS = 30


def _ensure_dir():
    os.makedirs(_BACKUP_DIR, exist_ok=True)


def list_backups():
    """返回备份文件列表，按时间从新到旧排序"""
    _ensure_dir()
    files = []
    for f in os.listdir(_BACKUP_DIR):
        if f.startswith("schedule_") and f.endswith(".db"):
            path = os.path.join(_BACKUP_DIR, f)
            files.append(path)
    files.sort(reverse=True)
    return files


def _make_backup():
    """创建一个备份，返回备份文件路径"""
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(_BACKUP_DIR, f"schedule_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def _clean_old():
    """保留最新的 MAX_BACKUPS 份，删除更早的"""
    files = list_backups()
    for old_file in files[_MAX_BACKUPS:]:
        try:
            os.remove(old_file)
        except OSError:
            pass


def auto_backup():
    """启动时自动备份，同一天只备份一次"""
    if not os.path.exists(DB_PATH):
        return
    today = datetime.now().strftime("%Y%m%d")
    backups = list_backups()
    for b in backups:
        if os.path.basename(b).startswith(f"schedule_{today}"):
            return
    _make_backup()
    _clean_old()


def manual_backup():
    """手动备份，始终创建新文件，返回备份路径"""
    if not os.path.exists(DB_PATH):
        raise Exception("数据库文件不存在")
    path = _make_backup()
    _clean_old()
    return path


def restore_backup(backup_path):
    """用备份文件替换当前数据库"""
    if not os.path.exists(backup_path):
        raise Exception("备份文件不存在")
    shutil.copy2(backup_path, DB_PATH)
