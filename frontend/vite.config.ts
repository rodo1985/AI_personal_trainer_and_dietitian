import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Build and test configuration for the React frontend.
 */
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts"
  }
});
