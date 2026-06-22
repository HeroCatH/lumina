import { CYBER } from '../theme'

export default function EmptyState({
  children,
  style,
}: {
  children: React.ReactNode
  style?: React.CSSProperties
}) {
  return (
    <div
      style={{
        padding: 24,
        border: `1px dashed ${CYBER.border}`,
        borderRadius: 6,
        color: CYBER.muted,
        textAlign: 'center',
        fontSize: 13,
        background: CYBER.panel,
        ...style,
      }}
    >
      {children}
    </div>
  )
}
