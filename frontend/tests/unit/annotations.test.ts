import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import {
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

  it("requests a rejected resource exactly once even after the component re-renders", async () => {
    vi.mocked(client.getAnnotationResource).mockRejectedValue(new client.ApiError("boom"));
    const wrapper = mount(CvTermList, {
      props: { cvterms: [{ qualifier: "BQB_IS", resources: ["urn:miriam:x"] }] },
    });
    await flushPromises();
    await wrapper.setProps({
      cvterms: [{ qualifier: "BQB_IS", resources: ["urn:miriam:x"] }],
    });
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
