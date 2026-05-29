"""
数据导入模块

实现清洗后数据的批量导入到MySQL数据库，支持导入验证和SQLite降级方案。

需求：3.1, 3.2, 3.3
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from config import (
    MYSQL_CONNECTION_STRING,
    SCHEMA_SQL_PATH,
    SQLITE_CONNECTION_STRING,
    SQLITE_DB_PATH,
)

logger = logging.getLogger(__name__)


class DBImporter:
    """MySQL数据导入模块

    负责将清洗后的DataFrame数据批量导入MySQL数据库，
    支持导入验证和MySQL不可用时降级为SQLite。

    Attributes:
        connection_string: 数据库连接字符串（支持mysql+pymysql://和sqlite:///）
        engine: SQLAlchemy数据库引擎
        is_sqlite: 是否使用SQLite降级方案
    """

    # price_data表的列映射（DataFrame列名 -> 数据库列名）
    PRICE_COLUMNS = [
        "product_name",
        "product_category",
        "market_name",
        "region",
        "date",
        "highest_price",
        "lowest_price",
        "average_price",
        "unit",
    ]

    # weather_data表的列映射
    WEATHER_COLUMNS = [
        "region",
        "date",
        "average_temperature",
        "highest_temperature",
        "lowest_temperature",
        "rainfall",
        "humidity",
        "sunshine_duration",
        "weather_condition",
    ]

    def __init__(self, connection_string: str):
        """初始化数据库连接

        Args:
            connection_string: SQLAlchemy格式的数据库连接字符串
                MySQL示例: mysql+pymysql://user:pass@host:port/db?charset=utf8mb4
                SQLite示例: sqlite:///path/to/db.sqlite
        """
        self.connection_string = connection_string
        self.is_sqlite = connection_string.startswith("sqlite")
        self._engine = None

    @property
    def engine(self):
        """延迟创建数据库引擎"""
        if self._engine is None:
            self._engine = create_engine(self.connection_string)
        return self._engine

    def create_tables(self) -> None:
        """根据schema.sql创建数据库表

        对于MySQL，直接执行schema.sql中的SQL语句。
        对于SQLite，将MySQL语法转换为SQLite兼容语法后执行。
        """
        if self.is_sqlite:
            self._create_sqlite_tables()
        else:
            self._create_mysql_tables()

    def _create_mysql_tables(self) -> None:
        """执行schema.sql创建MySQL表"""
        schema_sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

        with self.engine.connect() as conn:
            for statement in statements:
                if statement and not statement.startswith("--"):
                    conn.execute(text(statement))
            conn.commit()

        logger.info("MySQL表创建完成")

    def _create_sqlite_tables(self) -> None:
        """创建SQLite兼容的表结构"""
        # SQLite不支持MySQL特有语法，使用兼容的DDL
        price_table_sql = """
        CREATE TABLE IF NOT EXISTS price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_category TEXT NOT NULL,
            market_name TEXT NOT NULL,
            region TEXT NOT NULL,
            date TEXT NOT NULL,
            highest_price REAL,
            lowest_price REAL,
            average_price REAL NOT NULL,
            unit TEXT DEFAULT '元/公斤',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        weather_table_sql = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            date TEXT NOT NULL,
            average_temperature REAL,
            highest_temperature REAL,
            lowest_temperature REAL,
            rainfall REAL,
            humidity REAL,
            sunshine_duration REAL,
            weather_condition TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 创建索引
        price_index_1 = """
        CREATE INDEX IF NOT EXISTS idx_price_product_date
        ON price_data (product_name, date)
        """
        price_index_2 = """
        CREATE INDEX IF NOT EXISTS idx_price_region_date
        ON price_data (region, date)
        """
        weather_index = """
        CREATE INDEX IF NOT EXISTS idx_weather_region_date
        ON weather_data (region, date)
        """

        with self.engine.connect() as conn:
            conn.execute(text(price_table_sql))
            conn.execute(text(weather_table_sql))
            conn.execute(text(price_index_1))
            conn.execute(text(price_index_2))
            conn.execute(text(weather_index))
            conn.commit()

        logger.info("SQLite表创建完成")

    def import_price_data(self, df: pd.DataFrame) -> int:
        """导入价格数据到price_data表

        将DataFrame中的价格数据批量插入到price_data表。
        仅导入表结构中定义的列，忽略多余列。

        Args:
            df: 包含价格数据的DataFrame，需包含以下列：
                product_name, product_category, market_name, region,
                date, highest_price, lowest_price, average_price, unit

        Returns:
            成功导入的记录数

        Raises:
            ValueError: 当DataFrame缺少必要列时
        """
        if df.empty:
            logger.warning("价格数据DataFrame为空，跳过导入")
            return 0

        # 筛选存在的列
        available_columns = [col for col in self.PRICE_COLUMNS if col in df.columns]
        import_df = df[available_columns].copy()

        # 确保必填字段存在
        required_columns = ["product_name", "product_category", "market_name",
                           "region", "date", "average_price"]
        missing_required = [col for col in required_columns if col not in import_df.columns]
        if missing_required:
            raise ValueError(f"价格数据缺少必要列: {missing_required}")

        # 设置默认unit值
        if "unit" not in import_df.columns:
            import_df["unit"] = "元/公斤"

        # 批量导入
        records_imported = self._bulk_insert(import_df, "price_data")
        logger.info(f"价格数据导入完成: {records_imported} 条记录")
        return records_imported

    def import_weather_data(self, df: pd.DataFrame) -> int:
        """导入气象数据到weather_data表

        将DataFrame中的气象数据批量插入到weather_data表。
        仅导入表结构中定义的列，忽略多余列。

        Args:
            df: 包含气象数据的DataFrame，需包含以下列：
                region, date, average_temperature, highest_temperature,
                lowest_temperature, rainfall, humidity, sunshine_duration,
                weather_condition

        Returns:
            成功导入的记录数

        Raises:
            ValueError: 当DataFrame缺少必要列时
        """
        if df.empty:
            logger.warning("气象数据DataFrame为空，跳过导入")
            return 0

        # 筛选存在的列
        available_columns = [col for col in self.WEATHER_COLUMNS if col in df.columns]
        import_df = df[available_columns].copy()

        # 确保必填字段存在
        required_columns = ["region", "date"]
        missing_required = [col for col in required_columns if col not in import_df.columns]
        if missing_required:
            raise ValueError(f"气象数据缺少必要列: {missing_required}")

        # 批量导入
        records_imported = self._bulk_insert(import_df, "weather_data")
        logger.info(f"气象数据导入完成: {records_imported} 条记录")
        return records_imported

    def verify_import(self, table_name: str, expected_count: int) -> bool:
        """验证导入后记录数与预期一致

        查询指定表的总记录数，与预期数量进行比较。

        Args:
            table_name: 表名（price_data 或 weather_data）
            expected_count: 预期的记录数（通常为CSV文件的数据行数）

        Returns:
            True 如果实际记录数等于预期记录数，否则 False
        """
        actual_count = self._get_table_count(table_name)
        is_match = actual_count == expected_count

        if is_match:
            logger.info(
                f"导入验证通过: {table_name} 表记录数 {actual_count} "
                f"与预期 {expected_count} 一致"
            )
        else:
            logger.warning(
                f"导入验证失败: {table_name} 表记录数 {actual_count} "
                f"与预期 {expected_count} 不一致"
            )

        return is_match

    def fallback_to_sqlite(self, sqlite_path: Optional[str] = None) -> "DBImporter":
        """MySQL不可用时降级为SQLite

        创建一个使用SQLite的新DBImporter实例，并初始化表结构。

        Args:
            sqlite_path: SQLite数据库文件路径。
                        如果为None，使用config.py中的默认路径。

        Returns:
            使用SQLite连接的新DBImporter实例
        """
        if sqlite_path is None:
            sqlite_path = str(SQLITE_DB_PATH)

        # 确保目录存在
        db_path = Path(sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        sqlite_conn_str = f"sqlite:///{sqlite_path}"
        logger.info(f"降级为SQLite: {sqlite_path}")

        sqlite_importer = DBImporter(sqlite_conn_str)
        sqlite_importer.create_tables()

        return sqlite_importer

    def clear_table(self, table_name: str) -> None:
        """清空指定表的所有数据

        Args:
            table_name: 表名（price_data 或 weather_data）
        """
        with self.engine.connect() as conn:
            conn.execute(text(f"DELETE FROM {table_name}"))
            conn.commit()
        logger.info(f"已清空表: {table_name}")

    def close(self) -> None:
        """关闭数据库连接"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    # ================================================================
    # 私有辅助方法
    # ================================================================

    def _bulk_insert(self, df: pd.DataFrame, table_name: str) -> int:
        """批量插入DataFrame数据到指定表

        使用pandas的to_sql方法进行批量插入，
        对于大数据集分批处理以避免内存问题。

        Args:
            df: 待插入的DataFrame
            table_name: 目标表名

        Returns:
            成功插入的记录数
        """
        if df.empty:
            return 0

        # 处理NaN值：将pandas的NaN转换为None（SQL NULL）
        import_df = df.where(pd.notna(df), None)

        # 使用pandas to_sql批量插入，append模式不会删除已有数据
        # chunksize控制每批插入的行数，避免大数据集内存溢出
        batch_size = 1000
        import_df.to_sql(
            name=table_name,
            con=self.engine,
            if_exists="append",
            index=False,
            chunksize=batch_size,
        )

        return len(df)

    def _get_table_count(self, table_name: str) -> int:
        """查询指定表的记录总数

        Args:
            table_name: 表名

        Returns:
            表中的记录总数
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
        return count

    @classmethod
    def create_with_fallback(cls, mysql_conn_str: Optional[str] = None) -> "DBImporter":
        """创建DBImporter实例，MySQL不可用时自动降级为SQLite

        尝试连接MySQL，如果连接失败则自动降级为SQLite。

        Args:
            mysql_conn_str: MySQL连接字符串，默认使用config.py中的配置

        Returns:
            DBImporter实例（MySQL或SQLite）
        """
        if mysql_conn_str is None:
            mysql_conn_str = MYSQL_CONNECTION_STRING

        # 尝试MySQL连接
        try:
            importer = cls(mysql_conn_str)
            # 测试连接是否可用
            with importer.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("MySQL连接成功")
            importer.create_tables()
            return importer
        except (OperationalError, Exception) as e:
            logger.warning(f"MySQL连接失败: {e}，降级为SQLite")
            importer = cls(SQLITE_CONNECTION_STRING)
            importer.create_tables()
            return importer


# 模块入口：直接运行时执行数据导入
if __name__ == "__main__":
    from config import PROCESSED_PRICE_CSV, PROCESSED_WEATHER_CSV

    logging.basicConfig(level=logging.INFO)

    print("[DBImporter] 开始数据导入...")

    # 创建导入器（自动降级）
    importer = DBImporter.create_with_fallback()
    db_type = "SQLite" if importer.is_sqlite else "MySQL"
    print(f"[DBImporter] 使用数据库: {db_type}")

    # 读取清洗后的数据
    if PROCESSED_PRICE_CSV.exists():
        price_df = pd.read_csv(PROCESSED_PRICE_CSV)
        print(f"[DBImporter] 读取价格数据: {len(price_df)} 条")

        # 导入价格数据
        price_count = importer.import_price_data(price_df)
        print(f"[DBImporter] 导入价格数据: {price_count} 条")

        # 验证导入
        if importer.verify_import("price_data", price_count):
            print("[DBImporter] 价格数据导入验证通过 ✓")
        else:
            print("[DBImporter] 价格数据导入验证失败 ✗")
    else:
        print(f"[DBImporter] 价格数据文件不存在: {PROCESSED_PRICE_CSV}")

    if PROCESSED_WEATHER_CSV.exists():
        weather_df = pd.read_csv(PROCESSED_WEATHER_CSV)
        print(f"[DBImporter] 读取气象数据: {len(weather_df)} 条")

        # 导入气象数据
        weather_count = importer.import_weather_data(weather_df)
        print(f"[DBImporter] 导入气象数据: {weather_count} 条")

        # 验证导入
        if importer.verify_import("weather_data", weather_count):
            print("[DBImporter] 气象数据导入验证通过 ✓")
        else:
            print("[DBImporter] 气象数据导入验证失败 ✗")
    else:
        print(f"[DBImporter] 气象数据文件不存在: {PROCESSED_WEATHER_CSV}")

    importer.close()
    print("[DBImporter] 数据导入完成！")
