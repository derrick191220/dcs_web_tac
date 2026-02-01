import os
import pytest
from src import db_init

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # 确保在测试前初始化数据库
    if not os.path.exists("data"):
        os.makedirs("data")
    db_init.init_db()
