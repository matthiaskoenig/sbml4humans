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
import NotesView from "@/components/misc/NotesView.vue";

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

describe("annotations", () => {
  afterEach(() => {
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

  it("lets a caller cancel a resolve that has not started yet, and requests it again later", async () => {
    // resources that keep every concurrent slot busy until settled by hand, so the resolve of
    // "urn:queued" below is guaranteed to sit in the queue, not started yet
    const busySettlers: (() => void)[] = [];
    vi.mocked(client.getAnnotationResource).mockImplementation(
      (resource: string) =>
        new Promise((resolve) => {
          busySettlers.push(() => resolve({ ...info, resource }));
        }),
    );
    const busy = Array.from({ length: MAX_CONCURRENT_RESOLVES }, (_, i) => `urn:busy:${i}`);
    for (const resource of busy) resolveAnnotation(resource);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_CONCURRENT_RESOLVES);

    const controller = new AbortController();
    resolveAnnotation("urn:queued", controller.signal);
    expect(client.getAnnotationResource).not.toHaveBeenCalledWith("urn:queued");
    controller.abort();

    // freeing a slot must not start the cancelled resolve
    busySettlers[0]!();
    await flushPromises();
    expect(client.getAnnotationResource).not.toHaveBeenCalledWith("urn:queued");

    // the resource is requestable again later, with a fresh request, not the cancelled one
    const queuedInfo = { ...info, resource: "urn:queued" };
    vi.mocked(client.getAnnotationResource).mockResolvedValueOnce(queuedInfo);
    await expect(resolveAnnotation("urn:queued")).resolves.toEqual(queuedInfo);
    expect(client.getAnnotationResource).toHaveBeenCalledWith("urn:queued");
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

  it("requests a rejected resource exactly once even after the component re-renders with the same list", async () => {
    vi.mocked(client.getAnnotationResource).mockRejectedValue(new client.ApiError("boom"));
    const cvterms = [{ qualifier: "BQB_IS", resources: ["urn:miriam:x"] }];
    const wrapper = mount(CvTermList, { props: { cvterms } });
    await flushPromises();
    // the same array reference, as an unrelated re-render of the inspector passes down again,
    // not a new element's cvterms: the resources list has not actually changed
    await wrapper.setProps({ cvterms });
    await flushPromises();
    expect(wrapper.get("[data-testid=cvterm-resource]").text()).toContain("urn:miriam:x");
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(1);
  });

  it("shows and resolves only the first 50 resources of a term and the rest after show all", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const resources = Array.from({ length: 120 }, (_, i) => `urn:test:${i}`);
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources }] },
    });
    await flushPromises();
    expect(wrapper.findAll("[data-testid=cvterm-resource]")).toHaveLength(50);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(50);

    await wrapper.get("[data-testid=show-all]").trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-testid=cvterm-resource]")).toHaveLength(120);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(120);
  });

  it("shows no show all button for a term of 50 or fewer resources", () => {
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
  });

  it("resolves what a term's own show all reveals, even for a term beyond the automatic budget", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    // two terms of 50 resources exhaust the MAX_AUTO_RESOLVES budget of 100, so a third term's
    // resources are shown without a label until its own show all is clicked
    const cvterms = Array.from({ length: 3 }, (_, i) => ({
      qualifier: "BQB_IS",
      resources: Array.from({ length: 50 }, (_, j) => `urn:term${i}:${j}`),
    }));
    const wrapper = mount(CvTermList, { props: { cvterms } });
    await flushPromises();
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(MAX_AUTO_RESOLVES);

    const thirdTerm = wrapper.findAll("[data-testid=cvterm]")[2]!;
    expect(thirdTerm.find("[data-testid=show-all]").exists()).toBe(false);
    for (const resource of cvterms[2]!.resources) {
      expect(client.getAnnotationResource).not.toHaveBeenCalledWith(resource);
    }
  });

  it("caps the terms shown and lets show all reveal the rest, resetting when the element changes", async () => {
    const cvterms = Array.from({ length: 60 }, (_, i) => ({
      qualifier: "BQB_IS",
      resources: [`urn:term${i}:0`],
    }));
    const wrapper = mount(CvTermList, { props: { cvterms } });
    expect(wrapper.findAll("[data-testid=cvterm]")).toHaveLength(50);
    await wrapper.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.findAll("[data-testid=cvterm]")).toHaveLength(60);

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

  it("sanitises the notes", () => {
    const wrapper = mount(NotesView, {
      props: {
        notes: "<p>Hello <b>world</b></p><script>alert(1)</script><img src=x onerror=alert(1)>",
      },
    });
    expect(wrapper.html()).toContain("<b>world</b>");
    expect(wrapper.html()).not.toContain("<script");
    expect(wrapper.html()).not.toContain("onerror");
  });
});
