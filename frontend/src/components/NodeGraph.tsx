import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import { CYBER } from '../theme'
import { GraphNode, GraphEdge } from '../types'

interface NodeGraphProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata: Record<string, any>
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function NodeGraph({ nodes, edges, metadata, selectedId, onSelect }: NodeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...nodes.map((n) => ({
          data: { id: n.id, label: n.display_name },
        })),
        ...edges.map((e) => ({
          data: { id: `${e.source}-${e.target}`, source: e.source, target: e.target },
        })),
      ],
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
      layout: metadata?.estimator?.includes('Tree') || metadata?.estimator?.includes('DecisionTree')
        ? ({ name: 'breadthfirst', directed: true, padding: 10 } as any)
        : ({ name: 'grid', padding: 10 } as any),
    })

    cy.on('tap', 'node', (evt) => {
      onSelect(evt.target.id())
    })

    cyRef.current = cy
    return () => cy.destroy()
  }, [nodes, edges, onSelect, metadata])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.nodes().removeClass('selected')
    if (selectedId) {
      cy.getElementById(selectedId).addClass('selected')
    }
  }, [selectedId])

  return <div ref={containerRef} style={{ width: '100%', height: '100%', background: CYBER.panel2 }} />
}
