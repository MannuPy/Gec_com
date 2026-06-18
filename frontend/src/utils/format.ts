/**
 * Formate un montant (Decimal renvoyé en string par l'API) en FCFA.
 * Ex. "12345.5" -> "12 346 FCFA"
 */
export function formatCurrency(value: string | number): string {
  const amount = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(amount)) return "-";

  return `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(amount)} FCFA`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("fr-FR").format(value);
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
