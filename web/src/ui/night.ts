/**
 * "The light at night" in the browser: the view from a ship's deck at sea, the light flashing in
 * its recorded pattern and colour at a distance the visitor chooses, with the controls, the live
 * readout, the strip's moving playhead and the mini-map ring (ui/night-map.ts, loaded when it
 * scrolls into view).
 *
 * Motion: the scene plays by itself only when the visitor has not asked for reduced motion and
 * the light flashes no more than three times a second; otherwise it shows a still frame and the
 * strip, with a Play button. It pauses whenever it is off screen or the tab is hidden.
 */
import { readLight } from '../lib/characteristic.ts';
import { lengthFor, nauticalMiles } from '../lib/format.ts';
import { html } from '../lib/html.ts';
import { lightEras, type LightEra } from '../lib/light-history.ts';
import { phaseAt, type Pattern, type PatternResult } from '../lib/pattern.ts';
import {
  DEFAULT_EYE_M,
  EYE_HEIGHTS,
  VISIBILITY,
  VISIBILITY_ORDER,
  defaultDistanceNm,
  maxDistanceNm,
  sight,
  type Sighting,
  type VisibilityId,
} from '../lib/sighting.ts';
import { eraBody, eraHead, patternFor, sightingWords, sourceName, viewsOf, type LightView, type NightData } from '../render/night.ts';
import { LIGHT_RGB } from '../render/strip.ts';

const FOV_EYE = 40;
const FOV_BINOCULARS = 7;
const MAX_SAFE_FLASH_RATE = 3;

interface State {
  era: number;
  light: number;
  view: number;
  /** 0: the record's characteristic; n: the nth other source's. */
  alt: number;
  /** -1: the record's focal height; n: the nth source's value. */
  focal: number;
  distance: number;
  eye: number;
  vis: VisibilityId;
  playing: boolean;
  binoculars: boolean;
}

/** A tiny seeded random generator, so the stars stay put. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

interface Star {
  x: number;
  y: number;
  r: number;
  a: number;
}

function makeStars(seed: number, n: number): Star[] {
  const rnd = mulberry32(seed);
  return Array.from({ length: n }, () => {
    const y = rnd() ** 1.4; // more stars high up, fewer near the hazy horizon
    return { x: rnd(), y, r: 0.4 + rnd() ** 3 * 1.1, a: 0.25 + rnd() * 0.6 };
  });
}

const STARS_EYE = makeStars(1791, 170);
const STARS_BINO = makeStars(1852, 60);

function hexToRgb(hex: string): [number, number, number] {
  const n = Number.parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function rgba(hex: string, a: number): string {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${Math.max(0, Math.min(1, a)).toFixed(3)})`;
}

const norm = (s: string | null | undefined) => (s ?? '').replace(/[\s.]+/g, '').toLowerCase();

export function initNight(host: HTMLElement): void {
  const section = host.closest('section') ?? document.body;
  let data: NightData;
  try {
    data = JSON.parse(host.dataset.night ?? '') as NightData;
  } catch {
    return;
  }
  const headPart = section.querySelector<HTMLElement>('[data-night-part="head"]');
  const bodyPart = section.querySelector<HTMLElement>('[data-night-part="body"]');
  const mapHost = section.querySelector<HTMLElement>('[data-night-map]');
  const country = data.country;
  const eras = lightEras({ light: data.light, events: data.events, status: data.status });
  if (!eras.length) return;

  // Other sources' patterns and heights, when sources disagree.
  const recordChar = data.light?.characteristic ?? null;
  const altChars = data.alt.characteristic.filter((v) => norm(v.value) !== norm(recordChar));
  const focalChoices = data.alt.focal.length > 1 ? data.alt.focal : [];
  const recordFocal = data.light?.focal_height_m ?? null;
  const defaultFocal = focalChoices.findIndex((v) => recordFocal !== null && Math.abs(v.value - recordFocal) < 0.05);

  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const st: State = { era: eras.length - 1, light: 0, view: 0, alt: 0, focal: defaultFocal, distance: 5, eye: DEFAULT_EYE_M, vis: 'normal', playing: false, binoculars: false };

  const era = (): LightEra => {
    let e = eras[st.era]!;
    const latest = st.era === eras.length - 1;
    if (latest && st.alt > 0) {
      const alt = altChars[st.alt - 1]!;
      e = { ...e, reading: readLight(alt.value), note: `The pattern as ${data.sources[alt.source] ?? sourceName(alt.source)} gives it, not the one in the facts above.` };
    }
    if (st.focal >= 0 && focalChoices[st.focal] && e.focalFrom !== 'era') e = { ...e, focalM: focalChoices[st.focal]!.value };
    return e;
  };
  const views = (e: LightEra): LightView[] => {
    const l = e.reading.lights[st.light];
    return l ? viewsOf(l) : [];
  };
  const current = () => {
    const e = era();
    const l = e.reading.lights[st.light] ?? null;
    const vs = views(e);
    const v = vs[st.view] ?? vs[0] ?? null;
    const res: PatternResult | null = l && v && !v.dark ? patternFor(l, v) : null;
    // The strip that shows this view: strips are drawn for the lit views only, in order.
    const stripIndex = v && !v.dark ? vs.filter((x) => !x.dark).indexOf(v) : -1;
    return { e, l, v, res, pattern: res?.ok ? res.pattern : null, stripIndex };
  };

  // Starting distance: a typical approach, inside the visible range.
  {
    const e = era();
    const s = sight({ focalM: e.focalM, nominalNm: e.nominalNm, eyeM: st.eye, distanceNm: 1, visibility: 'normal' });
    st.distance = defaultDistanceNm(s.visibleNm);
  }

  /* ---------- Markup ---------- */
  const uid = `night-${Math.random().toString(36).slice(2, 8)}`;
  const maxNm = () => {
    const e = era();
    return maxDistanceNm(e.focalM, e.nominalNm);
  };
  host.innerHTML = html`
    <div class="night-pickers" data-pickers></div>
    <div class="night-stage">
      <canvas class="night-canvas" aria-hidden="true"></canvas>
      <div class="night-tools">
        <button type="button" class="btn btn-chip night-play" data-play><span data-play-label>Play</span></button>
        <button type="button" class="btn btn-chip night-bino" aria-pressed="false" data-bino>Binoculars (7×)</button>
      </div>
    </div>
    <p class="night-warn fine" data-warn hidden></p>
    <p class="night-readout" role="status" aria-live="polite" data-readout></p>
    <div class="night-settings">
      <div class="night-field night-dist">
        <label for="${uid}-d">Your distance from the light <output id="${uid}-o" for="${uid}-d" data-dist-out></output></label>
        <input type="range" id="${uid}-d" min="0.5" max="${maxNm()}" step="0.5" value="${st.distance}" data-dist>
        <span class="night-dist-ends fine" aria-hidden="true"><span>0.5 nmi</span><span data-dist-max>${maxNm()} nmi</span></span>
      </div>
      <div class="night-field">
        <label for="${uid}-e">Your eye above the water</label>
        <select id="${uid}-e" data-eye>${EYE_HEIGHTS.map((h) => html`<option value="${h.m}"${h.m === st.eye ? html` selected` : ''}>${lengthFor(country, h.m)}, ${h.label}</option>`)}</select>
      </div>
      <fieldset class="night-field night-vis">
        <legend>Visibility</legend>
        <div class="seg">${VISIBILITY_ORDER.map((v) => html`<label title="${VISIBILITY[v].meaning}"><input type="radio" name="${uid}-v" value="${v}"${v === st.vis ? html` checked` : ''}><span>${VISIBILITY[v].label}</span></label>`)}</div>
        <p class="fine" data-vis-meaning></p>
      </fieldset>
      ${focalChoices.length
        ? html`<fieldset class="night-field night-focal"><legend>Sources disagree on its height: use</legend>${focalChoices.map((v, i) => html`<label class="opt-line"><input type="radio" name="${uid}-f" value="${i}"${i === st.focal ? html` checked` : ''}> ${lengthFor(country, v.value)} <span class="fine">(${data.sources[v.source] ?? sourceName(v.source)})</span></label>`)}</fieldset>`
        : ''}
    </div>`.value;
  host.hidden = false;

  const $ = <T extends Element>(sel: string) => host.querySelector<T>(sel)!;
  const canvas = $<HTMLCanvasElement>('canvas');
  const stage = $<HTMLElement>('.night-stage');
  const pickers = $<HTMLElement>('[data-pickers]');
  const playBtn = $<HTMLButtonElement>('[data-play]');
  const binoBtn = $<HTMLButtonElement>('[data-bino]');
  const warn = $<HTMLElement>('[data-warn]');
  const readout = $<HTMLElement>('[data-readout]');
  const dist = $<HTMLInputElement>('[data-dist]');
  const distOut = $<HTMLOutputElement>('[data-dist-out]');
  const distMax = $<HTMLElement>('[data-dist-max]');
  const eyeSel = $<HTMLSelectElement>('[data-eye]');
  const visMeaning = $<HTMLElement>('[data-vis-meaning]');

  /* ---------- Pickers: year, which light, which source, which sector ---------- */
  const renderPickers = () => {
    const e = era();
    const lights = e.reading.lights;
    const vs = views(e);
    pickers.innerHTML = html`
      ${eras.length > 1
        ? html`<div class="night-field"><label for="${uid}-y">The light in</label>
            <select id="${uid}-y" data-era>${eras.map((x, i) => html`<option value="${i}"${i === st.era ? html` selected` : ''}>${x.short}${x.reading.lights.length ? '' : ' (pattern not recorded)'}</option>`)}</select></div>`
        : ''}
      ${altChars.length && st.era === eras.length - 1
        ? html`<fieldset class="night-field"><legend>Sources give different patterns: show</legend>
            <label class="opt-line"><input type="radio" name="${uid}-a" value="0"${st.alt === 0 ? html` checked` : ''}> <code class="char">${recordChar ?? ''}</code> <span class="fine">(${data.sources[data.light?.from ?? ''] ?? 'the facts above'})</span></label>
            ${altChars.map((v, i) => html`<label class="opt-line"><input type="radio" name="${uid}-a" value="${i + 1}"${st.alt === i + 1 ? html` checked` : ''}> <code class="char">${v.value}</code> <span class="fine">(${data.sources[v.source] ?? sourceName(v.source)})</span></label>`)}
          </fieldset>`
        : ''}
      ${lights.length > 1
        ? html`<fieldset class="night-field"><legend>Which light</legend><div class="seg">${lights.map((l, i) => html`<label><input type="radio" name="${uid}-l" value="${i}"${i === st.light ? html` checked` : ''}><span>${l.role ? l.role.replace(/^./, (c) => c.toUpperCase()) : l.era ? l.era.label.replace(/^./, (c) => c.toUpperCase()) : `Light ${i + 1}`}</span></label>`)}</div></fieldset>`
        : ''}
      ${vs.length > 1
        ? html`<fieldset class="night-field"><legend>Where you are</legend><div class="seg">${vs.map((v, i) => html`<label><input type="radio" name="${uid}-s" value="${i}"${i === st.view ? html` checked` : ''}><span>${v.label}</span></label>`)}</div>
            <p class="fine">The record does not say which way each sector faces${vs.some((v) => /°/.test(v.label)) ? ' (except as shown)' : ''}, so choose the one you want to see.</p></fieldset>`
        : ''}`.value;
    pickers.hidden = !pickers.innerHTML.trim();
  };

  const renderEraParts = () => {
    const e = era();
    if (headPart) headPart.innerHTML = eraHead(e, eras.length).value;
    if (bodyPart) bodyPart.innerHTML = eraBody(e, country, `strip-${data.id}`).value;
  };

  /* ---------- Derived state ---------- */
  let cur = current();
  let seen: Sighting = sight({ focalM: cur.e.focalM, nominalNm: cur.e.nominalNm, eyeM: st.eye, distanceNm: st.distance, visibility: st.vis });
  let stripHead: SVGLineElement | null = null;
  let stripMeta = { x0: 0, w: 0, span: 1 };

  const steadyOrNone = (p: Pattern | null) => !p || p.steady;

  const refresh = (opts: { eraChanged?: boolean } = {}) => {
    cur = current();
    if (opts.eraChanged) {
      renderPickers();
      renderEraParts();
      const m = maxNm();
      dist.max = String(m);
      distMax.textContent = `${m} nmi`;
      if (st.distance > m) st.distance = m;
    }
    seen = sight({ focalM: cur.e.focalM, nominalNm: cur.e.nominalNm, eyeM: st.eye, distanceNm: st.distance, visibility: st.vis });
    dist.value = String(st.distance);
    distOut.textContent = nauticalMiles(st.distance) ?? '';
    dist.setAttribute('aria-valuetext', nauticalMiles(st.distance) ?? '');
    visMeaning.textContent = `${VISIBILITY[st.vis].meaning.replace(/^./, (c) => c.toUpperCase())}.`;
    const sightable = cur.e.focalM !== null || cur.e.nominalNm !== null;
    // Distance, eye height and weather change nothing when neither height nor range is known.
    host.querySelector<HTMLElement>('.night-settings')!.hidden = !sightable;
    // The flashing warning and the play button.
    const p = cur.pattern;
    const fast = !!p && p.flashRate > MAX_SAFE_FLASH_RATE;
    const reasons: string[] = [];
    if (cur.res && !cur.res.ok) reasons.push(cur.res.reason);
    if (fast) reasons.push(`This light flashes ${p!.flashRate} times within a second, so the scene does not play by itself. Press Play only if flashing is comfortable for you.`);
    warn.textContent = reasons.join(' ');
    warn.hidden = !reasons.length;
    playBtn.disabled = steadyOrNone(p);
    playBtn.title = steadyOrNone(p) ? (p ? 'A steady light: there is no rhythm to play' : 'There is no pattern to play') : '';
    // The readout.
    readout.textContent = sightingWords(seen, {
      distanceNm: st.distance,
      eyeM: st.eye,
      visibility: st.vis,
      country,
      past: cur.e.past,
      drawable: !!p,
      dark: !!cur.v?.dark,
    });
    // The strip that matches the view.
    stripHead = null;
    if (bodyPart) {
      const figs = [...bodyPart.querySelectorAll<HTMLElement>('figure.strip')];
      for (const fig of figs) {
        const on = fig.dataset.view === `${st.light}-${cur.stripIndex}`;
        fig.classList.toggle('is-current', on && figs.length > 1);
        const svg = fig.querySelector<SVGSVGElement>('svg');
        const head = svg?.querySelector<SVGLineElement>('.strip-head') ?? null;
        if (head) head.setAttribute('visibility', 'hidden');
        if (on && svg && head && p && !p.steady && p.periodRecorded) {
          stripHead = head;
          stripMeta = { x0: Number(svg.dataset.x0), w: Number(svg.dataset.w), span: Number(svg.dataset.span) || p.period };
        }
      }
    }
    mapUpdate?.();
    draw();
  };

  /* ---------- Play, pause, binoculars ---------- */
  let raf = 0;
  let clock0 = performance.now();
  let frozen = 0.05;
  let onScreen = true;
  const t = () => (st.playing ? (performance.now() - clock0) / 1000 : frozen);
  const loop = () => {
    raf = 0;
    if (!st.playing || !onScreen || document.hidden) return;
    draw();
    raf = requestAnimationFrame(loop);
  };
  const kick = () => {
    if (!raf && st.playing && onScreen && !document.hidden) raf = requestAnimationFrame(loop);
  };
  const setPlaying = (on: boolean) => {
    if (on === st.playing) return;
    if (on) clock0 = performance.now() - frozen * 1000;
    else frozen = t();
    st.playing = on;
    playBtn.classList.toggle('is-playing', on);
    playBtn.querySelector('[data-play-label]')!.textContent = on ? 'Pause' : 'Play';
    if (on) kick();
    else draw();
  };
  playBtn.addEventListener('click', () => setPlaying(!st.playing));
  binoBtn.addEventListener('click', () => {
    st.binoculars = !st.binoculars;
    binoBtn.setAttribute('aria-pressed', String(st.binoculars));
    draw();
  });

  /* ---------- Settings ---------- */
  dist.addEventListener('input', () => {
    st.distance = Number(dist.value);
    refresh();
  });
  eyeSel.addEventListener('change', () => {
    st.eye = Number(eyeSel.value);
    refresh();
  });
  host.addEventListener('change', (ev) => {
    const el = ev.target as HTMLInputElement | HTMLSelectElement;
    const name = el.getAttribute('name') ?? '';
    if (el.matches('[data-era]')) {
      st.era = Number(el.value);
      st.light = 0;
      st.view = 0;
      st.alt = 0;
      refresh({ eraChanged: true });
    } else if (name === `${uid}-v`) {
      st.vis = el.value as VisibilityId;
      refresh();
    } else if (name === `${uid}-a`) {
      st.alt = Number(el.value);
      st.light = 0;
      st.view = 0;
      refresh({ eraChanged: true });
    } else if (name === `${uid}-l`) {
      st.light = Number(el.value);
      st.view = 0;
      renderPickers();
      refresh();
    } else if (name === `${uid}-s`) {
      st.view = Number(el.value);
      refresh();
    } else if (name === `${uid}-f`) {
      st.focal = Number(el.value);
      refresh({ eraChanged: true });
    }
  });

  /* ---------- Drawing ---------- */
  const g = canvas.getContext('2d');
  let W = 0;
  let H = 0;
  const size = () => {
    const w = Math.round(stage.clientWidth);
    if (!w) return;
    const h = Math.round(w * (w < 560 ? 0.72 : 0.5));
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    if (w === W && h === H && canvas.width === Math.round(w * dpr)) return;
    W = w;
    H = h;
    canvas.style.height = `${h}px`;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    g?.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  };

  const label = (text: string, x: number, y: number, align: CanvasTextAlign = 'center') => {
    if (!g) return;
    g.font = `600 ${W < 420 ? 12 : 13}px 'Atkinson Hyperlegible Next Variable', system-ui, sans-serif`;
    g.textAlign = align;
    g.textBaseline = 'bottom';
    g.fillStyle = 'rgba(205,218,230,0.92)';
    g.shadowColor = 'rgba(0,0,0,0.8)';
    g.shadowBlur = 3;
    g.fillText(text, x, y);
    g.shadowBlur = 0;
  };

  const brackets = (x: number, y: number, r = 9) => {
    if (!g) return;
    g.strokeStyle = 'rgba(150,172,194,0.8)';
    g.lineWidth = 1.4;
    const k = 4;
    g.beginPath();
    for (const [sx, sy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const) {
      g.moveTo(x + sx * r, y + sy * (r - k));
      g.lineTo(x + sx * r, y + sy * r);
      g.lineTo(x + sx * (r - k), y + sy * r);
    }
    g.stroke();
  };

  function draw(): void {
    if (!g || !W || !H) return;
    const time = t();
    const vis = st.vis;
    const fov = ((st.binoculars ? FOV_BINOCULARS : FOV_EYE) * Math.PI) / 180;
    const pxPerRad = W / fov;
    const yEye = H * 0.42;
    const yHor = Math.min(H - 4, yEye + seen.dip * pxPerRad);

    // Sky
    const sky = g.createLinearGradient(0, 0, 0, yHor);
    const skyLow = vis === 'clear' ? '#0b1a2d' : vis === 'normal' ? '#0d1c2c' : vis === 'haze' ? '#1b2633' : '#262f38';
    sky.addColorStop(0, vis === 'fog' ? '#1c242c' : '#01040b');
    sky.addColorStop(1, skyLow);
    g.fillStyle = sky;
    g.fillRect(0, 0, W, yHor + 1);

    // Stars
    if (vis !== 'fog') {
      const stars = st.binoculars ? STARS_BINO : STARS_EYE;
      const dim = vis === 'clear' ? 1 : vis === 'normal' ? 0.8 : 0.35;
      for (const s of stars) {
        const sy = yHor - (s.y * 0.97 + 0.03) * yHor;
        const fade = vis === 'haze' && yHor - sy < yHor * 0.5 ? 0.25 : 1;
        if (vis === 'haze' && s.a < 0.45) continue;
        g.fillStyle = `rgba(230,236,245,${(s.a * dim * fade).toFixed(3)})`;
        g.beginPath();
        g.arc(s.x * W, sy, s.r * (st.binoculars ? 1.25 : 1), 0, Math.PI * 2);
        g.fill();
      }
    }

    // Sea
    const sea = g.createLinearGradient(0, yHor, 0, H);
    sea.addColorStop(0, vis === 'fog' ? '#1f282f' : '#07101b');
    sea.addColorStop(1, vis === 'fog' ? '#12181d' : '#010307');
    g.fillStyle = sea;
    g.fillRect(0, yHor, W, H - yHor);
    // A few swell lines, closer together towards the horizon (static: no motion).
    if (vis !== 'fog') {
      g.strokeStyle = 'rgba(120,150,180,0.06)';
      g.lineWidth = 1;
      for (let i = 1; i < 9; i++) {
        const y = yHor + (H - yHor) * (i / 9) ** 1.8;
        g.beginPath();
        g.moveTo(0, y);
        g.lineTo(W, y);
        g.stroke();
      }
    }
    // Horizon
    if (vis !== 'fog') {
      g.strokeStyle = vis === 'haze' ? 'rgba(140,165,190,0.14)' : 'rgba(140,165,190,0.3)';
      g.lineWidth = 1;
      g.beginPath();
      g.moveTo(0, yHor + 0.5);
      g.lineTo(W, yHor + 0.5);
      g.stroke();
    }

    const cx = W / 2;
    const ly = seen.elevation !== null ? Math.min(yHor - 0.5, yEye - seen.elevation * pxPerRad) : yHor - 0.5;
    const p = cur.pattern;
    const ph = p ? phaseAt(p, time) : null;
    const level = ph && ph.colour ? ph.level : 0;
    const hex = ph?.colour ? LIGHT_RGB[ph.colour] ?? LIGHT_RGB.W! : LIGHT_RGB.W!;

    if (cur.v?.dark) {
      brackets(cx, yHor - 6);
      label('dark sector: the light is screened off from here', cx, yHor - 20);
    } else if (seen.state === 'below_horizon') {
      if (seen.loom > 0 && p) {
        const lv = p.steady ? 1 : level;
        if (lv > 0) {
          g.save();
          g.beginPath();
          g.rect(0, 0, W, yHor);
          g.clip();
          const rx = W * (st.binoculars ? 0.5 : 0.16);
          const ry = H * 0.14;
          g.translate(cx, yHor);
          g.scale(1, ry / rx);
          const loom = g.createRadialGradient(0, 0, 0, 0, 0, rx);
          loom.addColorStop(0, rgba(hex, 0.3 * seen.loom * lv));
          loom.addColorStop(1, rgba(hex, 0));
          g.fillStyle = loom;
          g.fillRect(-rx, -rx, rx * 2, rx * 2);
          g.restore();
        }
        label('loom: the glow of its beam above your horizon', cx, yHor - H * 0.16);
      } else {
        brackets(cx, yHor - 4);
        label('below your horizon', cx, yHor - 18);
      }
    } else if (seen.state === 'too_faint') {
      brackets(cx, ly);
      label('too faint to see from here', cx, ly - 14);
    } else if (p) {
      const x = seen.ratio !== null ? Math.max(0, Math.log10(seen.ratio)) : 1.2;
      if (level > 0) {
        const bino = st.binoculars ? 1.5 : 1;
        const strength = Math.min(1, 0.3 + x / 3) * level;
        // Scattering halo in haze and fog.
        if (vis === 'fog' || vis === 'haze') {
          const hr = (vis === 'fog' ? 46 : 18) * bino;
          const halo = g.createRadialGradient(cx, ly, 0, cx, ly, hr);
          halo.addColorStop(0, rgba(hex, 0.22 * strength));
          halo.addColorStop(1, rgba(hex, 0));
          g.fillStyle = halo;
          g.fillRect(cx - hr, ly - hr, hr * 2, hr * 2);
        }
        // Reflection on the water.
        if (vis !== 'fog' && x > 0.3) {
          const len = (H - yHor) * Math.min(0.7, 0.25 + x / 8);
          const wd = (2 + x * 1.6) * bino;
          for (let y = yHor + 2; y < yHor + len; y += 3) {
            const f = 1 - (y - yHor) / len;
            g.fillStyle = rgba(hex, 0.16 * strength * f);
            const jitter = Math.sin(y * 1.7) * wd * 0.35;
            g.fillRect(cx - wd / 2 + jitter, y, wd * (0.6 + 0.4 * Math.sin(y * 0.9) ** 2), 1);
          }
        }
        // Glow and core.
        const gr = (3 + 2.4 * Math.min(x, 5)) * bino;
        const glow = g.createRadialGradient(cx, ly, 0, cx, ly, gr);
        glow.addColorStop(0, rgba(hex, 0.75 * strength));
        glow.addColorStop(0.35, rgba(hex, 0.28 * strength));
        glow.addColorStop(1, rgba(hex, 0));
        g.fillStyle = glow;
        g.fillRect(cx - gr, ly - gr, gr * 2, gr * 2);
        g.fillStyle = rgba('#ffffff', Math.min(1, 0.45 + x / 3) * level);
        g.beginPath();
        g.arc(cx, ly, (1.1 + 0.3 * Math.min(x, 4)) * bino, 0, Math.PI * 2);
        g.fill();
      }
      if (seen.ratio !== null && seen.ratio < 3) label('just visible, if you know where to look', cx, ly - 16);
      else if (seen.state === 'unknown' && seen.aboveHorizon === null) label('height and range not recorded: drawn on the horizon', cx, ly - 16);
      else if (seen.state === 'unknown') label('brightness not recorded', cx, ly - 16);
      else if (seen.aboveHorizon === null) label('height not recorded: drawn on the horizon', cx, ly - 16);
    } else {
      brackets(cx, ly);
      label(cur.res && !cur.res.ok ? 'the pattern cannot be drawn' : 'pattern not recorded', cx, ly - 14);
    }

    // What the view is.
    g.font = `500 11px 'Atkinson Hyperlegible Next Variable', system-ui, sans-serif`;
    g.textAlign = 'right';
    g.textBaseline = 'bottom';
    g.fillStyle = 'rgba(170,188,205,0.75)';
    g.fillText(st.binoculars ? '7× binoculars, 7° wide' : 'naked eye, 40° wide', W - 8, H - 6);
    g.textAlign = 'left';
    g.fillText(`${nauticalMiles(st.distance)} · eye ${lengthFor(country, st.eye)} · ${VISIBILITY[vis].label.toLowerCase()}`, 8, H - 6);

    // Strip playhead.
    if (stripHead && p) {
      const span = stripMeta.span;
      const x = stripMeta.x0 + ((((time % span) + span) % span) / span) * stripMeta.w;
      stripHead.setAttribute('x1', x.toFixed(1));
      stripHead.setAttribute('x2', x.toFixed(1));
      stripHead.setAttribute('visibility', 'visible');
    }
  }

  /* ---------- Mini-map (loaded when it scrolls near) ---------- */
  let mapUpdate: (() => void) | null = null;
  if (mapHost) {
    const startMap = async () => {
      const { createNightMap } = await import('./night-map.ts');
      const m = await createNightMap(mapHost, { lat: data.lat, lon: data.lon, name: data.name, country });
      if (!m) return;
      mapUpdate = () => m.update({ sighting: seen, distanceNm: st.distance, eyeM: st.eye, visibility: st.vis, past: cur.e.past });
      mapUpdate();
    };
    if (typeof IntersectionObserver === 'function') {
      const io = new IntersectionObserver((entries) => {
        if (entries.some((en) => en.isIntersecting)) {
          io.disconnect();
          void startMap();
        }
      }, { rootMargin: '300px' });
      mapHost.hidden = false;
      io.observe(mapHost);
    } else {
      mapHost.hidden = false;
      void startMap();
    }
  }

  /* ---------- Start ---------- */
  renderPickers();
  refresh();
  if (typeof ResizeObserver === 'function') new ResizeObserver(size).observe(stage);
  else addEventListener('resize', size);
  size();
  if (typeof IntersectionObserver === 'function') {
    new IntersectionObserver((entries) => {
      onScreen = entries.some((en) => en.isIntersecting);
      kick();
    }).observe(stage);
  }
  document.addEventListener('visibilitychange', kick);
  const autoplay = () => !reduced.matches && !!cur.pattern && !cur.pattern.steady && cur.pattern.flashRate <= MAX_SAFE_FLASH_RATE;
  if (autoplay()) setPlaying(true);
  reduced.addEventListener('change', () => {
    if (reduced.matches) setPlaying(false);
  });
  // Fonts load after first paint; redraw the labels with the right face.
  void document.fonts?.ready.then(() => draw());
}
