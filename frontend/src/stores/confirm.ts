import { defineStore } from "pinia";

interface ConfirmState {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  resolveFn: ((value: boolean) => void) | null;
}

export const useConfirmStore = defineStore("confirm", {
  state: (): ConfirmState => ({
    open: false,
    title: "",
    description: "",
    confirmLabel: "Eliminar",
    resolveFn: null,
  }),
  actions: {
    ask(title: string, description: string, confirmLabel = "Eliminar"): Promise<boolean> {
      this.title = title;
      this.description = description;
      this.confirmLabel = confirmLabel;
      this.open = true;
      return new Promise((resolve) => {
        this.resolveFn = resolve;
      });
    },
    resolve(value: boolean) {
      this.open = false;
      if (this.resolveFn) {
        this.resolveFn(value);
        this.resolveFn = null;
      }
    },
  },
});
