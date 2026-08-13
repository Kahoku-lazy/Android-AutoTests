/** SSE Streaming API — TypeScript（单请求直连 Django，Agent 内嵌运行） */
import axios from 'axios'
import { SSEMessageBuilder } from '@/shared/sse/SSEMessageBuilder'
import {
  getToken,
  getRefreshToken,
  setToken,
  clearToken,
  getActive,
} from '@/shared/auth/token-storage'
import { ROUTE_LOGIN } from '../constants'

// ── SSE Stream ──

export interface SSECallbacks {
  onTextDelta?: (delta: string, text: string) => void
  onThinkingDelta?: (delta: string, thinking: string) => void
  onStatus?: (status: string) => void
  onDone?: () => void
  onError?: (err: Error) => void
  _completed?: boolean
  [key: string]: unknown
}

/**
 * Send message and stream Agent reply via SSE from Django.
 *
 * Replaces the old subscribeStream() + triggerChat() dual-request flow
 * (which required AgentScope FastAPI on :8000) with a single POST to
 * Django's /api/ai/conversations/{id}/chat/stream endpoint.
 *
 * Agent runs in the Django process; events are streamed directly as SSE.
 *
 * Uses native fetch() for ReadableStream support (axios can't stream).
 * Token is read from the auth_accounts pool via getToken().
 * On 401, auto-refreshes via the /refresh endpoint and retries once.
 */
export function streamChat(
  convId: number,
  message: string,
  callbacks: SSECallbacks = {},
  images?: { media_type: string; data: string }[],
  displayText?: string,
): { controller: AbortController; builder: SSEMessageBuilder } {
  const controller = new AbortController()
  const builder = new SSEMessageBuilder()
  const url = `/api/ai/conversations/${convId}/chat/stream`

  /** Attempt the SSE fetch with the given token. On 401, refresh + retry. */
  function doFetch(authToken: string, isRetry: boolean = false): void {
    const body: {
      message: string
      display_text?: string
      images?: { media_type: string; data: string }[]
    } = { message }
    if (displayText) body.display_text = displayText
    if (images?.length) body.images = images

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    }).then(response => {
      // ── 401 → attempt token refresh once ──
      if (response.status === 401 && !isRetry) {
        const refreshToken = getRefreshToken()
        if (!refreshToken) {
          clearToken()
          const active = getActive()
          if (!active) window.location.href = ROUTE_LOGIN
          else callbacks.onError?.(new Error('登录已过期，请重新登录'))
          return
        }
        return axios.post('/api/auth/refresh', { refresh_token: refreshToken })
          .then(refreshResp => {
            if (refreshResp.data?.status === true) {
              const access = refreshResp.data.data.access_token
              setToken(access)
              doFetch(access, true)
            } else {
              clearToken()
              const active = getActive()
              if (!active) window.location.href = ROUTE_LOGIN
              else callbacks.onError?.(new Error('登录已过期，请重新登录'))
            }
          })
          .catch(() => {
            clearToken()
            const active = getActive()
            if (!active) window.location.href = ROUTE_LOGIN
            else callbacks.onError?.(new Error('登录已过期，请重新登录'))
          })
      }

      if (!response.ok) {
        throw new Error(`Chat stream failed: HTTP ${response.status}`)
      }
      if (!response.body) {
        callbacks.onError?.(new Error('Response body is empty'))
        return
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      function read(): void {
        reader.read().then(({ done, value }) => {
          if (done) {
            if (!callbacks._completed) {
              callbacks.onError?.(new Error('SSE stream closed before REPLY_END'))
            }
            return
          }
          buffer += decoder.decode(value, { stream: true })
          const events = buffer.split('\n\n')
          buffer = events.pop()!

          for (const evtBlock of events) {
            const dataLines: string[] = []
            for (const line of evtBlock.split('\n')) {
              if (line.startsWith('data: ')) dataLines.push(line.slice(6))
              else if (line.startsWith('data:')) dataLines.push(line.slice(5))
            }
            if (!dataLines.length) continue
            let raw: Record<string, unknown> | null = null
            try { raw = JSON.parse(dataLines.join('\n')) } catch { /* skip non-JSON lines (heartbeat comments) */ }
            if (raw) {
              // Track backend-saved message ID so frontend can skip duplicate save
              if (raw._backend_msg_id) {
                ;(builder as { _backendMsgId?: number })._backendMsgId = raw._backend_msg_id as number
              }
              const uiEvent = builder.processEvent(raw)
              if (uiEvent.phase === 'reply_end' || uiEvent.phase === 'exceed_max_iters') {
                callbacks._completed = true
              }
              dispatchUIEvent(uiEvent, callbacks)
            }
          }
          read()
        }).catch(err => {
          if ((err as Error).name !== 'AbortError') callbacks.onError?.(err as Error)
        })
      }
      read()
    }).catch(err => {
      if ((err as Error).name !== 'AbortError') callbacks.onError?.(err as Error)
    })
  }

  doFetch(getToken())
  return { controller, builder }
}

/** snake_case → camelCase, e.g. 'tool_call_end' → 'toolCallEnd' */
function snakeToCamel(s: string): string {
  return s.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
}

/** snake_case phase → callback name, e.g. 'tool_call_end' → 'onToolCallEnd' */
function phaseToCallbackName(phase: string): string {
  return `on${snakeToCamel(phase).charAt(0).toUpperCase()}${snakeToCamel(phase).slice(1)}`
}

/** Dispatch processed UI event to callbacks */
function dispatchUIEvent(uiEvent: { phase: string; [key: string]: unknown }, callbacks: SSECallbacks): void {
  const phase = uiEvent.phase
  if (phase === 'text_delta') {
    callbacks.onTextDelta?.(uiEvent.delta as string, uiEvent.text as string)
    callbacks.onStatus?.('streaming')
    return
  }
  if (phase === 'thinking_delta') {
    callbacks.onThinkingDelta?.(uiEvent.delta as string, uiEvent.thinking as string)
    callbacks.onStatus?.('thinking')
    return
  }
  const cbName = phaseToCallbackName(phase)
  const cb = callbacks[cbName] as ((evt: object) => void) | undefined
  if (cb) cb(uiEvent)

  if (phase === 'reply_end' || phase === 'exceed_max_iters') {
    callbacks.onStatus?.('done')
    callbacks.onDone?.()
  } else if (phase === 'tool_call_start' || phase === 'tool_result_start') {
    callbacks.onStatus?.('tool_calling')
  } else if (phase === 'model_call_start') {
    callbacks.onStatus?.('calling_model')
  }
}
