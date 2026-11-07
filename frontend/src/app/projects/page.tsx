"use client";

import React, { useState } from "react";
import {
  FolderGit2,
  Plus,
  Calendar,
  CheckCircle2,
  X,
  Target,
  Layers,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Project {
  id: string;
  name: string;
  description: string;
  category: "work" | "academic" | "personal";
  color: string;
  progress: number;
  total_tasks: number;
  completed_tasks: number;
  deadline: string;
  status: "active" | "in_review" | "completed";
  milestones: Array<{ name: string; is_done: boolean }>;
}

const MOCK_PROJECTS: Project[] = [
  {
    id: "proj-1",
    name: "THOZHI AI MVP Delivery",
    description: "Build multilingual AI sovereign personal planning engine with Gnani Prisma v3 STT.",
    category: "work",
    color: "#38BDF8", // Sky blue
    progress: 75,
    total_tasks: 12,
    completed_tasks: 9,
    deadline: "2026-11-20",
    status: "active",
    milestones: [
      { name: "Stage 0 Evidence Audit & Research", is_done: true },
      { name: "Stage 1 Architecture & PRD Specification", is_done: true },
      { name: "Stage 2 Complete Dark Cyber UI System", is_done: true },
      { name: "Stage 3 Core Database & ASR Integration", is_done: false },
    ],
  },
  {
    id: "proj-2",
    name: "College Final Capstone Submission",
    description: "Complete thesis documentation, simulation experiments, and advisor slide decks.",
    category: "academic",
    color: "#F59E0B", // Amber
    progress: 50,
    total_tasks: 8,
    completed_tasks: 4,
    deadline: "2026-12-05",
    status: "active",
    milestones: [
      { name: "Literature Review Chapter", is_done: true },
      { name: "Dataset Normalization", is_done: true },
      { name: "Empirical Benchmark Run", is_done: false },
      { name: "Final Defense Presentation", is_done: false },
    ],
  },
  {
    id: "proj-3",
    name: "Freelance Client Consulting Pipeline",
    description: "Deliver API integration contracts for 3 active client accounts.",
    category: "work",
    color: "#10B981", // Emerald
    progress: 90,
    total_tasks: 10,
    completed_tasks: 9,
    deadline: "2026-11-15",
    status: "active",
    milestones: [
      { name: "Initial Discovery Call", is_done: true },
      { name: "FastAPI Backend Scaffolding", is_done: true },
      { name: "Client Acceptance Testing", is_done: true },
      { name: "Final Invoice & Handover", is_done: false },
    ],
  },
];

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>(MOCK_PROJECTS);
  const [selectedProject, setSelectedProject] = useState<Project | null>(projects[0]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New Project Form
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deadline, setDeadline] = useState("");
  const [category, setCategory] = useState<"work" | "academic" | "personal">("work");

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const newProj: Project = {
      id: `proj-${Date.now()}`,
      name: name.trim(),
      description: description.trim(),
      category,
      color: category === "work" ? "#38BDF8" : category === "academic" ? "#F59E0B" : "#10B981",
      progress: 0,
      total_tasks: 0,
      completed_tasks: 0,
      deadline: deadline || "2026-12-31",
      status: "active",
      milestones: [{ name: "Project Initialization", is_done: true }],
    };

    setProjects([newProj, ...projects]);
    setSelectedProject(newProj);
    setIsModalOpen(false);
    setName("");
    setDescription("");
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Projects & Milestones</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-semibold">
              {projects.length} Active
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Group related tasks, track milestone progress, and prevent deadline slippage.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="btn-primary px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </button>
      </div>

      {/* Main Grid: Projects List + Selected Project Drilldown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Project Cards (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {projects.map((proj) => {
            const isSelected = selectedProject?.id === proj.id;
            return (
              <div
                key={proj.id}
                onClick={() => setSelectedProject(proj)}
                className={cn(
                  "surface-card surface-card-hover p-5 cursor-pointer transition space-y-4 relative overflow-hidden",
                  isSelected
                    ? "border-sky-400/80 shadow-lg shadow-sky-500/10 ring-1 ring-sky-400/40"
                    : "border-sky-500/20"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: proj.color }}
                      />
                      <h3 className="text-base font-bold text-white">{proj.name}</h3>
                      <span className="text-[10px] px-2 py-0.5 rounded-full uppercase font-bold bg-canvas-subtle text-slate-400 border border-slate-700">
                        {proj.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                      {proj.description}
                    </p>
                  </div>
                  <ChevronRight
                    className={cn(
                      "w-5 h-5 text-slate-500 transition-transform",
                      isSelected && "text-sky-400 translate-x-1"
                    )}
                  />
                </div>

                {/* Progress Bar & Stats */}
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">
                      {proj.completed_tasks} / {proj.total_tasks} Tasks Done
                    </span>
                    <span className="font-bold text-white font-mono">{proj.progress}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-canvas-subtle overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${proj.progress}%`,
                        backgroundColor: proj.color,
                      }}
                    />
                  </div>
                </div>

                {/* Footer Metadata */}
                <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                  <span className="flex items-center gap-1.5 text-cyber-amber-400">
                    <Calendar className="w-3.5 h-3.5" /> Due {proj.deadline}
                  </span>
                  <span className="font-semibold text-slate-300">
                    {proj.milestones.filter((m) => m.is_done).length} / {proj.milestones.length} Milestones
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Project Drilldown & Milestones (5 cols) */}
        {selectedProject && (
          <div className="lg:col-span-5 surface-card p-6 border-sky-500/20 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-sky-400" />
                <h2 className="text-base font-bold text-white uppercase tracking-wider">
                  Milestone Roadmap
                </h2>
              </div>
              <span className="text-xs font-mono font-bold text-sky-400">
                {selectedProject.name}
              </span>
            </div>

            {/* Milestones Checklist */}
            <div className="space-y-3">
              {selectedProject.milestones.map((m, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "p-3.5 rounded-xl border flex items-center justify-between gap-3 text-xs transition",
                    m.is_done
                      ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                      : "bg-canvas-subtle border-slate-800 text-slate-300"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <CheckCircle2
                      className={cn(
                        "w-4 h-4 flex-shrink-0",
                        m.is_done ? "text-emerald-400" : "text-slate-600"
                      )}
                    />
                    <span className={cn(m.is_done && "line-through text-slate-400")}>
                      {m.name}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono uppercase font-bold text-slate-500">
                    {m.is_done ? "Done" : "Pending"}
                  </span>
                </div>
              ))}
            </div>

            {/* Connected Tasks Teaser */}
            <div className="p-4 rounded-xl bg-canvas-subtle/80 border border-slate-800 space-y-2">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-cyber-amber-400" />
                <span>Automated Planning Connection</span>
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Tasks created under this project are automatically scheduled according to priority and due date constraints in your Intelligent Planner.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* CREATE PROJECT MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="surface-card w-full max-w-lg p-6 border-sky-500/30 shadow-2xl relative animate-scaleUp">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <FolderGit2 className="w-5 h-5 text-sky-400" />
              <span>Create New Project</span>
            </h2>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Project Title *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="E.g. Autonomous Mobile Robot Simulation"
                  className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Strategic goal and scope of this project..."
                  rows={3}
                  className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400 resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) =>
                      setCategory(e.target.value as "work" | "academic" | "personal")
                    }
                    className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-sky-400"
                  >
                    <option value="work">Work & Freelance</option>
                    <option value="academic">Academic & College</option>
                    <option value="personal">Personal Goal</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Target Completion Date
                  </label>
                  <input
                    type="date"
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-sky-400"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary px-5 py-2 rounded-xl text-xs font-bold"
                >
                  Save Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
