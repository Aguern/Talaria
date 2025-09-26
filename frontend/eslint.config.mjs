import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const compat = new FlatCompat({ baseDirectory: __dirname });

export default [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "import/order": [
        "warn",
        {
          "alphabetize": { order: "asc", caseInsensitive: true },
          "newlines-between": "always",
          "groups": ["builtin", "external", "internal", ["parent", "sibling"], "index", "object", "type"],
          "pathGroups": [{ pattern: "@/**", group: "internal", position: "after" }],
          "pathGroupsExcludedImportTypes": ["builtin"],
        },
      ],
      "react/jsx-no-useless-fragment": "warn",
      "react/no-unescaped-entities": "warn",
    },
    languageOptions: {
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
    },
  },
];