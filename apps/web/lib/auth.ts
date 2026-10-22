// เก็บ JWT ใน localStorage — พอสำหรับโปรเจกต์นี้ (เขียนเป็นข้อจำกัดใน README: ถ้าเว็บโดน XSS token จะถูกขโมยได้)

const KEY = "thamdi_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string) {
  try {
    localStorage.setItem(KEY, token);
  } catch {}
}

export function clearToken() {
  try {
    localStorage.removeItem(KEY);
  } catch {}
}
