// Marketplace taxonomy (mirrors backend app/models/enums.py). Drives the sell
// form, filters and labels for devices, components and materials.

export const KINDS = [
  { value: 'device', label: 'Device' },
  { value: 'component', label: 'Component' },
  { value: 'material', label: 'Material' },
];

export const CATEGORIES = {
  device: ['smartphone', 'laptop', 'tablet'],
  component: ['cpu', 'gpu', 'ram', 'motherboard', 'storage', 'cooler', 'other'],
  material: ['rare_earth', 'silicon', 'copper', 'aluminium', 'gold', 'other'],
};

export const UNITS = ['g', 'kg', 'tonne', 'piece'];

const LABELS = {
  smartphone: 'Smartphone', laptop: 'Laptop', tablet: 'Tablet',
  cpu: 'CPU', gpu: 'Graphics Card (GTX/RTX)', ram: 'RAM',
  motherboard: 'Motherboard', storage: 'Secondary Storage', cooler: 'Cooler (CPU/Liquid)',
  rare_earth: 'Rare-earth metals', silicon: 'Silicon', copper: 'Copper',
  aluminium: 'Aluminium', gold: 'Gold', other: 'Other',
};
export const categoryLabel = (c) => LABELS[c] || c;

const KIND_LABELS = { device: 'Device', component: 'Component', material: 'Material' };
export const kindLabel = (k) => KIND_LABELS[k] || k;
