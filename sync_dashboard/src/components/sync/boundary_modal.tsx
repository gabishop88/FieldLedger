import { useMemo } from "react";
import L from "leaflet"

import type { SyncLink } from "../../types/fl";
import type { JDBoundary } from "../../types/jd";
import { Badge, Card, DataList, Divider, Group, Modal, Stack, Text } from "@mantine/core";
import { MapContainer, GeoJSON, TileLayer } from "react-leaflet";
import UpdateStatusActions from "./status_actions";
import { statusDetails } from "./status_info";

interface Props {
  boundary: SyncLink<JDBoundary> | null;
  onClose: () => void;
}

export default function BoundaryModal({ boundary, onClose }: Props) {
  const baseMapUrl = "https://gis.apfo.usda.gov/arcgis/rest/services/NAIP/USDA_CONUS_PRIME/ImageServer/tile/{z}/{y}/{x}";
  const geometry = useMemo(
    () => !!boundary ? ({
      type: "MultiPolygon",
      coordinates: boundary?.data.multipolygons.map(polygon => [
        ...polygon.rings.filter((r) => r.type === "exterior").map(
          ring => ring.points.map(p => [p.lon, p.lat])
        ),
        ...polygon.rings.filter((r) => r.type === "interior").map(
          ring => ring.points.map(p => [p.lon, p.lat])
        ),
      ]),
    }) as GeoJSON.MultiPolygon : undefined,
    [boundary]
  );
  const bounds = useMemo(() => L.geoJSON(geometry).getBounds(), [geometry]);

  const showWorkable = 
    boundary?.data.area?.value !== boundary?.data.area?.value ||
    boundary?.data.area?.unit !== boundary?.data.area?.unit

  const statusInfo = statusDetails[boundary?.status || "Unsynced"];

  return !boundary 
    ? <Modal opened={false} onClose={onClose} />
    : <Modal opened onClose={onClose} title={boundary?.data.name ?? "Boundary"} size="lg">
    <Stack gap="md">
      {geometry && bounds && 
        <Card withBorder radius="md" p={0} style={{ overflow: "hidden" }}>
          <MapContainer bounds={bounds} style={{ height: 350 }} scrollWheelZoom={false}>
              <TileLayer url={baseMapUrl} />

              <GeoJSON data={geometry} />
          </MapContainer>
        </Card>
      }

      <Card withBorder radius="md">
        <Stack gap="sm">
          <Text span fw={500} size="lg">Details</Text>

          <Divider />

          <DataList>
            <DataList.Item>
              <DataList.ItemLabel>Name</DataList.ItemLabel>
              <DataList.ItemValue>{boundary?.data.name}</DataList.ItemValue>
            </DataList.Item>

            <DataList.Item>
              <DataList.ItemLabel>Area</DataList.ItemLabel>
              <DataList.ItemValue>
                {`${boundary?.data.area?.value.toFixed(2)} ${boundary?.data.area?.unit}`}
              </DataList.ItemValue>
            </DataList.Item>

            {showWorkable && 
              <DataList.Item>
                <DataList.ItemLabel>Workable</DataList.ItemLabel>
                <DataList.ItemValue>
                  {`${boundary?.data.workableArea?.value.toFixed(2)} ${boundary?.data.workableArea?.unit}`}
                </DataList.ItemValue>
              </DataList.Item>
            }

            <DataList.Item>
              <DataList.ItemLabel>Centroid</DataList.ItemLabel>
              <DataList.ItemValue>
                {`${boundary?.data.centroid?.lat.toFixed(6)}, ${boundary?.data.centroid?.lon.toFixed(6)}`}
              </DataList.ItemValue>
            </DataList.Item>
          </DataList>

          <Group gap="xs" pt="sm">
            <Badge color={boundary?.data.active ? "green" : "gray"}>
              {boundary?.data.active ? "Active" : "Inactive"}
            </Badge>

            <Badge color={boundary?.data.archived ? "orange" : "gray"}>
              {boundary?.data.archived ? "Archived" : "Not Archived"}
            </Badge>

            <Badge color={boundary?.data.irrigated ? "cyan": "gray"}>
              {boundary?.data.irrigated ? "Irrigated" : "Not Irrigated"}
            </Badge>
          </Group>

        </Stack>
      </Card>

      <Group justify="space-between">
        <Badge color={statusInfo.color} leftSection={<statusInfo.icon size={16}/>}>{boundary.status}</Badge>

        <Group>
          <Text>Actions:</Text>

          <UpdateStatusActions node={boundary} />
        </Group>
      </Group>
    </Stack>
  </Modal>
}

// import { useMemo } from "react";
// import {
//   Group,
//   Modal,
//   Paper,
//   Stack,
//   Text,
// } from "@mantine/core";
// import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
// import L from "leaflet";
// import "leaflet/dist/leaflet.css";

// import UpdateStatusActions from "./status_actions";
// import type { SyncLink } from "../../types/fl";
// import type { JDBoundary } from "../../types/jd";

// interface Props {
//   boundary: SyncLink<JDBoundary> | null;
//   onClose: () => void;
// }

// export default function BoundaryModal({ boundary, onClose }: Props) {
//   if (!boundary) {
//     return <Modal opened={false} onClose={onClose} />;
//   }

//   const baseMapUrl = "https://gis.apfo.usda.gov/arcgis/rest/services/NAIP/USDA_CONUS_PRIME/ImageServer/tile/{z}/{y}/{x}"

//   const geometry = useMemo(() => {
//     const data = boundary.data;
//     return {
//       type: "MultiPolygon",
//       coordinates: data.multipolygons.map((polygon: any) => [
//         ...polygon.rings
//           .filter((ring: any) => ring.type === "exterior")
//           .map((ring: any) =>
//             ring.points.map((point: any) => [point.lon, point.lat])
//           ),
//         ...polygon.rings
//           .filter((ring: any) => ring.type !== "exterior")
//           .map((ring: any) =>
//             ring.points.map((point: any) => [point.lon, point.lat])
//           ),
//       ]),
//     };
//   }, [boundary]);

//   const bounds = useMemo(() => {
//     return L.geoJSON(geometry).getBounds();
//   }, [geometry]);

//   const data = boundary.data;

//   return <Modal opened onClose={onClose} title={data.name} size="lg">
//     <Stack>

//       <Paper withBorder radius="0.5rem">
//         <MapContainer
//           bounds={bounds}
//           style={{ height: 350, borderRadius: "0.5rem" }}
//           scrollWheelZoom={false}
//         >
//           <TileLayer url={baseMapUrl} />

//           <GeoJSON data={geometry} />
//         </MapContainer>
//       </Paper>

//       <Paper withBorder p="md">
//         <Text fw={600} mb="sm">
//           Details
//         </Text>

//         <Stack gap={4}>
//           <Text>Name: {String(data.name)}</Text>
//           <Text>
//             Area: {data.area?.value.toFixed(2)} {data.area?.unit}
//           </Text>
//           <Text>
//             Workable Area: {data.workableArea?.value.toFixed(2)}{" "}{data.workableArea?.unit}
//           </Text>
//           <Text>
//             Irrigated: {data.irrigated ? "Yes" : "No"}
//           </Text>
//           <Text>
//             Active: {data.active ? "Yes" : "No"}
//           </Text>
//           <Text>
//             Archived: {data.archived ? "Yes" : "No"}
//           </Text>
//           <Text>
//             Centroid: {data.centroid?.lat.toFixed(6)},{" "}{data.centroid?.lon.toFixed(6)}
//           </Text>
//         </Stack>
//       </Paper>

//       <Group>
//         <Text>Actions:</Text>
//         <UpdateStatusActions node={boundary} />
//       </Group>

//     </Stack>
//   </Modal>;
// }
 