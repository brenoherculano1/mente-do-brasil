const FLAG_COPY: Record<string, string> = {
  SMALL_SUICIDE_COUNT:
    "Pouco número de óbitos por suicídio no período agregado; a estimativa deve ser interpretada com cautela.",
  ZERO_REGISTERED_BEDS:
    "Nenhum leito SUS deste tipo foi registrado na medida utilizada. Isso não implica necessariamente ausência de acesso regional por referência para outros territórios.",
};

export function DataQualityNotice({ flags }: { flags: string[] }) {
  const knownFlags = flags.filter((flag) => FLAG_COPY[flag]);
  if (knownFlags.length === 0) return null;
  return (
    <div className="profile-section">
      <h2>Observações sobre os dados</h2>
      {knownFlags.map((flag) => (
        <div className="notice" key={flag}>
          {FLAG_COPY[flag]}
        </div>
      ))}
    </div>
  );
}
