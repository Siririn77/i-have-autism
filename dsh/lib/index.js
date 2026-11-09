// i-have-autism for DeepSeek Harness.
//
// DeepSeek Harness composes a profile from plugin rows, and the system prompt is
// assembled from registered sections. This plugin registers one section holding
// the ruleset, so the rules are present before the first token instead of being
// read on request like a skill.
//
// The ruleset is read from `rules.md` at boot, which is the same condensed core
// every other client injects. It is a file rather than a literal so that the
// build step can copy it from the single source; `tools/build_dsh_plugin.py
// --check` fails when the two drift apart.
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

/** Cordis plugin name; also the section name the prompt shows. */
export const name = 'i-have-autism'

/** The prompt service must exist before `apply` runs. */
export const inject = ['systemPrompt']

/**
 * Sort order of the section. The deployment persona prefix sits at 0 and the
 * suffix at 10200, so 50 places these rules directly after the persona and
 * before the first-party guidance they are meant to constrain.
 */
export const ORDER = 50

const HERE = dirname(fileURLToPath(import.meta.url))
const DEFAULT_RULES = join(HERE, '..', 'rules.md')

/**
 * Read the ruleset, or fail loudly. A section registered with an empty string
 * looks like success in every log and gives the reader no rules at all, so an
 * empty or missing file throws instead.
 * @param {string} [path] absolute path to the ruleset (tests pass their own)
 * @returns {string} the rules text, without a trailing newline
 */
export function loadRules(path = DEFAULT_RULES) {
  const text = readFileSync(path, 'utf8').trim()
  if (!text) throw new Error(`i-have-autism: ruleset at ${path} is empty`)
  return text
}

/**
 * Register the always-on section.
 * @param {import('@deepseek-ai/cordis').Context} ctx
 */
export function apply(ctx) {
  // One environment variable is the off switch, so a single run can opt out
  // without editing the profile: I_HAVE_AUTISM_OFF=1 dsh headless "..."
  if (process.env.I_HAVE_AUTISM_OFF === '1') return
  const text = loadRules(process.env.I_HAVE_AUTISM_RULES || DEFAULT_RULES)
  ctx.systemPrompt.section({
    name,
    order: ORDER,
    text,
    // Literal text: a `{{name}}` group anywhere in a future rule would otherwise be
    // read as a prompt variable and fail assembly.
    interpolate: false,
  })
}
