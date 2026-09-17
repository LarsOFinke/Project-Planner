from math import isfinite
from uuid import uuid4

from project_planner.core.application.artifacts.documents.DiagramDocument import (
    DiagramDocument,
)
from project_planner.core.application.artifacts.documents.DiagramNode import DiagramNode


class DiagramDocumentCodec:
    CURRENT_VERSION = 1

    def decode(self, data: object) -> DiagramDocument:
        if not isinstance(data, dict):
            return DiagramDocument()
        version = self._version(data.get("version", 1))
        nodes: list[DiagramNode] = []
        seen_ids: set[str] = set()
        raw_nodes = data.get("nodes", [])
        if isinstance(raw_nodes, list):
            for entry in raw_nodes:
                if not isinstance(entry, dict):
                    continue
                node_id = str(entry.get("id") or uuid4())
                if node_id in seen_ids:
                    continue
                try:
                    node = DiagramNode(
                        node_id=node_id,
                        label=str(entry.get("label", "Node")),
                        x=self._finite_float(entry.get("x", 40)),
                        y=self._finite_float(entry.get("y", 40)),
                    )
                except (TypeError, ValueError):
                    continue
                seen_ids.add(node_id)
                nodes.append(node)

        edges: list[tuple[str, str]] = []
        seen_edges: set[frozenset[str]] = set()
        raw_edges = data.get("edges", [])
        if isinstance(raw_edges, list):
            for entry in raw_edges:
                if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                    continue
                edge = (str(entry[0]), str(entry[1]))
                identity = frozenset(edge)
                if (
                    edge[0] in seen_ids
                    and edge[1] in seen_ids
                    and edge[0] != edge[1]
                    and identity not in seen_edges
                ):
                    edges.append(edge)
                    seen_edges.add(identity)
        return DiagramDocument(tuple(nodes), tuple(edges), version)

    def encode(self, document: DiagramDocument) -> dict[str, object]:
        return {
            "version": self.CURRENT_VERSION,
            "nodes": [
                {
                    "id": node.node_id,
                    "label": node.label,
                    "x": node.x,
                    "y": node.y,
                }
                for node in document.nodes
            ],
            "edges": [list(edge) for edge in document.edges],
        }

    def _version(self, value: object) -> int:
        try:
            version = int(value)
        except (TypeError, ValueError):
            version = 1
        if version > self.CURRENT_VERSION:
            raise ValueError(f"Unsupported diagram document version: {version}")
        return max(1, version)

    @staticmethod
    def _finite_float(value: object) -> float:
        parsed = float(value)
        if not isfinite(parsed):
            raise ValueError("A diagram coordinate must be finite")
        return parsed
