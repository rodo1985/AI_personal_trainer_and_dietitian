import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Provides Vite and Vitest configuration for the day-log frontend.
 *
 * @returns The Vite runtime and test configuration.
 * @example
 * // Vite loads this file automatically when running npm scripts.
 */
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    coverage: {
      reporter: ["text", "html"]
    }
  }
});
