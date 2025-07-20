import React, { useState } from "react";
import { ZoomIn, ZoomOut, X, Maximize, Network } from "lucide-react";
import Icon from '../atoms/icons';
import Button from '../atoms/buttons';

// Placeholder for GraphNodeTooltip to prevent runtime errors
const GraphNodeTooltip = ({ node, visible, position }) => visible && node ? (
  <div style={{ position: 'fixed', left: position.x, top: position.y, zIndex: 100 }} className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg p-2 text-xs max-w-xs">
    <div className="font-semibold mb-1">{node.title}</div>
    <div>{node.snippet}</div>
  </div>
) : null;


const RAGGraphModal = ({ isOpen, onClose }) => {
  const [tooltip, setTooltip] = useState({ visible: false, node: null, position: { x: 0, y: 0 } });

  if (!isOpen) return null;

  const handleNodeHover = (node, event) => {
    setTooltip({
      visible: true,
      node,
      position: { x: event.clientX + 10, y: event.clientY + 10 }
    });
  };

  const handleNodeLeave = () => {
    setTooltip({ visible: false, node: null, position: { x: 0, y: 0 } });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-11/12 h-5/6 max-w-6xl">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            RAG Knowledge Graph
          </h2>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm">
              <Icon icon={ZoomIn} />
            </Button>
            <Button variant="ghost" size="sm">
              <Icon icon={ZoomOut} />
            </Button>
            <Button variant="ghost" size="sm">
              <Icon icon={Maximize} />
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <Icon icon={X} />
            </Button>
          </div>
        </div>

        <div className="flex-1 p-4 relative">
          <div className="w-full h-full bg-gray-50 dark:bg-gray-900 rounded-lg flex items-center justify-center">
            {/* Mock graph visualization */}
            <div className="text-center">
              <Icon icon={Network} size="lg" className="mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Knowledge Graph Visualization
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Interactive graph showing document relationships and retrieved context
              </p>

              {/* Mock graph nodes */}
              <div className="flex justify-center space-x-8 mt-8">
                {['Document 1', 'Document 2', 'Query'].map((label, i) => (
                  <div
                    key={i}
                    className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium cursor-pointer hover:bg-blue-600 transition-colors"
                    onMouseEnter={(e) => handleNodeHover({
                      title: label,
                      snippet: `This is a sample snippet from ${label} showing relevant content...`
                    }, e)}
                    onMouseLeave={handleNodeLeave}
                  >
                    {label.split(' ')[0]}
                  </div>
                ))}
              </div>

              {/* Mock connections */}
              <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: -1 }}>
                <line x1="200" y1="300" x2="350" y2="300" stroke="#6B7280" strokeWidth="2" />
                <line x1="350" y1="300" x2="500" y2="300" stroke="#6B7280" strokeWidth="2" />
              </svg>
            </div>
          </div>

          <GraphNodeTooltip
            node={tooltip.node}
            visible={tooltip.visible}
            position={tooltip.position}
          />
        </div>
      </div>
    </div>
  );
};

export default RAGGraphModal;