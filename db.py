import pymysql
from dbutils.pooled_db import PooledDB
import os

class Db:
    _pool = None

    @classmethod
    def init(cls, host, user, password, database, maxconnections=10):
        # Перехватываем переменные из Railway, если они есть.
        # Если их нет (например, на локальном ПК), используем то, что передал разработчик.
        db_host = os.environ.get("MYSQLHOST", host)
        db_user = os.environ.get("MYSQLUSER", user)
        db_pass = os.environ.get("MYSQLPASSWORD", password)
        db_name = os.environ.get("MYSQLDATABASE", database)
        db_port = int(os.environ.get("MYSQLPORT", 3306))

        cls._pool = PooledDB(
            creator=pymysql,
            maxconnections=maxconnections,
            mincached=2,
            maxcached=5,
            blocking=True,
            autocommit=False,
            cursorclass=pymysql.cursors.DictCursor,
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name,
            port=db_port, # Добавили порт специально для Railway
            charset="utf8mb4"
        )

    @classmethod
    def get_connection(cls):
        if not cls._pool:
            raise Exception("Не получилось синициализировать пул соединений")
        return cls._pool.connection()