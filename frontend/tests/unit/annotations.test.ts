import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import {
  MAX_AUTO_RESOLVES,
  MAX_CONCURRENT_RESOLVES,
  resetAnnotationCache,
  resolveAnnotation,
} from "@/api/annotations";
import CvTermList from "@/components/misc/CvTermList.vue";
import XhtmlView from "@/components/misc/XhtmlView.vue";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return { ...original, getAnnotationResource: vi.fn() };
});

const info = {
  resource: "https://identifiers.org/chebi/CHEBI:15377",
  resource_normalized: null,
  collection: "chebi",
  term: "CHEBI:15377",
  label: "water",
  description: null,
  url: "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:15377",
  synonyms: [],
  xrefs: [],
  errors: [],
  warnings: [],
};

/** Resources whose requests keep every concurrent slot busy until they are settled. */
const BUSY = Array.from({ length: MAX_CONCURRENT_RESOLVES }, (_, i) => `urn:busy:${i}`);

/** Lets every annotation request wait until it is settled by hand; a settled request resolves
 * with a label built from its resource. */
function holdRequests(): Map<string, () => void> {
  const settlers = new Map<string, () => void>();
  vi.mocked(client.getAnnotationResource).mockImplementation(
    (resource: string) =>
      new Promise((resolve) => {
        settlers.set(resource, () => resolve({ ...info, resource, label: `label of ${resource}` }));
      }),
  );
  return settlers;
}

/** Settles every held request, including the requests that start once others settle. */
async function settleAll(settlers: Map<string, () => void>): Promise<void> {
  while (settlers.size > 0) {
    const settles = [...settlers.values()];
    settlers.clear();
    settles.forEach((settle) => settle());
    await flushPromises();
  }
}

function requestsOf(resource: string): number {
  return vi
    .mocked(client.getAnnotationResource)
    .mock.calls.filter(([requested]) => requested === resource).length;
}

describe("annotations", () => {
  afterEach(async () => {
    // the requests a test leaves settling finish first, so they cannot free a queue slot of the
    // next test
    await flushPromises();
    resetAnnotationCache();
    vi.mocked(client.getAnnotationResource).mockReset();
  });

  it("caches the resolution per resource", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const [a, b] = await Promise.all([
      resolveAnnotation(info.resource),
      resolveAnnotation(info.resource),
    ]);
    expect(a).toBe(b);
    await resolveAnnotation(info.resource);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(1);
  });

  it("resolves at most MAX_CONCURRENT_RESOLVES resources at the same time and resolves them all", async () => {
    const resources = Array.from({ length: 10 }, (_, i) => `urn:test:${i}`);
    const settlers: (() => void)[] = [];
    vi.mocked(client.getAnnotationResource).mockImplementation(
      (resource: string) =>
        new Promise((resolve) => {
          settlers.push(() => resolve({ ...info, resource }));
        }),
    );

    const pending = resources.map((resource) => resolveAnnotation(resource));
    // the requests start synchronously, so the count is already final without waiting a tick
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_CONCURRENT_RESOLVES);

    // settle the in-flight requests one at a time; the queue keeps exactly MAX_CONCURRENT_RESOLVES
    // requests in flight until the queue itself is empty
    for (let settled = 1; settled <= resources.length; settled += 1) {
      settlers[settled - 1]!();
      await flushPromises();
      expect(client.getAnnotationResource).toHaveBeenCalledTimes(
        Math.min(resources.length, settled + MAX_CONCURRENT_RESOLVES),
      );
    }

    await Promise.all(pending);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(resources.length);
  });

  it("frees a queue slot on a rejection too, so a 5th queued resolve starts", async () => {
    const resources = Array.from({ length: 5 }, (_, i) => `urn:reject:${i}`);
    const settlers: (() => void)[] = [];
    vi.mocked(client.getAnnotationResource).mockImplementation(
      (resource: string) =>
        new Promise((_resolve, reject) => {
          settlers.push(() => reject(new client.ApiError(`boom ${resource}`)));
        }),
    );

    resources.forEach((resource) => resolveAnnotation(resource).catch(() => null));
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_CONCURRENT_RESOLVES);

    settlers[0]!();
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(5);

    // settle the rest too, so nothing is left dangling for later tests
    settlers.forEach((settle) => settle());
  });

  it("keeps a queued resolve for a caller that still waits for it when another caller aborts", async () => {
    const settlers = holdRequests();
    BUSY.forEach((resource) => resolveAnnotation(resource));
    const aborting = new AbortController();
    const waiting = new AbortController();
    resolveAnnotation("urn:shared", aborting.signal);
    const shared = resolveAnnotation("urn:shared", waiting.signal);
    aborting.abort();

    await settleAll(settlers);
    expect(requestsOf("urn:shared")).toBe(1);
    await expect(shared).resolves.toMatchObject({ label: "label of urn:shared" });
  });

  it("rejects a queued resolve with an AbortError once all its callers abort, and requests it again later", async () => {
    const settlers = holdRequests();
    BUSY.forEach((resource) => resolveAnnotation(resource));
    const first = new AbortController();
    const second = new AbortController();
    const rejected = vi.fn();
    resolveAnnotation("urn:queued", first.signal).catch(rejected);
    resolveAnnotation("urn:queued", second.signal).catch(rejected);
    first.abort();
    await flushPromises();
    expect(rejected).not.toHaveBeenCalled();

    second.abort();
    await flushPromises();
    expect(rejected).toHaveBeenCalledTimes(2);
    for (const [error] of rejected.mock.calls) {
      expect(error).toBeInstanceOf(DOMException);
      expect((error as DOMException).name).toBe("AbortError");
    }

    // freeing the slots must not start the dropped resolve
    await settleAll(settlers);
    expect(requestsOf("urn:queued")).toBe(0);

    // the resource is requestable again, with a fresh request
    const again = resolveAnnotation("urn:queued");
    await settleAll(settlers);
    await expect(again).resolves.toMatchObject({ label: "label of urn:queued" });
    expect(requestsOf("urn:queued")).toBe(1);
  });

  it("drops a queued resolve at once for a caller whose signal has already aborted", async () => {
    const settlers = holdRequests();
    BUSY.forEach((resource) => resolveAnnotation(resource));
    const controller = new AbortController();
    controller.abort();
    const rejected = vi.fn();
    resolveAnnotation("urn:queued", controller.signal).catch(rejected);
    await flushPromises();
    expect((rejected.mock.calls[0]?.[0] as DOMException | undefined)?.name).toBe("AbortError");

    await settleAll(settlers);
    expect(requestsOf("urn:queued")).toBe(0);
  });

  it("requests a resource once when it is requested again right after its queued resolve was dropped", async () => {
    const settlers = holdRequests();
    BUSY.forEach((resource) => resolveAnnotation(resource));
    const controller = new AbortController();
    resolveAnnotation("urn:queued", controller.signal).catch(() => undefined);
    controller.abort();
    // requested again before the rejection of the dropped resolve has settled
    const again = resolveAnnotation("urn:queued");
    await flushPromises();
    const later = resolveAnnotation("urn:queued");

    await settleAll(settlers);
    expect(requestsOf("urn:queued")).toBe(1);
    await expect(again).resolves.toMatchObject({ label: "label of urn:queued" });
    await expect(later).resolves.toMatchObject({ label: "label of urn:queued" });
  });

  it("removes the abort listeners of every queued entry on reset, so an old signal cannot drop a later queued resolve of the same resource", async () => {
    holdRequests();
    BUSY.forEach((resource) => resolveAnnotation(resource));
    const controller = new AbortController();
    resolveAnnotation("urn:reset", controller.signal).catch(() => undefined);
    expect(requestsOf("urn:reset")).toBe(0);

    resetAnnotationCache();
    const settlers = holdRequests();
    // fill the concurrent slots again, so the resource requested next stays queued rather than
    // starting right away
    BUSY.forEach((resource) => resolveAnnotation(resource));
    const again = resolveAnnotation("urn:reset");
    expect(requestsOf("urn:reset")).toBe(0);

    // aborting the old, pre-reset signal must not touch the newly queued entry
    controller.abort();
    await flushPromises();

    await settleAll(settlers);
    expect(requestsOf("urn:reset")).toBe(1);
    await expect(again).resolves.toMatchObject({ label: "label of urn:reset" });
  });

  it("keeps a started resolve running and cached when its callers abort", async () => {
    const settlers = holdRequests();
    const controller = new AbortController();
    const started = resolveAnnotation("urn:started", controller.signal);
    expect(client.getAnnotationResource).toHaveBeenCalledWith("urn:started");
    controller.abort();

    await settleAll(settlers);
    await expect(started).resolves.toMatchObject({ label: "label of urn:started" });
    await resolveAnnotation("urn:started");
    expect(requestsOf("urn:started")).toBe(1);
  });

  it("renders qualifier, resource and the resolved label", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources: [info.resource] }] },
    });
    expect(wrapper.text()).toContain("BQB_IS");
    await flushPromises();
    const resource = wrapper.get("[data-testid=cvterm-resource]");
    expect(resource.text()).toContain("water");
    expect(resource.get("a").attributes("href")).toBe(info.resource);
  });

  it("keeps the resource text when the resolution fails", async () => {
    vi.mocked(client.getAnnotationResource).mockRejectedValue(new client.ApiError("boom"));
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources: ["urn:miriam:x"] }] },
    });
    await flushPromises();
    expect(wrapper.get("[data-testid=cvterm-resource]").text()).toContain("urn:miriam:x");
  });

  it("requests a rejected resource exactly once, also when show all resolves the rest of its term", async () => {
    vi.mocked(client.getAnnotationResource).mockImplementation((resource: string) =>
      resource === "urn:test:0"
        ? Promise.reject(new client.ApiError("boom"))
        : Promise.resolve({ ...info, resource }),
    );
    const resources = Array.from({ length: 60 }, (_, i) => `urn:test:${i}`);
    const wrapper = mount(CvTermList, { props: { cvterms: [{ qualifier: "BQB_IS", resources }] } });
    await flushPromises();
    expect(requestsOf("urn:test:0")).toBe(1);

    // show all runs the resolution of the term again for every resource it shows
    await wrapper.get("[data-testid=show-all]").trigger("click");
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(60);
    expect(requestsOf("urn:test:0")).toBe(1);
    expect(wrapper.findAll("[data-testid=cvterm-resource]")[0]!.text()).toContain("urn:test:0");
  });

  it("shows and resolves only the first 50 resources of a term and the rest after show all, which then disappears", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const resources = Array.from({ length: 120 }, (_, i) => `urn:test:${i}`);
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources }] },
    });
    await flushPromises();
    expect(wrapper.findAll("[data-testid=cvterm-resource]")).toHaveLength(50);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(50);
    expect(wrapper.find("[data-testid=resolve-all]").exists()).toBe(false);

    await wrapper.get("[data-testid=show-all]").trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-testid=cvterm-resource]")).toHaveLength(120);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(120);
    expect(wrapper.find("[data-testid=show-all]").exists()).toBe(false);
  });

  it("shows no show all button for a term of 50 or fewer resources", () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const resources = Array.from({ length: 50 }, (_, i) => `urn:test:${i}`);
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources }] },
    });
    expect(wrapper.find("[data-testid=show-all]").exists()).toBe(false);
  });

  it("resets show all and still requests the resources of a newly selected element", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const first = Array.from({ length: 60 }, (_, i) => `urn:first:${i}`);
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources: first }] },
    });
    await flushPromises();
    await wrapper.get("[data-testid=show-all]").trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-testid=cvterm-resource]")).toHaveLength(60);

    // another element is selected: the cvterms prop is replaced wholesale, the same component
    // instance is reused (same v-for index) with a different term
    const second = Array.from({ length: 60 }, (_, i) => `urn:second:${i}`);
    await wrapper.setProps({ cvterms: [{ qualifier: "BQB_IS", resources: second }] });
    await flushPromises();
    expect(wrapper.findAll("[data-testid=cvterm-resource]")).toHaveLength(50);
    expect(wrapper.get("[data-testid=show-all]").text()).toBe("show all (10)");
    // 60 requests for the fully expanded first term, plus the 50 shown of the second
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(60 + 50);
  });

  it("shows the first 50 terms of an element and requests at most MAX_AUTO_RESOLVES resources", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const cvterms = Array.from({ length: 200 }, (_, i) => ({
      qualifier: "BQB_IS",
      resources: Array.from({ length: 50 }, (_, j) => `urn:term${i}:${j}`),
    }));
    const wrapper = mount(CvTermList, { props: { cvterms } });
    await flushPromises();
    expect(wrapper.findAll("[data-testid=cvterm]")).toHaveLength(50);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_AUTO_RESOLVES);
    expect(wrapper.get("[data-testid=resolve-all]").text()).toBe(
      `resolve all (${50 * 50 - MAX_AUTO_RESOLVES})`,
    );
  });

  it("resolves what a term's own show all reveals, even for a term beyond the automatic budget", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    // two terms of 50 resources spend the MAX_AUTO_RESOLVES budget of 100, so the 60 resources of
    // the third term stay unresolved until its own show all is clicked
    const cvterms = [50, 50, 60].map((length, i) => ({
      qualifier: "BQB_IS",
      resources: Array.from({ length }, (_, j) => `urn:term${i}:${j}`),
    }));
    const wrapper = mount(CvTermList, { props: { cvterms } });
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_AUTO_RESOLVES);
    for (const resource of cvterms[2]!.resources) {
      expect(client.getAnnotationResource).not.toHaveBeenCalledWith(resource);
    }
    expect(wrapper.get("[data-testid=resolve-all]").text()).toBe("resolve all (50)");

    const thirdTerm = wrapper.findAll("[data-testid=cvterm]")[2]!;
    await thirdTerm.get("[data-testid=show-all]").trigger("click");
    await flushPromises();
    expect(thirdTerm.findAll("[data-testid=cvterm-resource]")).toHaveLength(60);
    for (const resource of cvterms[2]!.resources) {
      expect(client.getAnnotationResource).toHaveBeenCalledWith(resource);
    }
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_AUTO_RESOLVES + 60);
    expect(wrapper.find("[data-testid=resolve-all]").exists()).toBe(false);

    // the budget applies again to the term at the same position of another element
    const other = [50, 50, 60].map((length, i) => ({
      qualifier: "BQB_IS",
      resources: Array.from({ length }, (_, j) => `urn:other${i}:${j}`),
    }));
    await wrapper.setProps({ cvterms: other });
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(2 * MAX_AUTO_RESOLVES + 60);
    expect(wrapper.get("[data-testid=resolve-all]").text()).toBe("resolve all (50)");
  });

  it("resolves the shown resources the automatic budget leaves out with resolve all, until another element is selected", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const termsOf = (element: string) =>
      Array.from({ length: 3 }, (_, i) => ({
        qualifier: "BQB_IS",
        resources: Array.from({ length: 50 }, (_, j) => `urn:${element}:term${i}:${j}`),
      }));
    const wrapper = mount(CvTermList, { props: { cvterms: termsOf("first") } });
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_AUTO_RESOLVES);
    expect(wrapper.get("[data-testid=resolve-all]").text()).toBe("resolve all (50)");

    await wrapper.get("[data-testid=resolve-all]").trigger("click");
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(150);
    expect(wrapper.find("[data-testid=resolve-all]").exists()).toBe(false);

    await wrapper.setProps({ cvterms: termsOf("second") });
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(150 + MAX_AUTO_RESOLVES);
    expect(wrapper.get("[data-testid=resolve-all]").text()).toBe("resolve all (50)");
  });

  it("shows the terms which qualify a term under it and resolves them on a resolve all", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const cvterms = [
      {
        qualifier: "BQB_HAS_TAXON",
        resources: ["urn:taxon:9606"],
        nested: [
          {
            qualifier: "BQB_IS_DESCRIBED_BY",
            resources: ["urn:pubmed:1"],
            nested: [{ qualifier: "BQB_IS", resources: ["urn:eco:1"] }],
          },
        ],
      },
    ];
    const wrapper = mount(CvTermList, { props: { cvterms } });
    await flushPromises();
    // the nesting is rendered, however deep it goes
    expect(wrapper.findAll("[data-testid=cvterm-nested]")).toHaveLength(2);
    expect(wrapper.text()).toContain("BQB_IS_DESCRIBED_BY");
    // the automatic budget resolves the term of the element, the two below it wait for a click
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(1);
    expect(wrapper.get("[data-testid=resolve-all]").text()).toBe("resolve all (2)");

    await wrapper.get("[data-testid=resolve-all]").trigger("click");
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(3);
    expect(wrapper.find("[data-testid=resolve-all]").exists()).toBe(false);
  });

  it("caps the terms shown, reveals the rest with a show all that then disappears and resets when the element changes", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const cvterms = Array.from({ length: 60 }, (_, i) => ({
      qualifier: "BQB_IS",
      resources: [`urn:term${i}:0`],
    }));
    const wrapper = mount(CvTermList, { props: { cvterms } });
    expect(wrapper.findAll("[data-testid=cvterm]")).toHaveLength(50);
    await wrapper.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.findAll("[data-testid=cvterm]")).toHaveLength(60);
    expect(wrapper.find("[data-testid=show-all]").exists()).toBe(false);

    const other = Array.from({ length: 60 }, (_, i) => ({
      qualifier: "BQB_IS",
      resources: [`urn:other${i}:0`],
    }));
    await wrapper.setProps({ cvterms: other });
    expect(wrapper.findAll("[data-testid=cvterm]")).toHaveLength(50);
    expect(wrapper.get("[data-testid=show-all]").text()).toBe("show all (10)");
  });

  it("cancels the queued resolves of the previous element when another element is selected", async () => {
    const settlers = new Map<string, () => void>();
    vi.mocked(client.getAnnotationResource).mockImplementation(
      (resource: string) =>
        new Promise((resolve) => {
          settlers.set(resource, () => resolve({ ...info, resource }));
        }),
    );
    // one term of MAX_CONCURRENT_RESOLVES + 2 resources: the first MAX_CONCURRENT_RESOLVES start,
    // the remaining 2 sit in the queue, not started yet
    const firstResources = Array.from(
      { length: MAX_CONCURRENT_RESOLVES + 2 },
      (_, i) => `urn:first:${i}`,
    );
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources: firstResources }] },
    });
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_CONCURRENT_RESOLVES);

    // another element is selected before the queued resolves of the first one ever start
    const secondResources = ["urn:second:0", "urn:second:1"];
    await wrapper.setProps({
      cvterms: [{ qualifier: "BQB_IS", resources: secondResources }],
    });
    await flushPromises();

    // free up slots held by the first element's already started requests, so the second
    // element's resolves (still queued behind them) get their turn
    settlers.get("urn:first:0")!();
    settlers.get("urn:first:1")!();
    await flushPromises();

    for (const resource of firstResources.slice(MAX_CONCURRENT_RESOLVES)) {
      expect(client.getAnnotationResource).not.toHaveBeenCalledWith(resource);
    }
    for (const resource of secondResources) {
      expect(client.getAnnotationResource).toHaveBeenCalledWith(resource);
    }
  });

  it.each([
    [
      "in another term",
      [
        { qualifier: "BQB_IS", resources: ["urn:shared"] },
        { qualifier: "BQB_IS_VERSION_OF", resources: ["urn:other"] },
      ],
    ],
    ["in another term, with fewer terms", [{ qualifier: "BQB_IS", resources: ["urn:shared"] }]],
    [
      "in the same term",
      [
        { qualifier: "BQB_IS", resources: ["urn:other"] },
        { qualifier: "BQB_IS_VERSION_OF", resources: ["urn:shared"] },
      ],
    ],
  ])(
    "resolves a queued resource the next element shows %s with a single request",
    async (_, next) => {
      const settlers = holdRequests();
      // the resource of the second term waits in the queue behind the requests of the first term
      const wrapper = mount(CvTermList, {
        props: {
          cvterms: [
            { qualifier: "BQB_IS", resources: BUSY },
            { qualifier: "BQB_IS_VERSION_OF", resources: ["urn:shared"] },
          ],
        },
      });
      await flushPromises();
      expect(requestsOf("urn:shared")).toBe(0);

      await wrapper.setProps({ cvterms: next });
      await settleAll(settlers);
      expect(wrapper.text()).toContain("label of urn:shared");
      expect(requestsOf("urn:shared")).toBe(1);
    },
  );

  it("cancels the queued resolve a term requested again for the next element once that element is left too", async () => {
    const settlers = holdRequests();
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources: [...BUSY, "urn:again"] }] },
    });
    await flushPromises();
    // the next element shows the queued resource in the same term: the resolve of the previous
    // list is dropped and the resource is requested again for this one
    const next = ["urn:again", ...Array.from({ length: 60 }, (_, i) => `urn:next:${i}`)];
    await wrapper.setProps({ cvterms: [{ qualifier: "BQB_IS", resources: next }] });
    await flushPromises();
    // show all runs the resolution of the term again, after the dropped resolve has settled
    await wrapper.get("[data-testid=show-all]").trigger("click");
    await flushPromises();
    // the element after that does not show it: the new resolve, still queued, is dropped too
    await wrapper.setProps({ cvterms: [{ qualifier: "BQB_IS", resources: ["urn:last"] }] });
    await settleAll(settlers);
    expect(requestsOf("urn:again")).toBe(0);
    expect(wrapper.get("[data-testid=cvterm-resource]").text()).toContain("label of urn:last");
  });

  it("clears the resolved labels and the resolve all count of a term the automatic budget skipped once its element is revisited", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const termsOf = (element: string) =>
      Array.from({ length: 3 }, (_, i) => ({
        qualifier: "BQB_IS",
        resources: Array.from({ length: 50 }, (_, j) => `urn:${element}:term${i}:${j}`),
      }));
    const first = termsOf("first");
    const wrapper = mount(CvTermList, { props: { cvterms: first } });
    await flushPromises();
    await wrapper.get("[data-testid=resolve-all]").trigger("click");
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(150);

    // another element is selected, then the first one again: the budget applies again and the
    // third term's resources fall outside it, same as on the first visit
    await wrapper.setProps({ cvterms: termsOf("second") });
    await flushPromises();
    await wrapper.setProps({ cvterms: first });
    await flushPromises();
    expect(wrapper.get("[data-testid=resolve-all]").text()).toBe("resolve all (50)");

    const thirdTerm = wrapper.findAll("[data-testid=cvterm]")[2]!;
    const resources = thirdTerm.findAll("[data-testid=cvterm-resource]");
    expect(resources).toHaveLength(50);
    for (const [index, resource] of resources.entries()) {
      expect(resource.get("a").text()).toBe(first[2]!.resources[index]);
    }

    // resolve all requests nothing new: the resources of the third term are already cached from
    // the first visit, and clicking resolves them from that cache
    const requestsBefore = vi.mocked(client.getAnnotationResource).mock.calls.length;
    await wrapper.get("[data-testid=resolve-all]").trigger("click");
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(requestsBefore);
    for (const resource of thirdTerm.findAll("[data-testid=cvterm-resource]")) {
      expect(resource.get("a").text()).toBe("water");
    }
  });

  it("sanitises the notes", () => {
    const wrapper = mount(XhtmlView, {
      props: {
        xhtml: "<p>Hello <b>world</b></p><script>alert(1)</script><img src=x onerror=alert(1)>",
      },
    });
    expect(wrapper.html()).toContain("<b>world</b>");
    expect(wrapper.html()).not.toContain("<script");
    expect(wrapper.html()).not.toContain("onerror");
  });
});
