import { createApp } from 'vue'
import { 
  ElButton, 
  ElCard, 
  ElTable, 
  ElTableColumn, 
  ElTag, 
  ElIcon,
  ElRow,
  ElCol,
  ElMessage,
  ElEmpty,
  ElLoading,
  ElInput,
  ElInputNumber,
  ElSelect,
  ElOption,
  ElForm,
  ElFormItem,
  ElDialog,
  ElUpload,
  ElRadio,
  ElRadioGroup,
  ElDropdown,
  ElDropdownMenu,
  ElDropdownItem,
  ElButtonGroup,
  ElCollapse,
  ElCollapseItem,
  ElContainer,
  ElHeader,
  ElMain,
  ElDivider,
  ElAlert,
  ElResult,
  ElText,
  ElAvatar
} from 'element-plus'
import { 
  Refresh, 
  Plus, 
  Delete, 
  Edit, 
  Search,
  Upload,
  Download,
  ArrowDown,
  Close,
  Check,
  User,
  Lock
} from '@element-plus/icons-vue'

// 按需引入样式
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/card/style/css'
import 'element-plus/es/components/table/style/css'
import 'element-plus/es/components/table-column/style/css'
import 'element-plus/es/components/tag/style/css'
import 'element-plus/es/components/icon/style/css'
import 'element-plus/es/components/row/style/css'
import 'element-plus/es/components/col/style/css'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/empty/style/css'
import 'element-plus/es/components/loading/style/css'
import 'element-plus/es/components/input/style/css'
import 'element-plus/es/components/input-number/style/css'
import 'element-plus/es/components/select/style/css'
import 'element-plus/es/components/option/style/css'
import 'element-plus/es/components/form/style/css'
import 'element-plus/es/components/form-item/style/css'
import 'element-plus/es/components/dialog/style/css'
import 'element-plus/es/components/upload/style/css'
import 'element-plus/es/components/radio/style/css'
import 'element-plus/es/components/radio-group/style/css'
import 'element-plus/es/components/dropdown/style/css'
import 'element-plus/es/components/dropdown-menu/style/css'
import 'element-plus/es/components/dropdown-item/style/css'
import 'element-plus/es/components/button-group/style/css'
import 'element-plus/es/components/collapse/style/css'
import 'element-plus/es/components/collapse-item/style/css'
import 'element-plus/es/components/container/style/css'
import 'element-plus/es/components/header/style/css'
import 'element-plus/es/components/main/style/css'
import 'element-plus/es/components/divider/style/css'
import 'element-plus/es/components/alert/style/css'
import 'element-plus/es/components/result/style/css'
import 'element-plus/es/components/text/style/css'
import 'element-plus/es/components/avatar/style/css'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册用到的组件
const components = [
  ElButton, ElCard, ElTable, ElTableColumn, 
  ElTag, ElIcon, ElRow, ElCol, ElMessage, ElEmpty, ElLoading,
  ElInput, ElInputNumber, ElSelect, ElOption, ElForm, ElFormItem,
  ElDialog, ElUpload, ElRadio, ElRadioGroup, ElDropdown, ElDropdownMenu,
  ElDropdownItem, ElButtonGroup, ElCollapse, ElCollapseItem, ElContainer,
  ElHeader, ElMain, ElDivider, ElAlert, ElResult, ElText, ElAvatar
]
components.forEach(c => app.use(c))

// 只注册用到的图标
const icons = {
  Refresh, Plus, Delete, Edit, Search, Upload, Download,
  ArrowDown, Close, Check, User, Lock
}
Object.entries(icons).forEach(([key, component]) => {
  app.component(key, component)
})

app.use(router)
app.mount('#app')
