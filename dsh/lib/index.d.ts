import type { Context } from '@deepseek-ai/cordis'

export declare const name: 'i-have-autism'
export declare const inject: readonly string[]
export declare const ORDER: number
export declare function loadRules(path?: string): string
export declare function apply(ctx: Context): void
