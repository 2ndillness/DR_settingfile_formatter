import re
import os
import sys
import argparse
from collections import defaultdict


class SettingFormatter:
    """設定ファイルの文字列リテラル整形クラス"""

    def __init__(self, input_file=None, overwrite=False):
        self.input_file = input_file
        self.overwrite = overwrite
        self.output_file = None
        self.token_pattern = r'([a-zA-Z_][a-zA-Z0-9_.]*)|(".*?[^\\]")|([{}(),=])'

        if input_file:
            self._set_output_file()

    def _set_output_file(self):
        """出力ファイル名を設定"""
        if self.overwrite:
            self.output_file = self.input_file
        else:
            dir_name = os.path.dirname(self.input_file)
            base_name = os.path.basename(self.input_file)
            self.output_file = os.path.join(dir_name, f"fixed_{base_name}")

    def set_input_file(self, input_file, overwrite=False):
        """入力ファイルと保存方式を設定"""
        self.input_file = input_file
        self.overwrite = overwrite
        self._set_output_file()

    def get_user_input(self):
        """ユーザーから入力ファイルと保存方式を取得"""
        print("=== 設定ファイル整形ツール ===")

        # ファイル選択
        while True:
            input_file = input("整形したいファイルのパスを入力してください: ").strip()
            if not input_file:
                print("ファイルパスを入力してください。")
                continue
            if not os.path.exists(input_file):
                print(f"ファイル '{input_file}' が見つかりません。")
                continue
            break

        # 保存方式選択
        while True:
            print("\n保存方式を選択してください:")
            print("1. 上書き保存")
            print("2. 別名保存 (ファイル名の先頭に 'fixed_' を付加)")
            choice = input("選択 (1 または 2): ").strip()

            if choice == "1":
                overwrite = True
                break
            elif choice == "2":
                overwrite = False
                break
            else:
                print("1 または 2 を選択してください。")

        self.set_input_file(input_file, overwrite)
        return True
    def tokenize_lines(self, lines):
        """各行をトークン化"""
        return [
            [match[0] or match[1] or match[2] for match in re.findall(self.token_pattern, line)]
            for line in lines
        ]

    def find_string_targets(self, line_tokens):
        """改行エスケープを含む文字列リテラルを特定"""
        targets = []
        stack = []  # (親ノードキー, 行番号, ネストレベル)
        current_context = {'key': None, 'after_equals': False, 'nest_level': 0}

        for line_num, tokens in enumerate(line_tokens):
            for token in tokens:
                if self._is_identifier(token):
                    current_context['key'] = token
                elif token == '=':
                    current_context['after_equals'] = True
                elif token == '{':
                    if current_context['key']:
                        stack.append((current_context['key'], line_num, current_context['nest_level']))
                    current_context['nest_level'] += 1
                    self._reset_context(current_context)
                elif token == '}':
                    if stack:
                        stack.pop()
                    current_context['nest_level'] -= 1
                    self._reset_context(current_context)
                elif self._is_multiline_string(token, current_context['after_equals']):
                    target = self._create_target(token, current_context['key'], stack, line_num)
                    targets.append(target)
                    self._reset_context(current_context)
                else:
                    self._reset_context(current_context)

        return targets

    def _is_identifier(self, token):
        """識別子かどうか判定"""
        return re.match(r'[a-zA-Z_][a-zA-Z0-9_.]*$', token) is not None

    def _is_multiline_string(self, token, after_equals):
        """改行エスケープを含む文字列リテラルかどうか判定"""
        return after_equals and token.startswith('"') and '\\n' in token[1:-1]

    def _reset_context(self, context):
        """コンテキストをリセット"""
        context.update({'key': None, 'after_equals': False})

    def _create_target(self, token, key, stack, line_num):
        """ターゲット情報を作成"""
        parent_info = stack[-1] if stack else (None, None, 0)
        return {
            'key': key,
            'value': token[1:-1],  # クォートを除去
            'parent_key': parent_info[0],
            'parent_line': parent_info[1],
            'parent_indent': '    ' * parent_info[2],
            'target_line': line_num
        }

    def format_string_literal(self, indent, key_part, value, add_comma=True):
        """文字列リテラルを整形"""
        lines = [f"{indent}{key_part}\n"]
        parts = value.split('\\n')

        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            suffix = (',' if add_comma else '') if is_last else ' ..'
            quote_content = f'"{part}\\n"' if not is_last else f'"{part}"'
            lines.append(f"{indent}{quote_content}{suffix}\n")

        return lines

    def join_tokens_until_key(self, tokens, target_key):
        """指定キーまでのトークンを結合"""
        result_tokens = []
        for token in tokens:
            if token == target_key:
                break
            result_tokens.append(token)

        return ' '.join(result_tokens).strip()

    def process_file(self):
        """メイン処理"""
        if not self.input_file or not self.output_file:
            print("Error: Input or output file not set.")
            return False

        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Input file '{self.input_file}' not found.")
            return False

        line_tokens = self.tokenize_lines(lines)
        targets = self.find_string_targets(line_tokens)

        # 処理対象行をグループ化
        target_by_line = defaultdict(list)
        for target in targets:
            target_by_line[target['target_line']].append(target)

        # 整形処理
        fixed_lines = []
        for i, line in enumerate(lines):
            if i in target_by_line:
                for target in target_by_line[i]:
                    indent = target['parent_indent'] + '    '

                    if target['parent_line'] == target['target_line']:
                        # 親ノードと同じ行の場合
                        parent_part = self.join_tokens_until_key(line_tokens[i], target['key'])
                        fixed_lines.append(f"{target['parent_indent']}{parent_part}\n")
                        fixed_lines.extend(
                            self.format_string_literal(indent, f"{target['key']} =", target['value'])
                        )
                        fixed_lines.append(f"{target['parent_indent']}}},\n")
                    else:
                        # 別行の場合
                        fixed_lines.extend(
                            self.format_string_literal(indent, f"{target['key']} =", target['value'])
                        )
            else:
                fixed_lines.append(line)

        # ファイル出力
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            return True
        except IOError:
            print(f"Error: Failed to write to output file '{self.output_file}'.")
            return False


def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description='設定ファイルの文字列リテラル整形ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog =
'''
使用例:
python formatter.py                          # 対話式実行
python formatter.py config.setting           # 別名保存
python formatter.py config.setting -o        # 上書き保存
python formatter.py config.setting --backup  # バックアップ付き上書き
'''
    )

    parser.add_argument('file', nargs='?', help='処理対象のファイルパス')
    parser.add_argument('-o', '--overwrite', action='store_true',
    help = '上書き保存（デフォルトは別名保存）')
    parser.add_argument('--backup', action='store_true',
    help = '上書き前にバックアップを作成（.bakファイル）')

    return parser.parse_args()


def create_backup(file_path):
    """バックアップファイルを作成"""
    backup_path = f"{file_path}.bak"
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"バックアップ作成: '{backup_path}'")
        return True
    except Exception as e:
        print(f"バックアップ作成失敗: {e}")
        return False
def main():
    """メイン関数"""
    args = parse_arguments()
    formatter = SettingFormatter()

    # コマンドライン引数での実行
    if args.file:
        if not os.path.exists(args.file):
            print(f"エラー: ファイル '{args.file}' が見つかりません。")
            sys.exit(1)

        # バックアップ作成
        if args.backup and args.overwrite:
            if not create_backup(args.file):
                print("バックアップ作成に失敗しました。処理を中止します。")
                sys.exit(1)

        formatter.set_input_file(args.file, args.overwrite)

        action = "上書き保存" if args.overwrite else "別名保存"
        backup_info = " (バックアップ付き)" if args.backup and args.overwrite else ""

        print(f"処理中: '{formatter.input_file}' -> '{formatter.output_file}' ({action}{backup_info})")

        if formatter.process_file():
            print(f"✓ 整形完了: '{formatter.output_file}'")
        else:
            print("✗ 整形に失敗しました。")
            sys.exit(1)

    else:
        # 対話式実行
        if not formatter.get_user_input():
            return

        print(f"\n処理中: '{formatter.input_file}' -> '{formatter.output_file}'")

        if formatter.process_file():
            action = "上書き保存" if formatter.overwrite else "別名保存"
            print(f"✓ 整形完了 ({action}): '{formatter.output_file}'")
        else:
            print("✗ 整形に失敗しました。")


def batch_mode(input_file, overwrite=False):
    """バッチ処理用関数（プログラムから呼び出す場合）"""
    formatter = SettingFormatter()
    formatter.set_input_file(input_file, overwrite)
    return formatter.process_file()


if __name__ == "__main__":
    main()
