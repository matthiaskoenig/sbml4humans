import type { PrimeVueConfiguration } from "primevue/config";

/** Global pass through classes of the PrimeVue components in unstyled mode. */
export const primevueOptions: PrimeVueConfiguration = {
  unstyled: true,
  ptOptions: { mergeSections: true, mergeProps: true },
  pt: {
    datatable: {
      root: "text-sm",
      tableContainer: "overflow-auto",
      table: "w-full border-collapse",
      thead: "sticky top-0 z-10 bg-gray-50",
      headerRow: "border-b border-gray-200",
      bodyRow: ({ context }: { context: { selected: boolean } }) => ({
        class: [
          "cursor-pointer border-b border-gray-100",
          context.selected ? "bg-selected" : "hover:bg-gray-50",
        ],
      }),
      emptyMessage: "text-gray-500",
    },
    column: {
      headerCell: "px-3 py-2 text-left font-medium text-gray-600 whitespace-nowrap select-none",
      columnHeaderContent: "flex items-center gap-1",
      columnTitle: "",
      sort: "text-gray-400",
      sortIcon: "size-3",
      bodyCell: "px-3 py-1.5 align-top whitespace-nowrap",
    },
    select: {
      root: "inline-flex items-center gap-2 rounded border border-gray-300 bg-white px-2 py-1 text-sm hover:border-gray-400 cursor-pointer",
      label: "truncate max-w-64",
      dropdown: "flex items-center text-gray-500",
      dropdownIcon: "size-3",
      overlay: "mt-1 rounded border border-gray-200 bg-white shadow-lg text-sm",
      listContainer: "max-h-80 overflow-auto",
      list: "py-1",
      option: ({ context }: { context: { selected: boolean; focused: boolean } }) => ({
        class: [
          "px-3 py-1.5 cursor-pointer whitespace-nowrap",
          context.selected ? "bg-selected" : context.focused ? "bg-gray-100" : "hover:bg-gray-50",
        ],
      }),
      optionLabel: "",
      emptyMessage: "px-3 py-1.5 text-gray-500",
    },
    tooltip: {
      root: "absolute z-50 max-w-md",
      text: "rounded bg-gray-900 px-2 py-1 font-mono text-xs text-white shadow",
      arrow: "hidden",
    },
  },
};
