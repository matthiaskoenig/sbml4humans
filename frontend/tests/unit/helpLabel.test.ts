import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { ref } from "vue";

import HelpButton from "@/components/help/HelpButton.vue";
import HelpLabel from "@/components/help/HelpLabel.vue";
import ElementSection from "@/components/report/ElementSection.vue";
import { TOOLTIP_ID, vTooltip } from "@/directives/tooltip";
import { ReportIndexKey } from "@/report/context";
import { typeEntry } from "@/report/glossary";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";
import { helpKeyOf } from "./help";

const index = new ReportIndex(loadReport("repressilator"));
const species = index.byType("BIOMD0000000012").get("Species")!;

let wrapper: VueWrapper | null = null;

afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
});

/** Clicks a link and keeps jsdom, which implements no navigation, from logging an error of its
 * own for the click the component leaves to the browser. The listener runs after the one of the
 * component and never changes whether the component answered the click itself. */
async function click(
  link: ReturnType<VueWrapper["get"]>,
  init: MouseEventInit = { button: 0 },
): Promise<void> {
  link.element.addEventListener("click", (event) => event.preventDefault(), { once: true });
  await link.trigger("click", init);
  // the route the click pushes is applied by the router asynchronously
  await flushPromises();
}

function mountLabel(props: Record<string, unknown>): VueWrapper {
  wrapper = mount(HelpLabel, {
    props,
    slots: { default: "initialAmount" },
    attachTo: document.body,
    global: { plugins: [router], directives: { tooltip: vTooltip } },
  }) as VueWrapper;
  return wrapper;
}

describe("HelpLabel", () => {
  it("is a link to the entry of its key, which a plain click opens in place", async () => {
    await router.push("/examples/BIOMD0000000012");
    const label = mountLabel({ helpKey: "types/Species/initialAmount", tooltip: "the amount" });
    const link = label.get("[data-testid=help-label]");
    expect(link.element.tagName).toBe("A");
    expect(link.text()).toBe("initialAmount");
    expect(helpKeyOf(link.attributes("href"))).toBe("types/Species/initialAmount");

    await click(link);
    expect(router.currentRoute.value.query.help).toBe("types/Species/initialAmount");
  });

  it("leaves a click held with a modifier key to the browser", async () => {
    await router.push("/examples/BIOMD0000000012");
    const label = mountLabel({ helpKey: "types/Species/initialAmount" });
    await click(label.get("[data-testid=help-label]"), { button: 0, ctrlKey: true });
    expect(router.currentRoute.value.query.help).toBeUndefined();
  });

  it("is the plain text it replaces without a key", async () => {
    await router.push("/examples/BIOMD0000000012");
    const label = mountLabel({ tooltip: "the amount" });
    expect(label.find("[data-testid=help-label]").exists()).toBe(false);
    expect(label.find("a").exists()).toBe(false);
    expect(label.text()).toBe("initialAmount");
  });

  it("keeps the tooltip of the label it replaces, with a key and without one", async () => {
    await router.push("/examples/BIOMD0000000012");
    for (const props of [{ helpKey: "types/Species/initialAmount" }, {}]) {
      const label = mountLabel({ ...props, tooltip: "the amount of the species" });
      await label.get("a, span").trigger("mouseenter");
      expect(document.getElementById(TOOLTIP_ID)?.textContent).toBe("the amount of the species");
      label.unmount();
    }
  });
});

describe("HelpButton", () => {
  it("is an icon link with a name of its own, next to a control which carries the label", async () => {
    await router.push("/examples/BIOMD0000000012");
    wrapper = mount(HelpButton, {
      props: { helpKey: "types/Species", label: "Species" },
      attachTo: document.body,
      global: { plugins: [router], directives: { tooltip: vTooltip } },
    }) as VueWrapper;
    const link = wrapper.get("[data-testid=help-button]");
    expect(link.attributes("aria-label")).toBe("explain Species");
    expect(helpKeyOf(link.attributes("href"))).toBe("types/Species");
    expect(link.get("svg").classes()).toContain("lucide-circle-help");
  });

  it("does not let its click reach the control it stands next to", async () => {
    await router.push("/examples/BIOMD0000000012");
    let clicks = 0;
    const Host = {
      components: { HelpButton },
      template: `<div><HelpButton help-key="types/Species" label="Species" /></div>`,
    };
    wrapper = mount(Host, {
      attachTo: document.body,
      global: { plugins: [router], directives: { tooltip: vTooltip } },
    }) as VueWrapper;
    wrapper.element.addEventListener("click", () => (clicks += 1));
    await click(wrapper.get("[data-testid=help-button]"));
    expect(clicks).toBe(0);
    expect(router.currentRoute.value.query.help).toBe("types/Species");
  });
});

describe("ElementSection", () => {
  it("explains the type of its heading", async () => {
    await router.push("/examples/BIOMD0000000012");
    wrapper = mount(ElementSection, {
      props: { type: "Species", rows: species, allRows: species, total: species.length },
      attachTo: document.body,
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    }) as VueWrapper;
    const link = wrapper.get("h2 [data-testid=help-button]");
    expect(helpKeyOf(link.attributes("href"))).toBe("types/Species");
    expect(link.attributes("aria-label")).toBe(`explain ${typeEntry("Species")!.label}`);
  });
});
