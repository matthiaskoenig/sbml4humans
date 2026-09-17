<script setup lang="ts">
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import { computed } from "vue";

import type { SbmlElement, ElementType } from "@/api/types";
import ElementCell from "@/components/report/ElementCell.vue";
import { columnsOf } from "@/report/columns";
import { useReportView } from "@/report/view";

const VIRTUAL_ROWS = 200;
/** The height of a virtualised row. The scroller places every row at `index * itemSize`,
 * so the row has to be exactly this high; a cell with a one line KaTeX fraction measures
 * 34 px, which leaves the 36 px of the scroller without clipping it. */
const ROW_HEIGHT = 36;

/** A virtualised row is pinned to `ROW_HEIGHT`: the padding of the cell moves into the
 * wrapper, which clips content taller than one line, for example a nested fraction. The
 * wrapper leaves the 1 px bottom border of the row, so the row measures `ROW_HEIGHT`. */
const VIRTUAL_CELL = { style: { paddingTop: "0px", paddingBottom: "0px" } };
const VIRTUAL_CONTENT = { height: `${ROW_HEIGHT - 1}px` };

const props = defineProps<{ type: ElementType; rows: SbmlElement[] }>();
const view = useReportView();

const columns = computed(() => columnsOf(props.type));
const selected = computed(() => props.rows.find((row) => row.pk === view.state.value.pk) ?? null);
const virtual = computed(() => props.rows.length > VIRTUAL_ROWS);

/** The row element carries its pk: PrimeVue passes the BodyRow instance, whose `rowData`
 * prop is the row, to the `bodyRow` pass through section. */
const rowPk = ({ instance }: { instance: { rowData?: SbmlElement } }) => ({
  "data-pk": instance.rowData?.pk,
});

function onSelect(row: SbmlElement | null): void {
  void view.select(row ? row.pk : null);
}
</script>

<template>
  <DataTable
    :value="rows"
    data-key="pk"
    selection-mode="single"
    :selection="selected"
    :meta-key-selection="false"
    :scrollable="virtual"
    :scroll-height="virtual ? `${ROW_HEIGHT * 15}px` : undefined"
    :virtual-scroller-options="virtual ? { itemSize: ROW_HEIGHT } : undefined"
    :pt="{ bodyRow: rowPk }"
    :data-testid="`table-${type}`"
    @update:selection="onSelect"
  >
    <Column
      v-for="column in columns"
      :key="column.field"
      :field="column.field"
      :header="column.header"
      :sortable="column.kind !== 'math' && column.kind !== 'units'"
      :style="column.width ? { width: column.width } : undefined"
      :pt="virtual ? { bodyCell: VIRTUAL_CELL } : undefined"
    >
      <template #body="{ data }">
        <div
          v-if="virtual"
          class="flex items-center overflow-hidden"
          :style="VIRTUAL_CONTENT"
          data-testid="virtual-cell"
        >
          <ElementCell :row="data as SbmlElement" :column="column" />
        </div>
        <ElementCell v-else :row="data as SbmlElement" :column="column" />
      </template>
    </Column>
  </DataTable>
</template>
