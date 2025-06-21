# settingfile formatter
これは`DaVinci Resolve`のマクロ用設定ファイル(.setting)の整形用`Python`スクリプトです。  

`DaVinci Resolve`が出力する`setting`ファイルをテキストエディタで再編集する際に、見辛い出力を整形して快適に再編集できるようにするツールです。

## 整形対象
### InstanceInput
`setting`ファイル最編集時にコントロールの順番入れ替えやラベルコントロールの差し込み等でバラバラになった`Inputxx`の番号を上から順に振り直します。
```lua
-- before
Input23 = InstanceInput {
    ...
},
Input58 = InstanceInput {
    ...
},
Input17 = InstanceInput {
    ...
},
Input23 = InstanceInput {
    ...
},
...
```
```lua
-- after
Input1 = InstanceInput {
    ...
},
Input2 = InstanceInput {
    ...
},
Input3 = InstanceInput {
    ...
},
Input4 = InstanceInput {
    ...
},
...
```
- `Inputxx = InstanceInput{...}`の形が対象です。`MainInput1 = InstanceInput {...}`等は対象となりません。
- 整形前に重複する番号があっても振り直しによって一意の番号になります。

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
## ファイル構成
```Bash
/
├─ drsetfmt.py              # 実行ファイル
├─ file_utils.py
├─ config_loader.py
├─ config.json
├─ cfggen.py
└─ formatters/
    ├─ __init__.py
    ├─ base.py
    ├─ instance_input.py
    ├─ string_literal.py
    ├─ user_controls.py
    └─ ...（他の整形ルールファイル）
```
|ファイル名 |内容     |
| :------- | :------ |
| drsetfmt|メインスクリプト。実行ファイル|
| file_utils|ファイル入出力に関するモジュール|
| config_loader|設定ファイル読み込みモジュール|
| cfggen|設定ファイル生成スクリプト|
| config ( json )|整形ルール設定ファイル|
|||
| base|整形処理の共通モジュール|
| instance_input|InstanceInput整形ルール|
| string_literal|文字列リテラル整形ルール|
| user_controls|UserControls整形ルール|

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
整形ルールを選択してください:
  1: instance_input
  2: string_literal
  3: user_controls
  4: 全てのルールを適用
適用するルール番号を選択してください(スペース区切りで複数可): 2 3
✓ 処理が完了しました (別名で保存しました): fixed_something.setting
```
2. 直接モード
```Bash
python drsetfmt.py something.setting
```
オプションを付けなかった場合のディフォルトは
- 別名保存 ( 読み込んだファイル名の先頭にfixed_を付けて出力 )
- バックアップ無し
- 整形ルールは全て適用  

|オプション|コマンド|
|--------|--------|
|上書き保存|--overwrite, -o|
|バックアップ作成|--backup|
|整形ルール指定|--rule, -r <br>instance_input<br>string_literal<br>user_controls|
```Bash
python drsetfmt.py something.setting -o --backup -r user_controls instance_input
```
- `--rule`もしくは`-r`の後に半角スペース区切りで整形ルールを指定 ( 複数指定可能 )
3. ヘルプ表示  
`--help`もしくは`-h`で実行可能なコマンドを確認できます。
```Bash
python drsetfmt.py -h
```

## 整形ルールの追加・削除
独自の整形ルールを追加したり、既存の整形ルールを削除したりできます。
1. `formatters/`ディレクトリに`XxxFormatter`クラスを持つ整形ルール用`Python`ファイルを追加、または不要な整形ルールファイルを削除
2. `config.json`と`formatters/__init__.py`を更新( 手動 or 半自動 )  
- 半自動更新  
プロジェクトルートで`cfggen.py`を実行
```bash
python cfggen.py
```
- `config.json`と`formatters/__init__.py`が最新状態に更新されます。
## 注意事項
本スクリプトは4スペースインデントを想定しています。(`Lua`の推奨インデント )それ以外のインデントでは正常に整形されない場合があります。  
また、`DaVinci Resolve`が出力する`setting`ファイルはタブインデントなので事前に4スペースインデントに変換しておく方が良いです。  
タブをスペースに変換するのは`VSCode`が便利です。

このスクリプトには特別な使用条件はありません。自由にご使用・改変・配布していただいて構いませんが、作者自身の利用や再配布の自由は常に保証されるものとします。

なお、本スクリプトの使用または改変により生じたいかなる損害についても、作者は一切の責任を負いかねます。あくまでも自己責任でご利用ください。
