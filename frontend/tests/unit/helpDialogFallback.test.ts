import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import HelpDialog from "@/components/help/HelpDialog.vue";
import { vTooltip } from "@/directives/tooltip";
import { loadGlossaryDetails } from "@/report/glossaryDetails";
import { router } from "@/router";

import { DETAILS, ENTRIES, stubDialogElement } from "./help";

vi.mock("@/report/glossaryDetails", () => ({ loadGlossaryDetails: vi.fn() }));

/** The chunk of the renderer of the descriptions cannot be loaded, a page of a deployment which
 * no longer has that file or a reader who lost the network. Vue keeps an async component which
 * failed to load failed for as long as the module which defines it lives, and the dialog defines
 * one, so this is a file of its own: vitest gives every file its own modules, and the dialogs of
 * `helpDialog.test.ts` render their markdown whatever the order of the two files. */
vi.mock("@/components/help/HelpMarkdown.vue", () => {
  throw new Error("the chunk of the renderer is gone");
});

const load = vi.mocked(loadGlossaryDetails);

let wrapper: VueWrapper | null = null;

async function mountDialog(query: Record<string, string>): Promise<VueWrapper> {
  await router.push({ path: "/report", query });
  await router.isReady();
  wrapper = mount(HelpDialog, {
    attachTo: document.body,
    global: { plugins: [router], directives: { tooltip: vTooltip } },
  });
  await flushPromises();
  await flushPromises();
  return wrapper;
}

describe("HelpDialog without the renderer of the descriptions", () => {
  beforeEach(() => {
    stubDialogElement();
    load.mockReset().mockResolvedValue(DETAILS);
  });

  afterEach(() => {
    wrapper?.unmount();
    wrapper = null;
    vi.restoreAllMocks();
  });

  it("shows the description as its text, with everything else of the entry", async () => {
    const dialog = await mountDialog({ help: "types/Species" });
    const text = (testid: string): string => dialog.get(`[data-testid=${testid}]`).text();

    expect(dialog.find("[data-testid=help-markdown]").exists()).toBe(false);
    expect(text("help-description-text")).toContain(ENTRIES["types/Species"]!.description);
    // the rest of the dialog is what it is with the renderer
    expect(text("help-summary")).toBe(ENTRIES["types/Species"]!.summary);
    expect(dialog.findAll("[data-testid=help-rule]")).toHaveLength(2);
    expect(dialog.find("[data-testid=help-fallback]").exists()).toBe(false);
  });
});
