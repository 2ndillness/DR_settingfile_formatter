import os
import argparse
import sys
from formatters.user_controls import UserControlsFormatter
from formatters.string_literal import StringLiteralFormatter
from file_utils import get_output_file, backup_file, read_file_content, write_file_content

RULE_MAP = {
    '1': 'user_controls',
    '2': 'string_literal',
    '3': 'all'
}

def parse_args():
    parser = argparse.ArgumentParser(description='整形ルール選択付き settingファイル整形ツール')
    parser.add_argument('file', nargs='?', help='処理対象ファイル')
    parser.add_argument('-o', '--overwrite', action='store_true', help='上書き保存')
    parser.add_argument('--backup', action='store_true', help='バックアップ作成')
    parser.add_argument('-r', '--rule',
                        choices=['user_controls', 'string_literal', 'all'],
                        default='all',
                        help='適用する整形ルール (user_controls, string_literal, all)')
    return parser.parse_args()

def get_user_input():
    print("=== settingファイル整形ツール ===")
    while True:
        file_path = input("ファイルパス: ").strip()
        if file_path and os.path.exists(file_path):
            break
        print("ファイルが見つかりません" if file_path else "パスを入力してください")
    while True:
        choice = input("保存方式 (1:上書き/2:別名): ").strip()
        if choice in ['1', '2']:
            break
        print("1 または 2 を選択してください")
    while True:
        rule = input(f"整形ルールを選択 (1:user_controls, 2:string_literal, 3:all): ").strip()
        if rule in RULE_MAP:
            break
        print("1, 2, 3 のいずれかを選択してください")
    return file_path, choice == '1', RULE_MAP[rule]

def apply_formatter(content: str, rule: str) -> str:
    """指定されたルールに基づいてコンテンツを整形する"""
    if rule == RULE_MAP['1']:
        return UserControlsFormatter().format_content(content)
    elif rule == RULE_MAP['2']:
        return StringLiteralFormatter().format_content(content)
    else:  # RULE_MAP['3']
        formatted = content
        for fmt in [UserControlsFormatter(), StringLiteralFormatter()]:
            formatted = fmt.format_content(formatted)
        return formatted

def process_file(input_file, overwrite=False, backup=False, rule='all') -> bool:
    if not os.path.exists(input_file):
        print(f"ファイルが見つかりません: {input_file}")
        return False

    output_file = get_output_file(input_file, overwrite)

    if backup and overwrite:
        try:
            backup_file(input_file)
        except Exception as e:
            print(f"バックアップ失敗: {e}")
            return False

    content = read_file_content(input_file)
    if content is None:
        return False

    try:
        formatted = apply_formatter(content, rule)
    except Exception as e:
        print(f"整形処理エラー: {e}")
        return False

    if write_file_content(output_file, formatted):
        action = "上書き" if overwrite else "別名"
        print(f"✓ 完了 ({action}): {output_file}")
        return True
    return False

def main():
    args = parse_args()
    if args.file:
        success = process_file(args.file, args.overwrite, args.backup, args.rule)
    else:
        input_file, overwrite, rule = get_user_input()
        success = process_file(input_file, overwrite, rule=rule)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()