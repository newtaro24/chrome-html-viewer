# Chrome Extension と MCP サーバーの使用例

## セットアップ手順

### 1. Chrome拡張機能のインストール

1. Chrome を開き、`chrome://extensions/` にアクセス
2. 右上の「デベロッパーモード」を有効化
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. `chrome-extension` ディレクトリを選択

### 2. MCP サーバーの起動

```bash
# 依存関係のインストール
pip install websockets mcp

# サーバーの起動
cd mcp-server
python mcp_chrome_server.py
```

### 3. Claude Desktop の設定

`claude_desktop_config.json` を以下の場所に配置:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

設定内容:
```json
{
  "mcpServers": {
    "chrome-bridge": {
      "command": "python",
      "args": ["/path/to/mcp-server/mcp_chrome_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/mcp/library"
      }
    }
  }
}
```

## 基本的な使用方法

### 1. ページ情報の取得

```
Claude: 現在開いているページのHTMLとCSSを取得してください
```

Claude は以下の情報を取得します:
- 完全なHTML構造
- すべてのスタイルシート
- インラインスタイル
- ビューポートサイズ

### 2. 要素の検査

```
Claude: .header-navigation クラスのスタイルを詳しく教えてください
```

指定したセレクタに一致する要素の:
- 計算済みスタイル
- 位置とサイズ
- HTML構造

### 3. リアルタイムCSS編集

```
Claude: ヘッダーの背景色を #f0f0f0 に変更してプレビューを見せてください
```

CSSを直接ページに注入してリアルタイムでプレビュー可能

### 4. スクリーンショット撮影

```
Claude: 現在のページのスクリーンショットを撮ってください
```

ページの表示領域のスクリーンショットを保存

## 高度な使用例

### デザインシステムの検証

```
Claude: このページで使用されている色とフォントを分析して、
デザインシステムに準拠しているか確認してください
```

Claude は以下を分析:
- 使用されている全ての色とその使用頻度
- フォントファミリーの一覧
- 余白（margin/padding）の一貫性
- メディアクエリのブレークポイント

### アクセシビリティチェック

```
Claude: このページのアクセシビリティの問題を指摘してください
```

以下の項目をチェック:
- alt属性のない画像
- 見出し構造の問題
- 色のコントラスト比（簡易チェック）

### Figmaデザインとの比較

```
Claude: このFigmaデザイン [URL] と現在のページを比較して、
実装の差異を教えてください
```

※ 現在はプレースホルダー実装。将来的にFigma APIと連携予定

### Git上のCSSとの差分確認

```
Claude: 現在のページのスタイルと、git の src/styles/main.css を
比較して違いを教えてください
```

ローカルのソースコードと実際のページのスタイルを比較

## Chrome拡張機能のUI機能

### 要素インスペクター
- ポップアップの「要素を検査」ボタンをクリック
- マウスホバーで要素をハイライト表示
- クリックで詳細情報を取得

### スタイル比較
1. 「現在のスタイルを記録」で初期状態を保存
2. ページに変更を加える
3. 「スタイルの変更を比較」で差分を確認

### デザインオーバーレイ
- 参照画像を半透明でオーバーレイ表示
- スライダーで透明度を調整
- ピクセルパーフェクトな比較が可能

### パフォーマンスメトリクス
- ページ読み込み時間
- DOM要素数
- CSSルール数
- 画像数

## トラブルシューティング

### 接続できない場合

1. MCPサーバーが起動しているか確認
   ```bash
   ps aux | grep mcp_chrome_server
   ```

2. WebSocketポート（8765）が使用可能か確認
   ```bash
   lsof -i :8765
   ```

3. Chrome拡張機能のコンソールでエラーを確認
   - 拡張機能ページで「サービスワーカー」をクリック
   - コンソールタブでエラーメッセージを確認

### スタイル情報が取得できない

- CORS制限により外部CSSが読み込めない場合があります
- その場合は computed styles のみ取得されます

### MCPサーバーが認識されない

1. Claude Desktop を完全に終了
2. 設定ファイルのパスと内容を確認
3. Claude Desktop を再起動

## 今後の拡張予定

- Figma API との直接連携
- より詳細なアクセシビリティチェック
- パフォーマンス分析の強化
- 複数タブの同時監視
- 変更履歴の記録と再生
