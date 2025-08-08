# config.py

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''               # ganti jika ada password
MYSQL_DB = 'pointmarket_rl'
MYSQL_PORT = 3306

# Tambahan wajib agar tidak kena KeyError
MYSQL_UNIX_SOCKET = None
MYSQL_CONNECT_TIMEOUT = 10
MYSQL_READ_DEFAULT_FILE = None
MYSQL_USE_UNICODE = True
MYSQL_CHARSET = 'utf8mb4'
MYSQL_SQL_MODE = None
MYSQL_CURSORCLASS = 'DictCursor'
MYSQL_AUTOCOMMIT = True
MYSQL_CUSTOM_OPTIONS = {}  # ✅ TAMBAHKAN INI
SECRET_KEY = 'rahasia_super_aman'
