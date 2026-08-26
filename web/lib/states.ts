export const STATE_NAMES = {
  AC: "Acre",
  AL: "Alagoas",
  AP: "Amapá",
  AM: "Amazonas",
  BA: "Bahia",
  CE: "Ceará",
  DF: "Distrito Federal",
  ES: "Espírito Santo",
  GO: "Goiás",
  MA: "Maranhão",
  MT: "Mato Grosso",
  MS: "Mato Grosso do Sul",
  MG: "Minas Gerais",
  PA: "Pará",
  PB: "Paraíba",
  PR: "Paraná",
  PE: "Pernambuco",
  PI: "Piauí",
  RJ: "Rio de Janeiro",
  RN: "Rio Grande do Norte",
  RS: "Rio Grande do Sul",
  RO: "Rondônia",
  RR: "Roraima",
  SC: "Santa Catarina",
  SP: "São Paulo",
  SE: "Sergipe",
  TO: "Tocantins",
} as const;

export type Uf = keyof typeof STATE_NAMES;

export const VALID_UFS = Object.keys(STATE_NAMES) as Uf[];

export function normalizeUf(value: string) {
  return value.trim().toUpperCase();
}

export function isValidUf(value: string): value is Uf {
  return VALID_UFS.includes(value as Uf);
}

export function stateNameForUf(uf: string) {
  return STATE_NAMES[uf as Uf] ?? uf;
}
