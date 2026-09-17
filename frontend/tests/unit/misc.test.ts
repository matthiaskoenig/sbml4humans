import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { vTooltip } from "@/directives/tooltip";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { MAX_LATEX_LENGTH } from "@/report/latex";
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

  it("renders booleans as marks", () => {
    expect(
      mount(BooleanMark, { props: { value: true } })
        .find("svg")
        .exists(),
    ).toBe(true);
    expect(mount(BooleanMark, { props: { value: false } }).text()).toBe("-");
    expect(mount(BooleanMark, { props: { value: null } }).text()).toBe("-");
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
    expect(text.text()).toBe(`${formula.slice(0, 120)}…`);
    await text.trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(`${formula} (click to copy)`);
    await text.trigger("mouseleave");

    const button = wrapper.get("[data-testid=math-render]");
    await button.trigger("click");
    expect(wrapper.find("[data-testid=math-text]").exists()).toBe(false);
    expect(wrapper.find(".katex").exists()).toBe(true);
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
});
