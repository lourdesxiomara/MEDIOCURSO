// Validates every Mermaid diagram in specs/ with the official parser.
// Usage: cd tools && npm install && node verificar-mermaid.mjs ../specs
import { JSDOM } from 'jsdom';
import fs from 'fs'; import path from 'path';
const dom = new JSDOM('<!doctype html><html><body></body></html>', { pretendToBeVisual: true });
globalThis.window = dom.window; globalThis.document = dom.window.document;
globalThis.DOMPurify = undefined;
const { default: mermaid } = await import('mermaid');
mermaid.initialize({ startOnLoad: false });
const root = process.argv[2]; let fallos = 0, total = 0;
const walk = d => fs.readdirSync(d,{withFileTypes:true}).flatMap(e => e.isDirectory()? walk(path.join(d,e.name)) : e.name.endsWith('.md')? [path.join(d,e.name)] : []);
for (const f of walk(root)) {
  const t = fs.readFileSync(f,'utf8'); const bloques = [...t.matchAll(/```mermaid\n([\s\S]*?)```/g)].map(m=>m[1]);
  for (const [i,b] of bloques.entries()) { total++;
    try { await mermaid.parse(b); } catch (e) { fallos++; console.log(`FAIL ${path.relative(root,f)} block ${i+1}: ${String(e.message||e).split('\n').slice(0,3).join(' | ')}`); } }
}
console.log(`${total} diagrams, ${fallos} with errors`); process.exit(fallos?1:0);
