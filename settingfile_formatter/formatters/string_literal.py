import re
from collections import defaultdict
from .base import ContentFormatter


class StringLiteralFormatter(ContentFormatter):

    def __init__(self):
        super().__init__()

    def find_string_targets(self, line_tokens):
        targets = []
        stack = []
        current_context = {'key': None, 'after_equals': False, 'nest_level': 0}
        for line_num, tokens in enumerate(line_tokens):
            for token in tokens:
                if self._is_identifier(token):
                    current_context['key'] = token
                elif token == '=':
                    current_context['after_equals'] = True
                elif token == '{' or token == '}':
                    current_context['nest_level'] = self.tokenizer.update_nest_level(token, current_context['nest_level'])
                    if token == '{' and current_context['key']:
                        stack.append((current_context['key'], line_num, current_context['nest_level'] - 1))
                    elif token == '}' and stack:
                        stack.pop()
                    self._reset_context(current_context)
                elif self._is_multiline_string(token, current_context['after_equals']):
                    target = self._create_target(token, current_context['key'], stack, line_num)
                    targets.append(target)
                    self._reset_context(current_context)
                else:
                    self._reset_context(current_context)
        return targets

    def _is_identifier(self, token):
        return self.tokenizer.pattern.match(token) and (token[0].isalpha() or token[0] == '_')

    def _is_multiline_string(self, token, after_equals):
        return after_equals and token.startswith('"') and '\\n' in token[1:-1]

    def _reset_context(self, context):
        context.update({'key': None, 'after_equals': False})

    def _create_target(self, token, key, stack, line_num):
        parent_info = stack[-1] if stack else (None, None, 0)
        return {
            'key': key,
            'value': token[1:-1],
            'parent_key': parent_info[0],
            'parent_line': parent_info[1],
            'parent_indent': self.tokenizer.INDENT * parent_info[2],
            'target_line': line_num
        }

    def format_string_literal(self, indent, key_part, value, add_comma=True):
        lines = [f"{indent}{key_part}\n"]
        parts = value.split('\\n')
        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            suffix = (',' if add_comma else '') if is_last else ' ..'
            quote_content = f'"{part}\\n"' if not is_last else f'"{part}"'
            lines.append(f"{indent}{quote_content}{suffix}\n")
        return lines

    def join_tokens_until_key(self, tokens, target_key):
        result_tokens = []
        for token in tokens:
            if token == target_key:
                break
            result_tokens.append(token)
        return ' '.join(result_tokens).strip()

    def is_already_formatted(self, lines, idx):
        if idx + 1 < len(lines):
            if re.match(r'.+=\s*$', lines[idx]) and re.match(r'\s*".*', lines[idx + 1]):
                return True
        return False

    def format_content(self, content: str) -> str:
        lines = content.splitlines(keepends=True)
        line_tokens = self.tokenizer.tokenize_content(content)
        targets = self.find_string_targets(line_tokens)
        target_by_line = defaultdict(list)
        for target in targets:
            target_by_line[target['target_line']].append(target)

        fixed_lines = []
        i = 0
        while i < len(lines):
            # 整形済みパターンならスキップ
            if self.is_already_formatted(lines, i):
                fixed_lines.append(lines[i])
                fixed_lines.append(lines[i + 1])
                i += 2
                continue
            if i in target_by_line:
                for target in target_by_line[i]:
                    indent = target['parent_indent'] + self.tokenizer.INDENT
                    if target['parent_line'] == target['target_line']:
                        parent_part = self.join_tokens_until_key(line_tokens[i], target['key'])
                        fixed_lines.append(f"{target['parent_indent']}{parent_part}\n")
                        fixed_lines.extend(
                            self.format_string_literal(indent, f"{target['key']} =", target['value'])
                        )
                        fixed_lines.append(f"{target['parent_indent']}}},\n")
                    else:
                        fixed_lines.extend(
                            self.format_string_literal(indent, f"{target['key']} =", target['value'])
                        )
            else:
                fixed_lines.append(lines[i])
            i += 1
        return ''.join(fixed_lines)