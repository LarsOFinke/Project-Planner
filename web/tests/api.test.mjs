import assert from 'node:assert/strict'
import test from 'node:test'
import { api, projectApi } from '../src/api.js'
import { validateDocument } from '../src/artifactDocument.js'

test('project writes use the versioned same-origin API', async () => {
  let request
  globalThis.fetch = async (url, options) => {
    request = { url, options }
    return { ok: true, status: 201, json: async () => ({ id: 'project-1' }) }
  }
  assert.deepEqual(await projectApi.create({ title: 'Example' }), { id: 'project-1' })
  assert.equal(request.url, '/api/v1/projects')
  assert.equal(request.options.method, 'POST')
  assert.equal(request.options.body, '{"title":"Example"}')
  assert.equal(request.options.headers['Content-Type'], 'application/json')
})

test('API errors include server details without a false success', async () => {
  globalThis.fetch = async () => ({ ok: false, status: 422, json: async () => ({ detail: 'Invalid project' }) })
  await assert.rejects(api('/projects'), /Invalid project/)
})

test('diagram validation refuses broken references before saving', () => {
  const valid = { version: 2, nodes: [{ id: 'a', label: 'A', x: 0, y: 0, width: 100, height: 50 }], edges: [] }
  assert.equal(validateDocument('diagram', valid), valid)
  assert.throws(() => validateDocument('diagram', { ...valid, edges: [['a', 'missing']] }), /invalid node/)
  assert.throws(() => validateDocument('diagram', { ...valid, version: 99 }), /version 2/)
})
