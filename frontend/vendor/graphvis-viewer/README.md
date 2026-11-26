# Graphvis viewer

A domain-neutral Cosmos viewer for fixed-coordinate graphs and point clouds. SBML parsing, expression matrices, metadata, and inspectors belong to the host application. The renderer consumes packed scene buffers and reports controlled entity selection.

`packScene(nodes, edges)` preserves visual instance IDs independently of entity IDs. An entity can have several graphical instances. Coordinates stay fixed, and edges are optional. Selection, color and metadata text updates do not upload topology or restart layout.

Endpoint triangles, inhibition bars, modifier circles and activation diamonds use shared native GPU atlas sprites. Their tips follow the visible glyph boundary while zooming. Render-only points resolve to their owning edge, and domain glyphs take precedence over transparent sprite padding when picking.

Labels use a bounded SVG layer sharing the Cosmos camera. A spatial index checks labels against all domain glyphs, and a grid prevents label overlap. Selected and hovered objects have priority. Text measurement and label placement are limited to 2,000 candidates and 160 labels per frame; the measurement cache is bounded. Label placement uses supplied fixed coordinates and performs no GPU position readback.

The optional `@graphvis/viewer/layout` module computes static force layouts in a host worker. It accepts numeric size, distance, strength and group hints without SBML semantics. It packs disconnected components, handles collisions, coalesces duplicate layout springs, and bounds force iterations by graph size. Supplied scientific coordinates bypass computed layout.

The Cosmos dependency is bundled by the host. The viewer does not download executable modules from a CDN. `loadGraph` can supply another compatible Cosmos constructor for tests or a host-managed loader. The host must provide a container with nonzero dimensions and call `destroy()` on unmount.

SBML Layout/Render geometry and arbitrary source curves require additional scene support. The host retains full metadata and controls selection; the viewer does not resolve identifiers itself.
