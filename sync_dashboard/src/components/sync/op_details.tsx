import { Card, DataList, Group, Loader, ScrollArea, Stack, Text } from "@mantine/core";
import { usePrepareOperation as usePrepareOp } from "../../hooks/use_sync_tree";
import type { AnySyncLink, SyncLink } from "../../types/fl";
import type { JDMeas, JDProduct, JDRing } from "../../types/jd";
import { IconArchive, IconArchiveOff, IconDroplet, IconDropletOff, IconLock, IconLockOff, IconMap2, IconMapOff } from "@tabler/icons-react";
import { useMemo } from "react";
import L from "leaflet";
import { MapContainer, GeoJSON, TileLayer } from "react-leaflet";

function formatMeasurement(val: JDMeas | null, precision: number = 2) {
  return val ? `${val.value.toFixed(precision)} ${val.unit}` : null;
}

// ------------------------------------------------------------------------------------------------
// #region --------------------------------------- DataCard ---------------------------------------
// ------------------------------------------------------------------------------------------------

type DataCardItem = {
  label: React.ReactNode;
  value: React.ReactNode;
}

interface DataCardProps {
  items: DataCardItem[];
  children?: React.ReactNode;
}

function DataCard({ items, children }: DataCardProps) {
  return <Card withBorder>
    {children}

    <DataList orientation="horizontal" labelWidth={100}>
      {items.map(({ label, value }) =>
        <DataList.Item key={String(label)}>
          <DataList.ItemLabel>{label}</DataList.ItemLabel>
          <DataList.ItemValue w="100%">{value}</DataList.ItemValue>
        </DataList.Item>
      )}
    </DataList>
  </Card>
}

// #endregion -------------------------------------------------------------------------------------
// #region ------------------------------------- FieldOpCard --------------------------------------
// ------------------------------------------------------------------------------------------------

interface OpCardProps {
  selectedOp: SyncLink<"field_op"> | null;
  title: string;
}

function FieldOpCard({ selectedOp, title }: OpCardProps) {
  function formatDate(dateString: string | undefined) {
    return dateString ? new Date(dateString).toLocaleString() : null;
  }

  function machinesInfo() {
    const machines = selectedOp?.data.fieldOperationMachines;
    const machineType = selectedOp?.data.adaptMachineType;
    return machines && machineType && <Stack>
      {machineType && <Text>{machineType}</Text>}
      {machines?.map(m => <Text key={m.GUID}>{m.name || m.vin || m.machineId || m.GUID}</Text>)}
    </Stack>;
  }

  function productsInfo() {
    const products = selectedOp?.data.products;
    const ingredients = (p: JDProduct) => [p.carrier, ...(p.components ?? [])].map(c => c?.name).join(", ");
    return products && <Stack>
      {products.map(p =>
        <Stack gap={0}>
          <Text>{p.brand} "{p.name}"</Text>
          {p.tankMix && <Text size="xs" c="dimmed">Contains: {ingredients(p)}</Text>}
        </Stack>
      )}
    </Stack>;
  }

  const data = selectedOp?.data ?? null;
  const items = [
    { label: <Text fw={700} fz="lg">Operation</Text>, value: title },
    { label: "Crop", value: data?.cropName },
    { label: "Started", value: formatDate(data?.startDate) },
    { label: "Ended", value: formatDate(data?.endDate) },
    { label: "Machines", value: machinesInfo() },
    { label: "Products", value: productsInfo() },
    { label: "Varieties", value: data?.varieties?.map(v => <Text key={v.guid}>{v.brand} "{v.name}"</Text>) },
    { label: "Tillage Type(s)", value: data?.tillageProducts?.map(t => t.tillageType) },
  ].filter(i => i.value != null);

  return <DataCard items={items} />
}

// #endregion -------------------------------------------------------------------------------------
// #region ------------------------------------- BoundaryCard -------------------------------------
// ------------------------------------------------------------------------------------------------

interface BoundaryCardProps {
  link: SyncLink<"boundary">;
  mapH?: number;
}

export function BoundaryCard({ link, mapH=150 }: BoundaryCardProps) {
  const baseMapUrl = "https://gis.apfo.usda.gov/arcgis/rest/services/NAIP/USDA_CONUS_PRIME/ImageServer/tile/{z}/{y}/{x}";
  const data = link.data;

  const exteriorFirst = (a: JDRing, b: JDRing) => Number(b.type === "exterior") - Number(a.type === "exterior");
  const geometry = useMemo(() => 
    !data ? null : {
      type: "MultiPolygon",
      coordinates: data.multipolygons.map(
        pgon => pgon.rings.toSorted(exteriorFirst).map(ring => ring.points.map(p => [p.lon, p.lat]))
      ),
    } as GeoJSON.MultiPolygon,
    [data]
  );

  const bounds = useMemo(() => L.geoJSON(geometry).getBounds(), [geometry]);

  const items = [
    { label: <Text fw={700} fz="lg">Boundary</Text>, value: data.name },
    { label: "Centroid", value: data.centroid ? `${data.centroid.lat.toFixed(6)}, ${data.centroid.lon.toFixed(6)}` : null },
    { label: "Area", value: formatMeasurement(data.area) },
    { label: "Workable Area", value: formatMeasurement(data.workableArea?.value === data.area?.value ? null : data.workableArea) },
    { label: "Active", value: data.active ? <IconMap2 color="var(--mantine-color-green-7)" /> : <IconMapOff color="var(--mantine-color-gray-6)" /> },
    { label: "Irrigated", value: data.irrigated ? <IconDroplet color="var(--mantine-color-cyan-7)" /> : <IconDropletOff color="var(--mantine-color-gray-6)" /> },
    { label: "Archived", value: data.archived ? <IconArchive color="var(--mantine-color-yellow-7)" /> : <IconArchiveOff color="var(--mantine-color-gray-6)" /> },
  ].filter(i => i.value != null);
  return <DataCard items={items}>
    <Card.Section pb="sm">
      {geometry &&
        <MapContainer
          bounds={bounds}
          key={JSON.stringify(geometry)}
          style={{ height: mapH, zIndex: "var(--mantine-z-index-app)" }}
          attributionControl={false}
          zoomControl={false}
        >
          <TileLayer url={baseMapUrl} />
          <GeoJSON data={geometry} />
        </MapContainer>
      }
    </Card.Section>
  </DataCard>
}

// #endregion -------------------------------------------------------------------------------------
// #region ------------------------------------ ProductUseCard ------------------------------------
// ------------------------------------------------------------------------------------------------

function ProductUseCard({ link, names }: { link: SyncLink<"op_input" | "op_output">, names: Map<string, string> }) {
  // TODO: I need to get the product name from the product info. It should either be in the new_org_children list
  //     OR it will be a child of the parent org, hopefully.
  const inOut = link.table_name === "op_input" ? "Input" : "Output";
  const data = link.data;
  const items = [
    { label: <Text fw={700} fz="lg">{inOut}</Text>, value: names.get(data.guid) ?? "NAME NOT FOUND" },
    { label: "Area", value: formatMeasurement(data.area) },
    { label: "Total", value: formatMeasurement("total" in data ? data.total : null) },
    { label: "Rate", value: formatMeasurement("rate" in data ? data.rate : null) },
  ].filter(i => i.value != null);
  return <DataCard items={items} />
}


// #endregion -------------------------------------------------------------------------------------
// #region ----------------------------------- ProductInfoCard ------------------------------------
// ------------------------------------------------------------------------------------------------

function ProductInfoCard({ link }: { link: SyncLink<"product"> }) {
  const data = link.data;
  const items = [
    { label: <Text fw={700} fz="lg">Product</Text>, value: data.name },
    { label: "Brand", value: data.companyName },
    { label: "Category", value: data.category },
    { label: "Specific Type", value: data.type },
    { label: "Registration", value: data.registration },
    { label: "Restricted", value: data.restrictedUse ? <IconLock color="var(--mantine-color-red-7)" /> : <IconLockOff color="var(--mantine-color-gray-6)" /> },
    { label: "Archived", value: data.archived ? <IconArchive color="var(--mantine-color-yellow-7)" /> : <IconArchiveOff color="var(--mantine-color-gray-6)" /> }
  ].filter(i => i.value != null);
  return <DataCard items={items} />
}

// #endregion -------------------------------------------------------------------------------------
// #region ----------------------------------- OperationDetails -----------------------------------
// ------------------------------------------------------------------------------------------------

export default function OperationDetails({ selectedOp, title }: OpCardProps) {
  const { data, isPending } = usePrepareOp(selectedOp?.uri);
  // TODO: Get the other products from the parent org's actual children.
  const nameMap = new Map(data?.new_org_children.map(p => [p.data.id, p.data.name]));

  function selectChildCard(item: AnySyncLink): React.ReactElement | null {
    switch (item.table_name) {
      case "boundary": return <BoundaryCard link={item} />
      case "op_input":
      case "op_output": return <ProductUseCard link={item} names={nameMap} />
      case "product": return <ProductInfoCard link={item} />
      default: return null;
    }
  }

  // TODO: change the first message when sync is active.
  // TODO: display the op/org children once they are synced
  return !selectedOp || isPending
    ? <Loader type="dots" w="100%" h="100%" />
    : <ScrollArea flex={1} miw={0} mih={0} type="auto" scrollbarSize={8}>
      <Stack p="md">
        <Text size="lg" fw={600}>This information will be synced on sync action:</Text>
        <Group><FieldOpCard selectedOp={selectedOp} title={title} /></Group>

        {!!data?.new_op_children.length && <>
          <Text size="lg" fw={600}>These will become available for sync upon syncing Operation:</Text>
          <Group align="flex-end">{data?.new_op_children.map(selectChildCard)}</Group>
        </>}

        {!!data?.new_org_children.length && <>
          <Text size="lg" fw={600}>These will become available under the parent Organization upon syncing Operation:</Text>
          <Group>{data?.new_org_children.map(selectChildCard)}</Group>
        </>}
      </Stack>
    </ScrollArea>
}
