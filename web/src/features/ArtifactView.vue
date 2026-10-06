<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '../api.js'
import { validateDocument } from '../artifactDocument.js'
import ActionDialog from '../components/ActionDialog.vue'
import DiagramEditor from './DiagramEditor.vue'
import WorkspaceEditor from './WorkspaceEditor.vue'

const props = defineProps({ project: Object, kind: String })
const path = `/projects/${props.project.id}/artifacts/${props.kind}`
const documentData = ref(null), revisions = ref([]), todos = ref([])
const subtab = ref('Canvas'), history = ref([]), future = ref([])
const dirty = ref(false), saving = ref(false), error = ref(''), message = ref('')
const dialog = ref(null), dialogError = ref(''), dialogBusy = ref(false), jsonText = ref('')
const editableVersion = computed(() => documentData.value?.version === (props.kind === 'diagram' ? 2 : 6))
let saveTimer = null
function freshDocument() { return props.kind === 'diagram' ? { version: 2, nodes: [], edges: [] } : { version: 6, strokes: [], shapes: [], images: [], texts: [] } }
function clone(value) { return JSON.parse(JSON.stringify(value)) }
async function load() {
  error.value = ''
  try {
    const data = await api(`${path}/content`)
    const [earlier, todoData] = await Promise.all([api(`${path}/revisions`), api(`/projects/${props.project.id}/todos?module=${props.kind}`)])
    documentData.value = Object.keys(data || {}).length ? data : freshDocument()
    jsonText.value = JSON.stringify(documentData.value, null, 2)
    revisions.value = earlier; todos.value = todoData; history.value = []; future.value = []; dirty.value = false
  } catch (caught) { error.value = caught.message }
}
function scheduleSave() { clearTimeout(saveTimer); saveTimer = setTimeout(save, 1500) }
function change(next) {
  if (!documentData.value) return
  history.value.push(clone(documentData.value))
  if (history.value.length > 50) history.value.shift()
  future.value = []
  documentData.value = clone(next)
  jsonText.value = JSON.stringify(next, null, 2)
  dirty.value = true; message.value = ''
  scheduleSave()
}
function undo() {
  if (!history.value.length) return
  future.value.push(clone(documentData.value))
  documentData.value = history.value.pop(); jsonText.value = JSON.stringify(documentData.value, null, 2)
  dirty.value = true; scheduleSave()
}
function redo() {
  if (!future.value.length) return
  history.value.push(clone(documentData.value))
  documentData.value = future.value.pop(); jsonText.value = JSON.stringify(documentData.value, null, 2)
  dirty.value = true; scheduleSave()
}
async function save() {
  clearTimeout(saveTimer)
  if (!dirty.value || !documentData.value) return
  if (saving.value) { scheduleSave(); return }
  saving.value = true; error.value = ''
  const snapshot = JSON.stringify(documentData.value)
  try {
    validateDocument(props.kind, documentData.value)
    await api(path, { method: 'PUT', body: { content: documentData.value } })
    revisions.value = await api(`${path}/revisions`)
    if (snapshot === JSON.stringify(documentData.value)) { dirty.value = false; message.value = 'Saved' }
    else scheduleSave()
  } catch (caught) { error.value = caught.message } finally { saving.value = false }
}
function applyJson() {
  try { change(validateDocument(props.kind, JSON.parse(jsonText.value))); error.value = '' }
  catch (caught) { error.value = caught.message }
}
function editTodo(item = null) {
  dialogError.value = ''
  dialog.value = { kind: 'todo', item, title: item ? 'Edit To-Do' : 'New To-Do', submitLabel: item ? 'Save To-Do' : 'Add To-Do', initial: item || { status: 'open' }, fields: [
    { name: 'title', label: 'Title', required: true, wide: true }, { name: 'description', label: 'Description', type: 'textarea', wide: true }, { name: 'status', label: 'Status', type: 'select', options: ['open', 'in_progress', 'done'] },
  ] }
}
function confirmRestore(revision) { dialogError.value = ''; dialog.value = { kind: 'restore', revision, title: 'Restore this version?', description: 'The current document will be kept as an earlier version.', submitLabel: 'Restore version' } }
function confirmTodoDelete(item) { dialogError.value = ''; dialog.value = { kind: 'delete-todo', item, title: `Delete “${item.title}”?`, submitLabel: 'Delete To-Do', danger: true } }
async function submitDialog(values) {
  dialogBusy.value = true; dialogError.value = ''
  try {
    if (dialog.value.kind === 'restore') { await api(`${path}/revisions/${dialog.value.revision.id}/restore`, { method: 'POST' }); await load() }
    if (dialog.value.kind === 'delete-todo') { await api(`/todos/${dialog.value.item.id}`, { method: 'DELETE' }); todos.value = await api(`/projects/${props.project.id}/todos?module=${props.kind}`) }
    if (dialog.value.kind === 'todo') {
      await api(dialog.value.item ? `/todos/${dialog.value.item.id}` : `/projects/${props.project.id}/todos`, { method: dialog.value.item ? 'PUT' : 'POST', body: { ...values, title: values.title.trim(), module: props.kind } })
      todos.value = await api(`/projects/${props.project.id}/todos?module=${props.kind}`)
    }
    dialog.value = null
  } catch (caught) { dialogError.value = caught.message } finally { dialogBusy.value = false }
}
onMounted(load)
onBeforeUnmount(() => { clearTimeout(saveTimer); if (dirty.value) save() })
</script>

<template>
  <div class="page-heading"><div><small>VISUAL ARTIFACT</small><h2>{{ kind === 'diagram' ? 'Diagram' : 'Workspace' }}</h2><p>Arrange ideas visually. Changes save automatically and keep earlier versions.</p></div><div class="button-row"><span class="save-indicator">{{ saving ? 'Saving…' : dirty ? 'Unsaved changes' : message || 'Up to date' }}</span><button :disabled="!history.length" @click="undo">Undo</button><button :disabled="!future.length" @click="redo">Redo</button><button class="primary" :disabled="!dirty || saving" @click="save">Save now</button></div></div>
  <p v-if="error" class="alert" role="alert">{{ error }}</p>
  <nav class="subtabs" aria-label="Artifact sections"><button :class="{ active: subtab === 'Canvas' }" @click="subtab = 'Canvas'">Canvas</button><button :class="{ active: subtab === 'To-Dos' }" @click="subtab = 'To-Dos'">To-Dos</button><button :class="{ active: subtab === 'Versions' }" @click="subtab = 'Versions'">Versions</button></nav>
  <template v-if="subtab === 'Canvas' && documentData"><p v-if="!editableVersion" class="alert">This document uses an older or unsupported version. Open it in Kivy to migrate it before editing here.</p><template v-else><DiagramEditor v-if="kind === 'diagram'" :document="documentData" @change="change" /><WorkspaceEditor v-else :document="documentData" :project-id="project.id" @change="change" @error="error = $event" /></template><details class="card advanced-editor"><summary>Advanced document JSON</summary><p class="muted">Edit the versioned document directly only when needed.</p><textarea v-model="jsonText" class="json-editor" spellcheck="false" aria-label="Artifact document JSON" /><button @click="applyJson">Apply JSON changes</button></details></template>
  <section v-if="subtab === 'To-Dos'" class="card"><div class="section-title"><h3>{{ kind === 'diagram' ? 'Diagram' : 'Workspace' }} To-Dos</h3><button class="primary" @click="editTodo()">+ To-Do</button></div><p v-if="!todos.length" class="muted">No to-dos yet.</p><div v-for="todo in todos" :key="todo.id" class="resource-row"><div><button class="text-button" @click="editTodo(todo)">{{ todo.title }}</button><p v-if="todo.description" class="muted">{{ todo.description }}</p><small>{{ todo.status.replace('_', ' ') }}</small></div><button class="subtle-danger" @click="confirmTodoDelete(todo)">Remove</button></div></section>
  <section v-if="subtab === 'Versions'" class="card"><h3>Earlier saved versions</h3><p v-if="!revisions.length" class="muted">No earlier versions yet.</p><div v-for="revision in revisions" :key="revision.id" class="list-row"><small>{{ new Date(revision.created_at).toLocaleString() }}</small><button @click="confirmRestore(revision)">Restore</button></div></section>
  <ActionDialog :open="!!dialog" :title="dialog?.title" :description="dialog?.description" :fields="dialog?.fields" :initial="dialog?.initial" :submit-label="dialog?.submitLabel" :danger="dialog?.danger" :busy="dialogBusy" :error="dialogError" @close="dialog = null" @submit="submitDialog" />
</template>
