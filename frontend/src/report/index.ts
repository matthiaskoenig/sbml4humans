import type {
  Association,
  Edge,
  EdgeKind,
  SbmlElement,
  ElementType,
  ExternalModelDefinition,
  Model,
  Node,
  Report,
  SBMLDocument,
  SBase,
} from "@/api/types";
import { ELEMENT_TYPES } from "@/data/sbmlTypes";

/** The edge kinds of a participation: a reaction links to every reactant, product and modifier
 * it lists, and each of those links to its species with the same kind. */
export const PARTICIPATION_KINDS = ["reactant", "product", "modifier"] as const;
export type ParticipationKind = (typeof PARTICIPATION_KINDS)[number];

function push<K, V>(map: Map<K, V[]>, key: K, value: V): void {
  const list = map.get(key);
  if (list) list.push(value);
  else map.set(key, [value]);
}

/** Lookups over one report: every element by pk, the elements of a model by type, the edges in both directions. */
export class ReportIndex {
  readonly report: Report;
  readonly elements = new Map<string, SBase>();
  readonly nodes = new Map<string, Node>();
  private readonly outgoing = new Map<string, Edge[]>();
  private readonly incoming = new Map<string, Edge[]>();
  private readonly byModel = new Map<string, Map<ElementType, SbmlElement[]>>();

  constructor(report: Report) {
    this.report = report;
    this.add(report.document);
    for (const definition of report.externalModelDefinitions ?? []) this.add(definition);
    for (const model of report.models ?? []) this.addModel(model);
    for (const node of Object.values(report.linkGraph?.nodes ?? {})) this.nodes.set(node.pk, node);
    for (const edge of report.linkGraph?.edges ?? []) {
      push(this.outgoing, edge.source, edge);
      push(this.incoming, edge.target, edge);
    }
  }

  get document(): SBMLDocument {
    return this.report.document;
  }

  get models(): Model[] {
    return this.report.models ?? [];
  }

  get externalModelDefinitions(): ExternalModelDefinition[] {
    return this.report.externalModelDefinitions ?? [];
  }

  /** The model of kind "model", else the first model definition. */
  get mainModel(): Model | null {
    return this.models.find((model) => model.kind === "model") ?? this.models[0] ?? null;
  }

  model(id: string): Model | null {
    return this.models.find((model) => model.id === id) ?? null;
  }

  get(pk: string): SBase | undefined {
    return this.elements.get(pk);
  }

  has(pk: string): boolean {
    return this.elements.has(pk);
  }

  /** The elements of the model grouped by type, every element type present, in list order. */
  byType(modelId: string): ReadonlyMap<ElementType, SbmlElement[]> {
    return this.byModel.get(modelId) ?? new Map();
  }

  /** The id of the containing model. The node only carries the model's pk, so this resolves
   * that pk one more hop to the model's id. */
  modelOf(pk: string): string | null {
    const modelPk = this.nodes.get(pk)?.model;
    if (!modelPk) return null;
    return this.nodes.get(modelPk)?.id ?? this.elements.get(modelPk)?.id ?? null;
  }

  /** The edges from the element to the elements it references. */
  references(pk: string): Edge[] {
    return this.outgoing.get(pk) ?? [];
  }

  /** The edges from the elements referencing the element. */
  referencedBy(pk: string): Edge[] {
    return this.incoming.get(pk) ?? [];
  }

  /** The reaction which lists a species or modifier reference and the role the reference plays
   * in it, read from the edge of the reaction to the reference. A species reference belongs to
   * exactly one list of one reaction, so there is at most one such edge. */
  participation(pk: string): { reaction: string; role: ParticipationKind } | null {
    for (const edge of this.referencedBy(pk)) {
      // the species a reference names carries the same kinds, from the reference; only the edge
      // of a reaction names a participation
      if (this.nodes.get(edge.source)?.sbmlType !== "Reaction") continue;
      if (PARTICIPATION_KINDS.includes(edge.kind as ParticipationKind)) {
        return { reaction: edge.source, role: edge.kind as ParticipationKind };
      }
    }
    return null;
  }

  /** The pk of the element with the id, or failing that the metaId, referenced by the source
   * through an edge of the kind, if any. */
  resolve(sourcePk: string, kind: EdgeKind, id: string | null | undefined): string | null {
    if (!id) return null;
    for (const edge of this.references(sourcePk)) {
      if (edge.kind !== kind) continue;
      const target = this.nodes.get(edge.target);
      const element = this.elements.get(edge.target);
      if (target?.id === id || element?.id === id || element?.metaId === id) return edge.target;
    }
    return null;
  }

  /** An element and everything nested in it which carries a pk of its own: its uncertainties,
   * the replacements of the comp package it carries and the chain of references below one. */
  private add(element: SBase): void {
    this.elements.set(element.pk, element);
    for (const uncertainty of element.uncertainties ?? []) this.add(uncertainty);
    if (element.comp?.replacedBy) this.add(element.comp.replacedBy);
    for (const replaced of element.comp?.replacedElements ?? []) this.add(replaced);
    if ("sbaseRef" in element && element.sbaseRef) this.add(element.sbaseRef);
  }

  private addModel(model: Model): void {
    this.add(model);
    const byType = new Map<ElementType, SbmlElement[]>();
    for (const info of ELEMENT_TYPES) {
      const list = (model[info.listKey] ?? []) as SbmlElement[];
      byType.set(
        info.type,
        list.filter((element) => element.sbmlType === info.type),
      );
    }
    for (const elements of byType.values()) {
      for (const element of elements) this.addElement(element);
    }
    if (model.id) this.byModel.set(model.id, byType);
  }

  /** A node of a gene product association and every node below it (fbc §3.10). */
  private addAssociation(node: Association | null | undefined): void {
    if (!node) return;
    this.add(node);
    if (node.sbmlType === "And" || node.sbmlType === "Or") {
      for (const child of node.associations ?? []) this.addAssociation(child);
    }
  }

  private addElement(element: SbmlElement): void {
    this.add(element);
    switch (element.sbmlType) {
      case "Reaction":
        for (const reference of element.listOfReactants ?? []) this.add(reference);
        for (const reference of element.listOfProducts ?? []) this.add(reference);
        for (const reference of element.listOfModifiers ?? []) this.add(reference);
        if (element.kineticLaw) {
          this.add(element.kineticLaw);
          for (const parameter of element.kineticLaw.listOfLocalParameters ?? [])
            this.add(parameter);
        }
        if (element.fbc?.geneProductAssociation) {
          this.add(element.fbc.geneProductAssociation);
          this.addAssociation(element.fbc.geneProductAssociation.association);
        }
        break;
      case "UserDefinedConstraint":
        for (const component of element.listOfUserDefinedConstraintComponents ?? [])
          this.add(component);
        break;
      case "Objective":
        for (const fluxObjective of element.listOfFluxObjectives ?? []) this.add(fluxObjective);
        break;
      case "Submodel":
        for (const deletion of element.listOfDeletions ?? []) this.add(deletion);
        break;
      case "Event":
        if (element.trigger) this.add(element.trigger);
        if (element.priority) this.add(element.priority);
        if (element.delay) this.add(element.delay);
        for (const assignment of element.listOfEventAssignments ?? []) this.add(assignment);
        break;
      case "Transition":
        for (const input of element.listOfInputs ?? []) this.add(input);
        for (const output of element.listOfOutputs ?? []) this.add(output);
        for (const term of element.listOfFunctionTerms ?? []) this.add(term);
        if (element.defaultTerm) this.add(element.defaultTerm);
        break;
      default:
        break;
    }
  }
}
