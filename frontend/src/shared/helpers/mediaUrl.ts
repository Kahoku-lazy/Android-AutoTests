export function mediaUrl(path?: string | null): string {
  return path ? `/media/${path}` : ""
}
