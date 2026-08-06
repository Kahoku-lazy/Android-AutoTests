/** useHeartbeat — 设备列表心跳轮询管理（从 useDeviceActions 提取） */
import { ref, onUnmounted, type Ref } from 'vue'
import { HEARTBEAT_INTERVAL } from '../constants'

export interface UseHeartbeatReturn {
  heartbeatActive: Ref<boolean>
  startHeartbeat: (tick: () => Promise<void>) => void
  stopHeartbeat: () => void
}

export function useHeartbeat(): UseHeartbeatReturn {
  const heartbeatActive = ref(false)
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null

  function startHeartbeat(tick: () => Promise<void>) {
    stopHeartbeat()
    heartbeatActive.value = true
    heartbeatTimer = setInterval(async () => {
      await tick()
    }, HEARTBEAT_INTERVAL)
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
    heartbeatActive.value = false
  }

  onUnmounted(() => {
    stopHeartbeat()
  })

  return { heartbeatActive, startHeartbeat, stopHeartbeat }
}
