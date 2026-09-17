import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { ref } from "vue";

import type { Parameter, Reaction, SbmlElement, Species } from "@/api/types";
import ElementCell from "@/components/report/ElementCell.vue";
import ElementTable from "@/components/report/ElementTable.vue";
import { vTooltip } from "@/directives/tooltip";
import { columnsOf, type ColumnDef } from "@/report/columns";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

/** The row height ElementTable pins a windowed row to. */
const ROW_HEIGHT = 36;

const index = new ReportIndex(loadReport("repressilator"));
const species = index.byType("BIOMD0000000012").get("Species") as Species[];
const icgBody = new ReportIndex(loadReport("icg_body"));

let wrapper: ReturnType<typeof mount> | null = null;

function mountTable(rows: SbmlElement[]) {
  wrapper = mount(ElementTable, {
    props: { type: "Species", rows },
    attachTo: document.body,
    global: {
      plugins: [router],
      directives: { tooltip: vTooltip },
      provide: { [ReportIndexKey as symbol]: ref(index) },
    },
  });
  return wrapper;
}

const header = (table: ReturnType<typeof mount>, title: string) =>
  table.findAll("thead th").find((th) => th.text() === title)!;
const ids = (table: ReturnType<typeof mount>) =>
  table.findAll("tbody tr[data-pk]").map((row) => row.find("td").text());
const nextFrame = () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));

afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
});

describe("ElementTable", () => {
  it("renders a row per element with the id, a compartment link and marks", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    expect(table.attributes("data-testid")).toBe("table-Species");
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows).toHaveLength(species.length);
    expect(rows[0]!.attributes("data-pk")).toBe(species[0]!.pk);
    expect(rows[0]!.text()).toContain(species[0]!.id);
    const link = rows[0]!.find("[data-testid=element-link]");
    expect(link.exists()).toBe(true);
    expect(link.text()).toBe(species[0]!.compartment);
    expect(table.findAll("thead th").map((th) => th.text())).toContain("compartment");
  });

  it("sorts by a click on the header and toggles the order", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    expect(ids(table)).toEqual(["PX", "PY", "PZ", "X", "Y", "Z"]);
    expect(header(table, "id").attributes("aria-sort")).toBe("none");

    await header(table, "id").get("[data-testid=sort-button]").trigger("click");
    expect(header(table, "id").attributes("aria-sort")).toBe("ascending");
    expect(ids(table)).toEqual(["PX", "PY", "PZ", "X", "Y", "Z"]);

    await header(table, "id").get("[data-testid=sort-button]").trigger("click");
    expect(header(table, "id").attributes("aria-sort")).toBe("descending");
    expect(ids(table)).toEqual(["Z", "Y", "X", "PZ", "PY", "PX"]);

    // another column starts ascending, equal values keep the order of the report
    await header(table, "initial amount").get("[data-testid=sort-button]").trigger("click");
    expect(header(table, "id").attributes("aria-sort")).toBe("none");
    expect(header(table, "initial amount").attributes("aria-sort")).toBe("ascending");
    expect(ids(table)).toEqual(["PX", "PY", "PZ", "X", "Z", "Y"]);
  });

  it("has no sort for the units columns", async () => {
    await router.push("/examples/BIOMD0000000012");
    const derived = header(mountTable(species), "derived units");
    expect(derived.find("[data-testid=sort-button]").exists()).toBe(false);
    expect(derived.attributes("aria-sort")).toBeUndefined();
  });

  it("selects a row by a click and clears the selection by a second click", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    await table.findAll("tbody tr[data-pk]")[1]!.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(species[1]!.pk);
    const selected = table.findAll("tbody tr[data-pk]")[1]!;
    expect(selected.attributes("aria-selected")).toBe("true");
    expect(selected.classes()).toContain("bg-selected");

    await selected.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBeUndefined();
    expect(table.findAll("tbody tr[data-pk]")[1]!.attributes("aria-selected")).toBe("false");
  });

  it("follows a link in a cell without selecting the row", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    const link = table.findAll("tbody tr[data-pk]")[0]!.get("[data-testid=element-link]");
    await link.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(link.attributes("data-pk"));
    expect(router.currentRoute.value.query.pk).not.toBe(species[0]!.pk);
  });

  it("moves the focus with the arrow keys and selects with Enter", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows.map((row) => row.attributes("tabindex"))).toEqual([
      "0",
      "-1",
      "-1",
      "-1",
      "-1",
      "-1",
    ]);
    (rows[0]!.element as HTMLElement).focus();
    await rows[0]!.trigger("keydown", { key: "ArrowDown" });
    await flushPromises();
    expect(document.activeElement).toBe(table.findAll("tbody tr[data-pk]")[1]!.element);
    await table.findAll("tbody tr[data-pk]")[1]!.trigger("keydown", { key: "Enter" });
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(species[1]!.pk);
    expect(table.findAll("tbody tr[data-pk]")[1]!.attributes("tabindex")).toBe("0");
  });
});

describe("ElementTable windowing", () => {
  /** More rows than the threshold of 200, with a pk of their own. */
  const many = Array.from({ length: 1000 }, (_, i) => ({ ...species[0]!, pk: `virtual:${i}` }));

  it("renders only the rows in view of a table above 200 rows", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(many);
    expect((table.element as HTMLElement).style.height).toBe(`${ROW_HEIGHT * 15}px`);
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows).toHaveLength(20);
    expect(rows[0]!.attributes("data-pk")).toBe("virtual:0");
    expect(table.find("[data-testid=spacer-before]").exists()).toBe(false);
    expect((table.get("[data-testid=spacer-after] td").element as HTMLElement).style.height).toBe(
      `${980 * ROW_HEIGHT}px`,
    );
    expect(table.findAll("[data-testid=virtual-cell]").length).toBeGreaterThan(0);
  });

  it("renders the rows of the scroll position", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(many);
    (table.element as HTMLElement).scrollTop = ROW_HEIGHT * 500;
    await table.trigger("scroll");
    await nextFrame();
    await flushPromises();
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows[0]!.attributes("data-pk")).toBe("virtual:495");
    expect(rows).toHaveLength(25);
    expect((table.get("[data-testid=spacer-before] td").element as HTMLElement).style.height).toBe(
      `${495 * ROW_HEIGHT}px`,
    );
    expect((table.get("[data-testid=spacer-after] td").element as HTMLElement).style.height).toBe(
      `${480 * ROW_HEIGHT}px`,
    );
  });

  it("renders a short table without windowing and with natural rows", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    expect((table.element as HTMLElement).style.height).toBe("");
    expect(table.find("[data-testid=virtual-cell]").exists()).toBe(false);
    expect(table.find("[data-testid=spacer-after]").exists()).toBe(false);
    expect(table.findAll("tbody tr[data-pk]")).toHaveLength(species.length);
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
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    });
  }

  it("renders the equation of the fixture verbatim", () => {
    expect(reaction.equation).toContain("➞");
    expect(
      mountCell(reaction, { field: "equation", header: "equation", kind: "text" }).text(),
    ).toBe(reaction.equation.trim());
  });

  it("renders the latex of a dimensionless unit as the placeholder", () => {
    expect(species[0]!.derivedUnits).toBe("item");
    expect(mountCell(species[0]!, units).find("[data-testid=units]").exists()).toBe(true);
    expect(parameter.derivedUnits).toBe("-");
    const placeholder = mountCell(parameter, units);
    expect(placeholder.find("[data-testid=units]").exists()).toBe(false);
    expect(placeholder.text()).toBe("-");
  });

  it("renders the latex of the substance units next to the unit id", () => {
    const species = icgBody.mainModel!.listOfSpecies!.find(
      (element) => element.id === "Cre_plasma_icg",
    ) as Species;
    expect(species.substanceUnits).toBe("mmole");
    expect(species.unitsLatex).toBe("mmol");
    const column = columnsOf("Species").find((c) => c.field === "substanceUnits")!;
    const wrapper = mount(ElementCell, {
      props: { row: species, column },
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(icgBody) },
      },
    });
    expect(wrapper.text()).toContain(species.substanceUnits);
    expect(wrapper.find("[data-testid=units]").exists()).toBe(true);
  });

  it("shows a unit id once when the units link has no renderable latex", () => {
    const dimensionless = icgBody.mainModel!.listOfParameters!.find(
      (p) => p.id === "Fblood",
    ) as Parameter;
    expect(dimensionless.unitsLatex).toBe("-");
    const wrapper = mount(ElementCell, {
      props: {
        row: dimensionless,
        column: { field: "units", header: "units", kind: "link", link: "units" },
      },
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(icgBody) },
      },
    });
    expect(wrapper.text()).toBe(dimensionless.units);
    expect(wrapper.find("[data-testid=units]").exists()).toBe(false);
  });
});
