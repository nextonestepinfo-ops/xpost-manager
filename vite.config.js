import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // GitHub Pagesにデプロイする場合、リポジトリ名に変更してください
  // 例: base: '/xpost-manager/'
  // ユーザー名.github.io のルートに置く場合は '/' のまま
  base: '/xpost-manager/',
})
