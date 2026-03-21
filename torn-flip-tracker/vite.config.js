import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// VITE_BASE_PATH is set by the GitHub Actions workflow to '/torn-flip-tracker/'
// For local dev it defaults to '/' (root)
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH || '/',
})
