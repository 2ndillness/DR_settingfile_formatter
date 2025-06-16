import os
import shutil
from typing import Optional, Tuple


def get_output_file(input_file: str, overwrite: bool, prefix: str = "fixed_") -> str:
    """出力ファイル名を取得"""
    if overwrite:
        return input_file
    return os.path.join(os.path.dirname(input_file), prefix + os.path.basename(input_file))


def backup_file(input_file: str) -> str:
    """バックアップファイルを作成"""
    backup_path = f"{input_file}.bak"
    shutil.copy2(input_file, backup_path)
    print(f"バックアップ: {backup_path}")
    return backup_path


def read_file_content(file_path: str) -> Optional[str]:
    """ファイルの内容を読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ファイル {file_path} が見つかりません")
        return None
    except Exception as e:
        print(f"ファイル読み込み中にエラーが発生しました: {e}")
        return None


def write_file_content(file_path: str, content: str) -> bool:
    """ファイルに内容を書き込む"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"ファイル書き込み中にエラーが発生しました: {e}")
        return False


def process_file(input_file: str, overwrite: bool, backup: bool = False) -> Tuple[bool, Optional[str]]:
    """ファイル処理のメイン関数"""
    if not os.path.exists(input_file):
        print(f"ファイル {input_file} が見つかりません")
        return False, None

    output_file = get_output_file(input_file, overwrite)

    if backup and overwrite:
        backup_file(input_file)

    content = read_file_content(input_file)
    if content is None:
        return False, None

    return True, output_file