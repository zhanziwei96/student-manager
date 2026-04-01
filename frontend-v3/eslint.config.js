import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'

export default defineConfigWithVueTs(
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,
  {
    ignores: ['dist', 'node_modules'],
  },
  {
    rules: {
      // P2: 强化类型安全 - 禁止显式使用 any 类型
      '@typescript-eslint/no-explicit-any': 'error',
      // 禁止未使用的变量（允许以 _ 开头的参数）
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      // 强制使用严格相等
      'eqeqeq': ['error', 'always'],
      // 放宽规则：允许单单词组件名（UI组件）
      'vue/multi-word-component-names': 'off',
      // 放宽规则：允许 props 没有默认值
      'vue/require-default-prop': 'off',
      // 放宽规则：允许空对象类型
      '@typescript-eslint/no-empty-object-type': 'off',
    },
  },
)
