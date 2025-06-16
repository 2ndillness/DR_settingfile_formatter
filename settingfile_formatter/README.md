# settingfile formatter
これは`DaVinci Resolve`のマクロ用設定ファイル(.setting)の整形用`Python`スクリプトです。  

`DaVinci Resolve`が出力する`setting`ファイルをテキストエディタで再編集する際に、見辛い出力を整形して快適に再編集できるようにするツールです。
## ファイル構成
```Bash
/
├─ drsetfmt.py              # 実行ファイル
├─ file_utils.py
└─ formatters/
    ├─ __init__.py
    ├─ base.py
    ├─ string_literal.py
    └─ user_controls.py
```
|ファイル名 |内容     |
| :------- | :------ |
| drsetfmt|メインスクリプト。実行ファイルです|
| file_utils|ファイル入出力に関するモジュール|
| base|整形処理の共通モジュール|
| string_literal|文字列リテラル整形ルール|
| user_controls|UserControls整形ルール|
## 整形対象
### 文字列リテラル
マクロを書き出すとレンダースクリプトや`Expression`、コメント等のテキストコントロールに入力した文字列がエスケープされた改行文字`\n`を含み1行で出力されるので、本来の見た目に近い形に整形します。
```lua
-- before
FrameRenderScript = Input { Value = "if check then\n    return valueTrue\nelse\n    return valueFalse\nend\n", }
```
```lua
-- after
FrameRenderScript = Input { 
    Value = 
    "if check then\n" ..
    "    return valueTrue\n" ..
    "else\n" ..
    "    return valueFalse\n" ..
    "end\n",
}
```
- エスケープされた改行(`\n`)毎に分割し`..`演算子で結合した後実改行を挿入します。
- 元々1行で書かれていた場合は整形の対象となりません。  
- `Expression`で1行で表示されていても内部的に改行コードが含まれていれば整形の対象となります。
### UserControls
コントロールを追加した時に`UserControls = ordered() {...} `ブロックが1行で出力される場合があるのでカンマ毎に改行して整形します。
```lua
-- before
UserControls = ordered() { aaa = { bbb = "ccc" }, ddd = { eee = 123, fff = true } }
```
```lua
-- after
UserControls = ordered() {
    aaa = { bbb = "ccc", },
    ddd = {
        eee = 123,
        fff = true,
    },
}
```
- `xxx = {...}`内の要素数が1つの場合は1行で出力します。
- 最終要素の後のカンマの有無に関わらず、最終要素の後にはカンマが付いた状態で出力します。  
(`Lua`では許容されるため、将来的な編集時のカンマ忘れによる構文エラーを防ぐ目的)
## 使用方法
1. 事前に`setting`ファイルを4スペースインデントに変換
2. 任意のディレクトリにファイル構成図のようにファイルを配置し`CLI`から実行ファイルの`drsetfmt.py`を実行  
#### 実行形式
1. 対話モード
```Bash
python drsetfmt.py
=== settingファイル整形ツール ===
ファイルパス: something.setting
保存方式 (1:上書き/2:別名): 2
整形ルールを選択 (1:user_controls, 2:string_literal, 3:all): 3
✓ 完了 (別名): fixed_something.setting
```
2. 直接モード
```Bash
python drsetfmt.py something.setting
```
上記コマンドで別名保存(読み込みファイル名の先頭にfixed_を付けて出力)、整形ルールは全て適用  
|オプション|コマンド|
|--------|--------|
|上書き保存|--overwrite, -o|
|バックアップ作成|--backup|
|整形ルール指定|--rule, -r <br>user_controls<br>string_literal|
```Bash
python drsetfmt.py something.setting -o --backup -r user_controls
```
## 注意事項
本スクリプトは4スペースインデントを想定しています。それ以外のインデントでは正常に整形されない場合があります。  
また、`DaVinci Resolve`が出力する`setting`ファイルはタブインデントなので事前に4スペースインデントに変換しておく方が良いです。  

このスクリプトには特別な使用条件はありません。自由にご使用・改変・配布していただいて構いませんが、作者自身の利用や再配布の自由は常に保証されるものとします。

なお、本スクリプトの使用または改変により生じたいかなる損害についても、作者は一切の責任を負いかねます。あくまでも自己責任でご利用ください。
