export function validateTradeItemDraft(quantity: number, unitValue: string): string | null {
  if (!Number.isSafeInteger(quantity) || quantity < 1) {
    return "Informe uma quantidade inteira maior que zero.";
  }
  if (!/^\d+(?:\.\d{1,2})?$/.test(unitValue) || !Number.isFinite(Number(unitValue))) {
    return "Informe um valor unitário válido, não negativo e com até duas casas decimais.";
  }
  return null;
}
