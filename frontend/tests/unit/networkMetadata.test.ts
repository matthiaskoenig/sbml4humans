import { mount, flushPromises } from "@vue/test-utils";
import { computed, defineComponent, shallowRef, ref } from "vue";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as client from "@/api/client";
import { resolveAnnotation, resetAnnotationCache } from "@/api/annotations";
import { ReportIndex } from "@/report/index";
import { buildNetwork } from "@/report/network";
import {
  useNetworkMetadata,
  identityResources,
  annotationLabel,
  networkLabels,
} from "@/report/network-metadata";
import type { AnnotationResource } from "@/types/annotation";
import { loadReport } from "./fixtures";

vi.mock("@/api/client", async (original) => ({
  ...(await original<typeof client>()),
  getAnnotationResource: vi.fn(),
}));
const wrappers: ReturnType<typeof mount>[] = [];
const info = (resource: string, label = "Resolved protein"): AnnotationResource => ({
  resource,
  collection: { prefix: "uniprot" },
  uniprot: { name: label },
  errors: [],
});
function setup(index = new ReportIndex(loadReport("repressilator"))) {
  const current = shallowRef(index),
    projection = computed(() =>
      buildNetwork(current.value, current.value.mainModel!, "base", "light"),
    );
  const node = projection.value.nodes.find((node) => node.element?.id === "PX")!;
  const targets = ref([node.id]);
  let result!: ReturnType<typeof useNetworkMetadata>;
  wrappers.push(
    mount(
      defineComponent({
        setup() {
          result = useNetworkMetadata(
            computed(() => projection.value.nodes),
            computed(() => targets.value),
          );
          return () => null;
        },
      }),
    ),
  );
  return { current, projection, node, targets, result };
}

afterEach(async () => {
  for (const wrapper of wrappers) wrapper.unmount();
  wrappers.length = 0;
  await flushPromises();
  resetAnnotationCache();
  vi.mocked(client.getAnnotationResource).mockReset();
});

describe("network metadata", () => {
  it("shares successful resource results with the report and ignores generic SBO labels", async () => {
    vi.mocked(client.getAnnotationResource).mockImplementation(async (resource) => info(resource));
    const index = new ReportIndex(loadReport("repressilator"));
    const node = buildNetwork(index, index.mainModel!, "base", "light").nodes.find(
      (n) => n.element?.id === "PX",
    )!;
    const resources = identityResources(node);
    expect(resources).toEqual(["http://identifiers.org/uniprot/P03023"]);
    await resolveAnnotation(resources[0]!);
    const { result } = setup(index);
    await flushPromises();
    expect(result.metadata.value.get(node.id)?.label).toBe("Resolved protein");
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(1);
    expect(
      annotationLabel({
        resource: "x",
        collection: { prefix: "sbo" },
        ontology: { label: "protein" },
      }),
    ).toBeUndefined();
  });

  it("does not leak resolved names across report indexes with identical primary keys", async () => {
    vi.mocked(client.getAnnotationResource).mockImplementation(async (resource) =>
      info(resource, "Original protein"),
    );
    const state = setup();
    await flushPromises();
    const old = state.result.metadata.value;
    const replacement = new ReportIndex(structuredClone(state.current.value.report));
    const next = buildNetwork(replacement, replacement.mainModel!, "base", "light");
    const i = next.nodes.findIndex((n) => n.id === state.node.id);
    expect(networkLabels(next, "annotation", old)[i]).not.toBe("Original protein");
    state.targets.value = [];
    state.current.value = replacement;
    await flushPromises();
    expect(state.result.metadata.value.has(state.node.id)).toBe(false);
  });

  it("retries a failed lookup on a later target activation", async () => {
    vi.mocked(client.getAnnotationResource)
      .mockRejectedValueOnce(new Error("temporary failure"))
      .mockImplementation(async (resource) => info(resource));
    const state = setup();
    await flushPromises();
    expect(state.result.metadata.value.get(state.node.id)?.state).toBe("failed");
    state.targets.value = [];
    await flushPromises();
    state.targets.value = [state.node.id];
    await flushPromises();
    expect(state.result.metadata.value.get(state.node.id)?.state).toBe("resolved");
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(2);
  });

  it("tries another identity provider after a transport failure", async () => {
    const report = structuredClone(loadReport("repressilator"));
    report.models![0]!.listOfSpecies![0]!.cvterms = [
      { qualifier: "BQB_IS", resources: ["urn:first", "urn:second"] },
    ];
    vi.mocked(client.getAnnotationResource).mockImplementation(async (resource) => {
      if (resource === "urn:first") throw new Error("provider unavailable");
      return info(resource, "Alternative provider");
    });
    const state = setup(new ReportIndex(report));
    await flushPromises();
    expect(state.result.metadata.value.get(state.node.id)?.label).toBe("Alternative provider");
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(2);
  });
});
