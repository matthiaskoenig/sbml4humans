/** `localStorage` guarded against a browser that blocks it (private mode, disabled storage,
 * a quota error): a read returns null, a write is silently dropped, and the component never
 * fails to mount over a convenience such as a remembered url or split pane size. */
export function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function writeStorage(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // storage is unavailable, the value is simply not remembered
  }
}
