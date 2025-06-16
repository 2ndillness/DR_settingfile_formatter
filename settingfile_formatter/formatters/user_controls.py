from typing import List, Tuple
from .base import ContentFormatter


class UserControlsFormatter(ContentFormatter):
    """UserControlsブロック整形処理"""

    BLOCK_START_TOKENS = ['UserControls', '=', 'ordered', '(', ')', '{']

    def format_content(self, content: str) -> str:
        """コンテンツを整形"""
        tokens = self.tokenizer.tokenize_content(content)
        blocks = self._find_blocks(tokens)
        if not blocks:
            return content

        result = []
        last_end = -1
        lines = content.splitlines()

        for start, end in blocks:
            # ブロック前の行を追加
            result.extend(lines[last_end + 1:start])

            # ブロックの開始行のインデントを取得
            indent = len(lines[start]) - len(lines[start].lstrip())

            # ブロックを整形
            formatted_block = self._format_block(tokens[start:end + 1], " " * indent)
            result.extend(formatted_block)

            last_end = end

        # 最後のブロック以降の行を追加
        result.extend(lines[last_end + 1:])
        return "\n".join(result)

    def _find_blocks(self, tokens: List[List[str]]) -> List[Tuple[int, int]]:
        """UserControlsブロックを検出"""
        blocks = []
        level = 0  # 初期値
        start = -1

        for i, line_tokens in enumerate(tokens):
            # ブロックの開始を検出
            if start == -1 and len(line_tokens) >= len(self.BLOCK_START_TOKENS):
                if line_tokens[:len(self.BLOCK_START_TOKENS)] == self.BLOCK_START_TOKENS:
                    start = i

            # ブロック内の場合、ネストレベルを更新
            if start != -1:
                for token in line_tokens:
                    level = self.tokenizer.update_nest_level(token, level)
                    if token == '}' and level == 0:
                        blocks.append((start, i))
                        start = -1
                        break

        return blocks

    def _format_block(self, block_tokens: List[List[str]], base_indent: str) -> List[str]:
        """ブロックを整形"""
        all_tokens = [t for line in block_tokens for t in line]
        tokens = self._extract_block_tokens(all_tokens)
        if not tokens:
            return [f"{base_indent}UserControls = ordered() {{}}"]

        result = [f"{base_indent}UserControls = ordered() {{"]
        child_indent = base_indent + self.tokenizer.INDENT
        result.extend(self._format_block_content(tokens, child_indent))
        result.append(f"{base_indent}}}")
        return result

    def _extract_block_tokens(self, all_tokens: List[str]) -> List[str]:
        try:
            start_idx = all_tokens.index('{') + 1
            tokens = all_tokens[start_idx:-1]
        except ValueError:
            return []
        return tokens

    def _format_block_content(self, tokens: List[str], child_indent: str) -> List[str]:
        result = []
        i = 0
        while i < len(tokens):
            if i + 2 < len(tokens) and tokens[i + 1] == '=' and tokens[i + 2] == '{':
                key = tokens[i]
                brace_end = self.tokenizer.find_brace_end(tokens, i + 2)
                if brace_end is not None:
                    inner = tokens[i + 3:brace_end]
                    if self.tokenizer.count_elements(inner) >= 2:
                        result.extend(self._format_multi_line(key, inner, child_indent, True))
                    else:   # 要素数が1つの場合
                        joined = ' '.join(inner).rstrip(',').rstrip()
                        result.append(f"{child_indent}{key} = {{ {joined}, }},")
                    i = brace_end + 2
                    continue
            i += 1
        return result