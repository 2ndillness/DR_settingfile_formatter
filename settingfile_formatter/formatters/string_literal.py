import re
from typing import List, Dict, Tuple

from .base import ContentFormatter


class StringLiteralFormatter(ContentFormatter):
    """'\n'を含む文字列リテラルを複数行に整形する"""

    def _check_brace_rev(self, token: str, nest_level: int) -> Tuple[bool, int]:
        """逆方向の括弧のネストをチェック"""
        updated_level = self.tokenizer.update_nest_rev(token, nest_level)
        found = updated_level < 0 and token == '{'
        return found, updated_level

    def _get_parent_indent(self, line_num: int, token_idx: int, lines: List[str], tokens_per_line: List[List[str]]) -> str:
        """親ブロックのインデントを取得"""
        nest_level = 0
        # 現在行を逆方向に検索
        for i in range(token_idx - 1, -1, -1):
            token = tokens_per_line[line_num][i]
            found, nest_level = self._check_brace_rev(token, nest_level)
            if found:
                return ' ' * (len(lines[line_num]) - len(lines[line_num].lstrip()))
        # 前の行を逆方向に検索
        for i in range(line_num - 1, -1, -1):
            for token in reversed(tokens_per_line[i]):
                found, nest_level = self._check_brace_rev(token, nest_level)
                if found:
                    return ' ' * (len(lines[i]) - len(lines[i].lstrip()))
        return ''

    def _find_targets(self, tokens_per_line: List[List[str]]) -> Dict[int, int]:
        """整形対象の文字列リテラルを検索"""
        targets = {}
        for line_num, tokens in enumerate(tokens_per_line):
            # 既に '..' 演算子で連結されている行は、整形済みとみなして全体をスキップ
            if '..' in tokens:
                continue

            for i in range(len(tokens) - 2):
                if (tokens[i+1] == '=' and tokens[i+2].startswith('"') and '\\n' in tokens[i+2]):
                    targets[line_num] = i
                    break
        return targets

    def _split_line_tokens(self, tokens: List[str], key_idx: int) -> Tuple[List[str], List[str]]:
        """行トークンを後続部と閉じ括弧に分割"""
        suffix_start = key_idx + 3
        if suffix_start < len(tokens) and tokens[suffix_start] == ',':
            suffix_start += 1

        brace_pos = next((i for i, t in enumerate(tokens) if t == '}'), -1)

        if brace_pos == -1 or brace_pos < suffix_start:
            return tokens[suffix_start:], []
        return tokens[suffix_start:brace_pos], tokens[brace_pos:]

    def format_content(self, content: str) -> str:
        lines = content.splitlines()
        tokens_per_line = self.tokenizer.tokenize_content(content)

        targets = self._find_targets(tokens_per_line)
        if not targets:
            return content

        for line_num in sorted(targets.keys(), reverse=True):
            key_idx = targets[line_num]
            tokens = tokens_per_line[line_num]
            key, value = tokens[key_idx], tokens[key_idx + 2]

            prefix = lines[line_num][:lines[line_num].find(key)]
            parent_indent = self._get_parent_indent(line_num, key_idx, lines, tokens_per_line)
            target_indent = parent_indent + self.tokenizer.INDENT
            suffix_tokens, closing_tokens = self._split_line_tokens(tokens, key_idx)

            new_lines = []
            if prefix.strip():
                new_lines.append(prefix.rstrip())

            # 1. 文字列をパーツに分割し、ダブルクォートで囲む
            value_parts = value[1:-1].split(r'\n')
            num_parts = len(value_parts)
            parts = []
            for i, part in enumerate(value_parts):
                is_last = (i == num_parts - 1)
                quoted_part = f'"{part}\\n"' if not is_last else f'"{part}"'
                parts.append(quoted_part)

            # 2. 複数行に連結された文字列を構築する
            new_lines.extend(self._format_concat_string(key, parts, target_indent, add_comma=True))

            if suffix_tokens:
                new_lines.append(f'{target_indent}{self._recombine_tokens(suffix_tokens)}')
            if closing_tokens:
                new_lines.append(f'{parent_indent}{self._recombine_tokens(closing_tokens)}')

            lines[line_num:line_num+1] = new_lines

        return '\n'.join(lines)
