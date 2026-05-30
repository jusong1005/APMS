-- ============================================================
-- 大数据价格预测分析系统 - MySQL 数据库表结构定义
-- 需求：3.1
-- ============================================================

-- 农产品价格数据表
CREATE TABLE IF NOT EXISTS price_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(50) NOT NULL COMMENT '农产品名称',
    product_category VARCHAR(50) NOT NULL COMMENT '类别',
    market_name VARCHAR(100) NOT NULL COMMENT '市场名称',
    region VARCHAR(50) NOT NULL COMMENT '地区',
    date DATE NOT NULL COMMENT '日期',
    highest_price DECIMAL(10,2) COMMENT '最高价(元/公斤)',
    lowest_price DECIMAL(10,2) COMMENT '最低价(元/公斤)',
    average_price DECIMAL(10,2) NOT NULL COMMENT '均价(元/公斤)',
    unit VARCHAR(20) DEFAULT '元/公斤' COMMENT '单位',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_product_date (product_name, date),
    INDEX idx_region_date (region, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='农产品价格数据表';

-- 气象数据表
CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region VARCHAR(50) NOT NULL COMMENT '地区',
    date DATE NOT NULL COMMENT '日期',
    average_temperature DECIMAL(5,2) COMMENT '日均气温(°C)',
    highest_temperature DECIMAL(5,2) COMMENT '最高气温(°C)',
    lowest_temperature DECIMAL(5,2) COMMENT '最低气温(°C)',
    rainfall DECIMAL(8,2) COMMENT '降雨量(mm)',
    humidity DECIMAL(5,2) COMMENT '相对湿度(%)',
    sunshine_duration DECIMAL(5,2) COMMENT '日照时长(小时)',
    weather_condition VARCHAR(50) COMMENT '天气状况',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_region_date (region, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='气象数据表';
