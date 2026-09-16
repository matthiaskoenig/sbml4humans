<script setup lang="ts">
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import { computed } from "vue";

import type { SbmlElement, ElementType } from "@/api/types";
import ElementCell from "@/components/report/ElementCell.vue";
import { columnsOf } from "@/report/columns";
import { useReportView } from "@/report/view";

const VIRTUAL_ROWS = 200;
const ROW_HEIGHT = 36;

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
    >
      <template #body="{ data }">
        <ElementCell :row="data as SbmlElement" :column="column" />
      </template>
    </Column>
  </DataTable>
</template>
