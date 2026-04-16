import { ref, onMounted, onUnmounted } from 'vue'
import { Html5Qrcode } from 'html5-qrcode'

const SCANNER_ELEMENT_ID = 'qr-reader'

export function useQRScanner(onSuccess: (decodedText: string) => void) {
  const isScanning = ref(false)
  const error = ref<string | null>(null)
  const isCameraSupported = ref(false)
  let scanner: Html5Qrcode | null = null

  onMounted(() => {
    // 检测浏览器是否支持 getUserMedia（夸克、iOS 微信等通常不支持）
    isCameraSupported.value = !!(
      navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function'
    )
  })

  const startScan = async () => {
    if (isScanning.value) return
    try {
      error.value = null
      scanner = new Html5Qrcode(SCANNER_ELEMENT_ID)
      await scanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        async (decodedText) => { await stopScan(); onSuccess(decodedText) },
        () => {}
      )
      isScanning.value = true
    } catch (err) {
      error.value = '无法启动相机，请检查权限设置'
      console.error(err)
    }
  }

  const stopScan = async () => {
    if (scanner && isScanning.value) {
      await scanner.stop()
      await scanner.clear()
      isScanning.value = false
      scanner = null
    }
  }

  const scanFile = async (file: File) => {
    error.value = null
    try {
      const html5QrCode = new Html5Qrcode('qr-file-reader-dummy')
      const result = await html5QrCode.scanFile(file, false)
      onSuccess(result)
    } catch (err) {
      error.value = '未能识别二维码，请重新拍照'
      console.error(err)
    }
  }

  onUnmounted(stopScan)

  return { isScanning, error, isCameraSupported, startScan, stopScan, scanFile, SCANNER_ELEMENT_ID }
}
