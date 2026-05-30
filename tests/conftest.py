"""
测试配置和共享fixtures

为属性测试、单元测试和集成测试提供公共配置和数据生成器。
"""

import sys
from pathlib import Path

import pytest

# 将项目根目录添加到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


@pytest.fixture
def project_root():
    """返回项目根目录路径"""
    return PROJECT_ROOT


@pytest.fixture
def raw_data_dir():
    """返回原始数据目录路径"""
    return PROJECT_ROOT / "data" / "raw"


@pytest.fixture
def processed_data_dir():
    """返回处理后数据目录路径"""
    return PROJECT_ROOT / "data" / "processed"


@pytest.fixture
def models_dir():
    """返回模型目录路径"""
    return PROJECT_ROOT / "models"
