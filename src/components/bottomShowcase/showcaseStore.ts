import { create } from 'zustand';

interface ShowcaseState {
  activeCardId: string | null;
  hoveredCardId: string | null;
  isModalOpen: boolean;
  setActiveCard: (id: string | null) => void;
  setHoveredCard: (id: string | null) => void;
  openModal: (id: string) => void;
  closeModal: () => void;
}

export const useShowcaseStore = create<ShowcaseState>((set) => ({
  activeCardId: null,
  hoveredCardId: null,
  isModalOpen: false,
  setActiveCard: (id) => set({ activeCardId: id }),
  setHoveredCard: (id) => set({ hoveredCardId: id }),
  openModal: (id) => set({ activeCardId: id, isModalOpen: true }),
  closeModal: () => set({ activeCardId: null, isModalOpen: false }),
}));
