import { useConfirmStore } from "@/stores/confirm";

export function useConfirm() {
  const store = useConfirmStore();
  function confirmDelete(title: string, description: string, confirmLabel = "Eliminar") {
    return store.ask(title, description, confirmLabel);
  }
  return { confirmDelete };
}
