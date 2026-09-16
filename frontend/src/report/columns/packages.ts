import type { ElementType } from "@/api/types";
import { ID_COLUMNS, type ColumnDef } from "@/report/columns/types";

type PackageType = Extract<ElementType, "Submodel" | "Port" | "GeneProduct" | "Objective">;

export const PACKAGE_COLUMNS: Readonly<Record<PackageType, readonly ColumnDef[]>> = {
  Submodel: [
    ...ID_COLUMNS,
    { field: "modelRef", header: "model", kind: "link", link: "modelRef" },
    {
      field: "timeConversionFactor",
      header: "time conversion factor",
      kind: "link",
      link: "conversionFactor",
    },
    {
      field: "extentConversionFactor",
      header: "extent conversion factor",
      kind: "link",
      link: "conversionFactor",
    },
    { field: "listOfDeletions.length", header: "deletions", kind: "count" },
  ],
  Port: [
    ...ID_COLUMNS,
    { field: "portRef", header: "port ref", kind: "link", link: "port" },
    { field: "idRef", header: "id ref", kind: "link", link: "port" },
    { field: "unitRef", header: "unit ref", kind: "link", link: "port" },
    { field: "metaIdRef", header: "meta id ref", kind: "text" },
  ],
  GeneProduct: [
    ...ID_COLUMNS,
    { field: "label", header: "label", kind: "text" },
    {
      field: "associatedSpecies",
      header: "associated species",
      kind: "link",
      link: "associatedSpecies",
    },
  ],
  Objective: [
    ...ID_COLUMNS,
    { field: "type", header: "type", kind: "text" },
    { field: "listOfFluxObjectives.length", header: "flux objectives", kind: "count" },
  ],
};
