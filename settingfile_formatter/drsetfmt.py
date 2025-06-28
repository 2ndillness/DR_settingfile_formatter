import argparse
import sys
from pathlib import Path
from typing import Tuple, List

from config_loader import ConfigLoader, FormatterError
from file_utils import prepare_file, read_file_content, write_file_content

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

def _prompt_for_filepath() -> str:
    """対話形式でファイルパスを取得し、ファイルの存在を確認する"""
    while True:
        file_path = input('ファイルパスを入力してください: ').strip()
        if Path(file_path).is_file():
            return file_path
        print(f"エラー: ファイル '{file_path}' が見つからないか、ディレクトリです。")

def _prompt_for_save_options() -> Tuple[bool, bool]:
    """対話形式で保存方法（上書き、バックアップ）を取得する"""
    while True:
        choice = input('保存方式を選択してください (1:上書き / 2:別名): ').strip()
        if choice == '1':
            while True:
                backup_choice = input('バックアップを作成しますか？ (y/n): ').strip().lower()
                if backup_choice in ['y', 'n']:
                    return True, backup_choice == 'y'
                print("エラー: 'y' または 'n' を入力してください")
        elif choice == '2':
            return False, False
        print("エラー: '1' または '2' を入力してください")

def _prompt_for_rules(config: ConfigLoader) -> List[str]:
    """対話形式で適用する整形ルールを取得する"""
    print(config.build_rule_prompt())
    while True:
        rule_input = input('適用するルール番号を選択してください(スペース区切りで複数可): ').strip()
        choices = rule_input.split()

        if not choices:
            print('エラー: ルール番号を入力してください')
            continue
        try:
            return config.get_rule_names(choices)
        except ValueError as e:
            print(f'エラー: {e}')

def get_interactive_inputs(config: ConfigLoader) -> Tuple[str, bool, bool, List[str]]:
    """対話形式でユーザーから設定を取得する"""
    print('=== settingファイル整形ツール ===')
    file_path = _prompt_for_filepath()
    overwrite, backup = _prompt_for_save_options()
    rules = _prompt_for_rules(config)
    return file_path, overwrite, backup, rules

def apply_formatting(content: str, rules: List[str], config: ConfigLoader) -> str:
    """指定されたルールに従ってフォーマッターを適用する"""
    for f in config.get_formatters(rules):
        content = f.format_content(content)
    return content

def process_file(file_path: str, overwrite: bool, backup: bool, rules: List[str], config: ConfigLoader):
    """単一のファイルを読み込み、整形し、保存する"""
    output_path = prepare_file(file_path, overwrite, backup)
    input_path = Path(file_path)

    content = read_file_content(input_path)
    formatted_content = apply_formatting(content, rules, config)
    write_file_content(output_path, formatted_content)

    action = '上書き保存しました' if overwrite else '別名で保存しました'
    print(f'✓ 処理が完了しました ({action}): {output_path}')

def main():
    """アプリケーションのエントリーポイント"""
    try:
        config = ConfigLoader()
        args = parse_args(config)

        if args.file:
            file_path = args.file
            overwrite = args.overwrite
            backup = args.backup
            rules = args.rule
        else:
            file_path, overwrite, backup, rules = get_interactive_inputs(config)

        process_file(file_path, overwrite, backup, rules, config)

    except (FormatterError, FileNotFoundError, IOError, ValueError) as e:
        print(f'\nエラー: {e}', file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n処理を中断しました。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'\n予期せぬエラーが発生しました: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()