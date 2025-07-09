import re
from typing import List, Dict, Tuple

from .base import ContentFormatter


class StringLiteralFormatter(ContentFormatter):
    """'\n'を含む文字列リテラルを複数行に整形する"""

    def _get_parent_indent(self, line_num: int, token_idx: int, lines: List[str], tokens_per_line: List[List[str]]) -> str:
        """親ブロックのインデント文字列を取得する"""
        nest_level = 0

        def seek_indent(token: str, target_line_num: int) -> str | None:
            nonlocal nest_level
            nest_level = self.tokenizer.update_nest_level_reverse(token, nest_level)
            if nest_level < 0 and token == '{':
                parent_line = lines[target_line_num]
                return " " * (len(parent_line) - len(parent_line.lstrip()))
            return None

        # 現在行を逆方向に検索
        for i in range(token_idx - 1, -1, -1):
            if (indent := seek_indent(tokens_per_line[line_num][i], line_num)) is not None:
                return indent

        # 前の行を逆方向に検索
        for i in range(line_num - 1, -1, -1):
            for token in reversed(tokens_per_line[i]):
                if (indent := seek_indent(token, i)) is not None:
                    return indent
        return ""

    def _find_targets(self, tokens_per_line: List[List[str]]) -> Dict[int, int]:
        """整形対象の `key = "value\n..."` の位置を特定する"""
        targets = {}
        for line_num, tokens in enumerate(tokens_per_line):
            for i in range(len(tokens) - 2):
                # 連結済み(`..`)はスキップ
                if i + 3 < len(tokens) and tokens[i+3] == '..':
                    continue

                if (tokens[i+1] == '=' and tokens[i+2].startswith('"') and '\\n' in tokens[i+2]):
                    targets[line_num] = i
                    break
        return targets

    def _split_line_tokens(self, tokens: List[str], key_idx: int) -> Tuple[List[str], List[str]]:
        """トークンを後続部と閉じ括弧に分割"""
        suffix_start = key_idx + 3
        if suffix_start < len(tokens) and tokens[suffix_start] == ',':
            suffix_start += 1

        brace_pos = next((i for i, t in enumerate(tokens) if t == '}'), -1)

        if brace_pos == -1 or brace_pos < suffix_start:
            return tokens[suffix_start:], []
        return tokens[suffix_start:brace_pos], tokens[brace_pos:]

    def _build_multiline_string(self, key: str, value: str, indent: str) -> List[str]:
        """複数行文字列を構築"""
        parts = value[1:-1].split('\\n')
        lines = [f"{indent}{key} ="]
        lines.extend([
            f'{indent}{self.tokenizer.INDENT}"{part}\\n" ..' if i < len(parts) - 1
            else f'{indent}{self.tokenizer.INDENT}"{part}",'
            for i, part in enumerate(parts)
        ])
        return lines

    def _recombine_tokens(self, tokens: List[str]) -> str:
        """トークンを再結合（空白調整）"""
        if not tokens: return ""
        result = ' '.join(tokens)
        result = re.sub(r'\s+([,;}])', r'\1', result)
        result = re.sub(r'([({[])\s+', r'\1', result)
        return result.strip()

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

            new_lines.extend(self._build_multiline_string(key, value, target_indent))

            if suffix_tokens:
                new_lines.append(f"{target_indent}{self._recombine_tokens(suffix_tokens)}")
            if closing_tokens:
                new_lines.append(f"{parent_indent}{self._recombine_tokens(closing_tokens)}")

            lines[line_num:line_num+1] = new_lines

        return "\n".join(lines)