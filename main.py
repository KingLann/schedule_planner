import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# database.py 模块级已调用 init_db()，无需重复调用
from database import init_db  # noqa: F401 - 确保模块加载

# 启动时自动备份
from utils.backup import auto_backup
auto_backup()

from views.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.run()