"""
大数据价格预测分析系统 - 项目配置文件

包含数据库连接、文件路径、模型参数等全局配置。
"""

import os
from pathlib import Path

# ============================================================
# 项目根目录
# ============================================================
PROJECT_ROOT = Path(__file__).parent.resolve()

# ============================================================
# 数据文件路径配置
# ============================================================
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

# 原始数据文件
RAW_PRICE_CSV = RAW_DATA_DIR / "price_data.csv"
RAW_WEATHER_CSV = RAW_DATA_DIR / "weather_data.csv"

# 清洗后数据文件
PROCESSED_PRICE_CSV = PROCESSED_DATA_DIR / "processed_price.csv"
PROCESSED_WEATHER_CSV = PROCESSED_DATA_DIR / "processed_weather.csv"
MERGED_DATA_CSV = PROCESSED_DATA_DIR / "merged_data.csv"

# 模型文件
RANDOM_FOREST_MODEL = MODELS_DIR / "random_forest_model.pkl"
ARIMA_MODEL = MODELS_DIR / "arima_model.pkl"

# ============================================================
# 数据库配置
# ============================================================
# MySQL 主数据库配置
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "123456"),
    "database": os.getenv("MYSQL_DATABASE", "price_prediction"),
    "charset": "utf8mb4",
}

# MySQL 连接字符串
MYSQL_CONNECTION_STRING = (
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
    f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    f"?charset={MYSQL_CONFIG['charset']}"
)

# SQLite 降级方案配置
SQLITE_DB_PATH = DATA_DIR / "price_prediction.db"
SQLITE_CONNECTION_STRING = f"sqlite:///{SQLITE_DB_PATH}"

# 数据库Schema文件
SCHEMA_SQL_PATH = PROJECT_ROOT / "backend" / "schema.sql"

# ============================================================
# 数据采集配置
# ============================================================
DATA_COLLECTION = {
    "min_records": 1000,          # 最低数据记录数
    "min_products": 3,            # 最少农产品种类
    "min_regions": 2,             # 最少地区数
    "min_months": 6,              # 最少时间跨度（月）
    "retry_count": 3,             # 数据获取重试次数
    "retry_interval_base": 5,     # 重试间隔基数（秒）
}

# ============================================================
# 数据清洗配置
# ============================================================
DATA_CLEANING = {
    "missing_threshold": 0.50,    # 缺失比例阈值（>=50%删除字段）
    "iqr_multiplier": 1.5,        # IQR异常值检测倍数
    "quality_max_missing": 0.20,  # 质量检查：最大缺失比例
    "quality_max_duplicate": 0.10, # 质量检查：最大重复比例
    "date_format": "%Y-%m-%d",    # 日期标准格式
    "price_unit": "元/公斤",       # 价格标准单位
}

# ============================================================
# 模型训练配置
# ============================================================
MODEL_CONFIG = {
    "min_training_records": 100,   # 最少训练数据记录数
    "test_size": 0.2,              # 测试集比例
    "random_state": 42,            # 随机种子
    "n_estimators": 100,           # 随机森林树数量
    "arima_trigger_rmse_ratio": 0.30,  # ARIMA触发：RMSE超过均价比例
    "arima_trigger_r2_threshold": 0.50, # ARIMA触发：R²低于此值
}

# ============================================================
# 后端API配置
# ============================================================
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "5000")),
    "debug": os.getenv("API_DEBUG", "True").lower() == "true",
    "cors_origins": [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
}

# ============================================================
# 前端配置
# ============================================================
FRONTEND_CONFIG = {
    "dev_port": 5173,
    "api_base_url": f"http://localhost:{API_CONFIG['port']}",
}

# ============================================================
# 项目管理配置
# ============================================================
PROJECT_CONFIG = {
    "project_name": "基于农业气象与农产品市场数据的大数据价格预测分析系统",
    "total_weeks": 4,
    "max_weekly_hours_per_member": 20.0,
    "max_workload_difference_ratio": 0.30,
    "members": [
        {"name": "马一凡", "role": "项目负责人"},
        {"name": "盛晓宇", "role": "数据采集负责人"},
        {"name": "武殊宇", "role": "数据处理负责人"},
        {"name": "王羽菲", "role": "数据分析负责人"},
        {"name": "靳康琦", "role": "模型预测负责人"},
    ],
}
