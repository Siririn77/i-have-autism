// Exercise the DSH plugin's `apply` without DeepSeek Harness present.
//
// The plugin only touches `ctx.systemPrompt.section`, so a fake context is a
// complete stand-in: nothing else about the host is involved. Usage:
//   node tests/dsh_plugin_driver.mjs <plugin dir> [rules path]
// Prints one JSON object describing the registered section, or the error.
import { pathToFileURL } from 'node:url'
import { join, resolve } from 'node:path'

const dir = resolve(process.argv[2])
const rules = process.argv[3]
const mod = await import(pathToFileURL(join(dir, 'lib', 'index.js')).href)

const sections = []
const ctx = { systemPrompt: { section: (s) => (sections.push(s), () => {}) } }

const out = {
  name: mod.name,
  inject: mod.inject,
  order: mod.ORDER,
  modules: Object.keys(mod).sort(),
  sections: 0,
  text: null,
  interpolate: null,
  error: null,
}

try {
  if (rules) process.env.I_HAVE_AUTISM_RULES = rules
  mod.apply(ctx)
  out.sections = sections.length
  if (sections.length) {
    out.sectionName = sections[0].name
    out.order = sections[0].order
    out.text = sections[0].text
    out.interpolate = sections[0].interpolate === true
  }
} catch (error) {
  out.error = String(error && error.message ? error.message : error)
}

process.stdout.write(JSON.stringify(out))
