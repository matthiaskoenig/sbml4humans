import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import HelpDialog from "@/components/help/HelpDialog.vue";
import { vTooltip } from "@/directives/tooltip";
import {
  loadGlossaryDetails,
  type GlossaryDetails,
  type HelpEntry,
} from "@/report/glossaryDetails";
import { router } from "@/router";

vi.mock("@/report/glossaryDetails", () => ({ loadGlossaryDetails: vi.fn() }));

const load = vi.mocked(loadGlossaryDetails);

/** A few entries in the shape the generator writes, enough for every part of the dialog: a type
 * with attributes, rules and related entries, one of its attributes, the common attributes the
 * last row of an attributes table leads to, a data type and a link kind, which carries nothing
 * but its description. */
const ENTRIES: Record<string, HelpEntry> = {
  "types/Species": {
    kind: "type",
    label: "Species",
    summary: "a pool of a chemical entity in a compartment",
    description: "A species is located in a [compartment](glossary:types/Compartment).",
    package: "core",
    docs: "reference/species/",
    spec: { label: "core 4.6", section: "4.6", url: "https://example.invalid/core" },
    rules: [
      {
        id: 20623,
        severity: "error",
        message: "A <species> object must have the required attributes 'id' and 'compartment'.",
        section: "L3V2 Section 4.6",
      },
      {
        id: 10713,
        severity: "warning",
        message: "The value of 'sboTerm' is expected to be an SBO identifier.",
      },
    ],
    attributes: ["types/Species/initialAmount"],
    related: ["types/Compartment"],
  },
  "types/Species/initialAmount": {
    kind: "attribute",
    label: "initialAmount",
    summary: "the amount of the species when the simulation starts",
    description: "The initial amount is the quantity of the species at the start of a simulation.",
    package: "core",
    docs: "reference/species/#initialamount",
    owner: "types/Species",
    type: { label: "double", key: "datatypes/double" },
    spec: { label: "core 4.6.4", section: "4.6.4", url: "https://example.invalid/core" },
    required: false,
    default: "the quantity is unknown or set by an initial assignment or a rule",
    rules: [{ id: 20609, severity: "error", message: "A <species> cannot set both values." }],
  },
  "types/Compartment": {
    kind: "type",
    label: "Compartment",
    summary: "a bounded space in which species are located",
    description: "A compartment is a bounded space.",
    package: "core",
    docs: "reference/compartment/",
  },
  "types/SBase": {
    kind: "type",
    label: "SBase",
    summary: "the attributes every element of an SBML model carries",
    description: "Almost every object of an SBML model derives from `SBase`.",
    package: "core",
    docs: "reference/sbase/",
    attributes: ["types/SBase/id"],
  },
  "types/SBase/id": {
    kind: "attribute",
    label: "id",
    summary: "the identifier other elements of the model use to reference the element",
    description: "The id is the name of the element inside the model.",
    package: "core",
    docs: "reference/sbase/#id",
    owner: "types/SBase",
    type: { label: "SId", key: "datatypes/SId" },
    required: false,
  },
  "datatypes/double": {
    kind: "datatype",
    label: "double",
    summary: "a number with a fractional part and an exponent",
    description: "A double is a floating point number.",
    package: "core",
    docs: "reference/datatypes/#double",
    values: ["1.0", "2.0"],
  },
  "datatypes/SId": {
    kind: "datatype",
    label: "SId",
    summary: "an identifier of an element of a model",
    description: "An SId is an identifier.",
    package: "core",
    docs: "reference/datatypes/#sid",
  },
  "links/compartment": {
    kind: "link",
    label: "compartment",
    summary: "the compartment a species is located in",
    description: "Every [species](glossary:types/Species) names its compartment.",
    package: "core",
    docs: "reference/links/#compartment",
  },
};

const DETAILS: GlossaryDetails = { entries: ENTRIES };

/** jsdom implements the `<dialog>` element and its `open` attribute and nothing else: neither
 * `showModal` nor `close` exists on `HTMLDialogElement`. These give it the part of the behaviour
 * the dialog builds on, a modal which opens, closes and fires `close` as Escape does. */
function stubDialogElement(): void {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement): void {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement): void {
    if (!this.hasAttribute("open")) return;
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
}

let wrapper: VueWrapper | null = null;
let showModal: ReturnType<typeof vi.spyOn>;
let close: ReturnType<typeof vi.spyOn>;

/** Settles the dialog: the details of the first flush, the description which the second renders
 * once `HelpMarkdown` and with it `markdown-it` are imported, and the route of a link which was
 * clicked, which the router applies asynchronously as well. */
async function settle(): Promise<void> {
  await flushPromises();
  await flushPromises();
}

async function mountDialog(query: Record<string, string> = {}): Promise<VueWrapper> {
  await router.push({ path: "/report", query });
  await router.isReady();
  wrapper = mount(HelpDialog, {
    attachTo: document.body,
    global: { plugins: [router], directives: { tooltip: vTooltip } },
  });
  await settle();
  return wrapper;
}

/** Opens an entry the way a label of the report does, by pushing its key into the route. */
async function open(key: string): Promise<void> {
  await router.push({ path: "/report", query: { help: key } });
  await settle();
}

const dialog = (): VueWrapper => wrapper!;
const text = (testid: string): string => dialog().get(`[data-testid=${testid}]`).text();
const has = (testid: string): boolean => dialog().find(`[data-testid=${testid}]`).exists();

/** Clicks a link of the dialog and lets the route follow. Every link of the dialog is a real
 * anchor, and jsdom implements no navigation: a click the dialog leaves to the browser, one held
 * with a modifier key, would log an error of jsdom into the output of the run, so the default is
 * prevented here, next to and after the handler of the component, which never changes whether
 * that handler answered the click itself. */
async function click(selector: string, init: MouseEventInit = { button: 0 }): Promise<void> {
  const link = dialog().get(selector);
  link.element.addEventListener("click", (event) => event.preventDefault(), { once: true });
  await link.trigger("click", init);
  await settle();
}

describe("HelpDialog", () => {
  // the dialog imports `HelpMarkdown`, and with it `markdown-it`, dynamically, so that neither is
  // part of the chunk every page loads. The first import of it is a transform of vitest, which
  // takes longer than the ticks a test flushes; importing it once here lets every dialog of the
  // run resolve it from the cache of the module graph instead.
  beforeAll(async () => {
    await import("@/components/help/HelpMarkdown.vue");
  });

  beforeEach(() => {
    stubDialogElement();
    showModal = vi.spyOn(HTMLDialogElement.prototype, "showModal");
    close = vi.spyOn(HTMLDialogElement.prototype, "close");
    load.mockReset().mockResolvedValue(DETAILS);
  });

  afterEach(() => {
    wrapper?.unmount();
    wrapper = null;
    vi.restoreAllMocks();
  });

  it("opens on a key of the route and closes when the key leaves it", async () => {
    await mountDialog();
    expect(showModal).not.toHaveBeenCalled();
    expect(has("help-title")).toBe(false);

    await open("types/Species");
    expect(showModal).toHaveBeenCalledTimes(1);
    expect(text("help-title")).toContain("Species");

    await router.push({ path: "/report", query: {} });
    await flushPromises();
    expect(close).toHaveBeenCalledTimes(1);
    expect(has("help-title")).toBe(false);
  });

  it("shows the summary and every part a type has", async () => {
    await mountDialog({ help: "types/Species" });
    expect(text("help-summary")).toBe(ENTRIES["types/Species"]!.summary);
    expect(text("help-overview")).toContain("A species is located in a compartment.");
    expect(text("help-technical")).toContain("core 4.6");
    expect(dialog().findAll("[data-testid=help-rule]")).toHaveLength(2);
    expect(dialog().findAll("[data-testid=help-attribute-row]")).toHaveLength(2);
    expect(text("help-related")).toContain("Compartment");
    expect(dialog().get("[data-testid=help-docs-link]").attributes("href")).toContain(
      "reference/species/",
    );
    // a type is not an attribute of something, so it has neither an owner nor the badges of one
    expect(has("help-owner")).toBe(false);
    expect(has("help-type-badge")).toBe(false);
    expect(has("help-required-badge")).toBe(false);
  });

  it("shows the owner, the data type and whether it is required of an attribute", async () => {
    await mountDialog({ help: "types/Species/initialAmount" });
    expect(text("help-breadcrumb")).toContain("Species");
    expect(text("help-owner")).toContain("Species");
    expect(dialog().get("[data-testid=help-owner]").attributes("href")).toContain(
      "help=types/Species",
    );
    expect(text("help-title")).toContain("initialAmount");
    expect(text("help-type-badge")).toBe("double");
    expect(text("help-required-badge")).toBe("optional");
    const technical = text("help-technical");
    expect(technical).toContain("double");
    expect(technical).toContain(
      "the quantity is unknown or set by an initial assignment or a rule",
    );
    expect(technical).toContain("core 4.6.4");
    // the row is headed "required", so it answers that question instead of repeating the badge:
    // "required: optional" reads as a contradiction
    const answers = dialog()
      .findAll("[data-testid=help-technical] dd")
      .map((value) => value.text());
    expect(answers).toContain("no");
    expect(technical).not.toContain("optional");
    // an attribute is no type: it lists no attributes of its own
    expect(has("help-attributes")).toBe(false);
  });

  it("renders no part the entry has nothing for", async () => {
    await mountDialog({ help: "links/compartment" });
    expect(text("help-summary")).toBe(ENTRIES["links/compartment"]!.summary);
    expect(has("help-overview")).toBe(true);
    expect(has("help-technical")).toBe(false);
    expect(has("help-rules")).toBe(false);
    expect(has("help-attributes")).toBe(false);
    expect(has("help-related")).toBe(false);
  });

  // the description of such a data type ends by announcing its values, so they belong to it and
  // not under a heading of their own further down
  it("lists the values of an enumeration at the end of the overview, not in the technical list", async () => {
    await mountDialog({ help: "datatypes/double" });
    expect(text("help-values")).toContain("1.0");
    expect(text("help-values")).toContain("2.0");
    expect(
      dialog().get("[data-testid=help-overview]").find("[data-testid=help-values]").exists(),
    ).toBe(true);
    // the values were the whole technical list of this entry, and it is no part of it any more
    expect(has("help-technical")).toBe(false);
  });

  it("opens the attribute of a row of the attributes table", async () => {
    await mountDialog({ help: "types/Species" });
    const row = dialog().get("[data-testid=help-attribute-row]");
    expect(row.text()).toContain("initialAmount");
    expect(row.text()).toContain("double");
    expect(row.text()).toContain("optional");
    expect(row.text()).toContain(ENTRIES["types/Species/initialAmount"]!.summary);
    await click("[data-testid=help-attribute-row] a");
    expect(router.currentRoute.value.query.help).toBe("types/Species/initialAmount");
  });

  it("ends the attributes of a type with the common attributes, named by their own entry", async () => {
    await mountDialog({ help: "types/Species" });
    const rows = dialog().findAll("[data-testid=help-attribute-row]");
    const last = rows[rows.length - 1]!;
    expect(last.text()).toContain("SBase");
    expect(last.text()).toContain(ENTRIES["types/SBase"]!.summary);
    await click("[data-testid=help-attribute-row]:last-child a");
    expect(router.currentRoute.value.query.help).toBe("types/SBase");
  });

  it("shows no attributes at all for a type which lists none", async () => {
    await mountDialog({ help: "types/Compartment" });
    expect(has("help-attributes")).toBe(false);
    expect(has("help-attribute-row")).toBe(false);
  });

  // the attributes are a table on the reference page and are one here, so that a screen reader
  // names the column of every cell instead of reading a row as a run of loose words
  it("names the columns of the attributes table for a screen reader", async () => {
    await mountDialog({ help: "types/Species" });
    const headers = dialog()
      .findAll("[data-testid=help-attributes] th")
      .map((header) => header.text());
    expect(headers).toEqual(["attribute", "type", "required", "meaning"]);
    expect(dialog().get("[data-testid=help-attributes] thead").classes()).toContain("sr-only");
    expect(dialog().get("[data-testid=help-attribute-row]").element.tagName).toBe("TR");
  });

  it("shows no row of common attributes on the entry of SBase itself", async () => {
    await mountDialog({ help: "types/SBase" });
    const rows = dialog().findAll("[data-testid=help-attribute-row]");
    expect(rows).toHaveLength(1);
    expect(rows[0]!.text()).toContain("id");
  });

  it("shows the number, the severity and the message of a rule, its angle brackets as text", async () => {
    await mountDialog({ help: "types/Species" });
    const rule = dialog().get("[data-testid=help-rule]");
    expect(rule.text()).toContain("20623");
    expect(rule.text()).toContain("A <species> object must have the required attributes");
    expect(rule.html()).toContain("&lt;species&gt;");
    expect(rule.html()).not.toContain("<species>");
    expect(rule.find("[aria-label=error]").exists()).toBe(true);
    const warning = dialog().findAll("[data-testid=help-rule]")[1]!;
    expect(warning.find("[aria-label=warning]").exists()).toBe(true);
  });

  it.each(["types/Nope", "foo/bar", "types/../Secret", "constructor", "types/Species/"])(
    "closes the key %s, which is no entry, without leaving a history entry behind",
    async (key) => {
      await mountDialog();
      const replace = vi.spyOn(router, "replace");
      await open(key);
      await flushPromises();
      expect(replace).toHaveBeenCalledTimes(1);
      expect(router.currentRoute.value.query.help).toBeUndefined();
      expect(has("help-title")).toBe(false);
    },
  );

  it("shows a skeleton and what the eager glossary knows while the details load", async () => {
    load.mockReset().mockReturnValue(new Promise(() => undefined));
    await mountDialog({ help: "types/Species" });
    expect(has("help-skeleton")).toBe(true);
    expect(text("help-title")).toContain("Species");
    expect(text("help-summary")).toContain("chemical entity");
    expect(has("help-overview")).toBe(false);
  });

  it("falls back to the summary and the documentation link when the details fail, and loads again on the next open", async () => {
    load.mockReset().mockRejectedValue(new Error("offline"));
    await mountDialog({ help: "types/Species" });
    expect(has("help-fallback")).toBe(true);
    expect(has("help-skeleton")).toBe(false);
    expect(text("help-summary")).toContain("chemical entity");
    expect(dialog().get("[data-testid=help-docs-link]").attributes("href")).toContain(
      "matthiaskoenig.github.io",
    );
    expect(load).toHaveBeenCalledTimes(1);

    await router.push({ path: "/report", query: {} });
    await flushPromises();
    load.mockReset().mockResolvedValue(DETAILS);
    await open("types/Species");
    expect(load).toHaveBeenCalledTimes(1);
    expect(has("help-fallback")).toBe(false);
    expect(has("help-overview")).toBe(true);
  });

  it("stays open when another entry is opened in it, scrolled to the top and focused on its title", async () => {
    await mountDialog({ help: "types/Species" });
    const body = dialog().get("[data-testid=help-body]").element;
    body.scrollTop = 120;
    await open("types/Species/initialAmount");
    expect(showModal).toHaveBeenCalledTimes(1);
    expect(close).not.toHaveBeenCalled();
    expect(body.scrollTop).toBe(0);
    expect(document.activeElement).toBe(dialog().get("[data-testid=help-title]").element);
    expect(text("help-title")).toContain("initialAmount");
  });

  it("opens the entry a link of the description names", async () => {
    await mountDialog({ help: "types/Species" });
    await click("[data-testid=help-markdown] a[data-help-key]");
    expect(router.currentRoute.value.query.help).toBe("types/Compartment");
  });

  it("opens the entry of a related chip, which is a real link", async () => {
    await mountDialog({ help: "types/Species" });
    const chip = dialog().get("[data-testid=help-related] a");
    expect(chip.attributes("href")).toContain("help=types/Compartment");
    await click("[data-testid=help-related] a");
    expect(router.currentRoute.value.query.help).toBe("types/Compartment");
  });

  it("keeps the rest of the route when it opens another entry", async () => {
    await mountDialog({ help: "types/Species", pk: "m/Species:S1", q: "laci" });
    await click("[data-testid=help-related] a");
    expect(router.currentRoute.value.query.pk).toBe("m/Species:S1");
    expect(router.currentRoute.value.query.q).toBe("laci");
  });

  it("leaves a click with a modifier key to the browser, so it opens a new tab", async () => {
    await mountDialog({ help: "types/Species" });
    await click("[data-testid=help-related] a", { button: 0, ctrlKey: true });
    expect(router.currentRoute.value.query.help).toBe("types/Species");
  });

  it("closes on a click on the backdrop, which is the dialog element itself", async () => {
    await mountDialog({ help: "types/Species" });
    const backdrop = dialog().get("[data-testid=help-dialog]");
    await backdrop.trigger("mousedown");
    await backdrop.trigger("click");
    await settle();
    expect(router.currentRoute.value.query.help).toBeUndefined();
  });

  // a selection of the text of the dialog which ends outside of it is delivered as a click on
  // their common ancestor, the dialog element, and must not be taken for a click on the backdrop
  it("stays open when a press inside it comes up on the backdrop", async () => {
    await mountDialog({ help: "types/Species" });
    await dialog().get("[data-testid=help-summary]").trigger("mousedown");
    await dialog().get("[data-testid=help-dialog]").trigger("click");
    await settle();
    expect(router.currentRoute.value.query.help).toBe("types/Species");
  });

  it("keeps the dialog open on a click inside it", async () => {
    await mountDialog({ help: "types/Species" });
    await dialog().get("[data-testid=help-body]").trigger("click");
    await settle();
    expect(router.currentRoute.value.query.help).toBe("types/Species");
  });

  it("closes on the close event of the dialog, which Escape fires", async () => {
    await mountDialog({ help: "types/Species" });
    (dialog().get("[data-testid=help-dialog]").element as HTMLDialogElement).close();
    await settle();
    expect(router.currentRoute.value.query.help).toBeUndefined();
  });

  it("closes on the close button", async () => {
    await mountDialog({ help: "types/Species" });
    await dialog().get("[data-testid=help-close]").trigger("click");
    await settle();
    expect(router.currentRoute.value.query.help).toBeUndefined();
  });
});
