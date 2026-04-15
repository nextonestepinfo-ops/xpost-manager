# X Post Manager

アフィリエイト投稿管理エディター for X (Twitter)

## 機能

- スレッド形式の投稿作成・管理
- ツイートごとの画像枚数設定（1〜4枚）
- 画像ライブラリ（ファイル/フォルダ一括アップロード、URL取得）
- 画像の一括割り当て（ファイル名順）
- X風スレッドプレビュー
- コンプライアンスチェック（リスクワード検出）
- 送信履歴管理・再利用
- バックアップ/復元（JSON形式）
- 画像枚数の不一致警告

## セットアップ

### 前提条件

- [Node.js](https://nodejs.org/) v18以上
- [Git](https://git-scm.com/)

### ローカルで動かす

```bash
# リポジトリをクローン
git clone https://github.com/あなたのユーザー名/xpost-manager.git
cd xpost-manager

# 依存パッケージをインストール
npm install

# 開発サーバー起動（http://localhost:5173 で開きます）
npm run dev
```

## GitHub Pagesにデプロイ

### 手順

1. **GitHubでリポジトリ作成**
   - https://github.com/new でリポジトリを作成
   - リポジトリ名: `xpost-manager`（`vite.config.js` の `base` と一致させる）

2. **コードをプッシュ**
   ```bash
   cd xpost-manager
   git init
   git add .
   git commit -m "first commit"
   git branch -M main
   git remote add origin https://github.com/あなたのユーザー名/xpost-manager.git
   git push -u origin main
   ```

3. **GitHub Pagesを有効化**
   - リポジトリの Settings → Pages
   - Source を「GitHub Actions」に変更
   - pushすると自動でビルド＆デプロイされます

4. **完了！**
   - `https://あなたのユーザー名.github.io/xpost-manager/` でアクセスできます

### リポジトリ名を変える場合

`vite.config.js` の `base` を変更してください：

```js
base: '/あなたのリポジトリ名/',
```

## 画像URLの一括取得（Pythonスクリプト）

同梱の `image_downloader.py` を使えば、Webページ内の全画像URLを自動抽出できます：

```bash
pip install requests beautifulsoup4
python image_downloader.py https://example.com/products ./images
```

ダウンロードした画像フォルダをエディターの「📁 フォルダ一括」で読み込めます。

## ライセンス

MIT
