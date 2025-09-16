import os
import importlib
import pkgutil
from pathlib import Path
import dotenv


def load_agents():
    """
    动态加载 agent 目录下的所有智能体模块。

    在加载前会检查关键环境变量是否已设置，若未设置则不进行加载。
    每个智能体模块应在被导入时自行注册到注册表（registry）。
    该函数会遍历 agent 目录下所有的 .py 文件（排除特殊模块），
    并通过 importlib 动态导入模块，实现自动发现和加载智能体。
    """
    # 检查关键环境变量 - 至少需要一个智能体的完整配置
    if os.path.exists('.env'):
        dotenv.load_dotenv('.env')
    
    # 检查 FastGPT 配置
    fastgpt_complete = all([
        os.getenv("FASTGPT_BASE_URL"),
        os.getenv("FASTGPT_API_KEY"),
        os.getenv("FASTGPT_APP_ID")
    ])
    
    # 检查 Dify 配置  
    dify_complete = all([
        os.getenv("DIFY_BASE_URL"),
        os.getenv("DIFY_API_KEY")
    ])
    
    # 检查 Zhipu 配置
    zhipu_complete = bool(os.getenv("ZHIPUAI_API_KEY"))

    if not (fastgpt_complete or dify_complete or zhipu_complete):
        print("未找到完整的智能体配置，需要至少配置一个智能体的环境变量")
        print("FastGPT 需要: FASTGPT_BASE_URL, FASTGPT_API_KEY, FASTGPT_APP_ID")
        print("Dify 需要: DIFY_BASE_URL, DIFY_API_KEY")
        print("Zhipu 需要: ZHIPUAI_API_KEY")
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