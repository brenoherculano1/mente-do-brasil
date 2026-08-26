import Link from "next/link";

export default function StateNotFound() {
  return (
    <div className="not-found-panel">
      <p className="eyebrow">Estado</p>
      <h1>Estado não encontrado.</h1>
      <p className="small-text">A UF informada não corresponde a uma UF válida neste release.</p>
      <Link className="button" href="/">
        Voltar para explorar o Brasil
      </Link>
    </div>
  );
}
