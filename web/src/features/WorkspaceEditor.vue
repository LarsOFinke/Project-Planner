<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../api.js'

const props = defineProps({ document: Object, projectId: String })
const emit = defineEmits(['change', 'error'])
const canvas = ref(null), mode = ref('select'), color = ref('#c9a55c'), shapeKind = ref('rectangle')
const newText = ref(''), selectedId = ref(''), selectedText = ref(''), drawing = ref(null), drag = ref(null), moved = ref(null), busy = ref(false)
const shapes = computed(() => props.document.shapes || [])
const texts = computed(() => props.document.texts || [])
const images = computed(() => props.document.images || [])
const selected = computed(() => [...shapes.value, ...texts.value, ...images.value].find(item => item.id === selectedId.value))
const width = computed(() => Math.max(1100, ...[...shapes.value, ...texts.value, ...images.value].map(item => item.x + item.width + 80)))
const height = computed(() => Math.max(650, ...[...shapes.value, ...texts.value, ...images.value].map(item => item.y + item.height + 80)))
watch(selected, item => { selectedText.value = item?.text || '' })
function point(event) { const p = canvas.value.createSVGPoint(); p.x = event.clientX; p.y = event.clientY; return p.matrixTransform(canvas.value.getScreenCTM().inverse()) }
function position(item) { return moved.value?.id === item.id ? moved.value : item }
function imageUrl(item) { return item.source?.startsWith('managed://images/') ? `/api/v1/projects/${props.projectId}/images/${encodeURIComponent(item.source.split('/').pop())}` : '' }
function addShape() {
  const offset = shapes.value.length * 26
  emit('change', { ...props.document, version: 6, shapes: [...shapes.value, { id: crypto.randomUUID(), kind: shapeKind.value, x: 60 + offset, y: 60 + offset, width: 160, height: 95, rotation: 0, color: color.value }] })
}
function addText() {
  if (!newText.value.trim()) return
  emit('change', { ...props.document, version: 6, texts: [...texts.value, { id: crypto.randomUUID(), text: newText.value.trim(), x: 80, y: 80, width: 220, height: 90, color: color.value }] })
  newText.value = ''
}
function updateText() {
  if (!selected.value || !selectedText.value.trim()) return
  emit('change', { ...props.document, texts: texts.value.map(item => item.id === selectedId.value ? { ...item, text: selectedText.value.trim() } : item) })
}
function removeSelected() {
  if (!selected.value) return
  emit('change', { ...props.document, shapes: shapes.value.filter(item => item.id !== selectedId.value), texts: texts.value.filter(item => item.id !== selectedId.value), images: images.value.filter(item => item.id !== selectedId.value) })
  selectedId.value = ''
}
async function uploadImage(event) {
  const file = event.target.files?.[0]
  if (!file) return
  busy.value = true
  try {
    const body = new FormData(); body.append('image', file)
    const uploaded = await api(`/projects/${props.projectId}/images`, { method: 'POST', body })
    emit('change', { ...props.document, version: 6, images: [...images.value, { id: crypto.randomUUID(), source: uploaded.reference, x: 90, y: 90, width: 240, height: 160, rotation: 0 }] })
  } catch (caught) { emit('error', caught.message) } finally { busy.value = false; event.target.value = '' }
}
function beginDraw(event) {
  if (mode.value !== 'draw') { selectedId.value = ''; return }
  const cursor = point(event)
  drawing.value = [Math.round(cursor.x), Math.round(cursor.y), Math.round(cursor.x), Math.round(cursor.y)]
  canvas.value.setPointerCapture(event.pointerId)
}
function beginDrag(event, item) {
  event.stopPropagation()
  if (mode.value === 'draw') return
  selectedId.value = item.id
  const cursor = point(event)
  drag.value = { id: item.id, x: cursor.x - item.x, y: cursor.y - item.y }
  canvas.value.setPointerCapture(event.pointerId)
}
function move(event) {
  if (drawing.value) { const cursor = point(event); drawing.value = [...drawing.value, Math.round(cursor.x), Math.round(cursor.y)] }
  if (drag.value) { const cursor = point(event); moved.value = { id: drag.value.id, x: Math.round(Math.max(0, cursor.x - drag.value.x)), y: Math.round(Math.max(0, cursor.y - drag.value.y)) } }
}
function finish() {
  if (drawing.value) {
    if (drawing.value.length >= 4) emit('change', { ...props.document, version: 6, strokes: [...(props.document.strokes || []), { points: drawing.value, color: color.value }] })
    drawing.value = null
  }
  if (drag.value) {
    if (moved.value) emit('change', { ...props.document, shapes: shapes.value.map(item => item.id === moved.value.id ? { ...item, x: moved.value.x, y: moved.value.y } : item), texts: texts.value.map(item => item.id === moved.value.id ? { ...item, x: moved.value.x, y: moved.value.y } : item), images: images.value.map(item => item.id === moved.value.id ? { ...item, x: moved.value.x, y: moved.value.y } : item) })
    drag.value = null; moved.value = null
  }
}
function points(stroke) { const p = stroke.points || []; return Array.from({ length: Math.floor(p.length / 2) }, (_, i) => `${p[i * 2]},${p[i * 2 + 1]}`).join(' ') }
</script>

<template>
  <div class="editor-layout">
    <aside class="toolbox card"><h3>Workspace toolbox</h3><div class="button-row"><button :class="{ selected: mode === 'select' }" @click="mode = 'select'">Select</button><button :class="{ selected: mode === 'draw' }" @click="mode = 'draw'">Draw</button></div><label class="tool-field">Color<input v-model="color" type="color" /></label><div class="toolbox-divider"></div><h4>Shapes</h4><div class="stacked-form"><label>Shape type<select v-model="shapeKind"><option v-for="kind in ['rectangle', 'ellipse', 'line', 'arrow']" :key="kind">{{ kind }}</option></select></label><button @click="addShape">+ Add shape</button></div><div class="toolbox-divider"></div><form class="stacked-form" @submit.prevent="addText"><h4>Text</h4><label>New text<textarea v-model="newText" rows="3" placeholder="Write a note on the canvas" required /></label><button type="submit">+ Add text</button></form><div class="toolbox-divider"></div><label class="file-choice">{{ busy ? 'Uploading…' : '+ Add image' }}<input type="file" accept="image/png,image/jpeg,image/gif,image/bmp,image/webp" :disabled="busy" @change="uploadImage" /></label><template v-if="selected"><div class="toolbox-divider"></div><h4>Selected item</h4><form v-if="selected.text !== undefined" class="stacked-form" @submit.prevent="updateText"><label>Text<textarea v-model="selectedText" rows="3" required /></label><button type="submit">Apply text</button></form><button class="danger" @click="removeSelected">Remove selected</button></template></aside>
    <div class="canvas-area"><div class="canvas-toolbar"><span>{{ shapes.length }} shapes · {{ texts.length }} texts · {{ images.length }} images</span><span>{{ mode === 'draw' ? 'Drag on empty canvas to draw' : 'Drag an item to move it' }}</span></div><div class="canvas-scroll"><svg ref="canvas" :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" role="img" aria-label="Editable project workspace" @pointermove="move" @pointerup="finish" @pointercancel="finish"><defs><pattern id="workspace-grid" width="25" height="25" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#30435a" /></pattern></defs><rect :width="width" :height="height" fill="url(#workspace-grid)" @pointerdown="beginDraw" /><polyline v-for="(stroke, index) in document.strokes || []" :key="index" :points="points(stroke)" fill="none" :stroke="stroke.color || '#d7dde5'" stroke-width="3" pointer-events="none" /><polyline v-if="drawing" :points="points({ points: drawing })" fill="none" :stroke="color" stroke-width="3" pointer-events="none" /><template v-for="shape in shapes" :key="shape.id"><ellipse v-if="shape.kind === 'ellipse'" :cx="position(shape).x + shape.width / 2" :cy="position(shape).y + shape.height / 2" :rx="shape.width / 2" :ry="shape.height / 2" fill="#1b2d44" :stroke="selectedId === shape.id ? '#e0c17c' : shape.color" stroke-width="3" class="movable" @pointerdown="beginDrag($event, shape)" /><line v-else-if="shape.kind === 'line' || shape.kind === 'arrow'" :x1="position(shape).x" :y1="position(shape).y" :x2="position(shape).x + shape.width" :y2="position(shape).y + shape.height" :stroke="selectedId === shape.id ? '#e0c17c' : shape.color" stroke-width="5" class="movable" @pointerdown="beginDrag($event, shape)" /><rect v-else :x="position(shape).x" :y="position(shape).y" :width="shape.width" :height="shape.height" rx="4" fill="#1b2d44" :stroke="selectedId === shape.id ? '#e0c17c' : shape.color" stroke-width="3" class="movable" @pointerdown="beginDrag($event, shape)" /></template><text v-for="item in texts" :key="item.id" :x="position(item).x" :y="position(item).y + 23" :fill="item.color || '#d7dde5'" class="movable" @pointerdown="beginDrag($event, item)">{{ item.text }}</text><image v-for="item in images" :key="item.id" :x="position(item).x" :y="position(item).y" :width="item.width" :height="item.height" :href="imageUrl(item)" class="movable" @pointerdown="beginDrag($event, item)" /></svg></div></div>
  </div>
</template>
