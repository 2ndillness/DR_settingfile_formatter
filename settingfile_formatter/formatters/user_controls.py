import re
from typing import List, Tuple
from .base import ContentFormatter


class UserControlsFormatter(ContentFormatter):
    """UserControlsブロックを整形"""
    BLOCK_START_TOKENS = ['UserControls', '=', 'ordered', '(', ')', '{']
    _REPLACE_PATTERN = re.compile(
        # 任意のキー(group 1)に紐づく、'..'を1つ以上含む文字列連結(group 2)をキャプチャ
        r'(\b[a-zA-Z_]\w*\b)\s*=\s*((?:"(?:\\.|[^"])*?"\s*\.\.\s*)+"(?:\\.|[^"])*?")',
        re.DOTALL
    )
    _RESTORE_PATTERN = re.compile(
        # 任意のキー(group 2)に紐づくプレースホルダーを検出
        r'(^\s*)(\b[a-zA-Z_]\w*\b)\s*=\s*"__PLACEHOLDER_(\d+)__"(,?)',
        re.MULTILINE
    )
    _QUOTED_STRING_PATTERN = re.compile(
        # エスケープ文字を考慮しつつ、ダブルクォートで囲まれた文字列を検出
        r'"(?:\\.|[^"])*?"'
    )

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

    def _replace_multiline(self, content: str) -> Tuple[str, List[List[str]]]:
        """連結された複数行文字列からクォート付きパーツを抽出し、プレースホルダーに置換する。"""
        placeholders = []
        def replacer(match):
            key = match.group(1)
            value_part = match.group(2)
            # 正規表現でクォート付きのパーツをすべて抽出
            quoted_parts = self._QUOTED_STRING_PATTERN.findall(value_part)
            placeholders.append(quoted_parts)
            placeholder_index = len(placeholders) - 1
            # 'key = "__PLACEHOLDER_n__"' の形式に変換
            return f'{key} = "__PLACEHOLDER_{placeholder_index}__"'

        replaced_content = self._REPLACE_PATTERN.sub(replacer, content)
        return replaced_content, placeholders

    def restore_placeholders(self, formatted_content: str, placeholders: List[List[str]]) -> str:
        """プレースホルダーを、保存しておいたクォート付きパーツを使って整形済みの複数行文字列に戻す"""
        def unreplacer(match):
            line_indent_str = match.group(1)
            key = match.group(2)
            index = int(match.group(3))
            trailing_comma = match.group(4)

            # 保存しておいたクォート付きのパーツリストを取得
            quoted_parts = placeholders[index]

            # 取得したパーツを元に、インデントと連結演算子を付与して再構築
            output_lines = [f"{line_indent_str}{key} ="]
            child_indent = line_indent_str + self.tokenizer.INDENT
            num_parts = len(quoted_parts)
            for i, part in enumerate(quoted_parts):
                separator = ' ..' if i < num_parts - 1 else trailing_comma
                output_lines.append(f"{child_indent}{part}{separator}")

            return '\n'.join(output_lines)

        return self._RESTORE_PATTERN.sub(unreplacer, formatted_content)

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
            result.extend(self._format_block_content(content_tokens, child_indent))
        result.append(f"{base_indent}}}")
        return result

    def _find_block_end(self, tokens: List[str], start_idx: int) -> int:
        """'{'で始まるブロックチャンクの終了インデックスを見つける"""
        brace_start = start_idx + 2
        brace_end = self.tokenizer.find_brace_end(tokens, brace_start)

        if brace_end is None:
            return start_idx + 1 # 処理不能な場合は、キーだけ進める

        end_idx = brace_end + 1
        # 末尾のカンマを含める
        if end_idx < len(tokens) and tokens[end_idx] == ',':
            end_idx += 1
        return end_idx

    def _find_simple_end(self, tokens: List[str], start_idx: int) -> int:
        """単純な代入チャンクの終了インデックスを見つける"""
        try:
            # 次のカンマまでをチャンクとする
            return tokens.index(',', start_idx) + 1
        except ValueError:
            # カンマがなければ最後までをチャンクとする
            return len(tokens)

    def _chunk_tokens(self, tokens: List[str]) -> List[List[str]]:
        """トークンリストを 'key = value,' または 'key = { ... },' の単位に分割する。"""
        chunks, i = [], 0
        while i < len(tokens):
            # 'key = value' の基本的な構造があるか確認
            if not (i + 2 < len(tokens) and tokens[i+1] == '='):
                i += 1
                continue

            start_idx = i
            end_idx = self._find_block_end(tokens, start_idx) if tokens[i+2] == '{' else self._find_simple_end(tokens, start_idx)
            chunks.append(tokens[start_idx:end_idx])
            i = end_idx
        return chunks

    def _format_block_content(self, tokens: List[str], child_indent: str) -> List[str]:
        """チャンク化されたトークンリストを整形し、文字列のリストとして返す"""
        result = []
        chunks = self._chunk_tokens(tokens)
        for chunk in chunks:
            if len(chunk) > 3 and chunk[2] == '{':  # key = { ... }チャンク
                key = chunk[0]
                inner_tokens = chunk[3:-2]  # { と }, を除く
                result.extend(self._format_multi_line(key, inner_tokens, child_indent, True))
            else:  # key = valueチャンク
                result.append(f"{child_indent}{self._recombine_tokens(chunk)}")
        return result