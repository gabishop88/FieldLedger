// -----------------------------------------------------------------------------
// Core Models
// -----------------------------------------------------------------------------

export interface JDLink {
  rel: string;
  uri: string;
}

export interface JDMeas {
  value: number;
  unit: string | null;
}

export interface JDModel {
  links: JDLink[];
}

export interface JDAuthInfo {
  authorized: boolean;
  auth_uri: string;
}

// -----------------------------------------------------------------------------
// Organization / Farm / Field Models
// -----------------------------------------------------------------------------

export interface JDOrg extends JDModel {
  id: string;
  name: string;
  member: boolean;
}

export interface JDFarm extends JDModel {
  id: string;
  name: string;
  archived: boolean;
}

export interface JDField extends JDModel {
  id: string;
  name: string;
  archived: boolean;
}

// -----------------------------------------------------------------------------
// Boundary Models
// -----------------------------------------------------------------------------

export interface JDPoint {
  lat: number;
  lon: number;
}

export interface JDRing {
  type: "interior" | "exterior";
  points: JDPoint[];
}

export interface JDPolygon {
  rings: JDRing[];
}

export interface JDBoundary extends JDModel {
  id: string;
  name: string | null;

  area: JDMeas | null;
  workableArea: JDMeas | null;

  multipolygons: JDPolygon[];

  centroid: JDPoint | null;

  archived: boolean;
  active: boolean;
  irrigated: boolean;
}

// -----------------------------------------------------------------------------
// Operation Models
// -----------------------------------------------------------------------------

export interface JDVarietyTotal {
  varietyId: string;
  name: string | null;

  area: JDMeas;

  yield: JDMeas | null;
  averageYield: JDMeas | null;

  averageMoisture: JDMeas | null;

  wetMass: JDMeas | null;
  averageWetMass: JDMeas | null;

  totalMaterial: JDMeas | null;
  averageMaterial: JDMeas | null;
}

export interface JDProductTotal {
  productId: string;
  name: string | null;
  brand: string | null;

  totalMaterial: JDMeas;
  averageMaterial: JDMeas;
}

export interface JDApplicationTotal {
  productId: string;
  name: string | null;

  area: JDMeas;

  averageSpeed: JDMeas;

  totalMaterial: JDMeas;
  averageMaterial: JDMeas;

  appliedArea: JDMeas | null;

  productTotals: JDProductTotal[];
}

export interface JDMeasurementType {
  measurementName: string;

  area: JDMeas | null;

  applicationProductTotals: JDApplicationTotal[] | null;

  totalMaterial: JDMeas | null;
  averageMaterial: JDMeas | null;

  yield: JDMeas | null;
  averageYield: JDMeas | null;

  averageMoisture: JDMeas | null;

  wetMass: JDMeas | null;
  averageWetMass: JDMeas | null;

  averageSpeed: JDMeas | null;

  averageDepth: JDMeas | null;
  averagePressure: JDMeas | null;

  varietyTotals: JDVarietyTotal[] | null;
  productTotals: JDProductTotal[] | null;
}

export interface InputMeasurements {
  guid: string;
  area: JDMeas | null;
  total: JDMeas | null;
  rate: JDMeas | null;
}

export interface OutputMeasurements {
  guid: string;
  area: JDMeas | null;
  wet_mass: JDMeas | null;
  wet_mass_rate: JDMeas | null;
  yield: JDMeas | null;
  yield_rate: JDMeas | null;
  moisture: JDMeas | null;
}

export interface JDMeasurements {
  area: JDMeas | null;
  speed: JDMeas | null;
  pressure: JDMeas | null;
  depth: JDMeas | null;

  inputs: Record<string, InputMeasurements>;
  outputs: Record<string, OutputMeasurements>;
}

export interface JDComponent {
  name: string;
  guid: string;
  productType: string;

  rate: JDMeas;
}

export interface JDProduct {
  guid: string;

  productType: string | null;

  productId: string | null;

  name: string | null;
  brand: string | null;

  tankMix: boolean;

  rate: JDMeas | null;

  carrier: JDComponent | null;
  components: JDComponent[] | null;
}

export interface JDOperationMachine {
  GUID: string;

  name: string | null;
  vin: string | null;

  machineId: number | null;
}

export interface JDTillageProduct {
  tillageType: string;
}

export interface JDFieldOp extends JDModel {
  id: string;

  fieldOperationType: string;
  adaptMachineType: string | null;

  cropSeason: number;

  startDate: string;
  endDate: string;

  cropName: string | null;

  products: JDProduct[] | null;
  measurementTypes: JDMeasurementType[] | null;
  fieldOperationMachines: JDOperationMachine[] | null;
  tillageProducts: JDTillageProduct[] | null;
  varieties: JDProduct[] | null;
}

// -----------------------------------------------------------------------------
// Resource Models
// -----------------------------------------------------------------------------

export interface JDProductDetails {
  id: string;
  name: string;
  companyName?: string;
  registration?: string;
  category: string;
  type?: string;
  restrictedUse?: boolean;
  archived?: boolean;
}
