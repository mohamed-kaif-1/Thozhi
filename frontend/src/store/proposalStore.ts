import { create } from "zustand";
import { Proposal, ProposalItemDecision, CaptureRecord } from "@/types";
import {
  listCaptures,
  listProposals,
  getCapture,
  getProposal,
  submitProposalApproval,
  rejectProposal as apiRejectProposal,
  clearCaptures as apiClearCaptures,
  ApprovalResponse,
} from "@/lib/api";

export type FilterStatus = "ALL" | "PENDING_REVIEW" | "COMMITTED" | "REJECTED";

interface ProposalState {
  captures: CaptureRecord[];
  proposals: Proposal[];
  activeProposalId: string | null;
  activeCaptureId: string | null;
  activeProposal: Proposal | null;
  itemDecisions: Record<string, ProposalItemDecision>;
  filterStatus: FilterStatus;
  isLoadingQueue: boolean;
  isSubmitting: boolean;

  // Actions
  loadInitialQueue: () => Promise<void>;
  setProposal: (proposal: Proposal) => void;
  setProposalLanguage: (proposal: Proposal) => void;
  selectCapture: (captureId: string) => Promise<void>;
  selectProposal: (proposalId: string) => Promise<void>;
  updateDecision: (itemId: string, patch: Partial<ProposalItemDecision>) => void;
  toggleApproval: (itemId: string) => void;
  approveAll: () => void;
  rejectAll: () => void;
  commitActiveProposal: () => Promise<ApprovalResponse | null>;
  rejectActiveProposal: (reason?: string) => Promise<Proposal | null>;
  clearProposal: () => void;
  clearHistory: () => Promise<void>;
  setFilterStatus: (filter: FilterStatus) => void;
  setSubmitting: (submitting: boolean) => void;
}

const initializeItemDecisions = (
  proposal: Proposal,
  existingDecisions: Record<string, ProposalItemDecision>
): Record<string, ProposalItemDecision> => {
  const updated = { ...existingDecisions };
  proposal.items.forEach((item) => {
    if (!updated[item.id]) {
      updated[item.id] = {
        id: item.id,
        proposed_title: item.proposed_title,
        estimated_duration_min: item.estimated_duration_min,
        priority: item.priority,
        normalized_deadline_iso: item.normalized_deadline || undefined,
        is_approved: true,
      };
    }
  });
  return updated;
};

export const useProposalStore = create<ProposalState>((set, get) => ({
  captures: [],
  proposals: [],
  activeProposalId: null,
  activeCaptureId: null,
  activeProposal: null,
  itemDecisions: {},
  filterStatus: "ALL",
  isLoadingQueue: false,
  isSubmitting: false,

  loadInitialQueue: async () => {
    set({ isLoadingQueue: true });
    try {
      const [fetchedCaptures, fetchedProposals] = await Promise.all([
        listCaptures().catch(() => []),
        listProposals().catch(() => []),
      ]);

      const state = get();
      let newActiveProposal: Proposal | null = state.activeProposal;
      let newActiveProposalId: string | null = state.activeProposalId;
      let newActiveCaptureId: string | null = state.activeCaptureId;

      // If activeProposal is not set or not in list, pick the first pending proposal or the latest proposal
      if (!newActiveProposal && fetchedProposals.length > 0) {
        const pending = fetchedProposals.find((p) => p.status === "PENDING_REVIEW");
        const chosen = pending || fetchedProposals[0];
        newActiveProposal = chosen;
        newActiveProposalId = chosen.id;
        newActiveCaptureId = chosen.capture_id || null;
      }

      // Initialize decisions for all proposals
      let mergedDecisions = { ...state.itemDecisions };
      fetchedProposals.forEach((p) => {
        mergedDecisions = initializeItemDecisions(p, mergedDecisions);
      });

      set({
        captures: fetchedCaptures,
        proposals: fetchedProposals,
        activeProposal: newActiveProposal,
        activeProposalId: newActiveProposalId,
        activeCaptureId: newActiveCaptureId,
        itemDecisions: mergedDecisions,
      });
    } catch (err) {
      console.error("Failed to load proposal queue:", err);
    } finally {
      set({ isLoadingQueue: false });
    }
  },

  setProposal: (proposal) => {
    set((state) => {
      const updatedDecisions = initializeItemDecisions(proposal, state.itemDecisions);
      const existingIdx = state.proposals.findIndex((p) => p.id === proposal.id);
      let updatedProposals: Proposal[];
      if (existingIdx >= 0) {
        updatedProposals = [...state.proposals];
        updatedProposals[existingIdx] = proposal;
      } else {
        updatedProposals = [proposal, ...state.proposals];
      }

      return {
        proposals: updatedProposals,
        activeProposal: proposal,
        activeProposalId: proposal.id,
        activeCaptureId: proposal.capture_id || null,
        itemDecisions: updatedDecisions,
      };
    });
    // Also trigger queue refresh in background to pick up the updated captures
    get().loadInitialQueue();
  },

  setProposalLanguage: (proposal) => {
    set((state) => {
      const updatedDecisions = { ...state.itemDecisions };
      proposal.items.forEach((item) => {
        const existing = updatedDecisions[item.id];
        if (existing) {
          updatedDecisions[item.id] = {
            ...existing,
            proposed_title: item.proposed_title,
          };
        } else {
          updatedDecisions[item.id] = {
            id: item.id,
            proposed_title: item.proposed_title,
            estimated_duration_min: item.estimated_duration_min,
            priority: item.priority,
            normalized_deadline_iso: item.normalized_deadline || undefined,
            is_approved: true,
          };
        }
      });

      const existingIdx = state.proposals.findIndex((p) => p.id === proposal.id);
      const updatedProposals = [...state.proposals];
      if (existingIdx >= 0) {
        updatedProposals[existingIdx] = proposal;
      }

      return {
        activeProposal: proposal,
        proposals: updatedProposals,
        itemDecisions: updatedDecisions,
      };
    });
  },

  selectCapture: async (captureId) => {
    const state = get();
    set({ activeCaptureId: captureId });

    // Find proposal linked to capture
    let matchingProposal = state.proposals.find((p) => p.capture_id === captureId);

    if (!matchingProposal) {
      try {
        const cap = await getCapture(captureId);
        if (cap.proposals && cap.proposals.length > 0) {
          matchingProposal = cap.proposals[0];
        }
      } catch (e) {
        console.warn("Could not fetch capture details:", e);
      }
    }

    if (matchingProposal) {
      const updatedDecisions = initializeItemDecisions(matchingProposal, state.itemDecisions);
      set({
        activeProposal: matchingProposal,
        activeProposalId: matchingProposal.id,
        itemDecisions: updatedDecisions,
      });
    }
  },

  selectProposal: async (proposalId) => {
    const state = get();
    let prop = state.proposals.find((p) => p.id === proposalId);
    if (!prop) {
      try {
        prop = await getProposal(proposalId);
      } catch (e) {
        console.warn("Could not fetch proposal:", e);
      }
    }

    if (prop) {
      const updatedDecisions = initializeItemDecisions(prop, state.itemDecisions);
      set({
        activeProposal: prop,
        activeProposalId: prop.id,
        activeCaptureId: prop.capture_id || null,
        itemDecisions: updatedDecisions,
      });
    }
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
      if (!state.activeProposal) return state;
      const updated = { ...state.itemDecisions };
      state.activeProposal.items.forEach((item) => {
        if (updated[item.id]) {
          updated[item.id] = { ...updated[item.id], is_approved: true };
        }
      });
      return { itemDecisions: updated };
    }),

  rejectAll: () =>
    set((state) => {
      if (!state.activeProposal) return state;
      const updated = { ...state.itemDecisions };
      state.activeProposal.items.forEach((item) => {
        if (updated[item.id]) {
          updated[item.id] = { ...updated[item.id], is_approved: false };
        }
      });
      return { itemDecisions: updated };
    }),

  commitActiveProposal: async () => {
    const state = get();
    if (!state.activeProposal) return null;

    set({ isSubmitting: true });
    try {
      const activeItems = state.activeProposal.items;
      const decisions = activeItems.map((item) => state.itemDecisions[item.id] || {
        id: item.id,
        is_approved: true,
      });

      const res = await submitProposalApproval(state.activeProposal.id, decisions);

      // Update active proposal status to COMMITTED
      const committedProposal: Proposal = {
        ...state.activeProposal,
        status: "COMMITTED",
      };

      const updatedProposals = state.proposals.map((p) =>
        p.id === committedProposal.id ? committedProposal : p
      );

      // Look for next pending review proposal
      const nextPending = updatedProposals.find(
        (p) => p.id !== committedProposal.id && p.status === "PENDING_REVIEW"
      );

      set({
        activeProposal: nextPending || committedProposal,
        activeProposalId: nextPending ? nextPending.id : committedProposal.id,
        activeCaptureId: nextPending ? (nextPending.capture_id || null) : (committedProposal.capture_id || null),
        proposals: updatedProposals,
      });

      // Reload captures to get fresh lifecycle_status
      const freshCaptures = await listCaptures().catch(() => state.captures);
      set({ captures: freshCaptures });

      return res;
    } finally {
      set({ isSubmitting: false });
    }
  },

  rejectActiveProposal: async (reason?: string) => {
    const state = get();
    if (!state.activeProposal) return null;

    set({ isSubmitting: true });
    try {
      const rejectedProp = await apiRejectProposal(state.activeProposal.id, reason);

      const updatedProposals = state.proposals.map((p) =>
        p.id === rejectedProp.id ? rejectedProp : p
      );

      // Look for next pending review proposal
      const nextPending = updatedProposals.find(
        (p) => p.id !== rejectedProp.id && p.status === "PENDING_REVIEW"
      );

      set({
        activeProposal: nextPending || rejectedProp,
        activeProposalId: nextPending ? nextPending.id : rejectedProp.id,
        activeCaptureId: nextPending ? (nextPending.capture_id || null) : (rejectedProp.capture_id || null),
        proposals: updatedProposals,
      });

      const freshCaptures = await listCaptures().catch(() => state.captures);
      set({ captures: freshCaptures });

      return rejectedProp;
    } finally {
      set({ isSubmitting: false });
    }
  },

  clearProposal: () =>
    set({
      activeProposal: null,
      activeProposalId: null,
      activeCaptureId: null,
    }),

  clearHistory: async () => {
    try {
      await apiClearCaptures();
      set({ captures: [] });
    } catch (err) {
      console.error("Failed to clear captures:", err);
    }
  },

  setFilterStatus: (filterStatus) => set({ filterStatus }),
  setSubmitting: (isSubmitting) => set({ isSubmitting }),
}));
