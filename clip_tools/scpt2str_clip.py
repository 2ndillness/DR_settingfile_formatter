import pyperclip

# クリップボードに格納されたテキストデータをLua文字列に変換してクリップボードに格納するスクリプト
def format_lua_string(text: str) -> str:
    lines = text.splitlines()
    formatted_lines = []

    for i, line in enumerate(lines):
        # エスケープ処理（\ → \\, " → \", 改行 → \n）
        escaped = line.replace('\\', '\\\\').replace('"', '\\"')
        if i < len(lines) - 1:
            escaped += '\\n'
        quoted = f'"{escaped}"'
        if i < len(lines) - 1:
            quoted += ' ..'
        formatted_lines.append(quoted)

    return '\n'.join(formatted_lines)

# クリップボード経由で処理する関数
def process_clipboard():
    text = pyperclip.paste()  # クリップボードの内容を取得
    formatted_text = format_lua_string(text)
    pyperclip.copy(formatted_text)  # 変換後のデータをクリップボードに格納
    print("変換完了！クリップボードにコピーされました。")

# --- メイン処理 ---
if __name__ == "__main__":
    process_clipboard()
