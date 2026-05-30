export function formatTime(iso: string): string {
  return iso.replace('T', ' ').slice(0, 16)
}
