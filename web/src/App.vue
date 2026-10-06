<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { projectApi } from './api.js'
import ActionDialog from './components/ActionDialog.vue'
import OverviewView from './features/OverviewView.vue'
import PlanningView from './features/PlanningView.vue'
import CollaborationView from './features/CollaborationView.vue'
import ArtifactView from './features/ArtifactView.vue'
import AdminView from './features/AdminView.vue'

const directory = ref([])
const selectedId = ref(localStorage.getItem('planner-project') || '')
const tab = ref('Overview')
const search = ref('')
const error = ref('')
const dialog = ref(null)
const dialogError = ref('')
const busy = ref(false)
const adminOpen = ref(false)
const scale = ref(Number(localStorage.getItem('planner-scale') || 100))
const categories = computed(() => directory.value.map(section => section.category).filter(Boolean))
const projects = computed(() => directory.value.flatMap(section => section.projects.map(item => item.project)))
const selected = computed(() => projects.value.find(project => project.id === selectedId.value))
const filtered = computed(() => directory.value.map(section => ({
  ...section,
  projects: section.projects.filter(item => item.project.title.toLowerCase().includes(search.value.toLowerCase())),
})).filter(section => section.projects.length || (!search.value && section.category)))
const projectFields = computed(() => [
  { name: 'title', label: 'Project name', required: true, placeholder: 'What are you planning?', wide: true },
  { name: 'description', label: 'Short description', type: 'textarea', placeholder: 'What should this project accomplish?', wide: true },
  { name: 'planning_method', label: 'Planning model', type: 'select', options: ['custom', 'agile', 'waterfall'], default: 'custom' },
  { name: 'category_id', label: 'Category', type: 'select', options: [{ value: '', label: 'Uncategorized' }, ...categories.value.map(item => ({ value: item.id, label: item.name }))] },
  { name: 'parent_id', label: 'Parent project', type: 'select', options: [{ value: '', label: 'None' }, ...projects.value.map(item => ({ value: item.id, label: item.title }))] },
  { name: 'status', label: 'Status', type: 'select', options: ['idea', 'planned', 'active', 'blocked', 'completed'], default: 'idea' },
  { name: 'start_date', label: 'Start date', type: 'date' },
  { name: 'target_date', label: 'Target date', type: 'date' },
  { name: 'owner', label: 'Project owner' },
  { name: 'assignee', label: 'Assignee' },
])

async function refresh(preferredId = selectedId.value) {
  directory.value = await projectApi.directory()
  selectedId.value = projects.value.some(project => project.id === preferredId)
    ? preferredId : (projects.value[0]?.id || '')
}
function showDialog(config) { dialogError.value = ''; dialog.value = config }
function newProject(categoryId = '') {
  showDialog({ kind: 'project', title: 'Create project', description: 'Start with a brief. You can add details in Overview.', fields: projectFields.value, initial: { category_id: categoryId, planning_method: 'custom', status: 'idea' }, submitLabel: 'Create project' })
}
function newCategory() { showDialog({ kind: 'category', title: 'New category', fields: [{ name: 'name', label: 'Category name', required: true, wide: true }], submitLabel: 'Create category' }) }
function renameCategory(category) { showDialog({ kind: 'rename-category', id: category.id, title: 'Rename category', fields: [{ name: 'name', label: 'Category name', required: true, wide: true }], initial: { name: category.name }, submitLabel: 'Save name' }) }
function removeCategory(category) { showDialog({ kind: 'remove-category', id: category.id, title: 'Delete category?', description: `Projects in “${category.name}” will move to Uncategorized.`, fields: [], submitLabel: 'Delete category', danger: true }) }
async function submitDialog(values) {
  busy.value = true; dialogError.value = ''
  try {
    const action = dialog.value
    if (action.kind === 'project') {
      const created = await projectApi.create({ ...values, title: values.title.trim(), category_id: values.category_id || null, parent_id: values.parent_id || null, start_date: values.start_date || null, target_date: values.target_date || null })
      await refresh(created.id)
    } else if (action.kind === 'category') {
      await projectApi.category(values.name.trim()); await refresh()
    } else if (action.kind === 'rename-category') {
      await projectApi.renameCategory(action.id, values.name.trim()); await refresh()
    } else if (action.kind === 'remove-category') {
      await projectApi.removeCategory(action.id); await refresh()
    }
    dialog.value = null
  } catch (caught) { dialogError.value = caught.message } finally { busy.value = false }
}
function selectProject(id) { selectedId.value = id; tab.value = 'Overview' }
function toggleFullscreen() { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen?.() }
watch(selectedId, id => localStorage.setItem('planner-project', id))
watch(scale, value => { localStorage.setItem('planner-scale', String(value)); document.documentElement.style.zoom = `${value}%` }, { immediate: true })
onMounted(async () => { try { await refresh() } catch (caught) { error.value = caught.message } })
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-identity"><span class="brand-mark">◈</span><div><strong>PROJECT PLANNER</strong><small>LOCAL-FIRST PLANNING WORKSPACE · 0.1</small></div></div>
      <div class="header-tools"><button @click="toggleFullscreen">Fullscreen</button><label class="scale-control">Scale <select v-model.number="scale"><option v-for="value in [75, 100, 125, 150, 200]" :key="value" :value="value">{{ value }}%</option></select></label><button @click="adminOpen = true">Admin</button></div>
    </header>
    <div class="work-area">
      <aside class="sidebar">
        <div class="sidebar-heading"><div><small>PROJECT DIRECTORY</small><strong>{{ projects.length }} projects</strong></div><button class="icon-button" aria-label="Create category" title="Create category" @click="newCategory">+</button></div>
        <div class="sidebar-actions"><button class="primary" @click="newProject()">+ New project</button></div>
        <label class="search-label">Search<input v-model="search" type="search" placeholder="Find a project…" /></label>
        <div class="directory"><section v-for="section in filtered" :key="section.category?.id || 'uncategorized'"><div class="category-heading"><span>{{ section.category?.name || 'Uncategorized' }}</span><div class="mini-actions"><button v-if="section.category" :aria-label="`Rename ${section.category.name}`" @click="renameCategory(section.category)">✎</button><button :aria-label="`Add project to ${section.category?.name || 'Uncategorized'}`" @click="newProject(section.category?.id || '')">+</button><button v-if="section.category" :aria-label="`Delete ${section.category.name}`" @click="removeCategory(section.category)">×</button></div></div><button v-for="item in section.projects" :key="item.project.id" class="project-row" :class="{ active: selectedId === item.project.id }" :style="{ paddingLeft: `${14 + item.depth * 18}px` }" @click="selectProject(item.project.id)"><span class="project-dot" :class="item.project.status"></span><span>{{ item.project.title }}</span></button></section><p v-if="!filtered.length" class="muted">No matching projects.</p></div>
        <div class="sidebar-foot">Project Planner · Web workspace</div>
      </aside>
      <main class="main-area">
        <div v-if="error" class="alert" role="alert">{{ error }} <button @click="error = ''">Dismiss</button></div>
        <template v-if="selected">
          <div class="workspace-heading"><div><small>PROJECT / {{ selected.planning_method.toUpperCase() }}</small><h1>{{ selected.title }}</h1></div><span class="status-pill">{{ selected.status }}</span></div>
          <nav class="tabs" aria-label="Project views"><button v-for="view in ['Overview', 'Plan Roadmap', 'Diagram', 'Workspace', 'Links']" :key="view" :class="{ active: tab === view }" @click="tab = view">{{ view }}</button></nav>
          <div class="content"><OverviewView v-if="tab === 'Overview'" :key="selected.id" :project="selected" :projects="projects" :categories="categories" @updated="refresh(selected.id)" @deleted="refresh('')" @navigate="selectProject" /><PlanningView v-else-if="tab === 'Plan Roadmap'" :key="selected.id" :project="selected" /><CollaborationView v-else-if="tab === 'Links'" :key="selected.id" :project="selected" /><ArtifactView v-else :key="selected.id + tab" :project="selected" :kind="tab.toLowerCase()" /></div>
        </template>
        <div v-else class="empty-state"><div class="empty-symbol">◈</div><h2>Select or create a project</h2><p>Plan your work, connect related ideas, and keep every artifact in one place.</p><button class="primary" @click="newProject()">Create a project</button></div>
      </main>
    </div>
    <ActionDialog :open="!!dialog" :title="dialog?.title" :description="dialog?.description" :fields="dialog?.fields" :initial="dialog?.initial" :submit-label="dialog?.submitLabel" :danger="dialog?.danger" :busy="busy" :error="dialogError" @close="dialog = null" @submit="submitDialog" />
    <AdminView :open="adminOpen" @close="adminOpen = false" />
  </div>
</template>
