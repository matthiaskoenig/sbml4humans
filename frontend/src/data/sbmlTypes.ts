import {
  ActivityIcon,
  ArrowRightLeftIcon,
  BoxIcon,
  CalculatorIcon,
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
  LockIcon,
  LogInIcon,
  NetworkIcon,
  SlidersHorizontalIcon,
  TagIcon,
  TargetIcon,
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

export type SbmlPackage = "core" | "comp" | "fbc" | "distrib";

export interface SbmlTypeInfo<T extends SbmlType = SbmlType> {
  type: T;
  /** Singular label. */
  label: string;
  /** Plural label, the section header. */
  plural: string;
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
    label: "Document",
    plural: "Documents",
    color: "#fcd090",
    icon: FileIcon,
    pkg: "core",
  },
  {
    type: "Model",
    label: "Model",
    plural: "Models",
    color: "#66c2a5",
    icon: NetworkIcon,
    pkg: "core",
  },
  {
    type: "ExternalModelDefinition",
    label: "External model definition",
    plural: "External model definitions",
    color: "#66c2a5",
    icon: ExternalLinkIcon,
    pkg: "comp",
  },
];

export const ELEMENT_TYPES: readonly ElementTypeInfo[] = [
  {
    type: "FunctionDefinition",
    label: "Function definition",
    plural: "Function definitions",
    color: "#e6f598",
    icon: CodeIcon,
    pkg: "core",
    listKey: "listOfFunctionDefinitions",
  },
  {
    type: "UnitDefinition",
    label: "Unit definition",
    plural: "Unit definitions",
    color: "#f1b6da",
    icon: CalculatorIcon,
    pkg: "core",
    listKey: "listOfUnitDefinitions",
  },
  {
    type: "Compartment",
    label: "Compartment",
    plural: "Compartments",
    color: "#92c5de",
    icon: BoxIcon,
    pkg: "core",
    listKey: "listOfCompartments",
  },
  {
    type: "Species",
    label: "Species",
    plural: "Species",
    color: "#abdda4",
    icon: CircleIcon,
    pkg: "core",
    listKey: "listOfSpecies",
  },
  {
    type: "Parameter",
    label: "Parameter",
    plural: "Parameters",
    color: "#fdae61",
    icon: SlidersHorizontalIcon,
    pkg: "core",
    listKey: "listOfParameters",
  },
  {
    type: "InitialAssignment",
    label: "Initial assignment",
    plural: "Initial assignments",
    color: "#fee08b",
    icon: CircleArrowLeftIcon,
    pkg: "core",
    listKey: "listOfInitialAssignments",
  },
  {
    type: "AssignmentRule",
    label: "Assignment rule",
    plural: "Assignment rules",
    color: "#fb9a99",
    icon: EqualIcon,
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "RateRule",
    label: "Rate rule",
    plural: "Rate rules",
    color: "#fb9a99",
    icon: ActivityIcon,
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "AlgebraicRule",
    label: "Algebraic rule",
    plural: "Algebraic rules",
    color: "#fb9a99",
    icon: HashIcon,
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "Constraint",
    label: "Constraint",
    plural: "Constraints",
    color: "#fdae61",
    icon: LockIcon,
    pkg: "core",
    listKey: "listOfConstraints",
  },
  {
    type: "Reaction",
    label: "Reaction",
    plural: "Reactions",
    color: "#a6cee3",
    icon: ArrowRightLeftIcon,
    pkg: "core",
    listKey: "listOfReactions",
  },
  {
    type: "Event",
    label: "Event",
    plural: "Events",
    color: "#fed08b",
    icon: ClockIcon,
    pkg: "core",
    listKey: "listOfEvents",
  },
  {
    type: "Submodel",
    label: "Submodel",
    plural: "Submodels",
    color: "#00ccff",
    icon: LayoutGridIcon,
    pkg: "comp",
    listKey: "listOfSubmodels",
  },
  {
    type: "Port",
    label: "Port",
    plural: "Ports",
    color: "#fed9a6",
    icon: LogInIcon,
    pkg: "comp",
    listKey: "listOfPorts",
  },
  {
    type: "GeneProduct",
    label: "Gene product",
    plural: "Gene products",
    color: "#d53e4f",
    icon: TagIcon,
    pkg: "fbc",
    listKey: "listOfGeneProducts",
  },
  {
    type: "Objective",
    label: "Objective",
    plural: "Objectives",
    color: "#f46d43",
    icon: TargetIcon,
    pkg: "fbc",
    listKey: "listOfObjectives",
  },
];

export const NESTED_TYPES: readonly SbmlTypeInfo<NestedElementType>[] = [
  {
    type: "SpeciesReference",
    label: "Species reference",
    plural: "Species references",
    color: "#abdda4",
    icon: CircleDotIcon,
    pkg: "core",
  },
  {
    type: "ModifierSpeciesReference",
    label: "Modifier species reference",
    plural: "Modifier species references",
    color: "#abdda4",
    icon: CircleIcon,
    pkg: "core",
  },
  {
    type: "KineticLaw",
    label: "Kinetic law",
    plural: "Kinetic laws",
    color: "#a6cee3",
    icon: CalculatorIcon,
    pkg: "core",
  },
  {
    type: "LocalParameter",
    label: "Local parameter",
    plural: "Local parameters",
    color: "#fdae61",
    icon: SlidersHorizontalIcon,
    pkg: "core",
  },
  {
    type: "Trigger",
    label: "Trigger",
    plural: "Triggers",
    color: "#fed08b",
    icon: ZapIcon,
    pkg: "core",
  },
  {
    type: "Priority",
    label: "Priority",
    plural: "Priorities",
    color: "#fed08b",
    icon: ChevronsUpIcon,
    pkg: "core",
  },
  {
    type: "Delay",
    label: "Delay",
    plural: "Delays",
    color: "#fed08b",
    icon: HourglassIcon,
    pkg: "core",
  },
  {
    type: "EventAssignment",
    label: "Event assignment",
    plural: "Event assignments",
    color: "#fed08b",
    icon: EqualIcon,
    pkg: "core",
  },
  {
    type: "Uncertainty",
    label: "Uncertainty",
    plural: "Uncertainties",
    color: "#c7c7c7",
    icon: CircleQuestionMarkIcon,
    pkg: "distrib",
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
