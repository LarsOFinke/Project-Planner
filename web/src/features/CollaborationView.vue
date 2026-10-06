<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api.js'
import ActionDialog from '../components/ActionDialog.vue'

const props = defineProps({ project: Object })
const root = `/projects/${props.project.id}`
const tab = ref('Web URLs')
const todos = ref([]), resources = ref([])
const dialog = ref(null), dialogError = ref(''), error = ref(''), busy = ref(false)
const visibleResources = computed(() => resources.value.filter(item => item.kind === (tab.value === 'Web URLs' ? 'web' : 'file')))
async function load() {
  error.value = ''
  try { [todos.value, resources.value] = await Promise.all([api(`${root}/todos?module=links`), api(`${root}/resources`)]) }
  catch (caught) { error.value = caught.message }
}
function editTodo(item = null) {
  dialogError.value = ''
  dialog.value = { kind: 'todo', item, title: item ? 'Edit To-Do' : 'New To-Do', submitLabel: item ? 'Save To-Do' : 'Add To-Do', initial: item || { status: 'open' }, fields: [
    { name: 'title', label: 'Title', required: true, wide: true },
    { name: 'description', label: 'Description', type: 'textarea', wide: true },
    { name: 'status', label: 'Status', type: 'select', options: ['open', 'in_progress', 'done'] },
  ] }
}
function addResource() {
  const kind = tab.value === 'Web URLs' ? 'web' : 'file'
  dialogError.value = ''
  dialog.value = { kind: 'resource', resourceKind: kind, title: kind === 'web' ? 'Add web URL' : 'Add local file', submitLabel: 'Add link', fields: [
    { name: 'title', label: 'Link title', required: true, wide: true },
    { name: 'target', label: kind === 'web' ? 'Web URL' : 'Absolute file path', type: kind === 'web' ? 'url' : 'text', required: true, wide: true, placeholder: kind === 'web' ? 'https://example.org' : '/path/to/file' },
  ] }
}
function askDelete(path, label) { dialogError.value = ''; dialog.value = { kind: 'delete', path, title: `Remove “${label}”?`, description: 'The linked file itself will not be deleted.', fields: [], danger: true, submitLabel: 'Remove' } }
async function submit(values) {
  const action = dialog.value
  busy.value = true; dialogError.value = ''; error.value = ''
  try {
    if (action.kind === 'delete') await api(action.path, { method: 'DELETE' })
    else if (action.kind === 'resource') await api(`${root}/resources`, { method: 'POST', body: { title: values.title.trim(), target: values.target.trim(), kind: action.resourceKind } })
    else if (action.kind === 'todo') await api(action.item ? `/todos/${action.item.id}` : `${root}/todos`, { method: action.item ? 'PUT' : 'POST', body: { title: values.title.trim(), description: values.description, status: values.status, module: 'links' } })
    dialog.value = null; await load()
  } catch (caught) { dialogError.value = caught.message } finally { busy.value = false }
}
onMounted(load)
</script>

<template>
  <div class="page-heading"><div><small>PROJECT REFERENCES</small><h2>Links</h2><p>Keep web resources, local file references, and follow-up work together.</p></div><button @click="load">Refresh</button></div>
  <p v-if="error" class="alert" role="alert">{{ error }}</p>
  <nav class="subtabs" aria-label="Link sections"><button v-for="value in ['Web URLs', 'Local Files', 'To-Dos']" :key="value" :class="{ active: tab === value }" @click="tab = value">{{ value }}</button></nav>
  <section v-if="tab !== 'To-Dos'" class="card"><div class="section-title"><h3>{{ tab }}</h3><button class="primary" @click="addResource">{{ tab === 'Web URLs' ? '+ Web URL' : '+ Local file' }}</button></div><p v-if="!visibleResources.length" class="muted">No {{ tab.toLowerCase() }} linked yet.</p><div v-for="resource in visibleResources" :key="resource.id" class="resource-row"><div><a v-if="resource.kind === 'web'" :href="resource.target" target="_blank" rel="noopener noreferrer">{{ resource.title }} ↗</a><strong v-else>{{ resource.title }}</strong><small>{{ resource.target }}</small></div><button class="subtle-danger" :aria-label="`Remove ${resource.title}`" @click="askDelete(`/resources/${resource.id}`, resource.title)">Remove</button></div></section>
  <section v-else class="card"><div class="section-title"><h3>Links To-Dos</h3><button class="primary" @click="editTodo()">+ To-Do</button></div><p v-if="!todos.length" class="muted">No follow-up work yet.</p><div v-for="todo in todos" :key="todo.id" class="resource-row"><div><button class="text-button" @click="editTodo(todo)">{{ todo.title }}</button><p v-if="todo.description" class="muted">{{ todo.description }}</p><small>{{ todo.status.replace('_', ' ') }}</small></div><button class="subtle-danger" :aria-label="`Remove ${todo.title}`" @click="askDelete(`/todos/${todo.id}`, todo.title)">Remove</button></div></section>
  <ActionDialog :open="!!dialog" :title="dialog?.title" :description="dialog?.description" :fields="dialog?.fields" :initial="dialog?.initial" :submit-label="dialog?.submitLabel" :danger="dialog?.danger" :busy="busy" :error="dialogError" @close="dialog = null" @submit="submit" />
</template>
