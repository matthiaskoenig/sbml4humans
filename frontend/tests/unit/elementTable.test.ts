import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import type { Event, Parameter, Reaction, SbmlElement, Species } from "@/api/types";
import ElementCell from "@/components/report/ElementCell.vue";
import ElementTable from "@/components/report/ElementTable.vue";
import { vTooltip } from "@/directives/tooltip";
import { columnsOf, type ColumnDef } from "@/report/columns";
import { attributeEntry } from "@/report/glossary";
import type * as Glossary from "@/report/glossary";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { elementLabel } from "@/report/label";
import { router } from "@/router";

import { loadReport } from "./fixtures";
import { helpKeyOf } from "./help";
import { summaryOf } from "./summary";

// a field a test below withholds the key of, to pin that the column of a field the glossary
// cannot resolve renders no help button; every field of the report does resolve in fact (the
// glossary check enforces it), so a real column never exercises this, and the mock stands in for
// one which would not. `vi.hoisted` gives the factory of the mock, which is itself hoisted above
// this import, a variable it can read at call time.
const noHelp = vi.hoisted(() => ({ field: null as string | null }));
vi.mock("@/report/glossary", async (importOriginal) => {
  const actual = await importOriginal<typeof Glossary>();
  return {
    ...actual,
    attributeKey: (type: Parameters<typeof actual.attributeKey>[0], field: string) =>
      field === noHelp.field ? undefined : actual.attributeKey(type, field),
  };
});

// jsdom does not implement scrollIntoView.
Element.prototype.scrollIntoView ??= function () {};

/** The row height ElementTable pins a windowed row to. */
const ROW_HEIGHT = 36;

const index = new ReportIndex(loadReport("repressilator"));
const species = index.byType("BIOMD0000000012").get("Species") as Species[];
const icgBody = new ReportIndex(loadReport("icg_body"));
const cellCycle = new ReportIndex(loadReport("cell_cycle"));

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
/** Dispatches a keydown that bubbles, so the default prevention of the row is observable. */
function pressKey(target: Element, key: string): KeyboardEvent {
  const event = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true });
  target.dispatchEvent(event);
  return event;
}

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

  it("explains the attribute of every column from its header, without sorting the table", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    // every column of the table is an attribute of the glossary, the two the report starts with
    // (`id` and `name`) the ones every element carries
    const keys = table
      .findAll("thead th")
      .map((th) => helpKeyOf(th.get("[data-testid=help-button]").attributes("href")));
    expect(keys.slice(0, 2)).toEqual(["types/SBase/id", "types/SBase/name"]);
    expect(keys).toContain("types/Species/initialAmount");

    const help = header(table, "id").get("[data-testid=help-button]");
    expect(help.attributes("aria-label")).toBe(`explain ${attributeEntry("Species", "id")!.label}`);

    const before = ids(table);
    help.element.addEventListener("click", (event) => event.preventDefault(), { once: true });
    await help.trigger("click", { button: 0 });
    await flushPromises();
    expect(router.currentRoute.value.query.help).toBe("types/SBase/id");
    expect(header(table, "id").attributes("aria-sort")).toBe("none");
    expect(ids(table)).toEqual(before);
  });

  it("renders no help button for a column the glossary gives no key to", async () => {
    noHelp.field = "id";
    try {
      await router.push("/examples/BIOMD0000000012");
      const table = mountTable(species);
      const idHeader = header(table, "id");
      expect(idHeader.find("[data-testid=help-button]").exists()).toBe(false);
      // the column still sorts: the missing key withholds the help alone
      expect(idHeader.find("[data-testid=sort-button]").exists()).toBe(true);
    } finally {
      noHelp.field = null;
    }
  });

  it("sorts without opening the dialog when the header itself is clicked", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    await header(table, "id").get("[data-testid=sort-button]").trigger("click");
    await flushPromises();
    expect(header(table, "id").attributes("aria-sort")).toBe("ascending");
    expect(router.currentRoute.value.query.help).toBeUndefined();
  });

  it("shows the summary of the column's attribute as the tooltip of its header", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    await header(table, "id").get("[data-testid=sort-button]").trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(
      summaryOf(attributeEntry("Species", "id"), "Species.id"),
    );
  });

  it("says in the tooltip of a column of counts that it counts", async () => {
    // the header of the function terms of a transition explains the terms, the cell counts them
    const qual = new ReportIndex(loadReport("qual_example"));
    await router.push("/examples/qual_example");
    wrapper = mount(ElementTable, {
      props: { type: "Transition", rows: qual.byType("qual_example").get("Transition")! },
      attachTo: document.body,
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(qual) },
      },
    });
    await header(wrapper, "listOfFunctionTerms")
      .get("[data-testid=sort-button]")
      .trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(
      `the number of elements of listOfFunctionTerms: ${attributeEntry("Transition", "listOfFunctionTerms")!.summary}`,
    );
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
    await header(table, "initialAmount").get("[data-testid=sort-button]").trigger("click");
    expect(header(table, "id").attributes("aria-sort")).toBe("none");
    expect(header(table, "initialAmount").attributes("aria-sort")).toBe("ascending");
    expect(ids(table)).toEqual(["PX", "PY", "PZ", "X", "Z", "Y"]);
  });

  it("sorts a row without an identifier by the name the report gives it", async () => {
    await router.push("/examples/BIOMD0000000012");
    const rules = index.byType("BIOMD0000000012").get("AssignmentRule")!;
    wrapper = mount(ElementTable, {
      props: { type: "AssignmentRule", rows: rules },
      attachTo: document.body,
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    });
    const names = rules.map((rule) => elementLabel(index, rule.pk)!);
    await header(wrapper, "id").get("[data-testid=sort-button]").trigger("click");
    expect(ids(wrapper)).toEqual(
      [...names].sort(new Intl.Collator(undefined, { numeric: true }).compare),
    );
    expect(ids(wrapper)[0]).not.toBe(ids(wrapper)[ids(wrapper).length - 1]);
  });

  it("sorts new rows with the current sort", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species.slice(0, 4));
    await header(table, "id").get("[data-testid=sort-button]").trigger("click");
    await header(table, "id").get("[data-testid=sort-button]").trigger("click");
    expect(ids(table)).toEqual(["X", "PZ", "PY", "PX"]);

    // a search or a type toggle passes new rows
    await table.setProps({ rows: species });
    expect(header(table, "id").attributes("aria-sort")).toBe("descending");
    expect(ids(table)).toEqual(["Z", "Y", "X", "PZ", "PY", "PX"]);
  });

  it("has no sort for the units columns", async () => {
    await router.push("/examples/BIOMD0000000012");
    const derived = header(mountTable(species), "derived units");
    expect(derived.find("[data-testid=sort-button]").exists()).toBe(false);
    expect(derived.attributes("aria-sort")).toBeUndefined();
  });

  it("shows the summary as the tooltip of a non sortable header too", async () => {
    await router.push("/examples/BIOMD0000000012");
    const derived = header(mountTable(species), "derived units");
    // the non sortable header has no button, the tooltip sits on the plain span instead
    expect(derived.find("[data-testid=sort-button]").exists()).toBe(false);
    await derived.get("span").trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(
      summaryOf(attributeEntry("Species", "derivedUnits"), "Species.derivedUnits"),
    );
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

  it("toggles the selection with Space", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    const row = () => table.findAll("tbody tr[data-pk]")[2]!;
    const space = pressKey(row().element, " ");
    expect(space.defaultPrevented).toBe(true);
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(species[2]!.pk);
    expect(row().attributes("aria-selected")).toBe("true");

    pressKey(row().element, " ");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBeUndefined();
    expect(row().attributes("aria-selected")).toBe("false");
  });

  it("clears the selection with Enter on the selected row", async () => {
    await router.push(`/examples/BIOMD0000000012?pk=${encodeURIComponent(species[3]!.pk)}`);
    const table = mountTable(species);
    const row = () => table.findAll("tbody tr[data-pk]")[3]!;
    expect(row().attributes("aria-selected")).toBe("true");
    pressKey(row().element, "Enter");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBeUndefined();
    expect(row().attributes("aria-selected")).toBe("false");
  });

  it("leaves the keys on a link in a row to the link", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    const link = table.findAll("tbody tr[data-pk]")[0]!.get("[data-testid=element-link]");
    const enter = pressKey(link.element, "Enter");
    await flushPromises();
    expect(enter.defaultPrevented).toBe(false);
    expect(router.currentRoute.value.query.pk).toBeUndefined();
    expect(table.findAll("tbody tr[data-pk]")[0]!.attributes("aria-selected")).toBe("false");
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

  it("scrolls the viewport when the arrow keys move the focus outside it", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(many);
    (table.element as HTMLElement).scrollTop = ROW_HEIGHT * 500;
    await table.trigger("scroll");
    await nextFrame();
    await flushPromises();

    // the first rendered row (virtual:495) is above the viewport (which starts at
    // virtual:500); ArrowUp moves to virtual:494, further above the render window too
    const first = table.findAll("tbody tr[data-pk]")[0]!;
    expect(first.attributes("data-pk")).toBe("virtual:495");
    await first.trigger("keydown", { key: "ArrowUp" });
    await flushPromises();
    expect(document.activeElement).toBe(table.get('[data-pk="virtual:494"]').element);
    expect((table.element as HTMLElement).scrollTop).toBe(494 * ROW_HEIGHT);

    // ArrowDown from the last rendered row moves past the render window's far edge too
    const last = table.findAll("tbody tr[data-pk]").at(-1)!;
    await last.trigger("keydown", { key: "ArrowDown" });
    await flushPromises();
    const lastIndex = Number(last.attributes("data-pk")!.split(":")[1]) + 1;
    expect(document.activeElement).toBe(table.get(`[data-pk="virtual:${lastIndex}"]`).element);
    expect((table.element as HTMLElement).scrollTop).toBe(500 * ROW_HEIGHT);
  });

  it("gives the roving tabindex to the first row of the viewport, not the overscan above it", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(many);
    (table.element as HTMLElement).scrollTop = ROW_HEIGHT * 500;
    await table.trigger("scroll");
    await nextFrame();
    await flushPromises();
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows[0]!.attributes("data-pk")).toBe("virtual:495");
    const tabbable = rows.filter((row) => row.attributes("tabindex") === "0");
    expect(tabbable).toHaveLength(1);
    expect(tabbable[0]!.attributes("data-pk")).toBe("virtual:500");
  });

  it("resyncs the scroll position once the table returns to windowing after a short spell", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(many);
    (table.element as HTMLElement).scrollTop = ROW_HEIGHT * 500;
    await table.trigger("scroll");
    await nextFrame();
    await flushPromises();

    // a search that thins the rows below the threshold, then the browser resets the
    // scroll of the now unscrollable table
    await table.setProps({ rows: species });
    (table.element as HTMLElement).scrollTop = 0;
    await table.trigger("scroll");
    await nextFrame();
    await flushPromises();

    // clearing the search brings the rows back above the threshold
    await table.setProps({ rows: many });
    await flushPromises();
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows[0]!.attributes("data-pk")).toBe("virtual:0");
    expect(table.find("[data-testid=spacer-before]").exists()).toBe(false);
  });
});

describe("ElementCell", () => {
  const reaction = index.byType("BIOMD0000000012").get("Reaction")![0]! as Reaction;
  const parameter = index.byType("BIOMD0000000012").get("Parameter")![0]! as Parameter;
  const units: ColumnDef = { field: "derivedUnits", header: "derived units", kind: "units" };

  function mountCell(row: SbmlElement, column: ColumnDef, reportIndex: ReportIndex = index) {
    return mount(ElementCell, {
      props: { row, column },
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(reportIndex) },
      },
    });
  }

  const idColumn = columnsOf("Species")[0]!;

  it("renders the type mark of the row before the id", () => {
    const wrapper = mountCell(species[0]!, idColumn);
    const mark = wrapper.get("[data-testid=type-mark]");
    expect(mark.attributes("aria-label")).toBe("Species");
    // the mark carries no text of its own, the cell still reads as the identifier alone
    expect(wrapper.text()).toBe(species[0]!.id);
    expect(wrapper.get("span.font-mono").text()).toBe(species[0]!.id);
  });

  it("keeps the type mark on a row without an identifier", () => {
    const wrapper = mountCell({ ...species[0]!, id: null }, idColumn);
    expect(wrapper.get("[data-testid=type-mark]").attributes("aria-label")).toBe("Species");
  });

  it("names a row without an identifier by the name the report gives it, set apart from an id", () => {
    // the rules of a Level 2 model carry no id; the report names them by the variable they set,
    // which is what the inspector and every link call them
    const rules = index.byType("BIOMD0000000012").get("AssignmentRule")!;
    const rule = rules[0]!;
    expect(rule.id).toBeNull();
    const wrapper = mountCell(rule, columnsOf("AssignmentRule")[0]!);
    const name = wrapper.get("[data-testid=report-name]");
    expect(name.text()).toBe(elementLabel(index, rule.pk));
    expect(name.text()).toBe("t_ave");
    expect(name.classes()).toContain("italic");
    // an id the file writes is shown as it is
    expect(mountCell(species[0]!, idColumn).find("[data-testid=report-name]").exists()).toBe(false);
  });

  it("renders the flux objectives of an objective as the sum of its terms", () => {
    // the column counted the terms, under a header which promises them
    const bounds = new ReportIndex(loadReport("fbc_bounds_v1"));
    const constraints = new ReportIndex(loadReport("fbc_constraints_v3"));
    const column = columnsOf("Objective").find((c) => c.header === "listOfFluxObjectives")!;
    const objective = (reportIndex: ReportIndex, id: string) =>
      reportIndex.mainModel!.listOfObjectives!.find((o) => o.id === id)!;

    const linear = mountCell(objective(bounds, "glc_min"), column, bounds);
    expect(linear.get("[data-testid=terms]").text()).toBe("-1 × EX_glc");
    expect(linear.get("[data-testid=element-link]").attributes("data-pk")).toBe(
      "fbc_bounds_v1/Reaction:EX_glc",
    );
    // a mixed quadratic term multiplies two fluxes (fbc Version 3 §3.7)
    const mixed = mountCell(objective(constraints, "uptake_min"), column, constraints);
    expect(mixed.get("[data-testid=terms]").text()).toBe("4 × v1 × v2");
    expect(mixed.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"))).toEqual(
      ["fbc_constraints_v3/Reaction:v1", "fbc_constraints_v3/Reaction:v2"],
    );
    const fbcExample = new ReportIndex(loadReport("fbc_example"));
    const sum = mountCell(objective(fbcExample, "biomass_max"), column, fbcExample);
    expect(sum.get("[data-testid=terms]").text()).toBe("1 × v1 + 1 × v2 + 1 × v3 + 1 × v4");
    // a list of terms has no order to sort the rows by
    expect(column.kind).not.toBe("count");
  });

  it("renders the components of a user defined constraint as the sum they weigh", () => {
    const constraints = new ReportIndex(loadReport("fbc_constraints_v3"));
    const column = columnsOf("UserDefinedConstraint").find(
      (c) => c.header === "listOfUserDefinedConstraintComponents",
    )!;
    const constraint = (id: string) =>
      constraints.mainModel!.listOfUserDefinedConstraints!.find((c) => c.id === id)!;
    const ratio = mountCell(constraint("ratio"), column, constraints);
    expect(ratio.get("[data-testid=terms]").text()).toBe("c_two × v1 + c_one × v2");
    expect(ratio.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"))).toEqual(
      [
        "fbc_constraints_v3/Parameter:c_two",
        "fbc_constraints_v3/Reaction:v1",
        "fbc_constraints_v3/Parameter:c_one",
        "fbc_constraints_v3/Reaction:v2",
      ],
    );
    expect(mountCell(constraint("budget"), column, constraints).text()).toBe(
      "c_one × v2 × maintenance",
    );
  });

  it("links every deletion of a submodel", () => {
    const deletion = new ReportIndex(loadReport("comp_deletion"));
    const column = columnsOf("Submodel").find((c) => c.header === "listOfDeletions")!;
    const submodel = (id: string) => deletion.mainModel!.listOfSubmodels!.find((s) => s.id === id)!;
    const links = mountCell(submodel("cell1"), column, deletion).findAll(
      "[data-testid=element-link]",
    );
    expect(links.map((l) => l.text())).toEqual(["del_k", "del_sink"]);
    expect(mountCell(submodel("cell2"), column, deletion).text()).toBe("-");
  });

  it("renders every assignment of an event as its variable and its formula", () => {
    const division = (cellCycle.byType("BIOMD0000000007").get("Event") as Event[]).find(
      (event) => event.id === "Division",
    )!;
    const assignments = division.listOfEventAssignments!;
    expect(assignments).toHaveLength(2);
    const column = columnsOf("Event").find((c) => c.header === "listOfEventAssignments")!;
    const wrapper = mountCell(division, column, cellCycle);

    const links = wrapper.findAll("[data-testid=element-link]");
    expect(links.map((link) => link.text())).toEqual(["kp", "Mass"]);
    // the variable is resolved through the "variable" edge of the assignment, not built from
    // its id: the assignment of "kp" points at the parameter of that id
    expect(links.map((link) => link.attributes("data-pk"))).toEqual([
      "BIOMD0000000007/Parameter:kp",
      "BIOMD0000000007/Parameter:Mass",
    ]);

    // the formula of every assignment is typeset next to its variable. KaTeX lays a fraction
    // out with the denominator first in the text flow and separates the two with a zero width
    // space, so "Mass / 2" reads as "2Mass" here.
    const maths = wrapper.findAll("[data-testid=math]");
    expect(maths.map((math) => math.text().replaceAll("​", ""))).toEqual(["2⋅kp", "2Mass"]);

    // one line: the assignments follow each other separated by a comma and a space
    expect(wrapper.text()).toBe("kp = 2⋅kp, Mass = 2Mass​");
  });

  it("shows the placeholder for an event without assignments", () => {
    const start = (cellCycle.byType("BIOMD0000000007").get("Event") as Event[])[0]!;
    const column = columnsOf("Event").find((c) => c.header === "listOfEventAssignments")!;
    const wrapper = mountCell({ ...start, listOfEventAssignments: [] }, column, cellCycle);
    expect(wrapper.find("[data-testid=element-link]").exists()).toBe(false);
    expect(wrapper.text()).toBe("-");
  });

  it("renders the equation of the fixture verbatim", () => {
    expect(reaction.equation).toContain("\u279e");
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
