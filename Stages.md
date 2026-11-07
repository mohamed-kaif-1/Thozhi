Brooo, now we're defining the official app development roadmap for THOZHI. Let's organize it like a real software product, with clear stages, phases, tasks and completion criteria.

# THOZHI — App Development Master Roadmap

# THOZHI

## Your thoughts. Your plans. Your direction.

Multilingual AI-powered personal planning assistant · Web application

[AI Personal Assistant | Automate Your Life with KeepClaw](https://images.openai.com/static-rsc-4/564qR-Bu24GbMZjG7_tzlzeQOrOoaeiE4LvFa1A91Tq9LrAtZ30SMgIoephmykKGmC36GNTNYMDc7UuALYwFCoTVCanGhrYkzElyKYhKXTMa3RiUYHCIlXjnKPphkyQ1_GVLhnVJJFuMG2BX7nALr3544K3dxk2NlEPxPbNd3hs?purpose=inline)

[keepclaw.ai](https://keepclaw.ai/ai-personal-assistant?utm_source=chatgpt.com)

Web-first

Python + FastAPI

Supabase

Hybrid memory

Validation pending

## 1. Product vision

THOZHI aims to help people transform unstructured thoughts, responsibilities and commitments into organized, realistic plans.

The core workflow:

1. User speaks or types their thoughts.
2. THOZHI understands the input.
3. It identifies tasks, commitments, deadlines and dependencies.
4. It detects missing information and potential conflicts.
5. It proposes an organized plan.
6. The user reviews, edits and approves it.
7. Approved tasks are saved and tracked.

Core principle: THOZHI must never silently turn an AI assumption into a user's commitment.

# 2. Development roadmap

## THOZHI development stages

1. Stage 0 — Product validation and approval

   Prove the problem before committing to implementation.
2. Stage 1 — Product specification and engineering design

   Finalize requirements, architecture and technical contracts.
3. Stage 2 — UI/UX design

   Design the complete user experience and interface.
4. Stage 3 — Development foundation

   Establish frontend, backend, database and infrastructure.
5. Stage 4 — Core AI understanding system

   Implement voice, transcription and intent extraction.
6. Stage 5 — Intelligent planning and task management

   Build the planning engine and user-approved task workflows.
7. Stage 6 — Memory and personalization

   Implement hybrid memory, preferences and contextual retrieval.
8. Stage 7 — Integration and complete application

   Connect all components into one working product.
9. Stage 8 — Testing and AI evaluation

   Verify functionality, accuracy, security and reliability.
10. Stage 9 — Deployment and release

    Deploy, document and prepare the final demonstration.

# Stage 0 — Product validation and approval

Current approval gate

Objective: Confirm that THOZHI solves a real problem.

### Phase 0.1 — Problem validation

- Finalize the problem hypothesis.
- Identify the initial target users.
- Conduct exploratory user interviews.
- Understand existing task-management workflows.
- Identify repeated planning difficulties.
- Document actual user examples.

### Phase 0.2 — Competitive validation

- Evaluate Todoist Ramble.
- Evaluate Gemini and other conversational assistants.
- Evaluate traditional task-management applications.
- Compare multilingual capabilities.
- Compare commitment understanding and planning.
- Identify evidence-backed differentiation.

### Phase 0.3 — Product approval

- Finalize the problem statement.
- Confirm the target user.
- Define THOZHI's unique value.
- Finalize the MVP direction.
- Obtain explicit product validation approval.

Deliverable: Approved problem statement and product direction.

Exit condition: No engineering implementation until this gate passes.

# Stage 1 — Product specification and engineering design

Objective: Define exactly what we are building.

### Phase 1.1 — Product requirements

- Create the Master PRD.
- Define target users and use cases.
- Define core product workflows.
- Define functional requirements.
- Define non-functional requirements.
- Define MVP and future features.
- Define acceptance criteria.

### Phase 1.2 — System architecture

- Finalize Next.js and TypeScript frontend architecture.
- Finalize Python FastAPI backend architecture.
- Define Supabase integration.
- Define authentication architecture.
- Define AI provider abstraction.
- Define API communication.
- Define error-handling architecture.

### Phase 1.3 — Database design

- Design the entity relationship diagram.
- Define user and profile entities.
- Define task and task-proposal entities.
- Define planning-session entities.
- Define project and dependency entities.
- Define memory entities.
- Define indexes and constraints.
- Define Row Level Security policies.

### Phase 1.4 — AI architecture

- Define Gnani Prisma integration.
- Define transcription pipeline.
- Define language-detection requirements.
- Define intent-extraction architecture.
- Define structured AI response schemas.
- Define clarification logic.
- Define planning-engine boundaries.
- Compare candidate LLM providers.
- Define AI evaluation datasets.

Deliverable: Approved engineering specification and architecture document.

# Stage 2 — UI/UX design

Objective: Design the entire experience before frontend implementation.

### Phase 2.1 — Design system

- Define THOZHI's visual identity.
- Define logo direction and brand guidelines.
- Define typography.
- Define primary and secondary colors.
- Define spacing and layout system.
- Define reusable components.
- Define light and dark themes.
- Define responsive design rules.

### Phase 2.2 — Information architecture

- Define application navigation.
- Define dashboard structure.
- Define task-management navigation.
- Define planning-session navigation.
- Define memory and settings navigation.
- Define user account navigation.

### Phase 2.3 — Wireframes

- Design onboarding.
- Design authentication.
- Design dashboard.
- Design voice capture.
- Design text input.
- Design transcription preview.
- Design task proposals.
- Design clarification interactions.
- Design schedule proposals.
- Design task list and details.
- Design memory settings.
- Design profile settings.

### Phase 2.4 — Interactive prototype

- Connect wireframes into a prototype.
- Simulate the complete user workflow.
- Test navigation consistency.
- Test the task approval interaction.
- Test the schedule-editing interaction.
- Review accessibility.
- Gather user feedback.
- Approve final UI design.

Deliverable: Complete UI/UX specification and approved interactive prototype.

# Stage 3 — Development foundation

Objective: Establish the technical foundation.

### Phase 3.1 — Frontend foundation

- Set up Next.js.
- Configure TypeScript.
- Configure Tailwind CSS.
- Integrate the chosen UI component system.
- Configure routing.
- Configure frontend environment variables.
- Establish component conventions.
- Configure frontend linting and testing.

### Phase 3.2 — Backend foundation

- Set up Python environment.
- Set up FastAPI.
- Configure Pydantic schemas.
- Define API versioning.
- Implement health-check endpoint.
- Configure logging.
- Configure exception handling.
- Establish backend module conventions.

### Phase 3.3 — Supabase foundation

- Create the approved Supabase project.
- Configure PostgreSQL.
- Configure Supabase Auth.
- Create database migrations.
- Create initial tables.
- Implement RLS policies.
- Configure database access from FastAPI.
- Verify user isolation.

### Phase 3.4 — Development infrastructure

- Configure Git repository.
- Establish branching conventions.
- Configure development and production environments.
- Configure secret management.
- Configure CI checks.
- Configure automated test execution.
- Document local development setup.

Deliverable: Working frontend, backend and database foundations.

# Stage 4 — Core AI understanding system

Objective: Build the system that understands user input.

### Phase 4.1 — Voice input

- Implement browser microphone access.
- Implement audio recording.
- Implement recording controls.
- Implement audio upload.
- Validate audio formats.
- Handle microphone permission failures.
- Handle upload interruptions.

### Phase 4.2 — Gnani integration

- Verify challenge API access.
- Verify available Prisma model version.
- Implement secure server-side API integration.
- Implement transcription requests.
- Implement language detection.
- Test selected Indian languages.
- Test code-mixed speech.
- Test transcription errors.
- Implement transcript editing.
- Measure API latency and credit consumption.

### Phase 4.3 — Text understanding

- Implement text-input processing.
- Normalize transcripts without changing their meaning.
- Identify tasks.
- Identify commitments.
- Identify intentions.
- Identify deadlines.
- Identify priorities.
- Identify durations when supported.
- Identify dependencies.
- Identify completed actions.
- Identify negations and corrections.

### Phase 4.4 — Structured intent extraction

- Design the task-extraction schema.
- Implement the LLM integration.
- Validate model-generated JSON.
- Implement confidence and uncertainty handling.
- Detect missing information.
- Generate clarification questions.
- Preserve the original input for review.
- Reject unsupported inferences.

Deliverable: Voice/text input transformed into validated task proposals.

# Stage 5 — Intelligent planning and task management

Objective: Make THOZHI more than a transcription and task-creation application.

### Phase 5.1 — Task proposal system

- Create task proposal objects.
- Display extracted tasks.
- Allow individual task editing.
- Allow task rejection.
- Allow task approval.
- Support batch approval.
- Track proposal status.
- Prevent unapproved proposals from entering the task list.

### Phase 5.2 — Planning engine

- Define availability rules.
- Define duration handling.
- Define priority calculation.
- Define deadline constraints.
- Implement dependency ordering.
- Implement schedule generation.
- Detect overloaded schedules.
- Detect conflicting deadlines.
- Detect impossible plans.
- Generate explanations for proposed schedules.

### Phase 5.3 — Clarification engine

- Detect ambiguous deadlines.
- Detect missing durations.
- Detect conflicting instructions.
- Detect unclear commitments.
- Generate relevant clarification questions.
- Update proposals after user responses.
- Recalculate plans after corrections.

### Phase 5.4 — Task management

- Implement task creation after approval.
- Implement task editing.
- Implement task deletion.
- Implement task completion.
- Implement task status.
- Implement task filtering.
- Implement task sorting.
- Implement deadline views.
- Implement project grouping if needed.
- Implement duplicate prevention.

### Phase 5.5 — Dashboard

- Show today's tasks.
- Show upcoming deadlines.
- Show overdue tasks.
- Show completed tasks.
- Show current planning sessions.
- Show important conflicts.
- Show progress summaries.

Deliverable: Functional planning engine and task-management experience.

# Stage 6 — Memory and personalization

Objective: Make THOZHI context-aware without compromising user control.

### Phase 6.1 — Operational memory

- Store approved task history.
- Track task completion.
- Track task status changes.
- Maintain planning-session history.
- Retrieve relevant active tasks.
- Track project relationships.

### Phase 6.2 — Personal memory

- Define personal preference categories.
- Ask permission before saving long-term preferences.
- Store approved working-hour preferences.
- Store approved language preferences.
- Store approved planning preferences.
- Allow users to review saved preferences.
- Allow users to correct preferences.
- Allow users to delete preferences.

### Phase 6.3 — Contextual memory

- Identify when historical context is necessary.
- Design relevant context retrieval.
- Summarize selected planning sessions where permitted.
- Avoid retrieving irrelevant history.
- Prevent deleted information from resurfacing.
- Evaluate whether pgvector is necessary.
- Add semantic retrieval only if justified.

### Phase 6.4 — Memory controls

- Implement memory settings.
- Implement retention controls.
- Implement transcript-history controls.
- Implement data deletion.
- Implement account data export if required.
- Define raw audio deletion.
- Test memory isolation between users.

Deliverable: User-controlled hybrid memory system.

# Stage 7 — Full application integration

Objective: Connect every component into a single coherent application.

### Phase 7.1 — Frontend and backend integration

- Connect authentication.
- Connect voice recording.
- Connect transcription.
- Connect AI extraction.
- Connect clarification.
- Connect planning.
- Connect task approval.
- Connect task persistence.
- Connect memory retrieval.
- Connect user settings.

### Phase 7.2 — End-to-end workflow

- Test typed brain dump.
- Test voice brain dump.
- Test multilingual input.
- Test transcript correction.
- Test task extraction.
- Test ambiguity handling.
- Test schedule generation.
- Test task editing.
- Test approval and rejection.
- Test task persistence.
- Test future-session context retrieval.

### Phase 7.3 — User experience refinement

- Add loading feedback.
- Add processing status.
- Add error recovery.
- Add retry behaviour.
- Add confirmation messages.
- Add empty states.
- Add responsive behaviour.
- Add accessibility improvements.

Deliverable: Complete end-to-end THOZHI application.

# Stage 8 — Testing and AI evaluation

Objective: Verify that the application is reliable, secure and useful.

### Phase 8.1 — Frontend testing

- Unit tests.
- Component tests.
- Form validation tests.
- Responsive-layout tests.
- Browser compatibility tests.
- Accessibility tests.

### Phase 8.2 — Backend testing

- API tests.
- Authentication tests.
- Authorization tests.
- Database tests.
- Migration tests.
- Error-handling tests.
- Duplicate-request tests.

### Phase 8.3 — AI testing

- Speech recognition evaluation.
- Code-mixed speech evaluation.
- Language detection evaluation.
- Task extraction evaluation.
- Commitment classification evaluation.
- Date extraction evaluation.
- Negation and correction evaluation.
- Planning feasibility evaluation.
- False-positive task creation evaluation.
- Hallucination and unsupported-inference evaluation.

### Phase 8.4 — Security testing

- Test RLS.
- Test cross-user access.
- Test secret exposure.
- Test unauthorized API requests.
- Test input validation.
- Test prompt injection.
- Test audio deletion.
- Test memory deletion.
- Test rate limits.
- Review security vulnerabilities.

### Phase 8.5 — User acceptance testing

- Recruit pilot participants.
- Prepare synthetic scenarios.
- Observe users using THOZHI.
- Collect usability feedback.
- Measure correction rates.
- Measure task approval and rejection.
- Measure planning usefulness.
- Identify major friction points.
- Fix critical issues.

Deliverable: Quality assurance and user acceptance report.

# Stage 9 — Deployment and release

Objective: Publish the working application and prepare the challenge submission.

### Phase 9.1 — Production deployment

- Select frontend hosting.
- Select Python backend hosting.
- Configure production Supabase.
- Configure HTTPS.
- Configure production secrets.
- Configure monitoring.
- Configure logging.
- Configure backups.
- Run production smoke tests.

### Phase 9.2 — Documentation

- Write README.
- Document architecture.
- Document API endpoints.
- Document database design.
- Document AI integrations.
- Document Gnani model usage.
- Document memory design.
- Document privacy and security.
- Document known limitations.

### Phase 9.3 — Challenge preparation

- Verify official challenge requirements.
- Verify Gnani integration.
- Verify synthetic-data compliance.
- Prepare demo scenarios.
- Record demonstration video if required.
- Prepare project presentation.
- Prepare LinkedIn/X post.
- Verify deployment URL.
- Perform final submission review.

Deliverable: Deployed THOZHI application and completed submission package.

# 3. Technology ownership map

| Area                | Technology                     |
| ------------------- | ------------------------------ |
| Frontend            | Next.js + TypeScript           |
| UI                  | Tailwind CSS + shadcn/ui       |
| Frontend API state  | TanStack Query                 |
| Backend             | Python + FastAPI               |
| Backend schemas     | Pydantic                       |
| Database            | Supabase PostgreSQL            |
| Authentication      | Supabase Auth                  |
| Database protection | RLS                            |
| Speech recognition  | Gnani Prisma                   |
| LLM                 | Selected after benchmarking    |
| Memory              | PostgreSQL + optional pgvector |
| Backend tests       | Pytest                         |
| Frontend tests      | Vitest + React Testing Library |
| Browser E2E         | Playwright                     |
| API testing         | Bruno / Postman                |
| Version control     | Git + GitHub                   |
| Frontend deployment | Vercel                         |
| Backend deployment  | Python-compatible hosting      |

# 4. Development priority

Not every feature deserves equal priority. This is the order I recommend.

## MVP priority classification

P0 — Essential

- Authentication
- Voice and text input
- Gnani transcription
- Task and commitment extraction
- Clarification
- Task proposal review
- User approval
- Task persistence
- Basic planning and conflict detection

P1 — Important

- Hybrid memory
- Task history
- Personalized preferences
- Schedule editing
- Dashboard analytics
- Deadline views

P2 — Later

- Calendar integrations
- Advanced semantic memory
- Live voice conversations
- Advanced notifications
- Team collaboration
- Mobile application
- Multiple AI agents

Do not let P2 features delay the first working product.

# 5. Development approval gates

| Gate | Required approval             |
| ---- | ----------------------------- |
| G0   | Product validation approved   |
| G1   | PRD and requirements approved |
| G2   | Architecture approved         |
| G3   | UI/UX approved                |
| G4   | Foundation approved           |
| G5   | Core AI workflow approved     |
| G6   | Planning and memory approved  |
| G7   | Integrated MVP approved       |
| G8   | Testing and security approved |
| G9   | Production release approved   |

Each stage must produce documentation, working evidence where applicable, and a review before the next stage.

# 6. Immediate project status

## THOZHI project tracker

Current authorized stage

Stage 0

Product validation pending

Development authorization

Not granted

Architecture

Provisional

UI/UX

Not started

Implementation

On hold

My instruction as your project mentor: Don't jump directly into frontend design or coding because the name and stack are decided. First validate the problem. Once approved, follow the stages in order. We should build THOZHI as a reliable planning product, not a flashy AI wrapper.

This is the development roadmap I recommend we use as the master plan for THOZHI.