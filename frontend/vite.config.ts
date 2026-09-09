import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Minimal chat + citations UI only — no streaming inspector or Mermaid viewer
// in MVP scope (CLAUDE.md).
export default defineConfig({
  plugins: [react()],
});
