/** Build WebSocket URL via same-origin proxy (/ws → backend). */
export function wsUrl(path) {
  const normalized = path.startsWith('/') ? path : `/${path}`
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${location.host}${normalized}`
}
