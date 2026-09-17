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
  /** PrimeIcons class without the `pi` prefix. */
  icon: string;
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
    icon: "pi-file",
    pkg: "core",
  },
  {
    type: "Model",
    label: "Model",
    plural: "Models",
    color: "#66c2a5",
    icon: "pi-sitemap",
    pkg: "core",
  },
  {
    type: "ExternalModelDefinition",
    label: "External model definition",
    plural: "External model definitions",
    color: "#66c2a5",
    icon: "pi-external-link",
    pkg: "comp",
  },
];

export const ELEMENT_TYPES: readonly ElementTypeInfo[] = [
  {
    type: "FunctionDefinition",
    label: "Function definition",
    plural: "Function definitions",
    color: "#e6f598",
    icon: "pi-code",
    pkg: "core",
    listKey: "listOfFunctionDefinitions",
  },
  {
    type: "UnitDefinition",
    label: "Unit definition",
    plural: "Unit definitions",
    color: "#f1b6da",
    icon: "pi-calculator",
    pkg: "core",
    listKey: "listOfUnitDefinitions",
  },
  {
    type: "Compartment",
    label: "Compartment",
    plural: "Compartments",
    color: "#92c5de",
    icon: "pi-box",
    pkg: "core",
    listKey: "listOfCompartments",
  },
  {
    type: "Species",
    label: "Species",
    plural: "Species",
    color: "#abdda4",
    icon: "pi-circle",
    pkg: "core",
    listKey: "listOfSpecies",
  },
  {
    type: "Parameter",
    label: "Parameter",
    plural: "Parameters",
    color: "#fdae61",
    icon: "pi-sliders-h",
    pkg: "core",
    listKey: "listOfParameters",
  },
  {
    type: "InitialAssignment",
    label: "Initial assignment",
    plural: "Initial assignments",
    color: "#fee08b",
    icon: "pi-arrow-circle-left",
    pkg: "core",
    listKey: "listOfInitialAssignments",
  },
  {
    type: "AssignmentRule",
    label: "Assignment rule",
    plural: "Assignment rules",
    color: "#fb9a99",
    icon: "pi-equals",
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "RateRule",
    label: "Rate rule",
    plural: "Rate rules",
    color: "#fb9a99",
    icon: "pi-wave-pulse",
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "AlgebraicRule",
    label: "Algebraic rule",
    plural: "Algebraic rules",
    color: "#fb9a99",
    icon: "pi-hashtag",
    pkg: "core",
    listKey: "listOfRules",
  },
  {
    type: "Constraint",
    label: "Constraint",
    plural: "Constraints",
    color: "#fdae61",
    icon: "pi-lock",
    pkg: "core",
    listKey: "listOfConstraints",
  },
  {
    type: "Reaction",
    label: "Reaction",
    plural: "Reactions",
    color: "#a6cee3",
    icon: "pi-arrow-right-arrow-left",
    pkg: "core",
    listKey: "listOfReactions",
  },
  {
    type: "Event",
    label: "Event",
    plural: "Events",
    color: "#fed08b",
    icon: "pi-clock",
    pkg: "core",
    listKey: "listOfEvents",
  },
  {
    type: "Submodel",
    label: "Submodel",
    plural: "Submodels",
    color: "#00ccff",
    icon: "pi-th-large",
    pkg: "comp",
    listKey: "listOfSubmodels",
  },
  {
    type: "Port",
    label: "Port",
    plural: "Ports",
    color: "#fed9a6",
    icon: "pi-sign-in",
    pkg: "comp",
    listKey: "listOfPorts",
  },
  {
    type: "GeneProduct",
    label: "Gene product",
    plural: "Gene products",
    color: "#d53e4f",
    icon: "pi-tag",
    pkg: "fbc",
    listKey: "listOfGeneProducts",
  },
  {
    type: "Objective",
    label: "Objective",
    plural: "Objectives",
    color: "#f46d43",
    icon: "pi-bullseye",
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
    icon: "pi-circle-fill",
    pkg: "core",
  },
  {
    type: "ModifierSpeciesReference",
    label: "Modifier species reference",
    plural: "Modifier species references",
    color: "#abdda4",
    icon: "pi-circle",
    pkg: "core",
  },
  {
    type: "KineticLaw",
    label: "Kinetic law",
    plural: "Kinetic laws",
    color: "#a6cee3",
    icon: "pi-calculator",
    pkg: "core",
  },
  {
    type: "LocalParameter",
    label: "Local parameter",
    plural: "Local parameters",
    color: "#fdae61",
    icon: "pi-sliders-h",
    pkg: "core",
  },
  {
    type: "EventAssignment",
    label: "Event assignment",
    plural: "Event assignments",
    color: "#fed08b",
    icon: "pi-equals",
    pkg: "core",
  },
  {
    type: "Uncertainty",
    label: "Uncertainty",
    plural: "Uncertainties",
    color: "#c7c7c7",
    icon: "pi-question-circle",
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
