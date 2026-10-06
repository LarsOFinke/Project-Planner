<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  open: Boolean,
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  fields: { type: Array, default: () => [] },
  initial: { type: Object, default: () => ({}) },
  submitLabel: { type: String, default: 'Save' },
  danger: Boolean,
  busy: Boolean,
  error: { type: String, default: '' },
})
const emit = defineEmits(['close', 'submit'])
const values = reactive({})
watch(() => props.open, open => {
  if (!open) return
  for (const key of Object.keys(values)) delete values[key]
  for (const field of props.fields) values[field.name] = props.initial[field.name] ?? field.default ?? ''
})
function submit() { emit('submit', { ...values }) }
</script>

<template>
  <div v-if="open" class="dialog-backdrop" @click.self="emit('close')" @keydown.esc="emit('close')">
    <section class="dialog card" role="dialog" aria-modal="true" :aria-label="title">
      <div class="dialog-heading"><div><small>PROJECT PLANNER</small><h2>{{ title }}</h2></div><button class="icon-button" aria-label="Close dialog" @click="emit('close')">×</button></div>
      <p v-if="description" class="muted">{{ description }}</p>
      <form @submit.prevent="submit">
        <div v-if="fields.length" class="form-grid dialog-form">
          <label v-for="field in fields" :key="field.name" :class="{ wide: field.wide }">
            {{ field.label }}
            <span v-if="field.type === 'multiselect'" class="checkbox-list"><span v-for="option in field.options" :key="option.value" class="checkbox-option"><input v-model="values[field.name]" type="checkbox" :value="option.value" />{{ option.label }}</span></span>
            <textarea v-else-if="field.type === 'textarea'" v-model="values[field.name]" :rows="field.rows || 3" :required="field.required" :placeholder="field.placeholder || ''" />
            <select v-else-if="field.type === 'select'" v-model="values[field.name]" :required="field.required">
              <option v-for="option in field.options" :key="option.value ?? option" :value="option.value ?? option">{{ option.label ?? option }}</option>
            </select>
            <input v-else v-model="values[field.name]" :type="field.type || 'text'" :required="field.required" :placeholder="field.placeholder || ''" :min="field.min" :max="field.max" />
          </label>
        </div>
        <p v-if="error" class="alert" role="alert">{{ error }}</p>
        <div class="dialog-actions"><button type="button" @click="emit('close')">Cancel</button><button type="submit" :class="danger ? 'danger' : 'primary'" :disabled="busy">{{ busy ? 'Working…' : submitLabel }}</button></div>
      </form>
    </section>
  </div>
</template>
