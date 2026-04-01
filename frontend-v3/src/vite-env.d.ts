/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, unknown>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_VERSION: string
  readonly VITE_AMAP_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// ==================== 高德地图 API 类型定义 ====================

/** 高德地图经纬度对象 */
interface AMapLngLat {
  /** 获取经度 */
  getLng(): number
  /** 获取纬度 */
  getLat(): number
}

/** 地图点击事件对象 */
interface AMapMapClickEvent {
  lnglat: AMapLngLat
  pixel: { x: number; y: number }
  target: AMapMap
}

/** 地图配置选项 */
interface AMapMapOptions {
  /** 地图缩放级别 */
  zoom?: number
  /** 地图中心点 [经度, 纬度] */
  center?: [number, number] | number[]
  /** 视图模式：'2D' | '3D' */
  viewMode?: '2D' | '3D'
  /** 是否允许缩放 */
  resizeEnable?: boolean
  /** 是否支持拖拽 */
  dragEnable?: boolean
  /** 是否支持键盘操作 */
  keyboardEnable?: boolean
  /** 是否支持双击放大 */
  doubleClickZoom?: boolean
}

/** 地图标记配置选项 */
interface AMapMarkerOptions {
  /** 标记位置 [经度, 纬度] */
  position: [number, number] | number[]
  /** 标记标题（鼠标悬停显示） */
  title?: string
  /** 是否可点击 */
  clickable?: boolean
  /** 是否可拖拽 */
  draggable?: boolean
  /** 自定义图标 */
  icon?: AMapIcon
  /** 锚点位置 */
  anchor?: string
  /** 偏移量 */
  offset?: AMapPixel
}

/** 高德地图图标 */
interface AMapIcon {
  /** 图标大小 */
  size: AMapSize
  /** 图标URL */
  image?: string
  /** 图片偏移 */
  imageOffset?: AMapPixel
}

/** 高德地图像素坐标 */
interface AMapPixel {
  x: number
  y: number
}

/** 高德地图尺寸 */
interface AMapSize {
  width: number
  height: number
}

/** 高德地图实例 */
interface AMapMap {
  /** 销毁地图实例 */
  destroy(): void
  /** 调整地图大小 */
  resize(): void
  /** 设置地图中心点 */
  setCenter(center: [number, number] | number[]): void
  /** 设置缩放级别 */
  setZoom(zoom: number): void
  /** 获取地图中心点 */
  getCenter(): AMapLngLat
  /** 获取缩放级别 */
  getZoom(): number
  /** 添加覆盖物（标记等） */
  add(overlay: AMapMarker | AMapMarker[]): void
  /** 移除覆盖物 */
  remove(overlay: AMapMarker | AMapMarker[]): void
  /** 清除所有覆盖物 */
  clearMap(): void
  /** 绑定事件监听 */
  on(event: string, callback: (e: AMapMapClickEvent) => void): void
  /** 解绑事件监听 */
  off(event: string, callback: (e: AMapMapClickEvent) => void): void
}

/** 高德地图标记实例 */
interface AMapMarker {
  /** 设置标记位置 */
  setPosition(position: [number, number] | number[]): void
  /** 获取标记位置 */
  getPosition(): AMapLngLat
  /** 设置标记标题 */
  setTitle(title: string): void
  /** 设置是否可拖拽 */
  setDraggable(draggable: boolean): void
  /** 显示标记 */
  show(): void
  /** 隐藏标记 */
  hide(): void
}

/** 高德地图构造函数 */
interface AMapConstructor {
  /** 地图类 */
  Map: new (container: string | HTMLElement, options?: AMapMapOptions) => AMapMap
  /** 标记类 */
  Marker: new (options?: AMapMarkerOptions) => AMapMarker
  /** 像素坐标类 */
  Pixel: new (x: number, y: number) => AMapPixel
  /** 尺寸类 */
  Size: new (width: number, height: number) => AMapSize
  /** 图标类 */
  Icon: new (options: { size: AMapSize; image?: string; imageOffset?: AMapPixel }) => AMapIcon
}

/** 扩展 Window 接口 */
interface Window {
  /** 高德地图 API */
  AMap: AMapConstructor
}
