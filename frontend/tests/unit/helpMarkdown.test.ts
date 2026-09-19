import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import HelpMarkdown from "@/components/help/HelpMarkdown.vue";
import type { GlossaryDetails } from "@/report/glossaryDetails";
import { renderHelpMarkdown } from "@/report/helpMarkdown";
import { router } from "@/router";

const hrefOf = (key: string): string => `/report?help=${key}`;

describe("renderHelpMarkdown", () => {
  it("turns a glossary link into an in-app anchor with the key and the href the caller gives", () => {
    const html = renderHelpMarkdown(
      "see the [compartment](glossary:types/Compartment) of it",
      hrefOf,
    );
    expect(html).toContain('href="/report?help=types/Compartment"');
    expect(html).toContain('data-help-key="types/Compartment"');
    expect(html).toContain('class="help-link"');
    expect(html).not.toContain("glossary:");
  });

  it("opens an external link in a new tab without leaking a referrer through target alone", () => {
    const html = renderHelpMarkdown(
      "see the [specification](https://example.invalid/spec)",
      hrefOf,
    );
    expect(html).toContain('href="https://example.invalid/spec"');
    expect(html).toContain('target="_blank"');
    expect(html).toContain('rel="noopener"');
  });

  it("never lets raw html of a description reach the rendered page as an element", () => {
    const html = renderHelpMarkdown("x <script>alert(1)</script> y", hrefOf);
    expect(html).not.toContain("<script");
    // the tag is escaped to text, so the script never runs, but its text is still shown
    expect(html).toContain("&lt;script&gt;");
  });

  it("never lets an image with an event handler of a description reach the rendered page", () => {
    const html = renderHelpMarkdown('x <img src="x" onerror="alert(1)"> y', hrefOf);
    expect(html).not.toContain("<img");
    // the tag is escaped to text, so no attribute of it is ever parsed as html
    expect(html).toContain("&lt;img");
  });

  it("renders inline code", () => {
    const html = renderHelpMarkdown("the `metaId` attribute", hrefOf);
    expect(html).toContain("<code>metaId</code>");
  });

  it("renders a list", () => {
    const html = renderHelpMarkdown("- a\n- b\n", hrefOf);
    expect(html).toContain("<ul>");
    expect(html).toContain("<li>a</li>");
    expect(html).toContain("<li>b</li>");
  });

  it("drops a link whose scheme is neither glossary, https, http nor mailto, keeping its text", () => {
    const html = renderHelpMarkdown("a [bad](javascript:alert(1)) link", hrefOf);
    expect(html).not.toContain("<a");
    expect(html).not.toContain('href="javascript:');
    expect(html).toContain("bad");
  });

  it("renders a glossary link with an empty key as plain text", () => {
    const html = renderHelpMarkdown("an [empty](glossary:) link", hrefOf);
    expect(html).not.toContain("<a");
    expect(html).not.toContain("data-help-key");
    expect(html).toContain("empty");
  });
});

// read with readFileSync, not through `loadGlossaryDetails`: the loader's dynamic `import()` is
// the only reference to the json the production bundle may carry, and a static import here, for
// a file this size, would pull the details back into the same chunk as everything else, exactly
// what `tests/unit/glossaryDetails.test.ts` avoids for the same reason.
const DETAILS_PATH = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "src",
  "data",
  "glossary-details.json",
);
const details = JSON.parse(readFileSync(DETAILS_PATH, "utf8")) as GlossaryDetails;
const keys = new Set(Object.keys(details.entries));

describe("renderHelpMarkdown of the real glossary", () => {
  it("renders every description with no surviving glossary href, script tag or unrendered link syntax", () => {
    for (const [key, entry] of Object.entries(details.entries)) {
      const html = renderHelpMarkdown(entry.description, hrefOf);
      expect(html, `${key}: a glossary: href survived`).not.toMatch(/href="glossary:/);
      expect(html, `${key}: a raw <script survived`).not.toContain("<script");
      expect(html, `${key}: unrendered markdown link syntax survived`).not.toContain("](");
      for (const match of html.matchAll(/data-help-key="([^"]+)"/g)) {
        expect(keys.has(match[1]!), `${key}: data-help-key ${match[1]} is not an entry`).toBe(true);
      }
    }
  });
});

async function mountMarkdown(markdown: string) {
  await router.push({ path: "/report", query: { pk: "kept" } });
  await router.isReady();
  return mount(HelpMarkdown, { props: { markdown }, global: { plugins: [router] } });
}

/** Dispatches a click with `cancelable: true` directly, so its `defaultPrevented` is readable
 * after the dispatch: `VueWrapper.trigger` resolves once Vue's reactivity settles, not to the
 * event itself. `keepDefault: false` (the default) adds a second listener which prevents the
 * default besides the component's own handler, so a real anchor a test leaves unprevented never
 * reaches jsdom's actual navigation, which it does not implement and would otherwise log: it runs
 * alongside the component's handler and never changes whether the component itself called
 * `preventDefault` first, which the "prevents the default" test below reads before it runs. */
function click(
  link: { element: Element },
  init: MouseEventInit = {},
  { keepDefault = false }: { keepDefault?: boolean } = {},
): MouseEvent {
  const event = new MouseEvent("click", { bubbles: true, cancelable: true, ...init });
  if (!keepDefault) link.element.addEventListener("click", (e) => e.preventDefault());
  link.element.dispatchEvent(event);
  return event;
}

describe("HelpMarkdown", () => {
  it("renders the markdown as sanitised html, with data-testid on its root", async () => {
    const wrapper = await mountMarkdown("a [compartment](glossary:types/Compartment) link");
    const root = wrapper.get("[data-testid=help-markdown]");
    expect(root.html()).toContain('data-help-key="types/Compartment"');
  });

  it("resolves a glossary link to an href of the current route with help set, other state kept", async () => {
    const wrapper = await mountMarkdown("a [compartment](glossary:types/Compartment) link");
    const link = wrapper.get("a[data-help-key]");
    const href = link.attributes("href")!;
    expect(href).toContain("help=types/Compartment");
    expect(href).toContain("pk=kept");
  });

  it("emits navigate and prevents the default on a plain left click of a glossary link", async () => {
    const wrapper = await mountMarkdown("a [compartment](glossary:types/Compartment) link");
    const link = wrapper.get("a[data-help-key]");
    const event = click(link, { button: 0 }, { keepDefault: true });
    expect(wrapper.emitted("navigate")).toEqual([["types/Compartment"]]);
    expect(event.defaultPrevented).toBe(true);
  });

  it("does not emit navigate on a ctrl-click, leaving the browser free to open a new tab", async () => {
    const wrapper = await mountMarkdown("a [compartment](glossary:types/Compartment) link");
    const link = wrapper.get("a[data-help-key]");
    click(link, { button: 0, ctrlKey: true });
    expect(wrapper.emitted("navigate")).toBeUndefined();
  });

  it("does not emit navigate on a click of an external link, which opens in a new tab", async () => {
    const wrapper = await mountMarkdown("see the [specification](https://example.invalid/spec)");
    const link = wrapper.get("a");
    expect(link.attributes("data-help-key")).toBeUndefined();
    expect(link.attributes("target")).toBe("_blank");
    click(link, { button: 0 });
    expect(wrapper.emitted("navigate")).toBeUndefined();
  });
});
