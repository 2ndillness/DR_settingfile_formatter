import re
from typing import List, Tuple
from .base import ContentFormatter


class UserControlsFormatter(ContentFormatter):
    """UserControlsブロックを整形"""
    BLOCK_START_TOKENS = ['UserControls', '=', 'ordered', '(', ')', '{']

    def format_content(self, content: str) -> str:
        """コンテンツ整形処理のメインフロー"""
        # 前処理: 複数行文字列をプレースホルダーに置換
        replaced_content, placeholders = self._replace_multiline(content)

        # メイン処理: ブロックの整形
        tokens_per_line = self.tokenizer.tokenize_content(replaced_content)
        blocks = self._extract_blocks(tokens_per_line, self.BLOCK_START_TOKENS)
        if not blocks:
            return content

        result_lines = []
        last_end = -1
        original_lines = replaced_content.splitlines()

        for start, end in blocks:
            result_lines.extend(original_lines[last_end + 1:start])
            indent = len(original_lines[start]) - len(original_lines[start].lstrip())
            block_tokens = tokens_per_line[start:end + 1]
            formatted_block = self._format_block(block_tokens, ' ' * indent)
            result_lines.extend(formatted_block)
            last_end = end

        result_lines.extend(original_lines[last_end + 1:])
        formatted_content = '\n'.join(result_lines)

        # 後処理: プレースホルダーを整形済みの複数行文字列に差し戻す
        final_content = self.restore_placeholders(formatted_content, placeholders)

        return final_content

    def _replace_multiline(self, content: str) -> Tuple[str, List[str]]:
        """'..'で連結された複数行文字列をプレースホルダーに置換する。"""
        placeholders = []
        def replacer(match):
            key = match.group(1)
            placeholders.append(match.group(0))
            placeholder_iidx = len(placeholders) - 1
            # 'key = "__PLACEHOLDER_n__"' の形式に変換
            return f'{key} = "__PLACEHOLDER_{placeholder_iidx}__"'

        # 任意のキー(group 1)に紐づく、'..'を1つ以上含む文字列連結(group 2)をキャプチャ
        pattern = re.compile(
            r'(\b[a-zA-Z_]\w*\b)\s*=\s*((?:"(?:\\.|[^"])*?"\s*\.\.\s*)+"(?:\\.|[^"])*?")',
            re.DOTALL
        )
        replaced_content = pattern.sub(replacer, content)
        return replaced_content, placeholders

    def restore_placeholders(self, formatted_content: str, placeholders: List[str]) -> str:
        """プレースホルダーを元に戻す"""
        def unreplacer(match):
            line_indent_str = match.group(1)
            key = match.group(2)
            index = int(match.group(3))
            trailing_comma = match.group(4)

            original_assignment = placeholders[index]
            _key, value_part = original_assignment.split('=', 1)

            parts = [p.strip() for p in value_part.split('..')]

            value_indent_str = line_indent_str + self.tokenizer.INDENT

            output_lines = [f"{line_indent_str}{key} ="]
            for i, part in enumerate(parts):
                separator = ' ..' if i < len(parts) - 1 else ''
                output_lines.append(f"{value_indent_str}{part}{separator}")

            output_lines[-1] += trailing_comma
            return '\n'.join(output_lines)

        # 任意のキー(group 2)に紐づくプレースホルダーを検出
        pattern = re.compile(
            r'(^\s*)(\b[a-zA-Z_]\w*\b)\s*=\s*"__PLACEHOLDER_(\d+)__"(,?)',
            re.MULTILINE
        )
        return pattern.sub(unreplacer, formatted_content)

    def _format_block(self, block_tokens: List[List[str]], base_indent: str) -> List[str]:
        """ブロックの枠組みを整形"""
        all_tokens = [t for line in block_tokens for t in line]
        try:
            start_idx = all_tokens.index('{') + 1
            end_idx = len(all_tokens) - 1 - all_tokens[::-1].index('}')
            content_tokens = all_tokens[start_idx:end_idx]
        except ValueError:
            return [f"{base_indent}UserControls = ordered() {{}}"]

        result = [f"{base_indent}UserControls = ordered() {{"]
        if content_tokens:
            child_indent = base_indent + self.tokenizer.INDENT
            result.extend(self._format_chunk_content(content_tokens, child_indent))
        result.append(f"{base_indent}}}")
        return result

    def _chunk_tokens(self, tokens: List[str]) -> List[List[str]]:
        """トークンリストを 'key = { ... }' または 'key = value,' 分割する。"""
        chunks, i = [], 0
        while i < len(tokens):
            start_idx = i
            if not (i + 1 < len(tokens) and tokens[i+1] == '='):
                i += 1
                continue

            value_start_idx = i + 2

            # Case 1: key = { ... }
            if value_start_idx < len(tokens) and tokens[value_start_idx] == '{':
                brace_end = self.tokenizer.find_brace_end(tokens, value_start_idx)
                if brace_end is not None:
                    end_idx = brace_end + 1
                    if end_idx < len(tokens) and tokens[end_idx] == ',':
                        end_idx += 1
                    chunks.append(tokens[start_idx:end_idx])
                    i = end_idx
                    continue

            else:  # Case 2: key = value,
                try:
                    end_of_chunk = tokens.index(',', start_idx) + 1
                except ValueError:
                    end_of_chunk = len(tokens)
                chunks.append(tokens[start_idx:end_of_chunk])
                i = end_of_chunk
                continue
            i += 1 # フォールバック
        return chunks

    def _format_chunk_content(self, tokens: List[str], child_indent: str) -> List[str]:
        """チャンク化されたトークンリストを整形し、文字列のリストとして返す"""
        result = []
        chunks = self._chunk_tokens(tokens)
        for chunk in chunks:
            if len(chunk) > 3 and chunk[2] == '{':  # key = { ... }チャンク
                key = chunk[0]
                inner_tokens = chunk[3:-2]  # { と }, を除く
                result.extend(self._format_multi_line(key, inner_tokens, child_indent, True))
            else:  # key = valueチャンク
                result.append(f"{child_indent}{' '.join(chunk)}")
        return result