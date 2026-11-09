// Generate the governed og:image set (1200x630) for every public route.
// Light "Luminous Silicon Atlas" palette, matching assets/css/main.css: pale
// silicon substrate with the die-reticle grid, copper/teal wafer, ink type,
// teal rule, monospace layer identifiers. Run: node scripts/generate-og-images.mjs
// Requires the globally installed playwright and the preinstalled Chromium.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { existsSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'assets', 'og');
mkdirSync(OUT, { recursive: true });

const PAGES = [
  { file: 'home', id: '', eyebrow: 'AI CHIP SYSTEMS INTELLIGENCE', title: 'AI Chips, from Silicon to Systems.' },
  { file: 'compute-sovereignty', id: '', eyebrow: 'CATEGORY DEFINITION', title: 'Compute Sovereignty' },
  { file: 'sovereignty-stack', id: '01–08', eyebrow: 'CORE ONTOLOGY', title: 'Silicon Sovereignty Stack' },
  { file: 'design-fabrication-packaging', id: '01–03', eyebrow: 'DEPENDENCY LAYERS', title: 'Design, Fabrication, Packaging' },
  { file: 'hbm-memory', id: '04', eyebrow: 'DEPENDENCY LAYER', title: 'Memory' },
  { file: 'interconnects', id: '05', eyebrow: 'DEPENDENCY LAYER', title: 'Interconnect' },
  { file: 'power-and-thermal-limits', id: '06', eyebrow: 'DEPENDENCY LAYER', title: 'Power / Thermal' },
  { file: 'export-control-layer', id: '07', eyebrow: 'DEPENDENCY LAYER', title: 'Export-Control' },
  { file: 'ai-chip-infrastructure', id: '08', eyebrow: 'DEPENDENCY LAYER', title: 'Deployment' },
  { file: 'chip-dependency-map', id: '', eyebrow: 'GOVERNED DIAGNOSTIC ENGINE', title: 'Chip Dependency Map' },
  { file: 'methodology', id: '', eyebrow: 'EVIDENCE GOVERNANCE', title: 'Methodology' },
  { file: 'sources', id: '', eyebrow: 'GOVERNED EVIDENCE', title: 'Source Registry' },
  { file: 'strategic-availability', id: '', eyebrow: 'GOVERNED ENGAGEMENT', title: 'Strategic Availability' },
];

function template({ eyebrow, title, id, small }) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;box-sizing:border-box}
  body{width:1200px;height:630px;background:#f5f7f5;color:#1a2935;
    font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
    background-image:linear-gradient(rgba(38,55,70,.06) 1px,transparent 1px),
      linear-gradient(90deg,rgba(38,55,70,.06) 1px,transparent 1px);
    background-size:48px 48px;position:relative;overflow:hidden;
    display:flex;flex-direction:column;justify-content:center;padding:0 84px}
  .wafer{position:absolute;right:-140px;top:50%;transform:translateY(-50%);
    width:520px;height:520px;border:2px solid #147881;border-radius:50%;background-color:#ffffff;
    background-image:repeating-radial-gradient(circle at center,transparent 0 34px,rgba(165,104,67,.25) 35px 36px),
      linear-gradient(45deg,transparent 49.7%,rgba(20,120,129,.4) 50%,transparent 50.3%),
      linear-gradient(-45deg,transparent 49.7%,rgba(20,120,129,.3) 50%,transparent 50.3%)}
  .wafer:before{content:"";position:absolute;left:-30%;top:50%;width:160%;height:1px;background:#a56843;opacity:.7}
  .wafer:after{content:"";position:absolute;top:-30%;left:50%;height:160%;width:1px;background:#a56843;opacity:.7}
  .core{position:absolute;right:75px;top:50%;transform:translateY(-50%);
    width:210px;height:210px;background:#ffffff;border:2px solid #a56843;
    display:flex;align-items:center;justify-content:center}
  .core span{font-family:ui-monospace,Consolas,monospace;font-size:64px;color:#8a5232;letter-spacing:.04em}
  .copy{max-width:740px;position:relative;z-index:2}
  .eyebrow{text-transform:uppercase;letter-spacing:.2em;font-size:22px;font-weight:700;color:#8a5232;margin-bottom:30px}
  h1{font-family:Charter,"Bitstream Charter","Iowan Old Style",Georgia,serif;font-size:${small ? '58px' : '76px'};line-height:1.05;letter-spacing:-.02em;font-weight:600}
  .rule{width:120px;height:3px;background:#147881;margin:38px 0 26px}
  .domain{font-size:26px;color:#4f5e6b;letter-spacing:.03em}
  .domain b{color:#1a2935;font-weight:700}
  </style></head><body>
    <div class="wafer"></div>
    ${id ? `<div class="core"><span>${id}</span></div>` : ''}
    <div class="copy">
      <div class="eyebrow">${eyebrow}</div>
      <h1>${title}</h1>
      <div class="rule"></div>
      <div class="domain"><b>AI</b>Electronic<b>Chips</b>.com — governed reference layer</div>
    </div>
  </body></html>`;
}

const PINNED = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const browser = await chromium.launch(existsSync(PINNED) ? { executablePath: PINNED } : {});
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
for (const p of PAGES) {
  await page.setContent(template(p), { waitUntil: 'networkidle' });
  await page.screenshot({ path: join(OUT, `${p.file}.png`) });
  console.log('generated', `${p.file}.png`);
}
await browser.close();
