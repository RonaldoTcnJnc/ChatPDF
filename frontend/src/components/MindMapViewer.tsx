import { useState, useMemo } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    ConnectionLineType,
    MarkerType,
    Position
} from 'reactflow';
import type { Node, Edge } from 'reactflow'; // Explicit type import
import 'reactflow/dist/style.css';
import axios from 'axios';
import { Network, X } from 'lucide-react';
import dagre from 'dagre';

interface MindMapViewerProps {
    pdfName: string;
    onClose: () => void;
}

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    // Configurar tamaños de nodos
    const nodeWidth = 220;
    const nodeHeight = 90;

    // Usar layout jerárquico de arriba a abajo (Top to Bottom)
    dagreGraph.setGraph({ rankdir: 'TB', nodesep: 100, ranksep: 120 });

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    // Aplicar layout Dagre
    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);

        // Dagre calcula el centro del nodo, ReactFlow usa la esquina superior izquierda
        node.targetPosition = Position.Top;
        node.sourcePosition = Position.Bottom;

        // Ajustar posición para que el centro del nodo esté en la posición calculada
        node.position = {
            x: nodeWithPosition.x - nodeWidth / 2,
            y: nodeWithPosition.y - nodeHeight / 2,
        };

        return node;
    });

    return { nodes: layoutedNodes, edges };
};


export default function MindMapViewer({ pdfName, onClose }: MindMapViewerProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [generated, setGenerated] = useState(false);

    // Memoize nodeTypes and edgeTypes to avoid recreating objects on each render
    const nodeTypes = useMemo(() => ({}), []);
    const edgeTypes = useMemo(() => ({}), []);

    const generateMap = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post('/api/pdf/mindmap', { pdf_name: pdfName });
            const data = response.data;

            // Process data to React Flow format
            // Expecting data.nodes and data.edges

            if (!data.nodes || !data.edges) {
                throw new Error("Formato de respuesta inválido");
            }

            // Create Raw Nodes (without position)
            const rawNodes: Node[] = data.nodes.map((n: any) => ({
                id: n.id,
                type: 'default', // Using default for now
                data: { label: n.label },
                position: { x: 0, y: 0 }, // Initial position
                style: {
                    background: n.type === 'main' ? '#FFD700' : '#fff',
                    border: '1px solid #777',
                    borderRadius: '5px',
                    padding: '10px',
                    fontWeight: n.type === 'main' ? 'bold' : 'normal',
                    width: 180,
                    textAlign: 'center',
                    fontSize: '14px',
                    color: 'black' // Ensure text is visible
                }
            }));

            const rawEdges: Edge[] = data.edges.map((e: any, idx: number) => ({
                id: `e${idx}`,
                source: e.source,
                target: e.target,
                label: e.label,
                type: ConnectionLineType.SmoothStep,
                markerEnd: { type: MarkerType.ArrowClosed },
                animated: true,
                style: { stroke: '#555' },
                labelStyle: { fill: '#555', fontWeight: 700 }
            }));

            // Apply Dagre Layout
            const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
                rawNodes,
                rawEdges
            );

            setNodes(layoutedNodes);
            setEdges(layoutedEdges);
            setGenerated(true);

        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || "Error al generar mapa");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg-secondary)', overflow: 'hidden' }}>
            {/* Header */}
            <div style={{ padding: '10px', background: 'var(--bg-tertiary)', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-primary)', overflow: 'hidden' }}>
                    <Network size={20} color="var(--accent-primary)" />
                    <span style={{ fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>Mapa Conceptual: {pdfName}</span>
                </div>
                <div style={{ display: 'flex', gap: '10px', flexShrink: 0 }}>
                    {!generated && (
                        <button
                            onClick={generateMap}
                            disabled={loading}
                            style={{ padding: '5px 15px', cursor: 'pointer', background: 'var(--accent-primary)', color: 'white', border: 'none', borderRadius: '4px' }}
                        >
                            {loading ? 'Generando (IA)...' : 'Generar Mapa'}
                        </button>
                    )}
                    <button onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-primary)' }}>
                        <X size={20} />
                    </button>
                </div>
            </div>

            {/* Canvas */}
            <div style={{ flex: 1, width: '100%', minHeight: 400, position: 'relative', overflow: 'hidden' }}>
                {error && <div style={{ position: 'absolute', top: 10, left: 10, padding: '10px', background: '#ffe6e6', color: 'red', zIndex: 10 }}>{error}</div>}

                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    nodeTypes={nodeTypes}
                    edgeTypes={edgeTypes}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    fitView
                    style={{ width: '100%', height: '100%' }}
                >
                    <Background />
                    <Controls />
                    <MiniMap />
                </ReactFlow>
            </div>
        </div>
    );
}
