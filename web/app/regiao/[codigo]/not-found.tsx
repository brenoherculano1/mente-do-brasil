import Link from "next/link";

export default function RegionNotFound() {
  return (
    <div className="not-found-panel">
      <p className="eyebrow">Perfil da Região de Saúde</p>
      <h1>Região de Saúde não encontrada.</h1>
      <p className="small-text">A região informada não foi encontrada nos dados disponíveis.</p>
      <Link className="button" href="/">
        Voltar para explorar o Brasil
      </Link>
    </div>
  );
}
