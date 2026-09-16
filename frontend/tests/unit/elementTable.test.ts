import PrimeVue from "primevue/config";
import DataTable from "primevue/datatable";
import Tooltip from "primevue/tooltip";
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import type { Parameter, Reaction, SbmlElement, Species } from "@/api/types";
import { primevueOptions } from "@/assets/primevue";
import ElementCell from "@/components/report/ElementCell.vue";
import ElementTable from "@/components/report/ElementTable.vue";
import type { ColumnDef } from "@/report/columns";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

/** The row height ElementTable pins a virtualised row to. */
const ROW_HEIGHT = 36;

// jsdom has no ResizeObserver, which the PrimeVue virtual scroller observes the table with
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
globalThis.ResizeObserver ??= ResizeObserverStub as unknown as typeof ResizeObserver;

const index = new ReportIndex(loadReport("repressilator"));
const species = index.byType("BIOMD0000000012").get("Species") as Species[];

describe("ElementTable", () => {
  it("renders a row per element with the id, a compartment link and marks", async () => {
    await router.push("/examples/BIOMD0000000012");
    const wrapper = mount(ElementTable, {
      props: { type: "Species", rows: species },
      global: {
        plugins: [router, [PrimeVue, primevueOptions]],
        directives: { tooltip: Tooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    });
    const rows = wrapper.findAll("tbody tr[data-pk]");
    expect(rows).toHaveLength(species.length);
    expect(rows[0]!.attributes("data-pk")).toBe(species[0]!.pk);
    expect(rows[0]!.text()).toContain(species[0]!.id);
    const link = rows[0]!.find("[data-testid=element-link]");
    expect(link.exists()).toBe(true);
    expect(link.text()).toBe(species[0]!.compartment);
    expect(wrapper.findAll("thead th").map((th) => th.text())).toContain("compartment");
  });
});

describe("ElementTable virtual scrolling", () => {
  function mountTable(rows: Species[]) {
    return mount(ElementTable, {
      props: { type: "Species", rows },
      global: {
        plugins: [router, [PrimeVue, primevueOptions]],
        directives: { tooltip: Tooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    });
  }

  /** More rows than the threshold of 200, with a pk of their own. */
  const many = Array.from({ length: 201 }, (_, i) => ({ ...species[0]!, pk: `virtual:${i}` }));

  it("renders the virtual scroller above 200 rows, 15 rows of the pinned height high", () => {
    const wrapper = mountTable(many);
    expect(wrapper.find("[data-pc-name=virtualscroller]").exists()).toBe(true);
    // jsdom lays the scroller out with a height of zero, so it renders no row of its own
    expect(wrapper.findAll("tbody tr[data-pk]").length).toBeLessThan(many.length);
    const table = wrapper.findComponent(DataTable);
    expect(table.props("virtualScrollerOptions")).toEqual({ itemSize: ROW_HEIGHT });
    expect(table.props("scrollHeight")).toBe(`${ROW_HEIGHT * 15}px`);
  });

  it("renders a short table without the virtual scroller and with natural rows", () => {
    const wrapper = mountTable(species);
    expect(wrapper.find("[data-pc-name=virtualscroller]").exists()).toBe(false);
    expect(wrapper.find("[data-testid=virtual-cell]").exists()).toBe(false);
    expect(wrapper.findComponent(DataTable).props("virtualScrollerOptions")).toBeNull();
    expect(wrapper.findAll("tbody tr[data-pk]")).toHaveLength(species.length);
  });
});

describe("ElementCell", () => {
  const reaction = index.byType("BIOMD0000000012").get("Reaction")![0]! as Reaction;
  const parameter = index.byType("BIOMD0000000012").get("Parameter")![0]! as Parameter;
  const units: ColumnDef = { field: "derivedUnits", header: "derived units", kind: "units" };

  function mountCell(row: SbmlElement, column: ColumnDef) {
    return mount(ElementCell, {
      props: { row, column },
      global: {
        plugins: [router],
        directives: { tooltip: Tooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    });
  }

  it("renders the equation with the character references of the report decoded", () => {
    expect(reaction.equation).toContain("&#");
    expect(
      mountCell(reaction, { field: "equation", header: "equation", kind: "text" }).text(),
    ).toBe("X \u279e");
  });

  it("renders the latex of a dimensionless unit as the placeholder", () => {
    expect(species[0]!.derivedUnits).toBe("item");
    expect(mountCell(species[0]!, units).find("[data-testid=units]").exists()).toBe(true);
    expect(parameter.derivedUnits).toBe("-");
    const placeholder = mountCell(parameter, units);
    expect(placeholder.find("[data-testid=units]").exists()).toBe(false);
    expect(placeholder.text()).toBe("-");
  });
});
