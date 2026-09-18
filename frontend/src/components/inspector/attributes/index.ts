import type { Component } from "vue";

import type { SbmlType } from "@/api/types";

import AlgebraicRuleAttributes from "./AlgebraicRuleAttributes.vue";
import AssignmentRuleAttributes from "./AssignmentRuleAttributes.vue";
import CompartmentAttributes from "./CompartmentAttributes.vue";
import ConstraintAttributes from "./ConstraintAttributes.vue";
import DelayAttributes from "./DelayAttributes.vue";
import EventAssignmentAttributes from "./EventAssignmentAttributes.vue";
import EventAttributes from "./EventAttributes.vue";
import ExternalModelDefinitionAttributes from "./ExternalModelDefinitionAttributes.vue";
import FunctionDefinitionAttributes from "./FunctionDefinitionAttributes.vue";
import GeneProductAttributes from "./GeneProductAttributes.vue";
import InitialAssignmentAttributes from "./InitialAssignmentAttributes.vue";
import KineticLawAttributes from "./KineticLawAttributes.vue";
import LocalParameterAttributes from "./LocalParameterAttributes.vue";
import ModelAttributes from "./ModelAttributes.vue";
import ModifierSpeciesReferenceAttributes from "./ModifierSpeciesReferenceAttributes.vue";
import ObjectiveAttributes from "./ObjectiveAttributes.vue";
import ParameterAttributes from "./ParameterAttributes.vue";
import PortAttributes from "./PortAttributes.vue";
import PriorityAttributes from "./PriorityAttributes.vue";
import RateRuleAttributes from "./RateRuleAttributes.vue";
import ReactionAttributes from "./ReactionAttributes.vue";
import SBMLDocumentAttributes from "./SBMLDocumentAttributes.vue";
import SpeciesAttributes from "./SpeciesAttributes.vue";
import SpeciesReferenceAttributes from "./SpeciesReferenceAttributes.vue";
import SubmodelAttributes from "./SubmodelAttributes.vue";
import TriggerAttributes from "./TriggerAttributes.vue";
import UncertaintyAttributes from "./UncertaintyAttributes.vue";
import UnitDefinitionAttributes from "./UnitDefinitionAttributes.vue";

/** The type specific attributes component of every SBML type, each taking `element`. */
export const ATTRIBUTE_COMPONENTS: Readonly<Record<SbmlType, Component>> = {
  SBMLDocument: SBMLDocumentAttributes,
  Model: ModelAttributes,
  ExternalModelDefinition: ExternalModelDefinitionAttributes,
  FunctionDefinition: FunctionDefinitionAttributes,
  UnitDefinition: UnitDefinitionAttributes,
  Compartment: CompartmentAttributes,
  Species: SpeciesAttributes,
  Parameter: ParameterAttributes,
  InitialAssignment: InitialAssignmentAttributes,
  AssignmentRule: AssignmentRuleAttributes,
  RateRule: RateRuleAttributes,
  AlgebraicRule: AlgebraicRuleAttributes,
  Constraint: ConstraintAttributes,
  Reaction: ReactionAttributes,
  Event: EventAttributes,
  Submodel: SubmodelAttributes,
  Port: PortAttributes,
  GeneProduct: GeneProductAttributes,
  Objective: ObjectiveAttributes,
  SpeciesReference: SpeciesReferenceAttributes,
  ModifierSpeciesReference: ModifierSpeciesReferenceAttributes,
  KineticLaw: KineticLawAttributes,
  LocalParameter: LocalParameterAttributes,
  Trigger: TriggerAttributes,
  Priority: PriorityAttributes,
  Delay: DelayAttributes,
  EventAssignment: EventAssignmentAttributes,
  Uncertainty: UncertaintyAttributes,
};
