import type { CSSProperties } from 'react'

export const CYBER = {
  bg: '#050505',
  panel: '#0a0a0a',
  panel2: '#111111',
  border: '#222222',
  green: '#00ff41',
  pink: '#ff00ff',
  blue: '#00ccff',
  red: '#ff3333',
  yellow: '#ffff00',
  text: '#e0e0e0',
  muted: '#888888',
  font: "'JetBrains Mono', 'Fira Code', monospace",
}

export function neonShadow(color: string, intensity: number = 0.35): string {
  return `0 0 ${8 * intensity}px ${color}`
}

export const panelStyle: CSSProperties = {
  background: CYBER.panel,
  border: `1px solid ${CYBER.border}`,
  borderRadius: 6,
}

export const cardStyle: CSSProperties = {
  background: CYBER.panel2,
  border: `1px solid ${CYBER.border}`,
  borderRadius: 4,
}

export const inputStyle: CSSProperties = {
  background: CYBER.panel2,
  color: CYBER.text,
  border: `1px solid ${CYBER.border}`,
  borderRadius: 4,
  padding: '8px 10px',
  fontFamily: CYBER.font,
  outline: 'none',
  width: '100%',
  boxSizing: 'border-box',
}

export function buttonStyle(color: string): CSSProperties {
  return {
    background: 'transparent',
    color,
    border: `1px solid ${color}`,
    borderRadius: 4,
    padding: '8px 14px',
    fontFamily: CYBER.font,
    cursor: 'pointer',
    boxShadow: `0 0 8px ${color}33`,
  }
}

export const thStyle: CSSProperties = {
  textAlign: 'left',
  padding: '8px 10px',
  color: CYBER.muted,
  fontWeight: 'normal',
  textTransform: 'uppercase',
  fontSize: 10,
}

export const tdStyle: CSSProperties = {
  padding: '8px 10px',
}

export function sectionTitle(color: string): CSSProperties {
  return {
    color,
    fontSize: 12,
    marginBottom: 10,
    textTransform: 'uppercase',
  }
}
