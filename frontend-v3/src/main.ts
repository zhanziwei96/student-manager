import { createApp } from 'vue'
import { VueQueryPlugin } from '@tanstack/vue-query'
import { pinia } from '@/stores'
import App from './App.vue'
import router from './router'
import './index.css'

const app = createApp(App)

// Pinia (state management)
app.use(pinia)

// Vue Router
app.use(router)

// TanStack Query (server state management)
app.use(VueQueryPlugin, {
  queryClientConfig: {
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5, // 5 minutes
        refetchOnWindowFocus: true,
        retry: 1,
      },
    },
  },
})

app.mount('#app')
