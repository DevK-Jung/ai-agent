# tests/conftest.py
import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires Docker)"
    )


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 fixture"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_python_codes():
    """테스트용 Python 코드 샘플들"""
    return {
        "simple_print": "print('Hello, World!')",
        "math_calculation": """
import math
result = math.sqrt(16) + math.pi
print(f"Result: {result:.2f}")
        """.strip(),
        "data_processing": """
import json
data = {"name": "test", "numbers": [1, 2, 3, 4, 5]}
total = sum(data["numbers"])
print(f"Total: {total}")
print(json.dumps(data, indent=2))
        """.strip(),
        "error_code": """
undefined_variable = some_undefined_var
print(undefined_variable)
        """.strip(),
        "infinite_loop": """
import time
while True:
    time.sleep(1)
    print("Running...")
        """.strip(),
        "seaborn_plot": """
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 샘플 데이터 생성
np.random.seed(42)
data = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100),
    'category': np.random.choice(['A', 'B', 'C'], 100)
})

# Seaborn 플롯 생성
plt.figure(figsize=(8, 6))
sns.scatterplot(data=data, x='x', y='y', hue='category')
plt.title('Seaborn Scatter Plot')
plt.savefig('/tmp/plot.png')
print("Plot saved successfully!")
print(f"Data shape: {data.shape}")
print(f"Categories: {data['category'].unique()}")
        """.strip()
    }


@pytest.fixture
def sample_javascript_codes():
    """테스트용 JavaScript 코드 샘플들"""
    return {
        "simple_log": "console.log('Hello from Node.js!');",
        "json_processing": """
const data = { name: 'test', numbers: [1, 2, 3, 4, 5] };
const total = data.numbers.reduce((a, b) => a + b, 0);
console.log(`Total: ${total}`);
console.log(JSON.stringify(data, null, 2));
        """.strip(),
        "async_example": """
async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    console.log('Starting...');
    await delay(100);
    console.log('Finished after delay!');
}

main().catch(console.error);
        """.strip()
    }


@pytest.fixture
def docker_test_config():
    """Docker 테스트 설정"""
    return {
        "timeout": 30,
        "memory_limit": "256m",
        "cpu_limit": 0.5,
        "test_timeout": 10
    }