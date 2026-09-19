import { computePosition, flip, offset, shift, type Placement } from "@floating-ui/dom";
import type { Directive, DirectiveBinding } from "vue";

/** The id of the one tooltip element of the application. */
export const TOOLTIP_ID = "app-tooltip";

type TooltipValue = string | null | undefined;

const PLACEMENTS = ["top", "bottom", "left", "right"] as const;

/** The tooltip of an explanation, which is a sentence, in the font of the application. */
const CLASS =
  "fixed top-0 left-0 z-50 max-w-md rounded bg-gray-900 px-2 py-1 text-xs break-words text-white shadow";
/** `v-tooltip.mono`: the tooltip of an id, a value or a formula, in the font they are shown in. */
const MONO_CLASS = `${CLASS} font-mono`;

interface TooltipTarget {
  text: TooltipValue;
  placement: Placement;
  mono: boolean;
  show: () => void;
  hide: () => void;
}

const targets = new WeakMap<HTMLElement, TooltipTarget>();
let tooltip: HTMLDivElement | null = null;
/** The element the tooltip is shown for. */
let owner: HTMLElement | null = null;

function tooltipElement(): HTMLDivElement {
  if (!tooltip?.isConnected) {
    tooltip = document.createElement("div");
    tooltip.id = TOOLTIP_ID;
    tooltip.setAttribute("role", "tooltip");
    tooltip.className = CLASS;
    tooltip.hidden = true;
    document.body.appendChild(tooltip);
  }
  return tooltip;
}

/** The one tooltip element, moved to where it is painted above the element it belongs to. A modal
 * dialog, the help dialog of the report, is painted in the top layer, above everything the page
 * itself paints, whatever its z-index: a tooltip for an element inside it has to live in that
 * dialog, or the backdrop of the dialog covers it. Everything else keeps it in the body. */
function hostedTooltip(el: HTMLElement): HTMLDivElement {
  const tip = tooltipElement();
  const host = el.closest("dialog[open]") ?? document.body;
  if (tip.parentElement !== host) host.appendChild(tip);
  return tip;
}

function placementOf(binding: DirectiveBinding<TooltipValue>): Placement {
  return PLACEMENTS.find((placement) => binding.modifiers[placement]) ?? "top";
}

async function position(el: HTMLElement, placement: Placement): Promise<void> {
  const tip = tooltipElement();
  const { x, y } = await computePosition(el, tip, {
    strategy: "fixed",
    placement,
    middleware: [offset(4), flip(), shift({ padding: 8 })],
  });
  // the tooltip may have moved on to another element while the position was computed
  if (owner !== el) return;
  tip.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") hide();
}

function onScroll(): void {
  hide();
}

function show(el: HTMLElement): void {
  const target = targets.get(el);
  if (!target?.text) return;
  if (owner && owner !== el) owner.removeAttribute("aria-describedby");
  owner = el;
  const tip = hostedTooltip(el);
  tip.textContent = target.text;
  tip.className = target.mono ? MONO_CLASS : CLASS;
  tip.hidden = false;
  el.setAttribute("aria-describedby", TOOLTIP_ID);
  document.addEventListener("keydown", onKeydown);
  document.addEventListener("scroll", onScroll, { capture: true, passive: true });
  void position(el, target.placement);
}

/** Hide the tooltip; with an element only when it is shown for that element. */
function hide(el?: HTMLElement): void {
  if (el && owner !== el) return;
  if (tooltip) tooltip.hidden = true;
  owner?.removeAttribute("aria-describedby");
  owner = null;
  document.removeEventListener("keydown", onKeydown);
  document.removeEventListener("scroll", onScroll, { capture: true });
}

/** `v-tooltip.bottom="text"`: a tooltip on hover and keyboard focus, positioned with
 * Floating UI so that it stays in the viewport. An empty text shows no tooltip. The text is an
 * explanation in the font of the application, `v-tooltip.mono` an id, a value or a formula. */
export const vTooltip: Directive<HTMLElement, TooltipValue> = {
  mounted(el, binding) {
    const target: TooltipTarget = {
      text: binding.value,
      placement: placementOf(binding),
      mono: binding.modifiers.mono === true,
      show: () => show(el),
      hide: () => hide(el),
    };
    targets.set(el, target);
    el.addEventListener("mouseenter", target.show);
    el.addEventListener("focusin", target.show);
    el.addEventListener("mouseleave", target.hide);
    el.addEventListener("focusout", target.hide);
  },
  updated(el, binding) {
    const target = targets.get(el);
    if (!target) return;
    target.text = binding.value;
    target.placement = placementOf(binding);
    target.mono = binding.modifiers.mono === true;
    if (owner !== el) return;
    if (!target.text) {
      hide(el);
      return;
    }
    const tip = tooltipElement();
    tip.textContent = target.text;
    tip.className = target.mono ? MONO_CLASS : CLASS;
    void position(el, target.placement);
  },
  beforeUnmount(el) {
    const target = targets.get(el);
    if (target) {
      el.removeEventListener("mouseenter", target.show);
      el.removeEventListener("focusin", target.show);
      el.removeEventListener("mouseleave", target.hide);
      el.removeEventListener("focusout", target.hide);
      targets.delete(el);
    }
    hide(el);
  },
};
