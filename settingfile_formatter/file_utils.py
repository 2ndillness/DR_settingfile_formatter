import shutil
from pathlib import Path

def prepare_file(file_path: str, overwrite: bool, backup: bool, prefix: str = 'fixed_') -> Path:
    """ファイルの存在確認、バックアップ作成、出力ファイルパスの決定を行う"""
    input_path = Path(file_path)
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

def read_file_content(file_path: Path) -> str:
    """ファイルを読み込み、その内容を返す"""
    try:
        return file_path.read_text(encoding='utf-8')
    except Exception as e:
        raise IOError(f'ファイルの読み込みに失敗しました: {file_path}') from e

def write_file_content(file_path: Path, content: str):
    """ファイルに内容を書き込む"""
    try:
        file_path.write_text(content, encoding='utf-8')
    except Exception as e:
        raise IOError(f'ファイルの書き込みに失敗しました: {file_path}') from e