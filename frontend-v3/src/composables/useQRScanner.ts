import { ref, onUnmounted } from 'vue'
import { Html5Qrcode } from 'html5-qrcode'

const SCANNER_ELEMENT_ID = 'qr-reader'

export function useQRScanner(onSuccess: (decodedText: string) => void) {
  const isScanning = ref(false)
  const error = ref<string | null>(null)
  let scanner: Html5Qrcode | null = null

  const startScan = async () => {
    try {
      error.value = null
      scanner = new Html5Qrcode(SCANNER_ELEMENT_ID)
      await scanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        (decodedText) => { onSuccess(decodedText); stopScan() },
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

  onUnmounted(stopScan)

  return { isScanning, error, startScan, stopScan, SCANNER_ELEMENT_ID }
}
