import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
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
  it("renders booleans as marks", () => {
    expect(
      mount(BooleanMark, { props: { value: true } })
        .find(".pi-check")
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
