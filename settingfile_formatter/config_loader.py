import json
import importlib
from pathlib import Path
from typing import Dict, List, Any

class FormatterError(Exception):
    pass

class ConfigLoader:
    def __init__(self, config_file: str = 'config.json'):
        self.config_path = Path(config_file)
        self._formatters_config = self._load_config()
        self._rule_map = self._build_rule_map()
        self._all_choice_num = str(len(self._rule_map) + 1)

    def _load_config(self) -> Dict[str, str]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイル '{self.config_path}' が見つかりません")
        try:
            with self.config_path.open('r', encoding='utf-8') as f:
                return json.load(f).get('formatters', {})
        except json.JSONDecodeError as e:
            raise FormatterError(f"設定ファイル '{self.config_path}' のJSON形式が正しくありません") from e
        except Exception as e:
            raise FormatterError(f'設定ファイルの読み込みに失敗しました: {e}') from e

    def _build_rule_map(self) -> Dict[str, str]:
        return {str(i): name for i, name in enumerate(self._formatters_config.keys(), 1)}

    def get_formatter_choices(self) -> List[str]:
        return list(self._formatters_config.keys()) + ['all']

    def get_rule_names(self, choices: List[str]) -> List[str]:
        """ユーザーの選択肢（番号リスト）を検証し、ルール名のリストに変換する"""
        if self._all_choice_num in choices:
            return ['all']

        valid_choices = set(self._rule_map.keys())
        selected_rules = set()
        for choice in choices:
            if choice not in valid_choices:
                raise ValueError(f"'{choice}' は有効な選択肢ではありません")
            selected_rules.add(self._rule_map[choice])

        return list(selected_rules)

    def _get_formatter_instance(self, rule_name: str) -> Any:
        if rule_name not in self._formatters_config:
            raise FormatterError(f"設定に存在しない整形ルールです: '{rule_name}'")

        module_name, class_name = self._formatters_config[rule_name].rsplit('.', 1)
        try:
            module = importlib.import_module(module_name)
            formatter_class = getattr(module, class_name)
            return formatter_class()
        except (ImportError, AttributeError) as e:
            raise FormatterError(f"整形ルール '{rule_name}' のクラス読み込みに失敗しました") from e

    def get_formatters(self, rule_names: List[str]) -> List[Any]:
        """指定されたルール名のリストに基づき、適用すべきフォーマッターのリストを返す"""
        if 'all' in rule_names or not rule_names:
            target_rules = self._formatters_config.keys()
        else:
            target_rules = rule_names

        return [self._get_formatter_instance(name) for name in target_rules]

    def build_rule_prompt(self) -> str:
        prompt_lines = ['---', '整形ルールを選択してください:']
        prompt_lines.extend([f'  {num}: {name}' for num, name in self._rule_map.items()])
        prompt_lines.append(f'  {self._all_choice_num}: 全てのルールを適用')
        return '\n'.join(prompt_lines)