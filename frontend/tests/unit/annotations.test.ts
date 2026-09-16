import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { resetAnnotationCache, resolveAnnotation } from "@/api/annotations";
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
