"use client";

import { useEffect, useState } from "react";

export function SharePanel({ title, text }: { title: string; text: string }) {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => setUrl(window.location.href), []);

  async function copy() {
    try {
      await navigator.clipboard.writeText(`${text}\n${url || window.location.href}`);
      setStatus("Texto e link copiados.");
    } catch {
      setStatus("Não foi possível copiar.");
    }
  }

  async function share() {
    if (!navigator.share) {
      await copy();
      return;
    }
    try {
      await navigator.share({ title, text, url: url || window.location.href });
      setStatus("Compartilhado.");
    } catch (error) {
      if (!(error instanceof DOMException && error.name === "AbortError")) {
        setStatus("Não foi possível compartilhar.");
      }
    }
  }

  const whatsappText = encodeURIComponent(`${text}\n${url}`);

  return (
    <section className="share-panel" aria-labelledby="share-panel-title">
      <div>
        <p className="eyebrow">Divulgação responsável</p>
        <h2 id="share-panel-title">Compartilhe estes dados</h2>
        <p>Envie a leitura com seu contexto e com o link para a fonte.</p>
      </div>
      <div className="share-panel-actions">
        <button className="primary-button" type="button" onClick={() => void share()}>
          Compartilhar
        </button>
        <a
          className="text-button"
          href={url ? `https://wa.me/?text=${whatsappText}` : undefined}
          target="_blank"
          rel="noreferrer"
          aria-disabled={!url}
        >
          Enviar pelo WhatsApp
        </a>
        <button className="text-button" type="button" onClick={() => void copy()}>
          Copiar texto e link
        </button>
      </div>
      {status && <p className="small-text share-status" role="status">{status}</p>}
    </section>
  );
}
