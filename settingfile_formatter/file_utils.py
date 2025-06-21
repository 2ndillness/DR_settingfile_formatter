import shutil
from pathlib import Path

def validate_and_prepare_file(file_path_str: str, overwrite: bool, backup: bool, prefix: str = 'fixed_') -> Path:
    """ファイルの存在確認、バックアップ作成、出力ファイルパスの決定を行う"""
    input_path = Path(file_path_str)
    if not input_path.is_file():
        raise FileNotFoundError(f'指定されたファイルが見つかりません: {input_path}')

    if backup and overwrite:
        backup_path = input_path.with_suffix(input_path.suffix + '.bak')
        try:
            shutil.copy2(input_path, backup_path)
            print(f'情報: バックアップを作成しました: {backup_path}')
        except Exception as e:
            raise IOError(f'ファイルのバックアップに失敗しました: {backup_path}') from e

    return input_path if overwrite else input_path.parent / (prefix + input_path.name)