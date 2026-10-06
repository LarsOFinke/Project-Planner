<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api, projectApi } from '../api.js'
import ActionDialog from '../components/ActionDialog.vue'
import TodoPanel from '../components/TodoPanel.vue'

const props = defineProps({ project: Object, projects: Array, categories: Array })
const emit = defineEmits(['updated', 'deleted', 'navigate'])
const form = reactive(Object.fromEntries(['title', 'description', 'status', 'planning_method', 'parent_id', 'category_id', 'start_date', 'target_date', 'owner', 'assignee', 'notes'].map(key => [key, props.project[key] ?? ''])))
const saving = ref(false)
const message = ref('')
const error = ref('')
const confirmAction = ref('')
const links = ref([])
const targets = ref([])
const linkTarget = ref('')
async function loadLinks() {
  try { [links.value, targets.value] = await Promise.all([api(`/projects/${props.project.id}/project-links?resolved=true`), api(`/projects/${props.project.id}/project-link-targets`)]) }
  catch (caught) { error.value = caught.message }
}
async function save() {
  saving.value = true; error.value = ''; message.value = ''
  try {
    const { category_id, ...fields } = form
    await projectApi.update(props.project.id, { ...fields, parent_id: form.parent_id || null, start_date: form.start_date || null, target_date: form.target_date || null })
    if ((category_id || null) !== props.project.category_id) {
      await projectApi.move(props.project.id, { parent_id: null, category_id: category_id || null })
    }
    message.value = 'Project saved.'; emit('updated')
  } catch (caught) { error.value = caught.message } finally { saving.value = false }
}
async function confirmLifecycle() {
  const action = confirmAction.value
  confirmAction.value = ''; error.value = ''
  try {
    if (action === 'archive') { await projectApi.archive(props.project.id); emit('updated') }
    if (action === 'delete') { await projectApi.remove(props.project.id); emit('deleted') }
  } catch (caught) { error.value = caught.message }
}
async function addLink() {
  if (!linkTarget.value) return
  error.value = ''
  try { await api(`/projects/${props.project.id}/project-links`, { method: 'POST', body: { target_id: linkTarget.value } }); linkTarget.value = ''; await loadLinks() }
  catch (caught) { error.value = caught.message }
}
onMounted(loadLinks)
</script>

<template>
  <div class="page-heading"><div><small>PROJECT DETAILS</small><h2>Overview</h2><p>Keep the essentials of this project in one place.</p></div></div>
  <p v-if="error" class="alert" role="alert">{{ error }}</p><p v-if="message" class="success" role="status">{{ message }}</p>
  <form @submit.prevent="save"><div class="two-columns">
    <section class="card"><h3>Identity</h3><div class="form-grid"><label>Title<input v-model="form.title" required /></label><label>Status<select v-model="form.status"><option v-for="value in ['idea', 'planned', 'active', 'blocked', 'completed', 'archived']" :key="value">{{ value }}</option></select></label><label class="wide">Description<textarea v-model="form.description" rows="3" /></label><label>Planning method<select v-model="form.planning_method"><option v-for="value in ['custom', 'agile', 'waterfall']" :key="value">{{ value }}</option></select></label><label>Category<select v-model="form.category_id"><option value="">Uncategorized</option><option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option></select></label><label>Parent project<select v-model="form.parent_id"><option value="">None</option><option v-for="choice in projects.filter(item => item.id !== project.id)" :key="choice.id" :value="choice.id">{{ choice.title }}</option></select></label></div></section>
    <section class="card"><h3>People & timing</h3><div class="form-grid"><label>Owner<input v-model="form.owner" /></label><label>Assignee<input v-model="form.assignee" /></label><label>Start date<input v-model="form.start_date" type="date" /></label><label>Target date<input v-model="form.target_date" type="date" /></label><label class="wide">Notes<textarea v-model="form.notes" rows="5" /></label></div></section>
  </div><div class="page-actions"><button class="primary" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save changes' }}</button></div></form>
  <section class="card"><div class="section-title"><h3>Related projects</h3><form class="button-row" @submit.prevent="addLink"><select v-model="linkTarget" aria-label="Related project"><option value="">Choose project…</option><option v-for="target in targets" :key="target.project_id" :value="target.project_id">{{ target.label }}</option></select><button type="submit" :disabled="!linkTarget">Add link</button></form></div><p v-if="!links.length" class="muted">No related projects yet.</p><div v-for="entry in links" :key="`${entry.link.source_id}:${entry.link.target_id}:${entry.link.relation}`" class="list-row"><button @click="emit('navigate', entry.other_project?.id)">{{ entry.other_project?.title || 'Unknown project' }}</button><small>{{ entry.link.relation }} · {{ entry.outgoing ? 'outgoing' : 'incoming' }}</small></div></section>
  <TodoPanel :project-id="project.id" module="overview" title="Overview To-Dos" />
  <section class="card danger-zone"><h3>Project lifecycle</h3><p>Archive a finished project or remove it and its owned planning data.</p><div class="button-row"><button @click="confirmAction = 'archive'">Archive project</button><button class="danger" @click="confirmAction = 'delete'">Delete project</button></div></section>
  <ActionDialog :open="!!confirmAction" :title="confirmAction === 'archive' ? 'Archive project?' : 'Delete project permanently?'" :description="confirmAction === 'archive' ? 'The project and its data will remain available in Archived status.' : 'Planning data owned by this project will also be removed.'" :submit-label="confirmAction === 'archive' ? 'Archive project' : 'Delete project'" :danger="confirmAction === 'delete'" @close="confirmAction = ''" @submit="confirmLifecycle" />
</template>
