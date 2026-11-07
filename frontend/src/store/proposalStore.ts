import { create } from "zustand";
import { Proposal, ProposalItemDecision } from "@/types";

interface ProposalState {
  activeProposal: Proposal | null;
  itemDecisions: Record<string, ProposalItemDecision>;
  isSubmitting: boolean;
  
  setProposal: (proposal: Proposal) => void;
  updateDecision: (itemId: string, patch: Partial<ProposalItemDecision>) => void;
  toggleApproval: (itemId: string) => void;
  approveAll: () => void;
  rejectAll: () => void;
  clearProposal: () => void;
  setSubmitting: (submitting: boolean) => void;
}

export const useProposalStore = create<ProposalState>((set) => ({
  activeProposal: null,
  itemDecisions: {},
  isSubmitting: false,

  setProposal: (proposal) => {
    const initialDecisions: Record<string, ProposalItemDecision> = {};
    proposal.items.forEach((item) => {
      initialDecisions[item.id] = {
        id: item.id,
        proposed_title: item.proposed_title,
        estimated_duration_min: item.estimated_duration_min,
        priority: item.priority,
        normalized_deadline_iso: item.normalized_deadline || undefined,
        is_approved: true,
      };
    });
    set({ activeProposal: proposal, itemDecisions: initialDecisions });
  },

  updateDecision: (itemId, patch) =>
    set((state) => ({
      itemDecisions: {
        ...state.itemDecisions,
        [itemId]: { ...state.itemDecisions[itemId], ...patch },
      },
    })),

  toggleApproval: (itemId) =>
    set((state) => {
      const current = state.itemDecisions[itemId];
      if (!current) return state;
      return {
        itemDecisions: {
          ...state.itemDecisions,
          [itemId]: { ...current, is_approved: !current.is_approved },
        },
      };
    }),

  approveAll: () =>
    set((state) => {
      const updated: Record<string, ProposalItemDecision> = {};
      Object.keys(state.itemDecisions).forEach((id) => {
        updated[id] = { ...state.itemDecisions[id], is_approved: true };
      });
      return { itemDecisions: updated };
    }),

  rejectAll: () =>
    set((state) => {
      const updated: Record<string, ProposalItemDecision> = {};
      Object.keys(state.itemDecisions).forEach((id) => {
        updated[id] = { ...state.itemDecisions[id], is_approved: false };
      });
      return { itemDecisions: updated };
    }),

  clearProposal: () => set({ activeProposal: null, itemDecisions: {} }),
  setSubmitting: (isSubmitting) => set({ isSubmitting }),
}));
