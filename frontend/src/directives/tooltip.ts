import { computePosition, flip, offset, shift, type Placement } from "@floating-ui/dom";
import type { Directive, DirectiveBinding } from "vue";

/** The id of the one tooltip element of the application. */
export const TOOLTIP_ID = "app-tooltip";

type TooltipValue = string | null | undefined;

const PLACEMENTS = ["top", "bottom", "left", "right"] as const;

interface TooltipTarget {
  text: TooltipValue;
  placement: Placement;
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
    tooltip.className =
      "fixed top-0 left-0 z-50 max-w-md rounded bg-gray-900 px-2 py-1 font-mono text-xs break-words text-white shadow";
    tooltip.hidden = true;
    document.body.appendChild(tooltip);
  }
  return tooltip;
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
  const tip = tooltipElement();
  tip.textContent = target.text;
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
 * Floating UI so that it stays in the viewport. An empty text shows no tooltip. */
export const vTooltip: Directive<HTMLElement, TooltipValue> = {
  mounted(el, binding) {
    const target: TooltipTarget = {
      text: binding.value,
      placement: placementOf(binding),
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
    if (owner !== el) return;
    if (!target.text) {
      hide(el);
      return;
    }
    tooltipElement().textContent = target.text;
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
