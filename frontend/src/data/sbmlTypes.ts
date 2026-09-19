import {
  ActivityIcon,
  AmpersandIcon,
  ArrowRightFromLineIcon,
  ArrowRightLeftIcon,
  ArrowRightToLineIcon,
  BoxIcon,
  CalculatorIcon,
  CornerDownRightIcon,
  ChevronsLeftRightEllipsisIcon,
  CircleArrowLeftIcon,
  CircleDotIcon,
  CircleIcon,
  ChevronsUpIcon,
  CircleQuestionMarkIcon,
  ClockIcon,
  CodeIcon,
  EqualIcon,
  ExternalLinkIcon,
  FileIcon,
  HashIcon,
  HourglassIcon,
  LayoutGridIcon,
  ListIcon,
  ListTreeIcon,
  LockIcon,
  LogInIcon,
  MoveHorizontalIcon,
  NetworkIcon,
  ReplaceIcon,
  ScaleIcon,
  SigmaIcon,
  SignalIcon,
  SlidersHorizontalIcon,
  SplitIcon,
  Table2Icon,
  TagIcon,
  TargetIcon,
  Trash2Icon,
  WaypointsIcon,
  WorkflowIcon,
  ZapIcon,
} from "@lucide/vue";
import type { Component } from "vue";

import type {
  DocumentElementType,
  ElementType,
  ModelListKey,
  NestedElementType,
  SbmlType,
} from "@/api/types";

export type SbmlPackage = "core" | "comp" | "fbc" | "qual" | "distrib";

export interface SbmlTypeInfo<T extends SbmlType = SbmlType> {
  /** The type, which is the name of its class in the specification and the only name the
   * application has for it: the type bar, the heading of a table and the header of the inspector
   * write `FunctionDefinition` as the specification and the reference do, not a label of their
   * own. */
  type: T;
  /** Marker colour. */
  color: string;
  /** The icon, a component of `@lucide/vue`. */
  icon: Component;
  pkg: SbmlPackage;
}

export interface ElementTypeInfo extends SbmlTypeInfo<ElementType> {
  /** The list of the model holding the elements. */
  listKey: ModelListKey;
}

export const DOCUMENT_TYPES: readonly SbmlTypeInfo<DocumentElementType>[] = [
  {
    type: "SBMLDocument",
    color: "#fcd090",
    icon: FileIcon,
    pkg: "core",
  },
  {
    type: "Model",
    color: "#66c2a5",
    icon: NetworkIcon,
    pkg: "core",
  },
  {
    type: "ExternalModelDefinition",
    color: "#66c2a5",
    icon: ExternalLinkIcon,
    pkg: "comp",
  },
];

export const ELEMENT_TYPES: readonly ElementTypeInfo[] = [
  {
    type: "FunctionDefinition",
    color: "#e6f598",
    icon: CodeIcon,
    pkg: "core",
    listKey: "listOfFunctionDefinitions",
  },
  {
    type: "Compartment",
    color: "#92c5de",
    icon: BoxIcon,
    pkg: "core",
    listKey: "listOfCompartments",
  },
  {
    type: "Species",
    color: "#abdda4",
    icon: CircleIcon,
    pkg: "core",
    listKey: "listOfSpecies",
  },
  {
    type: "Parameter",
    color: "#fdae61",
    icon: SlidersHorizontalIcon,
    pkg: "core",
    listKey: "listOfParameters",
  },
  {
    type: "InitialAssignment",
    color: "#fee08b",
    icon: CircleArrowLeftIcon,
    pkg: "core",
    listKey: "listOfInitialAssignments",
  },
  {
    type: "AssignmentRule",
    color: "#fb9a99",
    icon: EqualIcon,
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "RateRule",
    color: "#fb9a99",
    icon: ActivityIcon,
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "AlgebraicRule",
    color: "#fb9a99",
    icon: HashIcon,
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "Constraint",
    color: "#fdae61",
    icon: LockIcon,
    pkg: "core",
    listKey: "listOfConstraints",
  },
  {
    type: "Reaction",
    color: "#a6cee3",
    icon: ArrowRightLeftIcon,
    pkg: "core",
    listKey: "listOfReactions",
  },
  {
    type: "Event",
    color: "#fed08b",
    icon: ClockIcon,
    pkg: "core",
    listKey: "listOfEvents",
  },
  {
    type: "Submodel",
    color: "#00ccff",
    icon: LayoutGridIcon,
    pkg: "comp",
    listKey: "listOfSubmodels",
  },
  {
    type: "Port",
    color: "#fed9a6",
    icon: LogInIcon,
    pkg: "comp",
    listKey: "listOfPorts",
  },
  {
    type: "GeneProduct",
    color: "#d53e4f",
    icon: TagIcon,
    pkg: "fbc",
    listKey: "listOfGeneProducts",
  },
  {
    type: "Objective",
    color: "#f46d43",
    icon: TargetIcon,
    pkg: "fbc",
    listKey: "listOfObjectives",
  },
  {
    type: "FluxBound",
    color: "#f46d43",
    icon: ChevronsLeftRightEllipsisIcon,
    pkg: "fbc",
    listKey: "listOfFluxBounds",
  },
  {
    type: "UserDefinedConstraint",
    color: "#f46d43",
    icon: ScaleIcon,
    pkg: "fbc",
    listKey: "listOfUserDefinedConstraints",
  },
  {
    type: "QualitativeSpecies",
    color: "#c2a5cf",
    icon: SignalIcon,
    pkg: "qual",
    listKey: "listOfQualitativeSpecies",
  },
  {
    type: "Transition",
    color: "#9970ab",
    icon: WorkflowIcon,
    pkg: "qual",
    listKey: "listOfTransitions",
  },
  // the unit definitions are the last table of a report and not the second one, where the
  // specification lists them: they are what the other tables link to for their units, not what a
  // model is about, and they would push the compartments and the species down the page
  {
    type: "UnitDefinition",
    color: "#f1b6da",
    icon: CalculatorIcon,
    pkg: "core",
    listKey: "listOfUnitDefinitions",
  },
];

export const NESTED_TYPES: readonly SbmlTypeInfo<NestedElementType>[] = [
  {
    type: "SpeciesReference",
    color: "#abdda4",
    icon: CircleDotIcon,
    pkg: "core",
  },
  {
    type: "ModifierSpeciesReference",
    color: "#abdda4",
    icon: CircleIcon,
    pkg: "core",
  },
  {
    type: "KineticLaw",
    color: "#a6cee3",
    icon: CalculatorIcon,
    pkg: "core",
  },
  {
    type: "LocalParameter",
    color: "#fdae61",
    icon: SlidersHorizontalIcon,
    pkg: "core",
  },
  {
    type: "Trigger",
    color: "#fed08b",
    icon: ZapIcon,
    pkg: "core",
  },
  {
    type: "Priority",
    color: "#fed08b",
    icon: ChevronsUpIcon,
    pkg: "core",
  },
  {
    type: "Delay",
    color: "#fed08b",
    icon: HourglassIcon,
    pkg: "core",
  },
  {
    type: "EventAssignment",
    color: "#fed08b",
    icon: EqualIcon,
    pkg: "core",
  },
  {
    type: "Deletion",
    color: "#00ccff",
    icon: Trash2Icon,
    pkg: "comp",
  },
  {
    type: "ReplacedElement",
    color: "#00ccff",
    icon: ReplaceIcon,
    pkg: "comp",
  },
  {
    type: "ReplacedBy",
    color: "#00ccff",
    icon: ReplaceIcon,
    pkg: "comp",
  },
  {
    type: "SBaseRef",
    color: "#fed9a6",
    icon: WaypointsIcon,
    pkg: "comp",
  },
  {
    type: "FluxObjective",
    color: "#f46d43",
    icon: TargetIcon,
    pkg: "fbc",
  },
  {
    type: "UserDefinedConstraintComponent",
    color: "#f46d43",
    icon: ScaleIcon,
    pkg: "fbc",
  },
  {
    type: "GeneProductAssociation",
    color: "#d53e4f",
    icon: ListTreeIcon,
    pkg: "fbc",
  },
  {
    type: "And",
    color: "#d53e4f",
    icon: AmpersandIcon,
    pkg: "fbc",
  },
  {
    type: "Or",
    color: "#d53e4f",
    icon: SplitIcon,
    pkg: "fbc",
  },
  {
    type: "GeneProductRef",
    color: "#d53e4f",
    icon: TagIcon,
    pkg: "fbc",
  },
  {
    type: "Input",
    color: "#c2a5cf",
    icon: ArrowRightToLineIcon,
    pkg: "qual",
  },
  {
    type: "Output",
    color: "#c2a5cf",
    icon: ArrowRightFromLineIcon,
    pkg: "qual",
  },
  {
    type: "FunctionTerm",
    color: "#9970ab",
    icon: Table2Icon,
    pkg: "qual",
  },
  {
    type: "DefaultTerm",
    color: "#9970ab",
    icon: CornerDownRightIcon,
    pkg: "qual",
  },
  {
    type: "Uncertainty",
    color: "#c7c7c7",
    icon: CircleQuestionMarkIcon,
    pkg: "distrib",
  },
  {
    type: "UncertParameter",
    color: "#c7c7c7",
    icon: SigmaIcon,
    pkg: "distrib",
  },
  {
    type: "UncertSpan",
    color: "#c7c7c7",
    icon: MoveHorizontalIcon,
    pkg: "distrib",
  },
  // a list of any type and of any package is of the one type ListOf, which the core defines:
  // its colour is a neutral one and not the colour of what a list holds
  {
    type: "ListOf",
    color: "#e5d8bd",
    icon: ListIcon,
    pkg: "core",
  },
];

export const SBML_TYPES: Readonly<Record<SbmlType, SbmlTypeInfo>> = Object.fromEntries(
  [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES].map((info) => [info.type, info]),
) as Record<SbmlType, SbmlTypeInfo>;

export function typeInfo(type: ElementType): ElementTypeInfo;
export function typeInfo(type: SbmlType): SbmlTypeInfo;
export function typeInfo(type: SbmlType): SbmlTypeInfo {
  return SBML_TYPES[type];
}

const ELEMENT_TYPE_SET = new Set<string>(ELEMENT_TYPES.map((info) => info.type));

export function isElementType(type: string): type is ElementType {
  return ELEMENT_TYPE_SET.has(type);
}
