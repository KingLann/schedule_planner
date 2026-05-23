import os
import hashlib
import hmac
import secrets

_APP_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SchedulePlanner')
_CONFIG_DIR = os.path.join(_APP_DIR, 'config')

CONFIG_FILE = os.path.join(_CONFIG_DIR, 'diary_password.txt')
SECURITY_FILE = os.path.join(_CONFIG_DIR, 'security_question.txt')


def ensure_config_dir():
    os.makedirs(_CONFIG_DIR, exist_ok=True)


def _hash_password(password, salt=None):
    """使用 PBKDF2-SHA256 + 随机盐哈希密码，返回 'pbkdf2:sha256$salt$hash' 格式"""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"pbkdf2:sha256${salt}${dk.hex()}"


def _verify_password(password, stored):
    """验证密码，兼容旧版 SHA-256 格式"""
    if stored.startswith("pbkdf2:sha256$"):
        parts = stored.split("$", 2)
        if len(parts) != 3:
            return False
        salt = parts[1]
        expected = parts[2]
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(dk.hex(), expected)
    else:
        # 兼容旧版无盐 SHA-256
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(hashed, stored)


def set_password(password):
    ensure_config_dir()
    hashed = _hash_password(password)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(hashed)
    return True


def get_password_hash():
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def check_password(password):
    stored_hash = get_password_hash()
    if stored_hash is None:
        return True  # 没有设置密码，直接通过
    return _verify_password(password, stored_hash)


def has_password():
    return get_password_hash() is not None


def remove_password():
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    if os.path.exists(SECURITY_FILE):
        os.remove(SECURITY_FILE)


def set_security_question(question, answer):
    ensure_config_dir()
    hashed_answer = _hash_password(answer)
    with open(SECURITY_FILE, 'w', encoding='utf-8') as f:
        f.write(f"{question}\n{hashed_answer}")
    return True


def get_security_question():
    ensure_config_dir()
    if os.path.exists(SECURITY_FILE):
        with open(SECURITY_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 1:
                return lines[0].strip()
    return None


def check_security_answer(answer):
    ensure_config_dir()
    if os.path.exists(SECURITY_FILE):
        with open(SECURITY_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                stored_hash = lines[1].strip()
                return _verify_password(answer, stored_hash)
    return False


def has_security_question():
    return get_security_question() is not None
