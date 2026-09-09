"use client";

import { useState } from "react";

export function ShareButton({ title, text }: { title: string; text: string }) {
  const [status, setStatus] = useState("");

  async function share() {
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ title, text, url });
        setStatus("Compartilhado.");
      } else {
        await navigator.clipboard.writeText(`${text} ${url}`);
        setStatus("Link e contexto copiados.");
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setStatus("Não foi possível compartilhar.");
    }
  }

  return (
    <span className="share-control">
      <button className="text-button" type="button" onClick={() => void share()}>
        Compartilhar estes dados
      </button>
      {status && <span className="small-text" role="status">{status}</span>}
    </span>
  );
}
