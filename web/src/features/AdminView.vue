<script setup>
import { ref, watch } from 'vue'
import { api } from '../api.js'
import ActionDialog from '../components/ActionDialog.vue'

const props = defineProps({ open: Boolean })
const emit = defineEmits(['close'])
const health = ref(null), issues = ref([]), backupFile = ref(null), report = ref(null)
const busy = ref(false), error = ref(''), confirmImport = ref(false)
async function refresh() {
  error.value = ''
  try { [health.value, issues.value] = await Promise.all([api('/health'), api('/issues?limit=20')]) }
  catch (caught) { error.value = caught.message }
}
watch(() => props.open, open => { if (open) refresh() })
async function exportBackup() {
  busy.value = true; error.value = ''
  try {
    const response = await fetch('/api/v1/backup/export')
    if (!response.ok) throw new Error(`Backup export failed (${response.status})`)
    const url = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a')
    anchor.href = url; anchor.download = `project-planner-${new Date().toISOString().slice(0, 10)}.tar.gz`; anchor.click()
    setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (caught) { error.value = caught.message } finally { busy.value = false }
}
function selectFile(event) { backupFile.value = event.target.files?.[0] || null; report.value = null }
async function dryRun() {
  if (!backupFile.value) return
  busy.value = true; error.value = ''
  try { const body = new FormData(); body.append('archive', backupFile.value); report.value = await api('/backup/import/dry-run', { method: 'POST', body }) }
  catch (caught) { error.value = caught.message } finally { busy.value = false }
}
async function importBackup() {
  confirmImport.value = false
  if (!backupFile.value) return
  busy.value = true; error.value = ''
  try { const body = new FormData(); body.append('archive', backupFile.value); report.value = await api('/backup/import', { method: 'POST', body }); await refresh() }
  catch (caught) { error.value = caught.message } finally { busy.value = false }
}
</script>

<template>
  <div v-if="open" class="dialog-backdrop" @click.self="emit('close')">
    <section class="admin-panel card" role="dialog" aria-modal="true" aria-label="Admin and health">
      <div class="dialog-heading"><div><small>GENERAL MANAGEMENT</small><h2>Admin and health</h2></div><button class="icon-button" aria-label="Close admin" @click="emit('close')">×</button></div>
      <p class="muted">Runtime health, complete backups, and recorded application errors.</p>
      <p v-if="error" class="alert" role="alert">{{ error }}</p>
      <div class="admin-grid"><section class="card"><div class="section-title"><h3>Runtime health</h3><button @click="refresh">Refresh</button></div><div v-if="health" class="health-grid"><span>Database</span><strong>{{ health.database_healthy ? 'Healthy' : 'Needs attention' }}</strong><span>Backend</span><strong>{{ health.database_backend }}</strong><span>Python</span><strong>{{ health.python_version }}</strong><span>Recorded issues</span><strong>{{ health.issue_count }}</strong></div></section>
        <section class="card"><h3>Complete backup</h3><p class="muted">Export the database and managed project images. Check an archive before importing it.</p><div class="button-row"><button :disabled="busy" @click="exportBackup">Export backup</button><label class="file-choice">Choose archive<input type="file" accept=".gz,.tar.gz" @change="selectFile" /></label></div><p v-if="backupFile" class="muted">{{ backupFile.name }}</p><div class="button-row"><button :disabled="!backupFile || busy" @click="dryRun">Dry run</button><button class="danger" :disabled="!backupFile || busy || !report" @click="confirmImport = true">Import backup</button></div><pre v-if="report" class="report">{{ JSON.stringify(report, null, 2) }}</pre></section></div>
      <section class="card"><h3>Recent issues</h3><p v-if="!issues.length" class="muted">No recorded application issues.</p><div v-for="issue in issues" :key="issue.id" class="list-row"><span>{{ issue.message }}</span><small>{{ issue.occurred_at }}</small></div></section>
    </section>
  </div>
  <ActionDialog :open="confirmImport" title="Import this backup?" description="The archive will merge its records and restore managed files. Review the dry-run report first." submit-label="Import backup" danger @close="confirmImport = false" @submit="importBackup" />
</template>
