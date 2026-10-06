<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({ document: Object })
const emit = defineEmits(['change'])
const canvas = ref(null), selectedId = ref(''), newLabel = ref(''), label = ref('')
const connecting = ref(''), drag = ref(null), temporaryPosition = ref(null)
const nodes = computed(() => props.document.nodes || [])
const selected = computed(() => nodes.value.find(node => node.id === selectedId.value))
const nodeMap = computed(() => new Map(nodes.value.map(node => [node.id, node])))
const edges = computed(() => (props.document.edges || []).filter(edge => nodeMap.value.has(edge[0]) && nodeMap.value.has(edge[1])))
const width = computed(() => Math.max(1100, ...nodes.value.map(node => node.x + node.width + 80)))
const height = computed(() => Math.max(650, ...nodes.value.map(node => node.y + node.height + 80)))
watch(selected, node => { label.value = node?.label || '' })
function point(event) {
  const svg = canvas.value
  const target = svg.createSVGPoint()
  target.x = event.clientX; target.y = event.clientY
  return target.matrixTransform(svg.getScreenCTM().inverse())
}
function position(node) { return temporaryPosition.value?.id === node.id ? temporaryPosition.value : node }
function addNode() {
  const title = newLabel.value.trim()
  if (!title) return
  const offset = nodes.value.length * 35
  emit('change', { ...props.document, version: 2, nodes: [...nodes.value, { id: crypto.randomUUID(), label: title, x: 60 + offset, y: 60 + offset, width: 170, height: 72 }] })
  newLabel.value = ''
}
function updateLabel() {
  if (!selected.value || !label.value.trim()) return
  emit('change', { ...props.document, nodes: nodes.value.map(node => node.id === selectedId.value ? { ...node, label: label.value.trim() } : node) })
}
function removeNode() {
  if (!selected.value) return
  emit('change', { ...props.document, nodes: nodes.value.filter(node => node.id !== selectedId.value), edges: edges.value.filter(edge => !edge.includes(selectedId.value)) })
  selectedId.value = ''
}
function startNode(event, node) {
  event.stopPropagation()
  selectedId.value = node.id
  if (connecting.value) {
    if (connecting.value !== node.id && !edges.value.some(edge => edge.includes(connecting.value) && edge.includes(node.id))) {
      emit('change', { ...props.document, edges: [...edges.value, [connecting.value, node.id]] })
    }
    connecting.value = ''
    return
  }
  const cursor = point(event)
  drag.value = { id: node.id, offsetX: cursor.x - node.x, offsetY: cursor.y - node.y }
  canvas.value.setPointerCapture(event.pointerId)
}
function move(event) {
  if (!drag.value) return
  const cursor = point(event)
  temporaryPosition.value = { id: drag.value.id, x: Math.round(Math.max(0, cursor.x - drag.value.offsetX)), y: Math.round(Math.max(0, cursor.y - drag.value.offsetY)) }
}
function finish() {
  if (!drag.value) return
  const moved = temporaryPosition.value
  if (moved) emit('change', { ...props.document, nodes: nodes.value.map(node => node.id === moved.id ? { ...node, x: moved.x, y: moved.y } : node) })
  drag.value = null; temporaryPosition.value = null
}
function removeEdge(edge) { emit('change', { ...props.document, edges: edges.value.filter(item => item !== edge) }) }
</script>

<template>
  <div class="editor-layout">
    <aside class="toolbox card"><h3>Diagram toolbox</h3><p class="muted">Create nodes, then drag them into place.</p><form class="stacked-form" @submit.prevent="addNode"><label>New node label<input v-model="newLabel" required placeholder="New node" /></label><button class="primary" type="submit">+ Add node</button></form><div class="toolbox-divider"></div><h4>Connections</h4><p class="muted">Choose a source node, then choose a target node.</p><button :class="{ selected: !!connecting }" :disabled="!selected" @click="connecting = selectedId">{{ connecting ? 'Choose target node…' : 'Connect selected node' }}</button><div v-for="edge in edges" :key="edge.join(':')" class="edge-row"><span>{{ nodeMap.get(edge[0])?.label }} → {{ nodeMap.get(edge[1])?.label }}</span><button class="subtle-danger" aria-label="Remove connection" @click="removeEdge(edge)">×</button></div><div v-if="selected" class="toolbox-divider"></div><form v-if="selected" class="stacked-form" @submit.prevent="updateLabel"><h4>Selected node</h4><label>Label<input v-model="label" required /></label><button type="submit">Apply label</button><button type="button" class="danger" @click="removeNode">Delete node</button></form></aside>
    <div class="canvas-area"><div class="canvas-toolbar"><span>{{ nodes.length }} nodes · {{ edges.length }} connections</span><span>Drag nodes to arrange</span></div><div class="canvas-scroll"><svg ref="canvas" :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" role="img" aria-label="Editable project diagram" @pointermove="move" @pointerup="finish" @pointercancel="finish" @click.self="selectedId = ''"><defs><pattern id="diagram-grid" width="25" height="25" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#30435a" /></pattern></defs><rect :width="width" :height="height" fill="url(#diagram-grid)" /><line v-for="edge in edges" :key="edge.join(':')" :x1="position(nodeMap.get(edge[0])).x + nodeMap.get(edge[0]).width / 2" :y1="position(nodeMap.get(edge[0])).y + nodeMap.get(edge[0]).height / 2" :x2="position(nodeMap.get(edge[1])).x + nodeMap.get(edge[1]).width / 2" :y2="position(nodeMap.get(edge[1])).y + nodeMap.get(edge[1]).height / 2" stroke="#c9a55c" stroke-width="2" /><g v-for="node in nodes" :key="node.id" class="diagram-node" :class="{ selected: selectedId === node.id, connecting: connecting === node.id }" @pointerdown="startNode($event, node)"><rect :x="position(node).x" :y="position(node).y" :width="node.width" :height="node.height" rx="10" /><text :x="position(node).x + 14" :y="position(node).y + 30">{{ node.label }}</text></g></svg></div></div>
  </div>
</template>
