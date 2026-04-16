/**
 * 设备指纹工具 - 增强版多维度设备标识
 * 解决 FingerprintJS 在学校机房环境下的碰撞问题
 */
import FingerprintJS from '@fingerprintjs/fingerprintjs'

const STORAGE_KEY = 'checkin_device_id'
const SALT_KEY = 'checkin_device_salt'
const UPDATED_AT_KEY = 'checkin_device_id_updated_at'
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000 // 7天

function getFromMultipleStorage(key: string): string | null {
  try {
    const local = localStorage.getItem(key)
    if (local) return local
  } catch {
    // ignore
  }
  try {
    const session = sessionStorage.getItem(key)
    if (session) return session
  } catch {
    // ignore
  }
  try {
    const match = document.cookie.match(new RegExp('(?:^|; )' + encodeURIComponent(key) + '=([^;]*)'))
    if (match) return decodeURIComponent(match[1])
  } catch {
    // ignore
  }
  return null
}

function saveToMultipleStorage(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    // ignore
  }
  try {
    sessionStorage.setItem(key, value)
  } catch {
    // ignore
  }
  try {
    const expires = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toUTCString()
    document.cookie = `${encodeURIComponent(key)}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
  } catch {
    // ignore
  }
}

function removeFromMultipleStorage(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch {
    // ignore
  }
  try {
    sessionStorage.removeItem(key)
  } catch {
    // ignore
  }
  try {
    document.cookie = `${encodeURIComponent(key)}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`
  } catch {
    // ignore
  }
}

function getCanvasFingerprint(): string {
  try {
    const canvas = document.createElement('canvas')
    canvas.width = 200
    canvas.height = 100
    const ctx = canvas.getContext('2d')
    if (!ctx) return ''

    // 绘制复杂图形以产生设备差异
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial'
    ctx.fillStyle = '#f60'
    ctx.fillRect(10, 10, 150, 60)
    ctx.fillStyle = '#069'
    ctx.fillText('ClassHub Device Fingerprint', 15, 25)
    ctx.strokeStyle = '#0f0'
    ctx.beginPath()
    ctx.moveTo(20, 50)
    ctx.lineTo(180, 80)
    ctx.lineTo(100, 20)
    ctx.closePath()
    ctx.stroke()

    const dataUrl = canvas.toDataURL('image/png')
    return dataUrl.slice(-50)
  } catch {
    return ''
  }
}

function getWebGLFingerprint(): string {
  try {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    if (!gl) return ''
    const debugInfo = (gl as WebGLRenderingContext).getExtension('WEBGL_debug_renderer_info')
    if (!debugInfo) return ''
    const vendor = (gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
    const renderer = (gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
    return `${vendor}|${renderer}`
  } catch {
    return ''
  }
}

function getOrCreatePersistentSalt(): string {
  const existing = getFromMultipleStorage(SALT_KEY)
  if (existing) return existing
  const array = new Uint8Array(16)
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(array)
  } else {
    for (let i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256)
    }
  }
  const hex = Array.from(array, (b) => b.toString(16).padStart(2, '0')).join('')
  saveToMultipleStorage(SALT_KEY, hex)
  return hex
}

async function hashComponents(components: string[]): Promise<string> {
  const text = components.join('::')
  const encoder = new TextEncoder()
  const data = encoder.encode(text)
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
  }
  // fallback: simple hash for environments without crypto.subtle
  let h = 0
  for (let i = 0; i < text.length; i++) {
    h = (h << 5) - h + text.charCodeAt(i)
    h |= 0
  }
  return Math.abs(h).toString(16).padStart(64, '0')
}

function isCacheValid(updatedAt: string | null): boolean {
  if (!updatedAt) return false
  const ts = parseInt(updatedAt, 10)
  return !isNaN(ts) && Date.now() - ts < CACHE_TTL_MS
}

/**
 * 生成增强版设备指纹
 * 结合 FingerprintJS + Canvas + WebGL + 持久化盐值，通过 SHA-256 哈希生成唯一标识
 */
export async function getEnhancedDeviceFingerprint(forceRefresh = false): Promise<string> {
  // 1. 检查多存储点缓存（带 TTL，避免碰撞问题永远无法自愈）
  if (!forceRefresh) {
    const cachedId = getFromMultipleStorage(STORAGE_KEY)
    const updatedAt = getFromMultipleStorage(UPDATED_AT_KEY)
    if (cachedId && isCacheValid(updatedAt)) return cachedId
  }

  // 2. 获取 FingerprintJS visitorId
  const fp = await FingerprintJS.load()
  const result = await fp.get()

  // 3. 获取 Canvas + WebGL 指纹
  const canvasFp = getCanvasFingerprint()
  const webglFp = getWebGLFingerprint()

  // 4. 获取随机盐
  const salt = getOrCreatePersistentSalt()

  // 5. 组合 SHA-256 哈希
  const hash = await hashComponents([result.visitorId, canvasFp, webglFp, salt])

  // 6. 多存储点保存并更新时间戳
  saveToMultipleStorage(STORAGE_KEY, hash)
  saveToMultipleStorage(UPDATED_AT_KEY, String(Date.now()))
  return hash
}

/**
 * 获取设备信息（用于记录）
 */
export function getDeviceInfo(): object {
  return {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    screen: {
      width: screen.width,
      height: screen.height,
      colorDepth: screen.colorDepth,
    },
    hardwareConcurrency: navigator.hardwareConcurrency,
    deviceMemory: (navigator as Navigator & { deviceMemory?: number }).deviceMemory,
    maxTouchPoints: navigator.maxTouchPoints,
    timezoneOffset: new Date().getTimezoneOffset(),
  }
}

/**
 * 清除设备ID（调试用）
 */
export function clearDeviceId(): void {
  removeFromMultipleStorage(STORAGE_KEY)
  removeFromMultipleStorage(SALT_KEY)
  removeFromMultipleStorage(UPDATED_AT_KEY)
}
