export function validateDocument(kind, value) {
  const version = kind === 'diagram' ? 2 : 6
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Document must be an object.')
  if (value.version !== version) throw new Error(`Expected ${kind} document version ${version}.`)
  const collections = kind === 'diagram' ? ['nodes', 'edges'] : ['strokes', 'shapes', 'images', 'texts']
  for (const key of collections) {
    if (!Array.isArray(value[key])) throw new Error(`${key} must be an array.`)
  }
  if (kind === 'diagram') {
    const ids = new Set()
    for (const node of value.nodes) {
      if (!node || typeof node.id !== 'string' || !node.id || ids.has(node.id) || typeof node.label !== 'string') throw new Error('Diagram nodes need unique IDs and labels.')
      ids.add(node.id)
      if (![node.x, node.y].every(finite) || ![node.width, node.height].every(positive)) throw new Error('Diagram node geometry is invalid.')
    }
    for (const edge of value.edges) {
      if (!Array.isArray(edge) || edge.length !== 2 || !ids.has(edge[0]) || !ids.has(edge[1]) || edge[0] === edge[1]) throw new Error('Diagram edge references an invalid node.')
    }
  } else {
    for (const stroke of value.strokes) {
      if (!Array.isArray(stroke?.points) || stroke.points.length < 4 || stroke.points.length % 2 || !stroke.points.every(finite)) throw new Error('Workspace stroke points are invalid.')
    }
    for (const [key, entries] of [['shapes', value.shapes], ['images', value.images], ['texts', value.texts]]) {
      for (const entry of entries) {
        if (!entry || typeof entry.id !== 'string' || ![entry.x, entry.y].every(finite) || ![entry.width, entry.height].every(positive)) throw new Error(`Workspace ${key} geometry is invalid.`)
        if (key === 'shapes' && !['rectangle', 'ellipse', 'line', 'arrow'].includes(entry.kind)) throw new Error('Workspace shape kind is invalid.')
        if (key === 'images' && !String(entry.source).startsWith('managed://images/')) throw new Error('Workspace images need managed references.')
        if (key === 'texts' && !String(entry.text).trim()) throw new Error('Workspace text must not be empty.')
      }
    }
  }
  return value
}

function finite(value) { return typeof value === 'number' && Number.isFinite(value) }
function positive(value) { return finite(value) && value > 0 }
