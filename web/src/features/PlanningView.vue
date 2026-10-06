<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api.js'
import ActionDialog from '../components/ActionDialog.vue'

const props = defineProps({ project: Object })
const root = `/projects/${props.project.id}`
const phases = ref([]), backlog = ref([]), sections = ref([]), sprints = ref([])
const sectionItems = ref({}), sectionPhases = ref({}), sectionBacklog = ref({}), sectionSprints = ref({}), tasks = ref({})
const error = ref(''), dialogError = ref(''), busy = ref(false), dialog = ref(null)
const statuses = ['not_started', 'in_progress', 'completed']
const backlogStatuses = ['backlog', 'in_progress', 'done']
const dateFields = [{ name: 'start_date', label: 'Start date', type: 'date' }, { name: 'end_date', label: 'End date', type: 'date' }]

async function load() {
  try {
    const [phaseData, backlogData, sectionData, sprintData] = await Promise.all([
      api(`${root}/phases`), api(`${root}/backlog-items`), api(`${root}/sections`), api(`${root}/sprints`),
    ])
    phases.value = phaseData; backlog.value = backlogData; sections.value = sectionData; sprints.value = sprintData
    sectionItems.value = Object.fromEntries(await Promise.all(sectionData.filter(item => item.section_type === 'free').map(async item => [item.id, await api(`/sections/${item.id}/items`)])))
    sectionPhases.value = Object.fromEntries(await Promise.all(sectionData.filter(item => item.section_type === 'waterfall').map(async item => [item.id, await api(`${root}/phases?section_id=${item.id}`)])))
    sectionBacklog.value = Object.fromEntries(await Promise.all(sectionData.filter(item => item.section_type === 'agile').map(async item => [item.id, await api(`${root}/backlog-items?section_id=${item.id}`)])))
    sectionSprints.value = Object.fromEntries(await Promise.all(sectionData.filter(item => item.section_type === 'agile').map(async item => [item.id, await api(`${root}/sprints?section_id=${item.id}`)])))
    const allPhases = [...phaseData, ...Object.values(sectionPhases.value).flat()]
    tasks.value = Object.fromEntries(await Promise.all(allPhases.map(async phase => [phase.id, await api(`/phases/${phase.id}/tasks`)])))
  } catch (caught) { error.value = caught.message }
}
function open(kind, { item = null, sectionId = null, phaseId = null } = {}) {
  const fields = {
    phase: [{ name: 'name', label: 'Phase name', required: true, wide: true }, { name: 'description', label: 'Description', type: 'textarea', wide: true }, { name: 'status', label: 'Status', type: 'select', options: statuses, default: statuses[0] }, { name: 'parallel_group', label: 'Parallel group' }, ...dateFields],
    task: [{ name: 'title', label: 'Task title', required: true, wide: true }, { name: 'description', label: 'Description', type: 'textarea', wide: true }, { name: 'assignee', label: 'Assignee' }, { name: 'status', label: 'Status', type: 'select', options: statuses, default: statuses[0] }, { name: 'start_date', label: 'Start date', type: 'date' }, { name: 'due_date', label: 'Due date', type: 'date' }],
    backlog: [{ name: 'title', label: 'Backlog item', required: true, wide: true }, { name: 'description', label: 'Description', type: 'textarea', wide: true }, { name: 'assignee', label: 'Assignee' }, { name: 'priority', label: 'Priority', type: 'select', options: ['high', 'medium', 'low'], default: 'medium' }, { name: 'status', label: 'Status', type: 'select', options: backlogStatuses, default: 'backlog' }],
    section: [{ name: 'name', label: 'Section name', required: true, wide: true }, { name: 'section_type', label: 'Structure', type: 'select', options: ['free', 'agile', 'waterfall'], default: 'free' }, { name: 'status', label: 'Status', type: 'select', options: statuses, default: statuses[0] }, { name: 'description', label: 'Description', type: 'textarea', wide: true }, ...dateFields],
    'section-item': [{ name: 'title', label: 'Item title', required: true, wide: true }, { name: 'description', label: 'Description', type: 'textarea', wide: true }, { name: 'assignee', label: 'Assignee' }, { name: 'status', label: 'Status', type: 'select', options: statuses, default: statuses[0] }, { name: 'item_date', label: 'Date', type: 'date' }],
    sprint: [{ name: 'name', label: 'Sprint name', required: true, wide: true }, { name: 'goal', label: 'Goal', type: 'textarea', wide: true }, ...dateFields.map(field => ({ ...field, required: true })), { name: 'selected_item_ids', label: 'Backlog items', type: 'multiselect', wide: true, default: [], options: (sectionId ? sectionBacklog.value[sectionId] || [] : backlog.value).filter(entry => !entry.sprint_id).map(entry => ({ value: entry.id, label: entry.title })) }],
  }
  dialogError.value = ''
  dialog.value = { kind, item, sectionId, phaseId, fields: fields[kind], initial: item || {}, title: `${item ? 'Edit' : 'Add'} ${kind.replace('-', ' ')}`, submitLabel: item ? 'Save changes' : `Add ${kind.replace('-', ' ')}` }
}
function askDelete(path, label) { dialogError.value = ''; dialog.value = { kind: 'delete', path, title: `Delete “${label}”?`, description: 'This action removes the item and its owned work.', fields: [], submitLabel: 'Delete', danger: true } }
function askComplete(sprint) { dialogError.value = ''; dialog.value = { kind: 'complete', item: sprint, title: `Complete “${sprint.name}”?`, description: 'The sprint will move to completed history.', fields: [], submitLabel: 'Complete sprint' } }
function normalized(values) {
  return Object.fromEntries(Object.entries(values).map(([key, value]) => [key, (key.endsWith('_date') || key === 'parallel_group') && !value ? null : value]))
}
async function submit(values) {
  const action = dialog.value
  const body = normalized(values)
  busy.value = true; dialogError.value = ''; error.value = ''
  try {
    if (action.kind === 'delete') await api(action.path, { method: 'DELETE' })
    else if (action.kind === 'complete') await api(`${root}/sprints/${action.item.id}/complete`, { method: 'POST', body: { section_id: action.item.section_id } })
    else {
      let path, method = action.item ? 'PUT' : 'POST'
      if (action.kind === 'phase') { path = `${root}/phases${action.item ? `/${action.item.id}` : ''}`; body.section_id = action.sectionId ?? action.item?.section_id ?? null }
      if (action.kind === 'task') { path = action.item ? `/tasks/${action.item.id}` : `/phases/${action.phaseId}/tasks`; method = action.item ? 'PATCH' : 'POST' }
      if (action.kind === 'backlog') { path = `${root}/backlog-items${action.item ? `/${action.item.id}` : ''}`; body.section_id = action.sectionId ?? action.item?.section_id ?? null }
      if (action.kind === 'section') path = action.item ? `/sections/${action.item.id}` : `${root}/sections`
      if (action.kind === 'section-item') path = action.item ? `/sections/${action.sectionId}/items/${action.item.id}` : `/sections/${action.sectionId}/items`
      if (action.kind === 'sprint') { path = `${root}/sprints`; body.section_id = action.sectionId; body.selected_item_ids = body.selected_item_ids || [] }
      await api(path, { method, body })
    }
    dialog.value = null; await load()
  } catch (caught) { dialogError.value = caught.message } finally { busy.value = false }
}
onMounted(load)
</script>

<template>
  <div class="page-heading"><div><small>PLAN ROADMAP</small><h2>{{ project.planning_method === 'custom' ? 'Custom roadmap' : project.planning_method === 'agile' ? 'Agile planning' : 'Waterfall planning' }}</h2><p>Organize work into sections, phases, tasks, and sprints.</p></div><button @click="load">Refresh</button></div>
  <p v-if="error" class="alert" role="alert">{{ error }}</p>
  <div class="planning-grid" :class="{ loading: busy }">
    <section v-if="project.planning_method === 'custom'" class="card"><div class="section-title"><h3>Roadmap sections</h3><button @click="open('section')">+ Section</button></div><p v-if="!sections.length" class="muted">Add a Free, Agile, or Waterfall section.</p><div v-for="section in sections" :key="section.id" class="planning-section"><div class="section-title"><div><strong>{{ section.name }}</strong><small class="tag">{{ section.section_type }}</small></div><div class="button-row"><button @click="open('section', { item: section })">Edit</button><button class="subtle-danger" @click="askDelete(`/sections/${section.id}`, section.name)">Delete</button></div></div><p v-if="section.description" class="muted">{{ section.description }}</p>
      <template v-if="section.section_type === 'free'"><div v-for="item in sectionItems[section.id] || []" :key="item.id" class="list-row"><button @click="open('section-item', { item, sectionId: section.id })">{{ item.title }}</button><small>{{ item.status }}</small><button class="subtle-danger" @click="askDelete(`/section-items/${item.id}`, item.title)">×</button></div><button @click="open('section-item', { sectionId: section.id })">+ Item</button></template>
      <template v-if="section.section_type === 'waterfall'"><div v-for="phase in sectionPhases[section.id] || []" :key="phase.id" class="planning-section"><div class="list-row"><button @click="open('phase', { item: phase, sectionId: section.id })">{{ phase.name }}</button><small>{{ phase.status }}</small><button @click="open('task', { phaseId: phase.id })">+ Task</button><button class="subtle-danger" @click="askDelete(`${root}/phases/${phase.id}`, phase.name)">×</button></div><div v-for="task in tasks[phase.id] || []" :key="task.id" class="list-row nested-row"><button @click="open('task', { item: task, phaseId: phase.id })">{{ task.title }}</button><small>{{ task.status }}</small><button class="subtle-danger" @click="askDelete(`/tasks/${task.id}`, task.title)">×</button></div></div><button @click="open('phase', { sectionId: section.id })">+ Phase</button></template>
      <template v-if="section.section_type === 'agile'"><div v-for="item in sectionBacklog[section.id] || []" :key="item.id" class="list-row"><button @click="open('backlog', { item, sectionId: section.id })">{{ item.title }}</button><small>{{ item.status }}</small><button class="subtle-danger" @click="askDelete(`/backlog-items/${item.id}`, item.title)">×</button></div><button @click="open('backlog', { sectionId: section.id })">+ Backlog item</button><div v-for="sprint in sectionSprints[section.id] || []" :key="sprint.id" class="list-row"><strong>{{ sprint.name }}</strong><small>{{ sprint.status }}</small><button v-if="sprint.status === 'planned'" @click="askComplete(sprint)">Complete</button></div><button @click="open('sprint', { sectionId: section.id })">+ Sprint</button></template>
    </div></section>
    <section v-if="project.planning_method !== 'agile'" class="card"><div class="section-title"><h3>Phases & tasks</h3><button @click="open('phase')">+ Phase</button></div><p v-if="!phases.length" class="muted">No phases yet.</p><div v-for="phase in phases" :key="phase.id" class="planning-section"><div class="section-title"><div><strong>{{ phase.name }}</strong><small class="tag">{{ phase.status }}</small></div><div class="button-row"><button @click="open('phase', { item: phase })">Edit</button><button class="subtle-danger" @click="askDelete(`${root}/phases/${phase.id}`, phase.name)">×</button></div></div><p v-if="phase.description" class="muted">{{ phase.description }}</p><div v-for="task in tasks[phase.id] || []" :key="task.id" class="list-row"><button @click="open('task', { item: task, phaseId: phase.id })">{{ task.title }}</button><small>{{ task.status }}</small><button class="subtle-danger" @click="askDelete(`/tasks/${task.id}`, task.title)">×</button></div><button @click="open('task', { phaseId: phase.id })">+ Task</button></div></section>
    <section v-if="project.planning_method !== 'waterfall'" class="card"><div class="section-title"><h3>Backlog</h3><button @click="open('backlog')">+ Item</button></div><p v-if="!backlog.length" class="muted">No backlog items yet.</p><div v-for="item in backlog" :key="item.id" class="list-row"><button @click="open('backlog', { item })">{{ item.title }}</button><small>{{ item.status }} · {{ item.priority }}</small><button class="subtle-danger" @click="askDelete(`/backlog-items/${item.id}`, item.title)">×</button></div><div class="section-title with-gap"><h3>Sprints</h3><button @click="open('sprint')">+ Sprint</button></div><div v-for="sprint in sprints" :key="sprint.id" class="list-row"><strong>{{ sprint.name }}</strong><small>{{ sprint.start_date }} – {{ sprint.end_date }} · {{ sprint.status }}</small><button v-if="sprint.status === 'planned'" @click="askComplete(sprint)">Complete</button></div></section>
  </div>
  <ActionDialog :open="!!dialog" :title="dialog?.title" :description="dialog?.description" :fields="dialog?.fields" :initial="dialog?.initial" :submit-label="dialog?.submitLabel" :danger="dialog?.danger" :busy="busy" :error="dialogError" @close="dialog = null" @submit="submit" />
</template>
