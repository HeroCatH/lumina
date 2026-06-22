# Phase 4: Global Cyberpunk UI 统一

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 把 Lumina 所有面板（App 导航栏、DataPanel、ModelPanel、ExperimentsPanel、EvaluatePanel 及共享组件）统一成赛博朋克视觉风格：深色背景、霓虹绿/粉/蓝强调色、等宽字体、剪裁感卡片与发光边框。

**Architecture:** 抽出统一的 `frontend/src/theme.ts` 调色板与样式常量；各面板和组件导入 theme，替换原有浅色/灰色调；保持组件结构与 API 调用不变，仅调整视觉层。

**Tech Stack:** Vite + React + TypeScript，纯 inline style（项目当前无 CSS 文件）。

---

## 文件结构

- `frontend/src/theme.ts` — 新建：赛博朋克配色、字体、通用组件样式（panel、card、input、button、neonShadow 等）。
- `frontend/src/panels/EvaluatePanel.tsx` — 修改：移除内嵌 `C` 常量，改用 `theme.ts`。
- `frontend/src/App.tsx` — 修改：header 导航栏赛博朋克化。
- `frontend/src/panels/DataPanel.tsx` — 修改：数据集列表与预览深色风格。
- `frontend/src/panels/ModelPanel.tsx` — 修改：模型分析面板深色风格。
- `frontend/src/panels/ExperimentsPanel.tsx` — 修改：Run 列表、metric 曲线、checkpoint 列表深色风格。
- `frontend/src/components/LayerTree.tsx` — 修改：左侧 layer 列表深色风格。
- `frontend/src/components/NodeGraph.tsx` — 修改：cytoscape 节点/边颜色改为霓虹风格。
- `frontend/src/components/DetailPanel.tsx` — 修改：详情面板深色风格。
- `frontend/src/api.ts` / `frontend/src/types.ts` — 不修改。
- `src/lumina/static/` — 由 `npm run build` 重新生成。

---

## Task 1: 创建共享 theme 模块

**Files:**
- Create: `frontend/src/theme.ts`

- [ ] **Step 1: 编写 theme.ts**

```ts
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

export const panelStyle: React.CSSProperties = {
  background: CYBER.panel,
  border: `1px solid ${CYBER.border}`,
  borderRadius: 6,
}

export const cardStyle: React.CSSProperties = {
  background: CYBER.panel2,
  border: `1px solid ${CYBER.border}`,
  borderRadius: 4,
}

export const inputStyle: React.CSSProperties = {
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

export function buttonStyle(color: string): React.CSSProperties {
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

export const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '8px 10px',
  color: CYBER.muted,
  fontWeight: 'normal',
  textTransform: 'uppercase',
  fontSize: 10,
}

export const tdStyle: React.CSSProperties = {
  padding: '8px 10px',
}

export function sectionTitle(color: string): React.CSSProperties {
  return {
    color,
    fontSize: 12,
    marginBottom: 10,
    textTransform: 'uppercase',
  }
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 3: 提交**

```bash
git add frontend/src/theme.ts
git commit -m "feat: add shared cyberpunk theme module"
```

---

## Task 2: EvaluatePanel 改用共享 theme

**Files:**
- Modify: `frontend/src/panels/EvaluatePanel.tsx`

- [ ] **Step 1: 替换导入与常量**

删除文件内的 `const C = {...}`，改为：

```ts
import { CYBER, buttonStyle, cardStyle, inputStyle, neonShadow, panelStyle, sectionTitle, tdStyle, thStyle } from '../theme'
```

- [ ] **Step 2: 全局替换 `C.` 为 `CYBER.`，并替换局部样式常量**

例如：
- `C.bg` → `CYBER.bg`
- `C.panel` → `CYBER.panel`
- `inputStyle` 改为从 theme 导入
- `thStyle`、`tdStyle` 改为从 theme 导入

保持所有布局与逻辑不变。

- [ ] **Step 3: 运行构建验证**

Run: `cd frontend && npm run build`
Expected: build succeeds

- [ ] **Step 4: 提交**

```bash
git add frontend/src/panels/EvaluatePanel.tsx
git commit -m "refactor: EvaluatePanel uses shared cyberpunk theme"
```

---

## Task 3: App 导航栏赛博朋克化

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 更新 header 样式**

导入 theme：

```ts
import { CYBER, neonShadow } from './theme'
```

把 `header` 的 `style` 替换为：

```tsx
<header
  style={{
    padding: '12px 20px',
    borderBottom: `1px solid ${CYBER.border}`,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    background: CYBER.panel,
    color: CYBER.text,
    fontFamily: CYBER.font,
  }}
>
```

- [ ] **Step 2: 更新标题与按钮样式**

标题：

```tsx
<h1 style={{ margin: 0, fontSize: 20, color: CYBER.green, textShadow: neonShadow(CYBER.green) }}>
  LUMINA
</h1>
```

按钮封装：

```tsx
function NavButton({ active, children, onClick }: { active?: boolean; children: React.ReactNode; onClick: () => void }) {
  const color = active ? CYBER.blue : CYBER.muted
  return (
    <button
      onClick={onClick}
      style={{
        background: 'transparent',
        color,
        border: `1px solid ${color}`,
        borderRadius: 4,
        padding: '6px 12px',
        fontFamily: CYBER.font,
        cursor: 'pointer',
        boxShadow: active ? `0 0 8px ${color}55` : 'none',
      }}
    >
      {children}
    </button>
  )
}
```

把各组 `<button onClick={() => setMode('...')}>...</button>` 替换为 `<NavButton onClick={() => setMode('...')}>...</NavButton>`。

- [ ] **Step 3: 验证构建**

Run: `cd frontend && npm run build`
Expected: build succeeds

- [ ] **Step 4: 提交**

```bash
git add frontend/src/App.tsx
git commit -m "feat: cyberpunk style for app header navigation"
```

---

## Task 4: DataPanel 赛博朋克化

**Files:**
- Modify: `frontend/src/panels/DataPanel.tsx`

- [ ] **Step 1: 导入 theme**

```ts
import { CYBER, cardStyle, panelStyle, sectionTitle, tdStyle, thStyle } from '../theme'
```

- [ ] **Step 2: 重写渲染**

根容器：

```tsx
<div style={{ display: 'flex', height: '100vh', background: CYBER.bg, color: CYBER.text, fontFamily: CYBER.font }}>
```

左侧边栏：

```tsx
<div style={{ width: 260, borderRight: `1px solid ${CYBER.border}`, padding: 12, background: CYBER.panel }}>
  <div style={sectionTitle(CYBER.blue)}>Datasets</div>
  <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
    {datasets.map((ds) => (
      <li
        key={ds.id}
        onClick={() => setSelected(ds.name)}
        style={{
          padding: '8px',
          cursor: 'pointer',
          background: ds.name === selected ? `${CYBER.blue}22` : 'transparent',
          border: `1px solid ${ds.name === selected ? CYBER.blue : 'transparent'}`,
          borderRadius: 4,
          marginBottom: 6,
        }}
      >
        <div style={{ color: ds.name === selected ? CYBER.blue : CYBER.text }}>{ds.name}</div>
        <div style={{ fontSize: 12, color: CYBER.muted }}>{ds.adapter_type}</div>
      </li>
    ))}
  </ul>
</div>
```

右侧主区域：

```tsx
<div style={{ flex: 1, padding: 16, overflow: 'auto' }}>
  {preview ? (
    <div>
      <div style={{ fontSize: 18, color: CYBER.green, textShadow: `0 0 10px ${CYBER.green}55`, marginBottom: 12 }}>
        {selected}
      </div>
      <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        <StatCard label="ROWS" value={preview.statistics.row_count} color={CYBER.blue} />
        <StatCard label="COLUMNS" value={preview.statistics.column_count} color={CYBER.pink} />
      </div>
      <div style={sectionTitle(CYBER.blue)}>Preview</div>
      <table style={{ borderCollapse: 'collapse', fontSize: 13, border: `1px solid ${CYBER.border}` }}>
        <thead style={{ background: CYBER.panel2 }}>
          <tr>
            {preview.statistics.columns.map((col) => (
              <th key={col} style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {preview.rows.map((row, idx) => (
            <tr key={idx} style={{ borderBottom: `1px solid ${CYBER.border}` }}>
              {preview.statistics.columns.map((col) => (
                <td key={col} style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>{String(row[col])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <div style={{ color: CYBER.muted }}>Select a dataset to preview.</div>
  )}
</div>
```

`StatCard`：

```tsx
function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ ...cardStyle, padding: 14, minWidth: 120, borderColor: `${color}55`, boxShadow: `0 0 12px ${color}22` }}>
      <div style={{ fontSize: 10, color: CYBER.muted }}>{label}</div>
      <div style={{ fontSize: 24, color, textShadow: `0 0 10px ${color}55` }}>{value}</div>
    </div>
  )
}
```

- [ ] **Step 3: 验证构建**

Run: `cd frontend && npm run build`
Expected: build succeeds

- [ ] **Step 4: 提交**

```bash
git add frontend/src/panels/DataPanel.tsx
git commit -m "feat: cyberpunk style for DataPanel"
```

---

## Task 5: ModelPanel 赛博朋克化

**Files:**
- Modify: `frontend/src/panels/ModelPanel.tsx`

- [ ] **Step 1: 导入 theme**

```ts
import { CYBER, cardStyle, inputStyle, thStyle, tdStyle } from '../theme'
```

- [ ] **Step 2: 重写根容器与顶部统计栏**

根容器：

```tsx
<div style={{ display: 'flex', height: '100vh', background: CYBER.bg, color: CYBER.text, fontFamily: CYBER.font }}>
```

顶部 stats bar：

```tsx
{stats && (
  <div style={{ padding: 12, borderBottom: `1px solid ${CYBER.border}`, background: CYBER.panel }}>
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13 }}>
      {[
        { label: 'PARAMS', value: stats.params.total_params.toLocaleString(), color: CYBER.green },
        { label: 'FLOPs', value: stats.flops.total_flops.toLocaleString(), color: CYBER.blue },
        { label: 'MACs', value: stats.flops.total_macs.toLocaleString(), color: CYBER.pink },
        { label: 'MEMORY', value: `${stats.memory.param_megabytes.toFixed(2)} MB`, color: CYBER.yellow },
      ].map((item) => (
        <span key={item.label} style={{ color: item.color }}>
          {item.label}: {item.value}
        </span>
      ))}
      {stats.shapes && (
        <span style={{ color: CYBER.muted }}>OUT: [{stats.shapes.output_shape.join(', ')}]</span>
      )}
    </div>
    <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
      <input
        type="text"
        value={shapeText}
        onChange={(e) => setShapeText(e.target.value)}
        placeholder="1,3,32,32"
        style={{ ...inputStyle, width: 'auto' }}
      />
      <button
        onClick={handleAnalyzeShape}
        style={{
          background: 'transparent',
          color: CYBER.blue,
          border: `1px solid ${CYBER.blue}`,
          borderRadius: 4,
          padding: '6px 12px',
          fontFamily: CYBER.font,
          cursor: 'pointer',
        }}
      >
        ANALYZE SHAPE
      </button>
    </div>
  </div>
)}
```

- [ ] **Step 3: 更新底部表格与边框**

底部表格容器：

```tsx
<div style={{ maxHeight: '40%', borderTop: `1px solid ${CYBER.border}`, overflow: 'auto', background: CYBER.panel }}>
  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
    <thead style={{ position: 'sticky', top: 0, background: CYBER.panel2 }}>
      <tr>
        {['Node', 'Type', 'Params', 'FLOPs', 'Memory', 'Input Shape', 'Output Shape'].map((h) => (
          <th key={h} style={thStyle}>{h}</th>
        ))}
      </tr>
    </thead>
    <tbody>
      {rows.map((row) => (
        <tr
          key={row.id}
          onClick={() => setSelectedId(row.id)}
          style={{
            background: selectedId === row.id ? `${CYBER.blue}22` : 'transparent',
            cursor: 'pointer',
            borderBottom: `1px solid ${CYBER.border}`,
          }}
        >
          <td style={{ ...tdStyle, color: selectedId === row.id ? CYBER.blue : CYBER.text }}>{row.id}</td>
          <td style={tdStyle}>{row.type}</td>
          <td style={{ ...tdStyle, textAlign: 'right' }}>{String(row.params)}</td>
          <td style={{ ...tdStyle, textAlign: 'right' }}>{String(row.flops)}</td>
          <td style={{ ...tdStyle, textAlign: 'right' }}>{String(row.memory)}</td>
          <td style={tdStyle}>{row.inputShape ? `[${row.inputShape.join(', ')}]` : '-'}</td>
          <td style={tdStyle}>{row.outputShape ? `[${row.outputShape.join(', ')}]` : '-'}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

- [ ] **Step 4: 验证构建**

Run: `cd frontend && npm run build`
Expected: build succeeds

- [ ] **Step 5: 提交**

```bash
git add frontend/src/panels/ModelPanel.tsx
git commit -m "feat: cyberpunk style for ModelPanel"
```

---

## Task 6: ExperimentsPanel 赛博朋克化

**Files:**
- Modify: `frontend/src/panels/ExperimentsPanel.tsx`

- [ ] **Step 1: 导入 theme**

```ts
import { CYBER, cardStyle, sectionTitle } from '../theme'
```

- [ ] **Step 2: 重写容器与 Run 列表**

根容器：

```tsx
<div style={{ display: 'flex', height: '100%', background: CYBER.bg, color: CYBER.text, fontFamily: CYBER.font }}>
```

左侧 Run 列表：

```tsx
<div style={{ width: 240, borderRight: `1px solid ${CYBER.border}`, padding: 12, overflow: 'auto', background: CYBER.panel }}>
  <div style={sectionTitle(CYBER.green)}>Runs</div>
  {runs.map((run) => (
    <div
      key={run.id}
      onClick={() => setSelectedRunId(run.id)}
      style={{
        padding: 8,
        marginBottom: 6,
        borderRadius: 4,
        cursor: 'pointer',
        background: run.id === selectedRunId ? `${CYBER.green}22` : CYBER.panel2,
        border: `1px solid ${run.id === selectedRunId ? CYBER.green : CYBER.border}`,
        boxShadow: run.id === selectedRunId ? `0 0 10px ${CYBER.green}33` : 'none',
      }}
    >
      <div style={{ fontWeight: 'bold', fontSize: 13, color: run.id === selectedRunId ? CYBER.green : CYBER.text }}>
        {run.name}
      </div>
      <div style={{ fontSize: 11, color: CYBER.muted }}>
        {run.status} • {run.source}
      </div>
    </div>
  ))}
</div>
```

- [ ] **Step 3: 更新右侧控制区与图表容器**

右侧控制区：

```tsx
<div style={{ flex: 1, padding: 16, display: 'flex', flexDirection: 'column', gap: 16, overflow: 'hidden' }}>
  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
    <button
      onClick={handleSync}
      style={{
        background: 'transparent',
        color: CYBER.green,
        border: `1px solid ${CYBER.green}`,
        borderRadius: 4,
        padding: '6px 12px',
        fontFamily: CYBER.font,
        cursor: 'pointer',
      }}
    >
      SYNC LOGS
    </button>
    {onEvaluate && (
      <button
        onClick={onEvaluate}
        style={{
          background: 'transparent',
          color: CYBER.pink,
          border: `1px solid ${CYBER.pink}`,
          borderRadius: 4,
          padding: '6px 12px',
          fontFamily: CYBER.font,
          cursor: 'pointer',
        }}
      >
        EVALUATE
      </button>
    )}
    <select
      value={metricName}
      onChange={(e) => setMetricName(e.target.value)}
      style={{
        background: CYBER.panel2,
        color: CYBER.text,
        border: `1px solid ${CYBER.border}`,
        borderRadius: 4,
        padding: '6px 8px',
        fontFamily: CYBER.font,
      }}
    >
      <option value="">All metrics</option>
      {metricNames.map((n) => (
        <option key={n} value={n}>{n}</option>
      ))}
    </select>
    {selectedRun && <span style={{ fontSize: 12, color: CYBER.muted }}>{selectedRun.name}</span>}
  </div>
  {loading && <div style={{ fontSize: 12, color: CYBER.blue }}>&gt; LOADING telemetry...</div>}
  {error && <div style={{ fontSize: 12, color: CYBER.red }}>[ERR] {error}</div>}
  <MetricCurve metrics={metrics} />
  <CheckpointList checkpoints={checkpoints} />
</div>
```

- [ ] **Step 4: 更新 MetricCurve 与 CheckpointList**

`MetricCurve` 容器：

```tsx
<div style={{ flex: 1, ...cardStyle, padding: 12 }}>
  <div style={sectionTitle(CYBER.blue)}>Metrics</div>
  ...
</div>
```

`SimpleLine` svg 背景：

```tsx
<svg width={width} height={height} style={{ background: CYBER.panel2, border: `1px solid ${CYBER.border}` }}>
  <polyline fill="none" stroke={CYBER.blue} strokeWidth={2} points={points.join(' ')} />
</svg>
```

`CheckpointList` 容器：

```tsx
<div style={{ height: 160, ...cardStyle, padding: 12, overflow: 'auto' }}>
  <div style={sectionTitle(CYBER.pink)}>Checkpoints</div>
  <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
    <thead>
      <tr style={{ textAlign: 'left', borderBottom: `1px solid ${CYBER.border}` }}>
        <th style={thStyle}>Step</th>
        <th style={thStyle}>Path</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {checkpoints.map((ckpt) => (
        <tr key={ckpt.id} style={{ borderBottom: `1px solid ${CYBER.border}` }}>
          <td style={tdStyle}>{ckpt.step}</td>
          <td style={tdStyle}>{ckpt.path}</td>
          <td style={tdStyle}>
            <a href={`/api/checkpoints/${ckpt.id}/download`} download style={{ color: CYBER.blue }}>
              Download
            </a>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

导入 `thStyle` 与 `tdStyle`。

- [ ] **Step 5: 验证构建**

Run: `cd frontend && npm run build`
Expected: build succeeds

- [ ] **Step 6: 提交**

```bash
git add frontend/src/panels/ExperimentsPanel.tsx
git commit -m "feat: cyberpunk style for ExperimentsPanel"
```

---

## Task 7: 共享组件赛博朋克化

**Files:**
- Modify: `frontend/src/components/LayerTree.tsx`
- Modify: `frontend/src/components/NodeGraph.tsx`
- Modify: `frontend/src/components/DetailPanel.tsx`

### LayerTree

- [ ] **Step 1: 导入 theme 并更新样式**

```ts
import { CYBER, sectionTitle } from '../theme'
```

```tsx
<div style={{ padding: 12, overflow: 'auto', height: '100%', background: CYBER.panel, color: CYBER.text, fontFamily: CYBER.font }}>
  <div style={sectionTitle(CYBER.blue)}>Layers</div>
  <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
    {nodes.map((node) => (
      <li
        key={node.id}
        onClick={() => onSelect(node.id)}
        style={{
          padding: '6px 8px',
          cursor: 'pointer',
          background: node.id === selectedId ? `${CYBER.blue}22` : 'transparent',
          borderBottom: `1px solid ${CYBER.border}`,
          color: node.id === selectedId ? CYBER.blue : CYBER.text,
        }}
      >
        <div style={{ fontWeight: 500 }}>{node.display_name}</div>
        <div style={{ fontSize: 12, color: CYBER.muted }}>{node.type}</div>
      </li>
    ))}
  </ul>
</div>
```

### NodeGraph

- [ ] **Step 2: 更新 cytoscape 配色**

导入：

```ts
import { CYBER } from '../theme'
```

把 style 数组替换为：

```ts
style: [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      width: 120,
      height: 40,
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': CYBER.blue,
      color: CYBER.bg,
      'font-size': 10,
      'border-width': 1,
      'border-color': CYBER.blue,
      'border-opacity': 1,
      'text-outline-color': CYBER.blue,
      'text-outline-width': 0,
    },
  },
  {
    selector: 'edge',
    style: {
      width: 2,
      'line-color': CYBER.muted,
      'target-arrow-color': CYBER.muted,
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
    },
  },
  {
    selector: '.selected',
    style: {
      'background-color': CYBER.pink,
      'border-color': CYBER.pink,
      'line-color': CYBER.pink,
      'target-arrow-color': CYBER.pink,
    },
  },
],
```

背景：

```tsx
return <div ref={containerRef} style={{ width: '100%', height: '100%', background: CYBER.panel2 }} />
```

### DetailPanel

- [ ] **Step 3: 导入 theme 并更新样式**

```ts
import { CYBER, sectionTitle } from '../theme'
```

```tsx
<div style={{ padding: 12, overflow: 'auto', height: '100%', background: CYBER.panel, color: CYBER.text, fontFamily: CYBER.font, borderLeft: `1px solid ${CYBER.border}` }}>
  <div style={sectionTitle(CYBER.blue)}>Details</div>
  {node ? (
    <div>
      <p><span style={{ color: CYBER.muted }}>ID:</span> {node.id}</p>
      <p><span style={{ color: CYBER.muted }}>Type:</span> {node.type}</p>
      <p><span style={{ color: CYBER.muted }}>Params:</span></p>
      <pre style={{ fontSize: 12, background: CYBER.panel2, padding: 8, border: `1px solid ${CYBER.border}`, overflow: 'auto' }}>
        {JSON.stringify(node.params, null, 2)}
      </pre>
    </div>
  ) : (
    <p style={{ color: CYBER.muted }}>Select a layer to see details.</p>
  )}

  <div style={sectionTitle(CYBER.green)}>Stats</div>
  {stats ? (
    <div>
      <p><span style={{ color: CYBER.muted }}>Total params:</span> {stats.params.total_params}</p>
      <p><span style={{ color: CYBER.muted }}>Trainable params:</span> {stats.params.trainable_params}</p>
    </div>
  ) : (
    <p style={{ color: CYBER.muted }}>Loading stats...</p>
  )}
</div>
```

- [ ] **Step 4: 验证构建**

Run: `cd frontend && npm run build`
Expected: build succeeds

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/LayerTree.tsx frontend/src/components/NodeGraph.tsx frontend/src/components/DetailPanel.tsx
git commit -m "feat: cyberpunk style for shared model components"
```

---

## Task 8: 最终构建与推送

- [ ] **Step 1: 运行完整前端构建**

Run:

```bash
cd frontend && npm run build
```

Expected: `tsc && vite build` succeeds.

- [ ] **Step 2: 运行后端测试**

Run:

```bash
.venv/bin/pytest tests/ -q
```

Expected: all tests pass.

- [ ] **Step 3: 提交并推送**

```bash
git add src/lumina/static/
git commit -m "build: regenerate static assets for cyberpunk UI"
git push
```

---

## Self-Review Checklist

- [ ] `theme.ts` 已创建且被所有面板使用
- [ ] `EvaluatePanel` 不再包含内嵌 `C` 常量
- [ ] `App` header、DataPanel、ModelPanel、ExperimentsPanel、共享组件均已深色/霓虹化
- [ ] TypeScript 编译通过
- [ ] 后端测试通过
- [ ] 静态资源已重新生成并提交
