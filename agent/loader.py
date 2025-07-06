import os
import importlib
import pkgutil
from pathlib import Path

def load_agents():
    """
    动态加载 agent 目录下的所有智能体模块。

    在加载前会检查关键环境变量是否已设置，若未设置则不进行加载。
    每个智能体模块应在被导入时自行注册到注册表（registry）。
    该函数会遍历 agent 目录下所有的 .py 文件（排除特殊模块），
    并通过 importlib 动态导入模块，实现自动发现和加载智能体。
    """
    # 检查关键环境变量
    required_envs = ["FASTGPT_BASE_URL", "FASTGPT_API_KEY", "FASTGPT_APP_ID", "DIFY_BASE_URL", "DIFY_API_KEY"]
    missing_envs = [env for env in required_envs if not os.getenv(env)]
    if missing_envs:
        print(f"缺少环境变量，未加载智能体: {', '.join(missing_envs)}")
        return

    # 获取当前包的目录路径
    package_dir = Path(__file__).parent
    
    # 遍历 agent 目录下所有模块
    for (_, module_name, _) in pkgutil.iter_modules([str(package_dir)]):
        # 跳过特殊模块
        if module_name in ['__init__', 'base', 'registry', 'loader']:
            continue
        
        # 动态导入模块
        try:
            importlib.import_module(f"agent.{module_name}")
            print(f"Loaded agent module: {module_name}")
        except Exception as e:
            print(f"Error loading agent module {module_name}: {e}")