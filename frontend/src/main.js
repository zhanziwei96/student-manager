import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'

import App from './App.vue'
import router from './router'

// 创建应用实例
const app = createApp(App)

// 使用 Pinia 状态管理
app.use(createPinia())

// 使用 Naive UI
app.use(naive)

// 使用路由
app.use(router)

// 挂载应用
app.mount('#app')
