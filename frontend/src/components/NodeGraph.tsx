import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
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
            'background-color': '#4a90d9',
            color: '#fff',
            'font-size': 10,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
        {
          selector: '.selected',
          style: {
            'background-color': '#e6a23c',
            'line-color': '#e6a23c',
            'target-arrow-color': '#e6a23c',
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
  }, [nodes, edges, onSelect])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.nodes().removeClass('selected')
    if (selectedId) {
      cy.getElementById(selectedId).addClass('selected')
    }
  }, [selectedId])

  return <div ref={containerRef} style={{ width: '100%', height: '100%', background: '#fafafa' }} />
}
