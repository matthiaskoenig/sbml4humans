import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import QualSignMark from "@/components/misc/QualSignMark.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { vTooltip } from "@/directives/tooltip";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { MAX_LATEX_LENGTH } from "@/report/latex";
import { pkKey } from "@/report/pk";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const tooltip = { mounted() {} };

function mountWithIndex(component: unknown, props: Record<string, unknown>) {
  return mount(
    component as never,
    {
      props,
      global: {
        plugins: [router],
        provide: { [ReportIndexKey as symbol]: ref(index) },
        directives: { tooltip },
      },
    } as never,
  );
}

describe("misc components", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the three states of a boolean as three marks", () => {
    // true, false and an attribute the file does not set are three different statements, and
    // `false` is a value: it reads as a cross and not as the dash of an unset attribute
    const mark = (value: boolean | null | undefined) => mount(BooleanMark, { props: { value } });
    expect(mark(true).get("svg").attributes("aria-label")).toBe("true");
    expect(mark(false).get("svg").attributes("aria-label")).toBe("false");
    expect(mark(false).text()).not.toBe("-");
    expect(mark(true).get("svg").html()).not.toBe(mark(false).get("svg").html());
    expect(mark(null).find("svg").exists()).toBe(false);
    expect(mark(null).text()).toBe("-");
    expect(mark(undefined).text()).toBe("-");
  });

  it("renders the sign of an input as the glyph of an influence graph", () => {
    const sign = (value: string | null) =>
      mount(QualSignMark, { props: { sign: value }, global: { directives: { tooltip } } }).text();
    expect(sign("positive")).toBe("+");
    expect(sign("negative")).toBe("\u2212");
    expect(sign("dual")).toBe("\u00b1");
    expect(sign("unknown")).toBe("?");
    expect(sign(null)).toBe("-");
  });

  it("renders missing values as a dash and rounds numbers", () => {
    expect(
      mount(ValueText, { props: { value: null }, global: { directives: { tooltip } } }).text(),
    ).toBe("-");
    expect(
      mount(ValueText, {
        props: { value: 0.123456789 },
        global: { directives: { tooltip } },
      }).text(),
    ).toBe("0.123457");
    expect(
      mount(ValueText, { props: { value: "abc" }, global: { directives: { tooltip } } }).text(),
    ).toBe("abc");
  });

  it("renders an infinite value as the sign of infinity and a NaN as NaN", () => {
    // JSON has no literal for them, so the report sends the three constants as strings; the
    // report used to show `null` for all of them, which reads as an unset attribute
    const render = (value: string | number) =>
      mount(ValueText, {
        props: { value, double: true },
        global: { directives: { tooltip } },
      }).text();
    expect(render("Infinity")).toBe("\u221e");
    expect(render("-Infinity")).toBe("-\u221e");
    expect(render("NaN")).toBe("NaN");
    expect(render(Infinity)).toBe("\u221e");
    expect(render(-Infinity)).toBe("-\u221e");
    expect(render(NaN)).toBe("NaN");
  });

  it("renders the word Infinity of a text as the word it is", () => {
    // only a double of the report arrives as one of the three strings; a name, a meta id or the
    // value of a key value pair which reads "Infinity" is text
    const render = (value: string) =>
      mount(ValueText, { props: { value }, global: { directives: { tooltip } } }).text();
    expect(render("Infinity")).toBe("Infinity");
    expect(render("-Infinity")).toBe("-Infinity");
    expect(render("NaN")).toBe("NaN");
  });

  it("renders the latex of a math with KaTeX", () => {
    const wrapper = mount(MathView, {
      props: { math: { latex: "\\frac{a}{b}", formula: "a / b" } },
      global: { directives: { tooltip } },
    });
    expect(wrapper.find(".katex").exists()).toBe(true);
    expect(
      mount(MathView, { props: { math: null }, global: { directives: { tooltip } } }).text(),
    ).toBe("-");
  });

  it("shows a formula longer than MAX_LATEX_LENGTH as truncated text and renders it on demand", async () => {
    const terms = Array.from({ length: 3000 }, (_, i) => i);
    const formula = terms.map((i) => `x${i}`).join(" + ");
    const latex = terms.map((i) => `x_{${i}}`).join(" + ");
    expect(latex.length).toBeGreaterThan(MAX_LATEX_LENGTH);
    const wrapper = mount(MathView, {
      props: { math: { latex, formula }, display: true },
      global: { directives: { tooltip: vTooltip } },
    });
    const text = wrapper.get("[data-testid=math-text]");
    // the 120th character of this formula is the space before the next term, so the truncation
    // must trim it before appending the ellipsis, or the ellipsis wraps onto its own line
    expect(formula[119]).toBe(" ");
    expect(text.text()).toBe(`${formula.slice(0, 120).trimEnd()}…`);
    await text.trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(`${formula} (click to copy)`);
    await text.trigger("mouseleave");

    const button = wrapper.get("[data-testid=math-render]");
    await button.trigger("click");
    expect(wrapper.find("[data-testid=math-text]").exists()).toBe(false);
    expect(wrapper.find(".katex").exists()).toBe(true);
  });

  it("resets the render-on-demand state when the math prop changes", async () => {
    const terms = Array.from({ length: 3000 }, (_, i) => i);
    const first = {
      latex: terms.map((i) => `x_{${i}}`).join(" + "),
      formula: terms.map((i) => `x${i}`).join(" + "),
    };
    const second = {
      latex: terms.map((i) => `y_{${i}}`).join(" + "),
      formula: terms.map((i) => `y${i}`).join(" + "),
    };
    const wrapper = mount(MathView, {
      props: { math: first, display: true },
      global: { directives: { tooltip: vTooltip } },
    });
    await wrapper.get("[data-testid=math-render]").trigger("click");
    expect(wrapper.find(".katex").exists()).toBe(true);

    await wrapper.setProps({ math: second });
    expect(wrapper.find("[data-testid=math-text]").exists()).toBe(true);
    expect(wrapper.find(".katex").exists()).toBe(false);
  });

  it("copies the formula with every run of whitespace collapsed to a single space", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    const wrapper = mount(MathView, {
      props: { math: { latex: "\\frac{a}{b}", formula: "a  /\n b" } },
      global: { directives: { tooltip: vTooltip } },
    });
    await wrapper.get("[data-testid=math]").trigger("click");
    expect(writeText).toHaveBeenCalledWith("a / b");
  });

  it("shows the unit id text when the latex is longer than MAX_LATEX_LENGTH", () => {
    const latex = "mole^{2}".repeat(MAX_LATEX_LENGTH);
    const wrapper = mount(UnitsView, {
      props: { latex, units: "mole^2" },
      global: { directives: { tooltip } },
    });
    expect(wrapper.find("[data-testid=units]").exists()).toBe(false);
    expect(wrapper.text()).toBe("mole^2");
  });

  it("renders a dash latex as the placeholder, not a KaTeX minus", () => {
    expect(
      mount(UnitsView, { props: { latex: "mole" }, global: { directives: { tooltip } } })
        .find("[data-testid=units]")
        .exists(),
    ).toBe(true);
    const placeholder = mount(UnitsView, {
      props: { latex: "-" },
      global: { directives: { tooltip } },
    });
    expect(placeholder.find("[data-testid=units]").exists()).toBe(false);
    expect(placeholder.text()).toBe("-");
    expect(
      mount(UnitsView, {
        props: { latex: "-", units: "mole" },
        global: { directives: { tooltip } },
      }).text(),
    ).toBe("mole");
    expect(
      mount(UnitsView, { props: { latex: null }, global: { directives: { tooltip } } }).text(),
    ).toBe("-");
  });

  it("links a pk the index knows and shows text otherwise", async () => {
    await router.push("/examples/BIOMD0000000012?q=x");
    const species = index.mainModel!.listOfSpecies![0]!;
    const link = mountWithIndex(ElementLink, { pk: species.pk });
    const anchor = link.get("[data-testid=element-link]");
    expect(anchor.text()).toBe(species.id);
    // vue-router's default query encoding (encodeURI-based) leaves "/" and ":" unescaped,
    // so the pk (format "<model>/<type>:<id>") appears literally, not percent-encoded.
    expect(anchor.attributes("href")).toContain(`pk=${species.pk}`);
    expect(anchor.attributes("href")).toContain("q=x");
    const text = mountWithIndex(ElementLink, { pk: null, label: "litre" });
    expect(text.find("[data-testid=element-link]").exists()).toBe(false);
    expect(text.text()).toBe("litre");
  });

  it("lets a link without a mark flow with the text around it", () => {
    // a link which is an inline flex box is a box of its own, and a line broke between the
    // opening parenthesis of a gene association and the gene behind it
    const species = index.mainModel!.listOfSpecies![0]!;
    const plain = mountWithIndex(ElementLink, { pk: species.pk }).get("[data-testid=element-link]");
    expect(plain.classes()).not.toContain("inline-flex");
    const marked = mountWithIndex(ElementLink, { pk: species.pk, mark: true }).get(
      "[data-testid=element-link]",
    );
    expect(marked.classes()).toContain("inline-flex");
  });

  it("names an element without an id by the key of its primary key", () => {
    // the rules of a Level 2 model carry no id, their key is the variable they set
    const rule = index.mainModel!.listOfRules![0]!;
    expect(rule.id).toBeNull();
    const link = mountWithIndex(ElementLink, { pk: rule.pk });
    expect(link.get("[data-testid=element-link]").text()).toBe(pkKey(rule.pk));
    expect(link.text()).not.toContain("/");
    // the name the report gives is set apart from an id the file writes
    expect(link.get("[data-testid=report-name]").classes()).toContain("italic");
    const species = index.mainModel!.listOfSpecies![0]!;
    expect(
      mountWithIndex(ElementLink, { pk: species.pk }).find("[data-testid=report-name]").exists(),
    ).toBe(false);
    // a label the caller passes is what the file writes, for example the variable of a rule
    expect(
      mountWithIndex(ElementLink, { pk: rule.pk, label: "t_ave" })
        .find("[data-testid=report-name]")
        .exists(),
    ).toBe(false);
  });

  it("names the trigger and the delay of an event by their event", () => {
    // the trigger and the delay of this model are keyed by their meta id, which says nothing
    // about the event they belong to
    const cellCycle = new ReportIndex(loadReport("cell_cycle"));
    const event = cellCycle.mainModel!.listOfEvents!.find((e) => e.delay)!;
    expect(event.trigger!.id).toBeNull();
    const link = mount(ElementLink, {
      props: { pk: event.trigger!.pk },
      global: {
        plugins: [router],
        provide: { [ReportIndexKey as symbol]: ref(cellCycle) },
        directives: { tooltip },
      },
    });
    expect(link.get("[data-testid=element-link]").text()).toBe(`${event.id}.trigger`);
  });

  it("names a species reference by its reaction and its species", () => {
    // the species references of this model are keyed by their meta id, which says nothing about
    // the participation; the inspector of a species lists them, so they name their reaction
    const reaction = index.mainModel!.listOfReactions!.find((r) => r.listOfReactants!.length > 0)!;
    const reactant = reaction.listOfReactants![0]!;
    expect(reactant.id).toBeNull();
    const link = mountWithIndex(ElementLink, { pk: reactant.pk });
    expect(link.get("[data-testid=element-link]").text()).toBe(
      `${reaction.id}.${reactant.species}`,
    );
  });
});
