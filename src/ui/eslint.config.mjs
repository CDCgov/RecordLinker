import { dirname } from "path";
import { fileURLToPath } from "url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
});

const eslintConfig = [
  ...compat.config({
    ignorePatterns:"*/__mocks__/**/*.js",
    extends: ["eslint:recommended","next/core-web-vitals", "next/typescript", "prettier"],
    plugins: ["unused-imports"],//"@typescript-eslint",
    rules:{
      "@typescript-eslint/no-unused-vars": ["warn", { 
        caughtErrors: "none"
      }]
    }
  }),
];

export default eslintConfig;
