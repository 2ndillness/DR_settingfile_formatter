import argparse
import sys
from pathlib import Path
from typing import Tuple, List

from config_loader import ConfigLoader, FormatterError
from file_utils import validate_and_prepare_file

def parse_args(config: ConfigLoader) -> argparse.Namespace:
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description='整形ルール選択付き settingファイル整形ツール')
    available_rules = config.get_formatter_choices()

    parser.add_argument('file', nargs='?', help='処理対象ファイル')
    parser.add_argument('-o', '--overwrite', action='store_true', help='上書き保存する')
    parser.add_argument('--backup', action='store_true', help='上書き保存時にバックアップを作成する')
    parser.add_argument(
        '-r', '--rule',
        nargs='+',  # 1つ以上の引数を受け取る
        metavar='RULE',
        default=['all'],
        help=f"適用する整形ルール (複数指定可)未指定時は 'all'利用可能: {', '.join(available_rules)}",
    )
    return parser.parse_args()

def prompt_user_for_settings(config: ConfigLoader) -> Tuple[str, bool, List[str]]:
    """対話形式でユーザーから設定を取得する"""
    print('=== settingファイル整形ツール ===')
    while True:
        file_path_str = input('ファイルパスを入力してください: ').strip()
        if Path(file_path_str).exists():
            break
        print(f"エラー: ファイル '{file_path_str}' が見つかりません")

    while True:
        choice = input('保存方式を選択してください (1:上書き / 2:別名): ').strip()
        if choice in ['1', '2']:
            break
        print("エラー: '1' または '2' を入力してください")

    while True:
        print(config.build_rule_prompt())
        rule_input = input('適用するルール番号を選択してください(スペース区切りで複数可): ').strip()
        choices = [c.strip() for c in rule_input.split() if c.strip()]

        if not choices:
            print('エラー: ルール番号を入力してください')
            continue

        try:
            selected_rules = config.get_rule_names_from_choices(choices)
            break
        except ValueError as e:
            print(f'エラー: {e}')

    return file_path_str, choice == '1', selected_rules

def apply_formatting(content: str, rules: List[str], config: ConfigLoader) -> str:
    for f in config.get_formatters_by_rules(rules):
        content = f.format_content(content)
    return content

def process_file(file_path_str: str, overwrite: bool, backup: bool, rules: List[str], config: ConfigLoader):
    output_path = validate_and_prepare_file(file_path_str, overwrite, backup)
    input_path = Path(file_path_str)

    try:
        content = input_path.read_text(encoding='utf-8')
    except Exception as e:
        raise IOError(f'ファイルの読み込みに失敗しました: {input_path}') from e

    try:
        output_path.write_text(apply_formatting(content, rules, config), encoding='utf-8')
    except Exception as e:
        raise IOError(f'ファイルの書き込みに失敗しました: {output_path}') from e

    action = '上書き保存しました' if overwrite else '別名で保存しました'
    print(f'✓ 処理が完了しました ({action}): {output_path}')

def main():
    """アプリケーションのエントリーポイント"""
    try:
        config = ConfigLoader()
        args = parse_args(config)

        if args.file:
            process_file(args.file, args.overwrite, args.backup, args.rule, config)
        else:
            file_path, overwrite, rules = prompt_user_for_settings(config)
            process_file(file_path, overwrite, backup=False, rules=rules, config=config)

    except (FormatterError, FileNotFoundError, IOError, ValueError) as e:
        print(f'\nエラー: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'\n予期せぬエラーが発生しました: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()