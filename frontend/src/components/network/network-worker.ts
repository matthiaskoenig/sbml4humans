import {
  NetworkPipeline,
  transferableNetwork,
  type NetworkRequest,
  decodeNetworkInput,
} from "@/report/network-pipeline";

let pipeline: NetworkPipeline | null = null;
self.onmessage = (
  event: MessageEvent<{
    generation: number;
    reports?: Uint8Array;
    request: NetworkRequest;
  }>,
) => {
  const { generation, reports, request } = event.data;
  try {
    if (reports) pipeline = new NetworkPipeline(decodeNetworkInput(reports));
    if (!pipeline) throw new Error("The network worker has no report.");
    const { result, transfer } = transferableNetwork(pipeline.prepare(request));
    self.postMessage({ generation, result }, { transfer });
  } catch (cause) {
    self.postMessage({
      generation,
      error: cause instanceof Error ? cause.message : "The network could not be prepared.",
    });
  }
};
