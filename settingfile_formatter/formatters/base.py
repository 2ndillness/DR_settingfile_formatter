import re
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod


class Tokenizer:
    """トークン化の共通処理を提供するクラス"""

    TOKEN_PATTERN = r'([a-zA-Z_][a-zA-Z0-9_.]*)|(".*?[^\\]")|(\.\.)|([-+]?\d*\.?\d+)|([{}(),=\[\]])'
    INDENT = '    '

    def __init__(self):
        self.pattern = re.compile(self.TOKEN_PATTERN)

    def update_nest_level(self, token: str, level: int) -> int:
        """括弧のネストレベルを更新 (順方向)"""
        return level + (1 if token == '{' else -1 if token == '}' else 0)

    def update_nest_rev(self, token: str, level: int) -> int:
        """括弧のネストレベルを更新 (逆方向)"""
        return level + (1 if token == '}' else -1 if token == '{' else 0)

    def tokenize_line(self, line: str) -> List[str]:
        """1行をトークン化"""
        matches = self.pattern.findall(line)
        return [item for match in matches for item in match if item]

    def tokenize_content(self, content: str) -> List[List[str]]:
        """コンテンツ全体をトークン化"""
        return [self.tokenize_line(line) for line in content.splitlines()]

    def find_brace_end(self, tokens: List[str], start: int) -> Optional[int]:
        """対応する閉じ括弧 '}' のインデックスを返す"""
        if not tokens or start >= len(tokens) or tokens[start] != '{': return None
        level = 1
        for i in range(start + 1, len(tokens)):
            level = self.update_nest_level(tokens[i], level)
            if level == 0 and tokens[i] == '}': return i
        return None

    def count_elements(self, tokens: List[str]) -> int:
        """要素数をカウント（末尾カンマ無視）"""
        if not tokens:
            return 0
        clean_tokens = tokens[:-1] if tokens[-1] == ',' else tokens
        return clean_tokens.count(',') + 1 if clean_tokens else 0


class ContentFormatter(ABC):
    """コンテンツ整形の基底クラス"""

    def __init__(self):
        self.tokenizer = Tokenizer()

    @abstractmethod
    def format_content(self, content: str) -> str:
        """コンテンツを整形"""
        pass

    def _extract_blocks(self, tokens_per_line: List[List[str]], start_tokens: List[str]) -> List[Tuple[int, int]]:
        """指定されたトークンで始まるブロックの範囲を抽出する"""
        blocks = []
        start_line = -1
        nest_level = 0

        for i, line_tokens in enumerate(tokens_per_line):
            if start_line == -1:
                if len(line_tokens) >= len(start_tokens) and line_tokens[:len(start_tokens)] == start_tokens:
                    start_line = i
                    nest_level = 0

            if start_line != -1:
                for token in line_tokens:
                    nest_level = self.tokenizer.update_nest_level(token, nest_level)

                if nest_level == 0:
                    blocks.append((start_line, i))
                    start_line = -1
        return blocks

    def _format_multi_line(self, key: str, tokens: List[str], indent: str, has_comma: bool) -> List[str]:
        """複数行形式で整形"""
        elements = []
        current = []

        for token in tokens:
            if token == ',':
                if current:
                    elements.append(' '.join(current))
                current = []
            else:
                current.append(token)
        if current:
            elements.append(' '.join(current))

        result = [f"{indent}{key} = {{"]
        for elem in elements:
            result.append(f"{indent}{self.tokenizer.INDENT}{elem},")

        result.append(f"{indent}}},")

        return result

    def _recombine_tokens(self, tokens: List[str]) -> str:
        """トークンを再結合（空白調整）"""
        if not tokens: return ""
        result = ' '.join(tokens)
        result = re.sub(r'\s+([,;}])', r'\1', result)
        result = re.sub(r'([({[])\s+', r'\1', result)
        return result.strip()