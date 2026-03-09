import pymysql
from dbutils.pooled_db import PooledDB

class Db:
    _pool = None

    @classmethod
    def init(cls, host, user, password, database, port=3306, maxconnections=5):
        """Инициализация пула соединений с явным указанием порта"""
        cls._pool = PooledDB(
            creator=pymysql,
            maxconnections=maxconnections,
            mincached=2,
            maxcached=5,
            blocking=True,
            host=host,
            user=user,
            password=password,
            database=database,
            port=int(port), # Это заставит скрипт использовать порт Railway
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            raise Exception("Database not initialized. Call Db.init() first.")
        return cls._pool.connection()