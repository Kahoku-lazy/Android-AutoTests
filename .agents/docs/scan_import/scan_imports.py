"""
调试入口: 
    python -m temps.runtime
"""
import ast, pathlib, collections

def scan_imports(file_path: str, invalid_module: list[str] = None) -> dict[str, int]:
    """
    扫描指定文件的 import 语句，统计导入的模块及其出现次数。
    :param file_path: 要扫描的 Python 文件路径
    :param invalid_module: 不允许导入的模块列表
    :return: 模块计数字典
    """
    if invalid_module is None:
        invalid_module = []
    
    # 判传入的是文件，还是目录；如果是目录就遍历，如果是文件就直接扫描
    if pathlib.Path(file_path).is_dir():
        for p in pathlib.Path(file_path).rglob('*.py'):
            scan_imports(str(p), invalid_module)
        return {}
    
    try:
        t = ast.parse(pathlib.Path(file_path).read_text(encoding='utf-8'))
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {}
    
    module_counter = collections.Counter()
    
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            for a in n.names:
                module_name = a.name.split('.')[0]
                module_counter[module_name] += 1
                if module_name in invalid_module:
                    print(f'❌ {file_path} 导入模块:{module_name}.*')
                    
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            module_name = n.module.split('.')[0]
            module_counter[module_name] += 1
            if module_name in invalid_module:
                print(f'❌ {module_counter[module_name]:2d} {file_path} 导入模块:{n.module}.*')
    
    return dict(module_counter)


engines_ae_harness = scan_imports



engines_ae_harness_path = "engines/ae_harness"
engines_ae_harness_invalid_modules = ["engines", "backend"]
result = engines_ae_harness(engines_ae_harness_path, engines_ae_harness_invalid_modules)
