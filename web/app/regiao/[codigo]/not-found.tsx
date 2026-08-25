import Link from "next/link";

export default function RegionNotFound() {
  return (
    <div className="not-found-panel">
      <p className="eyebrow">Perfil da Região de Saúde</p>
      <h1>Região de Saúde não encontrada.</h1>
      <p className="small-text">O código informado não corresponde a uma Região de Saúde neste release.</p>
      <Link className="button" href="/">
        Voltar para explorar o Brasil
      </Link>
    </div>
  );
}
