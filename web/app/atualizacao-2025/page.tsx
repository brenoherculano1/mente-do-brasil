import { EditionGate } from "@/features/availability/EditionGate";

export const dynamic = "force-dynamic";

export default function UpdateStatusPage() {
  return <EditionGate year="2025" context="Mapa" />;
}
