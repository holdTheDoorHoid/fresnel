/**
 * The map key, always one click away: a "Key" button on the map opens a panel with the same key
 * as the About page (render/site.ts mapKey). It opens by itself on a wide screen the first time,
 * so a new visitor sees what the shapes mean; after that it remembers being open or closed
 * (localStorage "fresnel.key", a per-browser convenience; it works without storage too).
 */
import { mapKey } from '../render/site.ts';

const KEY = 'fresnel.key';

function remembered(): 'open' | 'closed' | null {
  try {
    const v = localStorage.getItem(KEY);
    return v === 'open' || v === 'closed' ? v : null;
  } catch {
    return null;
  }
}

function remember(open: boolean): void {
  try {
    localStorage.setItem(KEY, open ? 'open' : 'closed');
  } catch {
    /* storage blocked: it just will not be remembered */
  }
}

export interface KeyPanel {
  readonly isOpen: boolean;
  open(focus?: boolean): void;
  close(focusButton?: boolean): void;
  /** Close it for now (another panel needs the room) without remembering it as closed. */
  hide(): void;
}

export function initKeyPanel(opts: { button: HTMLButtonElement; panel: HTMLElement; body: HTMLElement; closeBtn: HTMLButtonElement; wide: () => boolean; onToggle?: (open: boolean) => void }): KeyPanel {
  const { button, panel, body, closeBtn } = opts;
  body.innerHTML = mapKey({ headingLevel: 3, idPrefix: 'map-key' }).value;
  const set = (open: boolean, focus: 'panel' | 'button' | null, save: boolean) => {
    panel.hidden = !open;
    button.setAttribute('aria-expanded', String(open));
    button.setAttribute('aria-pressed', String(open));
    if (save) remember(open);
    if (open && focus === 'panel') panel.focus({ preventScroll: true });
    if (!open && focus === 'button') button.focus();
    opts.onToggle?.(open);
  };
  const ctl: KeyPanel = {
    get isOpen() {
      return !panel.hidden;
    },
    open: (focus = true) => set(true, focus ? 'panel' : null, true),
    close: (focusButton = true) => set(false, focusButton ? 'button' : null, true),
    hide: () => set(false, null, false),
  };
  button.addEventListener('click', () => (panel.hidden ? ctl.open() : ctl.close()));
  closeBtn.addEventListener('click', () => ctl.close());
  panel.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      ctl.close();
    }
  });
  const was = remembered();
  set(was ? was === 'open' : opts.wide(), null, false);
  return ctl;
}
