import type {
  Association,
  Edge,
  EdgeKind,
  SbmlElement,
  ElementType,
  ExternalModelDefinition,
  ListOf,
  Model,
  Node,
  Report,
  SBMLDocument,
  SBase,
  UncertMeasure,
  Uncertainty,
  ValidationIssue,
} from "@/api/types";
import { ELEMENT_TYPES } from "@/data/sbmlTypes";
import { bySeverity, worse, type Severity } from "@/report/validation";

/** The edge kinds of a participation: a reaction links to every reactant, product and modifier
 * it lists, and each of those links to its species with the same kind. */
export const PARTICIPATION_KINDS = ["reactant", "product", "modifier"] as const;
export type ParticipationKind = (typeof PARTICIPATION_KINDS)[number];

/** How deep a gene product association is followed: the tree of a reaction of Recon3D is a
 * few operators deep, and the limit only keeps a graph which is not a tree from recursing
 * without end. */
const MAX_ASSOCIATION_DEPTH = 64;

function push<K, V>(map: Map<K, V[]>, key: K, value: V): void {
  const list = map.get(key);
  if (list) list.push(value);
  else map.set(key, [value]);
}

/** An element of the report of an archive: its pk and the manifest location of its entry, null
 * for the entry which is shown. A pk alone names an element of one entry only, two entries may
 * hold the same one. */
export interface ElementRef {
  pk: string;
  entry: string | null;
}

/** An edge which leaves its entry, with the entries of both of its ends: a reference of a comp
 * model which follows an external model definition into the document it names. */
export interface CrossEdge {
  source: string;
  sourceEntry: string;
  target: string;
  targetEntry: string;
  kind: EdgeKind;
}

/** Lookups over one report: every element by pk, the elements of a model by type, the edges in both directions. */
export class ReportIndex {
  readonly report: Report;
  /** The manifest location of the entry of the report, null for a report on its own. */
  readonly location: string | null;
  readonly elements = new Map<string, SBase>();
  readonly nodes = new Map<string, Node>();
  private readonly outgoing = new Map<string, Edge[]>();
  private readonly incoming = new Map<string, Edge[]>();
  private readonly outgoingAcross = new Map<string, CrossEdge[]>();
  private readonly incomingAcross = new Map<string, CrossEdge[]>();
  private entries: ReadonlyMap<string, ReportIndex> = new Map();
  private readonly byModel = new Map<string, Map<ElementType, SbmlElement[]>>();
  /** The issues of the validation of the document, in the order of libsbml. */
  readonly issues: readonly ValidationIssue[];
  private readonly issuesByPk = new Map<string, ValidationIssue[]>();
  private readonly worstByPk = new Map<string, Severity>();
  /** The element with a row of a table which holds an element without one, by the pk of the
   * nested element: the kinetic law, the species references and the lists of a reaction, the
   * trigger of an event, and everything else `addElement` adds below an element of a table. */
  private readonly rowOf = new Map<string, string>();
  /** The issues of the nested elements without a row, by the pk of the row which holds them. */
  private readonly heldByPk = new Map<string, ValidationIssue[]>();
  /** The element of a table whose nested elements `add` is adding, null outside one. */
  private holder: string | null = null;
  /** The number of issues of each severity. */
  readonly issueCounts: Record<Severity, number> = { error: 0, warning: 0, info: 0 };

  constructor(report: Report, location: string | null = null) {
    this.report = report;
    this.location = location;
    // the document, an external model definition and a model have no row of a table: their entry
    // of the type bar is their row, which the issues of what they hold without a row mark
    this.addHolder(report.document);
    for (const definition of report.externalModelDefinitions ?? []) this.addHolder(definition);
    for (const model of report.models ?? []) this.addModel(model);
    for (const node of Object.values(report.linkGraph?.nodes ?? {})) this.nodes.set(node.pk, node);
    for (const edge of report.linkGraph?.edges ?? []) {
      // an edge into another entry names a pk of that entry, which may be a pk of this one as
      // well: it is kept apart, so that every lookup by pk stays inside the entry
      if (edge.targetEntry && edge.targetEntry !== location) {
        if (location === null) continue;
        const { source, target, kind, targetEntry } = edge;
        push(this.outgoingAcross, source, {
          source,
          sourceEntry: location,
          target,
          targetEntry,
          kind,
        });
        continue;
      }
      push(this.outgoing, edge.source, edge);
      push(this.incoming, edge.target, edge);
    }
    this.issues = report.validation ?? [];
    for (const issue of this.issues) {
      push(this.issuesByPk, issue.pk, issue);
      // the issue of an element without a row marks the row which holds it
      const row = this.rowOf.get(issue.pk);
      if (row) push(this.heldByPk, row, issue);
      for (const marked of row ? [issue.pk, row] : [issue.pk]) {
        this.worstByPk.set(marked, worse(this.worstByPk.get(marked) ?? null, issue.severity));
      }
      this.issueCounts[issue.severity] += 1;
    }
  }

  /** The indexes of the entries of one archive by location, connected: every edge which leaves
   * its entry is known to the entry it ends in, so that an element lists who names it from
   * another document. */
  static forEntries(reports: Record<string, { report: Report }>): Map<string, ReportIndex> {
    const indexes = new Map(
      Object.entries(reports).map(([location, entry]) => [
        location,
        new ReportIndex(entry.report, location),
      ]),
    );
    for (const index of indexes.values()) {
      index.entries = indexes;
      for (const edges of index.outgoingAcross.values()) {
        for (const edge of edges) {
          const target = indexes.get(edge.targetEntry);
          if (target) push(target.incomingAcross, edge.target, edge);
        }
      }
    }
    return indexes;
  }

  /** The index of another entry of the archive, this one for null and for its own location. */
  entry(location: string | null | undefined): ReportIndex | null {
    if (!location || location === this.location) return this;
    return this.entries.get(location) ?? null;
  }

  /** The issues of an element, errors first. */
  issuesOf(pk: string): ValidationIssue[] {
    return bySeverity(this.issuesByPk.get(pk) ?? []);
  }

  /** The issues of the elements an element of a table holds which have no row of their own, the
   * kinetic law of a reaction or the trigger of an event, errors first; each names its element by
   * its pk. Empty for every element which is no row of a table. */
  heldIssuesOf(pk: string): ValidationIssue[] {
    return bySeverity(this.heldByPk.get(pk) ?? []);
  }

  /** The issues of an element and of those it holds (`heldIssuesOf`), errors first: the issues
   * of its row, its tooltip and its inspector. */
  rowIssuesOf(pk: string): ValidationIssue[] {
    return bySeverity([...(this.issuesByPk.get(pk) ?? []), ...(this.heldByPk.get(pk) ?? [])]);
  }

  /** Why the consistency of the document was not checked, null where it was: its issues are then
   * those of reading it alone. */
  get validationSkipped(): Report["validationSkipped"] {
    return this.report.validationSkipped ?? null;
  }

  /** The worst severity of the issues of an element and of those it holds (`heldIssuesOf`), null
   * without one: the mark of its row. */
  worstSeverity(pk: string): Severity | null {
    return this.worstByPk.get(pk) ?? null;
  }

  /** The worst severity of the elements of a type in one model: the type bar and the tables
   * show one model, and an issue of another model is not theirs. */
  worstSeverityOfType(type: ElementType, modelId: string): Severity | null {
    let worst: Severity | null = null;
    for (const element of this.byType(modelId).get(type) ?? []) {
      const severity = this.worstByPk.get(element.pk);
      if (severity) worst = worse(worst, severity);
    }
    return worst;
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

  /** The id of the model which holds the element, the id of a model for the model itself. */
  modelIdOf(pk: string): string | null {
    const element = this.elements.get(pk);
    if (element?.sbmlType === "Model") return element.id ?? null;
    return this.modelOf(pk);
  }

  /** The list of an element with the name the list has in the file, `listOfSpecies` of a model
   * or `listOfReactants` of a reaction, where it states something of its own: a plain list is
   * no element of the report. The three tables of the rules share the one `listOfRules`. */
  list(pk: string, element: string): ListOf | null {
    return this.elements.get(pk)?.lists?.find((list) => list.element === element) ?? null;
  }

  /** The edges from the element to the elements of its entry it references. */
  references(pk: string): Edge[] {
    return this.outgoing.get(pk) ?? [];
  }

  /** The edges from the elements of its entry referencing the element. */
  referencedBy(pk: string): Edge[] {
    return this.incoming.get(pk) ?? [];
  }

  /** The edges from the element to the elements of other entries it references. */
  referencesAcross(pk: string): CrossEdge[] {
    return this.outgoingAcross.get(pk) ?? [];
  }

  /** The edges from the elements of other entries referencing the element. */
  referencedAcross(pk: string): CrossEdge[] {
    return this.incomingAcross.get(pk) ?? [];
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

  /** The reaction whose gene product association holds the node, read upwards over the edges
   * of the association tree, which lead from the reaction to its association and from every
   * node to the nodes below it (fbc §3.9 to §3.13). Null for anything which is no node of a
   * tree. */
  associationReaction(pk: string): string | null {
    let current = pk;
    for (let depth = 0; depth < MAX_ASSOCIATION_DEPTH; depth++) {
      const parent = this.referencedBy(current).find(
        (edge) => edge.kind === "geneProductAssociation",
      )?.source;
      if (!parent) return null;
      if (this.nodes.get(parent)?.sbmlType === "Reaction") return parent;
      current = parent;
    }
    return null;
  }

  /** The gene products the association of a reaction names, once each, in the order in which
   * the tree names them. */
  geneProducts(reactionPk: string): string[] {
    const products = new Set<string>();
    const walk = (pk: string, depth: number): void => {
      if (depth > MAX_ASSOCIATION_DEPTH) return;
      for (const edge of this.references(pk)) {
        if (edge.kind === "geneProductAssociation") walk(edge.target, depth + 1);
        else if (edge.kind === "geneProduct") products.add(edge.target);
      }
    };
    walk(reactionPk, 0);
    return [...products];
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
   * the replacements of the comp package it carries, the chain of references below one and its
   * lists which state something of their own. Every element of the report passes through here,
   * so the lists of the document, of a model and of a nested element are found alike. */
  private add(element: SBase): void {
    this.elements.set(element.pk, element);
    if (this.holder !== null && element.pk !== this.holder) this.rowOf.set(element.pk, this.holder);
    for (const list of element.lists ?? []) this.add(list);
    for (const uncertainty of element.uncertainties ?? []) this.addUncertainty(uncertainty);
    if (element.comp?.replacedBy) this.add(element.comp.replacedBy);
    for (const replaced of element.comp?.replacedElements ?? []) this.add(replaced);
    if ("sbaseRef" in element && element.sbaseRef) this.add(element.sbaseRef);
  }

  private addModel(model: Model): void {
    this.addHolder(model);
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

  /** An uncertainty or one of its measures and every measure below it: a distribution is
   * defined by uncert parameters of its own, to any depth (distrib §3.11.7). */
  private addUncertainty(owner: Uncertainty | UncertMeasure): void {
    this.add(owner);
    for (const measure of owner.uncertParameters ?? []) this.addUncertainty(measure);
  }

  /** A node of a gene product association and every node below it (fbc §3.10). */
  private addAssociation(node: Association | null | undefined): void {
    if (!node) return;
    this.add(node);
    if (node.sbmlType === "And" || node.sbmlType === "Or") {
      for (const child of node.associations ?? []) this.addAssociation(child);
    }
  }

  /** An element of a table and the elements nested in it, which the issues they have mark it. */
  private addElement(element: SbmlElement): void {
    this.holder = element.pk;
    this.addNested(element);
    this.holder = null;
  }

  /** An element whose row is its entry of the type bar, the document, an external model
   * definition or a model, and what it holds without a row: its lists and its uncertainties. */
  private addHolder(element: SBase): void {
    this.holder = element.pk;
    this.add(element);
    this.holder = null;
  }

  private addNested(element: SbmlElement): void {
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
