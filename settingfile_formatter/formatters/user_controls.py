import re
from typing import List, Tuple
from .base import ContentFormatter


class UserControlsFormatter(ContentFormatter):
    """UserControlsブロックを整形"""
    BLOCK_START_TOKENS = ['UserControls', '=', 'ordered', '(', ')', '{']

    def format_content(self, content: str) -> str:
        """コンテンツを整形"""
        tokens_per_line = self.tokenizer.tokenize_content(content)
        blocks = self._extract_blocks(tokens_per_line, self.BLOCK_START_TOKENS)
        if not blocks:
            return content

        result_lines = []
        last_end = -1
        original_lines = content.splitlines()

        for start, end in blocks:
            result_lines.extend(original_lines[last_end + 1:start])
            indent_str = ' ' * (len(original_lines[start]) - len(original_lines[start].lstrip()))
            block_tokens = tokens_per_line[start:end + 1]
            formatted_block = self._format_block(block_tokens, indent_str)
            result_lines.extend(formatted_block)
            last_end = end

        result_lines.extend(original_lines[last_end + 1:])
        return '\n'.join(result_lines)

    def _format_block(self, block_tokens: List[List[str]], indent: str) -> List[str]:
        """ブロックを整形"""
        all_tokens = [t for line in block_tokens for t in line]
        try:
            start_idx = all_tokens.index('{') + 1
            end_idx = len(all_tokens) - 1 - all_tokens[::-1].index('}')
            content_tokens = all_tokens[start_idx:end_idx]
        except ValueError:
            return [f"{indent}UserControls = ordered() {{}}"]

        result = [f"{indent}UserControls = ordered() {{"]
        if content_tokens:
            child_indent = indent + self.tokenizer.INDENT
            result.extend(self._format_block_content(content_tokens, child_indent))
        result.append(f"{indent}}}")
        return result

    def _find_block_end(self, tokens: List[str], start_idx: int) -> int:
        """ブロックチャンクの終了位置を検索"""
        brace_start = start_idx + 2
        brace_end = self.tokenizer.find_brace_end(tokens, brace_start)
        if brace_end is None:
            return start_idx + 1

        end_idx = brace_end + 1
        if end_idx < len(tokens) and tokens[end_idx] == ',':
            end_idx += 1
        return end_idx

    def _find_simple_end(self, tokens: List[str], start_idx: int) -> int:
        """単純代入チャンクの終了位置を検索"""
        try:
            return tokens.index(',', start_idx) + 1
        except ValueError:
            return len(tokens)

    def _find_concat_end(self, tokens: List[str], start_idx: int) -> int:
        """文字列連結チャンクの終了位置を検索"""
        i = start_idx + 2
        while i + 1 < len(tokens):
            is_string = tokens[i].startswith('"')
            is_concat_op = tokens[i+1] == '..'
            if is_string and is_concat_op:
                i += 2
            else:
                break
        if i < len(tokens) and tokens[i].startswith('"'):
            i += 1
        if i < len(tokens) and tokens[i] == ',':
            i += 1
        return i

    def _chunk_tokens(self, tokens: List[str]) -> List[List[str]]:
        """トークンを意味のあるチャンクに分割"""
        chunks, i = [], 0
        while i < len(tokens):
            if i + 2 < len(tokens) and tokens[i+1] == '=':
                start_idx = i
                value_start_token = tokens[i+2]

                if value_start_token == '{':
                    end_idx = self._find_block_end(tokens, start_idx)
                elif value_start_token.startswith('"') and i + 3 < len(tokens) and tokens[i+3] == '..':
                    end_idx = self._find_concat_end(tokens, start_idx)
                else:
                    end_idx = self._find_simple_end(tokens, start_idx)

                chunks.append(tokens[start_idx:end_idx])
                i = end_idx
            else:
                i += 1
        return chunks

    def _format_block_content(self, tokens: List[str], indent: str) -> List[str]:
        """ブロックコンテンツを整形"""
        result = []
        chunks = self._chunk_tokens(tokens)
        for chunk in chunks:
            if len(chunk) > 3 and chunk[2] == '{':
                key = chunk[0]
                add_comma = chunk[-1] == ','
                inner_tokens = chunk[3:-2]
                result.append(f"{indent}{key} = {{")
                result.extend(self._format_block_content(inner_tokens, indent + self.tokenizer.INDENT))
                result.append(f"{indent}}}{',' if add_comma else ''}")
            elif '..' in chunk:
                key = chunk[0]
                parts = [token for token in chunk if token.startswith('"')]
                add_comma = chunk[-1] == ','
                result.extend(self._format_concat_string(key, parts, indent, add_comma))
            else:
                result.append(f"{indent}{self._recombine_tokens(chunk)}")
        return result
