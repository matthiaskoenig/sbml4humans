/** The report types generated from the JSON schema plus the unions the components work with. */
import type {
  AlgebraicRule,
  And,
  AssignmentRule,
  Compartment,
  Constraint,
  Delay,
  Deletion,
  Event,
  EventAssignment,
  ExternalModelDefinition,
  FluxBound,
  FluxObjective,
  FunctionDefinition,
  GeneProduct,
  GeneProductAssociation,
  GeneProductRef,
  InitialAssignment,
  KineticLaw,
  LocalParameter,
  Model,
  ModifierSpeciesReference,
  Objective,
  Or,
  Parameter,
  Port,
  Priority,
  RateRule,
  Reaction,
  ReplacedBy,
  ReplacedElement,
  SBaseRef,
  SBMLDocument,
  Species,
  SpeciesReference,
  Submodel,
  Trigger,
  Uncertainty,
  UnitDefinition,
  UserDefinedConstraint,
  UserDefinedConstraintComponent,
} from "@/types/report";

export type * from "@/types/report";

/** The objects of the document group of the type bar. */
export type DocumentElement = SBMLDocument | Model | ExternalModelDefinition;

/** The objects with a table of their own. */
export type SbmlElement =
  | FunctionDefinition
  | UnitDefinition
  | Compartment
  | Species
  | Parameter
  | InitialAssignment
  | AssignmentRule
  | RateRule
  | AlgebraicRule
  | Constraint
  | Reaction
  | Event
  | Submodel
  | Port
  | GeneProduct
  | Objective
  | FluxBound
  | UserDefinedConstraint;

/** The objects nested in another object, reachable through the inspector only. */
export type NestedElement =
  | SpeciesReference
  | ModifierSpeciesReference
  | KineticLaw
  | LocalParameter
  | Trigger
  | Priority
  | Delay
  | EventAssignment
  | Deletion
  | ReplacedElement
  | ReplacedBy
  | SBaseRef
  | FluxObjective
  | UserDefinedConstraintComponent
  | GeneProductAssociation
  | And
  | Or
  | GeneProductRef
  | Uncertainty;

export type SBase = DocumentElement | SbmlElement | NestedElement;
export type Rule = AssignmentRule | RateRule | AlgebraicRule;
/** One node of the gene product association of a reaction (fbc §3.10). */
export type Association = GeneProductRef | And | Or;

export type SbmlType = NonNullable<SBase["sbmlType"]>;
export type ElementType = NonNullable<SbmlElement["sbmlType"]>;
export type DocumentElementType = NonNullable<DocumentElement["sbmlType"]>;
export type NestedElementType = NonNullable<NestedElement["sbmlType"]>;

/** The keys of the SBML lists of a model. */
export type ModelListKey = {
  [K in keyof Model]-?: K extends `listOf${string}` ? K : never;
}[keyof Model];

/** `GET /api/examples` entry. */
export interface ExampleMetaData {
  id: string;
  name: string | null;
  description: string | null;
  packages: string[];
}

/** `GET /api/annotation_resource` body (snake_case, as pymetadata returns it). */
export interface AnnotationInfo {
  resource: string;
  resource_normalized: string | null;
  collection: string | null;
  term: string | null;
  label: string | null;
  description: string | null;
  url: string | null;
  /** synonyms and cross references of the term, as objects of the ontology service; the report
   * shows neither of them. */
  synonyms: unknown[];
  xrefs: unknown[];
  errors: string[];
  warnings: string[];
}
