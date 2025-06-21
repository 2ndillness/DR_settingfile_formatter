from .base import ContentFormatter
import re

class InstanceInputFormatter(ContentFormatter):
    """Inputxx = InstanceInput 再インデックス処理"""

    INPUT_PATTERN = re.compile(r'^(\s*)Input\d+\s*=\s*InstanceInput\s*\{')

    def format_content(self, content: str) -> str:
        lines = content.splitlines(keepends=True)
        new_lines = []
        input_count = 1
        for line in lines:
            m = self.INPUT_PATTERN.match(line)
            if m:
                indent = m.group(1)
                replaced = f"{indent}Input{input_count} = InstanceInput {{"
                new_line = replaced + line[len(m.group(0)):]
                new_lines.append(new_line)
                input_count += 1
            else:
                new_lines.append(line)
        return ''.join(new_lines)
