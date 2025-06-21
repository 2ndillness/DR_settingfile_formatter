import os
import re
import json
from pathlib import Path

FORMATTERS_DIR = Path(__file__).parent / 'formatters'
CONFIG_PATH = Path(__file__).parent / 'config.json'
INIT_PATH = FORMATTERS_DIR / '__init__.py'

# base.pyは除外
EXCLUDE_FILES = {'base.py', '__init__.py'}

# Formatterクラス検出用パターン
CLASS_PATTERN = re.compile(r'class\s+(\w+Formatter)\b')

def find_formatter_classes():
    formatters = {}
    for file in FORMATTERS_DIR.glob('*.py'):
        if file.name in EXCLUDE_FILES:
            continue
        with file.open(encoding='utf-8') as f:
            content = f.read()
        matches = CLASS_PATTERN.findall(content)
        for cls in matches:
            key = file.stem  # ファイル名（拡張子なし）
            formatters[key] = f"formatters.{key}.{cls}"
    return formatters

def update_config_json(formatters):
    config = {"formatters": formatters}
    with CONFIG_PATH.open('w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"config.jsonを更新しました: {CONFIG_PATH}")

def update_init_py(formatters):
    # base.pyのimportを先頭に追加
    lines = [
        "from .base import ContentFormatter, Tokenizer"
    ]
    # Formatterクラスのimport
    lines += [f"from .{key} import {val.split('.')[-1]}" for key, val in formatters.items()]
    # __all__ の生成
    all_list = ["'ContentFormatter'", "'Tokenizer'"] + [f"'{val.split('.')[-1]}'" for val in formatters.values()]
    lines.append(f"__all__ = [{', '.join(all_list)}]")
    with INIT_PATH.open('w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"__init__.pyを更新しました: {INIT_PATH}")

def main():
    formatters = find_formatter_classes()
    update_config_json(formatters)
    update_init_py(formatters)

if __name__ == '__main__':
    main()
