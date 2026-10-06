<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api.js'
import ActionDialog from './ActionDialog.vue'

const props = defineProps({ projectId: String, module: String, phaseId: { type: String, default: null }, title: { type: String, default: 'To-Dos' } })
const todos = ref([]), error = ref(''), dialogError = ref(''), busy = ref(false), dialog = ref(null)
async function load() {
  try { const query = new URLSearchParams({ module: props.module }); if (props.phaseId) query.set('phase_id', props.phaseId); todos.value = await api(`/projects/${props.projectId}/todos?${query}`) }
  catch (caught) { error.value = caught.message }
}
function edit(item = null) {
  dialogError.value = ''
  dialog.value = { kind: 'edit', item, title: item ? 'Edit To-Do' : 'New To-Do', submitLabel: item ? 'Save To-Do' : 'Add To-Do', initial: item || { status: 'open' }, fields: [
    { name: 'title', label: 'Title', required: true, wide: true }, { name: 'description', label: 'Description', type: 'textarea', wide: true }, { name: 'status', label: 'Status', type: 'select', options: ['open', 'in_progress', 'done'] },
  ] }
}
function remove(item) { dialogError.value = ''; dialog.value = { kind: 'delete', item, title: `Delete “${item.title}”?`, submitLabel: 'Delete To-Do', danger: true } }
async function submit(values) {
  busy.value = true; dialogError.value = ''
  try {
    if (dialog.value.kind === 'delete') await api(`/todos/${dialog.value.item.id}`, { method: 'DELETE' })
    else await api(dialog.value.item ? `/todos/${dialog.value.item.id}` : `/projects/${props.projectId}/todos`, { method: dialog.value.item ? 'PUT' : 'POST', body: { ...values, title: values.title.trim(), module: props.module, ...(!dialog.value.item ? { phase_id: props.phaseId } : {}) } })
    dialog.value = null; await load()
  } catch (caught) { dialogError.value = caught.message } finally { busy.value = false }
}
onMounted(load)
</script>

<template>
  <section class="card"><div class="section-title"><h3>{{ title }}</h3><button @click="edit()">+ To-Do</button></div><p v-if="error" class="alert" role="alert">{{ error }}</p><p v-if="!todos.length" class="muted">No to-dos yet.</p><div v-for="todo in todos" :key="todo.id" class="list-row"><button @click="edit(todo)">{{ todo.title }}</button><small>{{ todo.status.replace('_', ' ') }}</small><button class="subtle-danger" @click="remove(todo)">×</button></div></section>
  <ActionDialog :open="!!dialog" :title="dialog?.title" :fields="dialog?.fields" :initial="dialog?.initial" :submit-label="dialog?.submitLabel" :danger="dialog?.danger" :busy="busy" :error="dialogError" @close="dialog = null" @submit="submit" />
</template>
