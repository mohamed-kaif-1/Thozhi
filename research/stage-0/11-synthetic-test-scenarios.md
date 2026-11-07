# 11 — Synthetic Test Scenarios & Edge-Case Evaluation Suite

## 1. Document Overview & Methodological Notice
> **CRITICAL RESEARCH NOTICE:**  
> The 18 scenarios contained in this document are **synthetic research test cases** designed by the AI Product Architecture team to stress-test natural language extraction, temporal ambiguity resolution, and constraint satisfaction logic.  
> **These scenarios DO NOT represent empirical human user interviews or recorded field data.** They serve strictly as an algorithmic benchmark suite for evaluating LLM prompts, ASR phonetic robustness, and deterministic planning algorithms.

---

## 2. Comprehensive Synthetic Scenario Catalog

---

### Scenario 01: Exam Preparation & Cramming Schedule
- **Input (Tanglish):**  
  *"Day after tomorrow morning DSP semester exam iruku. Today DSP syllabus full-ah cover pannanum, especially Unit 3 FFT algorithms paakanum. Aana evening 6 to 8 PM college lab record submit panna lab session iruku. Night padikalam, but I need at least 6 hours sleep."*
- **Expected Interpretation:**  
  Student has a hard exam in 48 hours. Urgent need to revise DSP syllabus (Unit 3 priority) today, interrupted by a mandatory fixed 2-hour lab session (18:00–20:00). Must preserve a 6-hour sleep block tonight.
- **Expected Tasks:**
  1. *Task 1:* Revise DSP Syllabus (Focus on Unit 3 FFT) | Duration: ~4h | Priority: P1_CRITICAL | Deadline: Today before midnight.
  2. *Task 2:* Attend College Lab Session & Submit Record | Duration: 2h | Fixed Window: 18:00–20:00 | Priority: P1_CRITICAL.
- **Non-Task Information:**  
  Hard constraint: Preserve 6 hours sleep window; Exam is day after tomorrow.
- **Ambiguities:**  
  How long does the student actually need for DSP revision? Is the lab record already written or does it need prep time before 6 PM?
- **Clarification Required:**  
  *"Is your lab record already written, or do you need time before 6:00 PM to finish writing it?"*
- **Expected Planning Constraints:**  
  Lab block locked at 18:00–20:00. DSP study blocks must be placed in morning/afternoon and post-lab 20:30–23:30.

---

### Scenario 02: Multiple Overlapping Coursework Assignments
- **Input (English):**  
  *"I have three assignments due this Friday at 5 PM: Database Normalization, Computer Networks packet tracing, and Software Engineering essay. The DB one will take 3 hours, Networks needs 2 hours, but SE essay needs at least 5 hours of research. Today is Wednesday and I only have 2 hours free after 4 PM."*
- **Expected Interpretation:**  
  10 hours of academic work required across 3 deliverables before Friday 17:00. Today has only 2 hours available; Thursday must absorb the remaining 8 hours.
- **Expected Tasks:**
  1. *Task 1:* Complete DB Normalization Assignment (3h, P2).
  2. *Task 2:* Complete CN Packet Tracing Assignment (2h, P2).
  3. *Task 3:* Research & Write SE Essay (5h, P2).
- **Non-Task Information:**  
  Current day: Wednesday. Available time today: 2h.
- **Ambiguities:**  
  Which assignment has the highest grade weight or should be tackled first?
- **Clarification Required:**  
  None strictly required; default to splitting work across Wednesday evening and Thursday.
- **Expected Planning Constraints:**  
  Wednesday allocated: 2h (e.g., CN Packet Tracing). Thursday allocated: 8h (DB + SE Essay). Flag workload warning for Thursday (heavy study day).

---

### Scenario 03: Corporate Work Deadlines & Client Deliverables
- **Input (Tanglish):**  
  *"Tomorrow 11 AM-ku US client sync call iruku, so before that deck update panni draft send pannanum. Also Karthik kooda sprint planning 3 PM-ku iruku. Client deck mudika at least 2.5 hours aagum."*
- **Expected Interpretation:**  
  Hard external meeting tomorrow at 11:00 AM. Prerequisite task (Client deck update, 2.5h) must complete before 11:00 AM. Internal meeting at 15:00.
- **Expected Tasks:**
  1. *Task 1:* Update Client Presentation Deck & Send Draft | Duration: 2.5h | Deadline: Tomorrow 10:30 AM | Priority: P1_CRITICAL.
  2. *Task 2:* Attend US Client Sync Call | Fixed Event: Tomorrow 11:00–12:00.
  3. *Task 3:* Attend Sprint Planning with Karthik | Fixed Event: Tomorrow 15:00–16:00.
- **Non-Task Information:**  
  Context about Karthik and sprint.
- **Ambiguities:**  
  Can the deck update happen today or tomorrow early morning?
- **Clarification Required:**  
  None. Schedule deck update either this evening or tomorrow 08:00–10:30 AM.
- **Expected Planning Constraints:**  
  `Task 1` must strictly precede `Task 2` ($t_{\text{end}}(T_1) \le 11:00$).

---

### Scenario 04: Personal & Family Responsibilities Collision
- **Input (Tanglish):**  
  *"Inniku evening romba tight. Amma-va 5:30 PM-ku Apollo hospital checkup kootitu ponum, minimum 2 hours aagum. Aana appa ku BP medicine vanganum before 9 PM medical shop closes. Meanwhile grocery list vera buy pannanum."*
- **Expected Interpretation:**  
  Medical appointment at 17:30 (approx 2h duration: 17:30–19:30). Two errands: Pharmacy (deadline 21:00) and Grocery shopping.
- **Expected Tasks:**
  1. *Task 1:* Take Mother to Apollo Hospital for Checkup | Duration: 2h | Fixed Window: 17:30–19:30 | Priority: P1_CRITICAL.
  2. *Task 2:* Buy BP Medicine for Father | Duration: 20m | Deadline: Today 21:00 | Priority: P1_CRITICAL.
  3. *Task 3:* Buy Groceries | Duration: 45m | Deadline: Today flexible | Priority: P3_LOW.
- **Non-Task Information:**  
  Medical shop closes at 9 PM.
- **Ambiguities:**  
  Can medicine be bought at the hospital pharmacy during the visit?
- **Clarification Required:**  
  Proposal optimization: *"Would you like to buy father's BP medicine at the hospital pharmacy around 19:15 to save a separate trip?"*
- **Expected Planning Constraints:**  
  Hospital locked 17:30–19:30. Pharmacy scheduled immediately after hospital (19:45). Groceries scheduled 20:15–21:00.

---

### Scenario 05: Side Projects & Freelancer Deliverables
- **Input (English):**  
  *"I promised the branding client I would deliver the logo vector files by tonight 8 PM. Also need to invoice them for milestone 2. I have to spend 90 minutes tweaking the SVG exports. Don't let me forget to send the invoice with the files."*
- **Expected Interpretation:**  
  Freelancer has a dual deliverable by 20:00 tonight: Logo export work (1.5h) followed by invoicing.
- **Expected Tasks:**
  1. *Task 1:* Tweak & Finalize Logo SVG Export Files | Duration: 1.5h | Deadline: Today 19:30 | Priority: P1_CRITICAL.
  2. *Task 2:* Generate & Send Milestone 2 Invoice with Files | Duration: 15m | Deadline: Today 20:00 | Priority: P1_CRITICAL | Dependency: [Task 1].
- **Non-Task Information:**  
  Branding client milestone context.
- **Ambiguities:**  
  None.
- **Clarification Required:**  
  None.
- **Expected Planning Constraints:**  
  `Task 1` $\rightarrow$ `Task 2`. Schedule `Task 1` at 17:30–19:00, `Task 2` at 19:00–19:15.

---

### Scenario 06: Conflicting Events & Calendar Oversubscription
- **Input (English):**  
  *"Tomorrow from 2 PM to 5 PM I am stuck in an all-hands offsite meeting. But my manager asked me to finish the 3-hour quarterly financial audit report by 4 PM tomorrow. How can I manage this?"*
- **Expected Interpretation:**  
  **MATHEMATICAL CONFLICT.** User has a 3-hour fixed meeting (14:00–17:00) and a 3-hour task due at 16:00 tomorrow.
- **Expected Tasks:**
  1. *Task 1:* Attend All-Hands Offsite Meeting | Fixed Event: Tomorrow 14:00–17:00.
  2. *Task 2:* Quarterly Financial Audit Report | Duration: 3h | Deadline: Tomorrow 16:00 | Priority: P1_CRITICAL.
- **Non-Task Information:**  
  User expresses distress / conflict question.
- **Ambiguities:**  
  Is the morning free before 2 PM?
- **Clarification Required:**  
  **CONFLICT WARNING:** *"Conflict detected: Your 3-hour audit report is due at 4:00 PM, but you have an all-hands meeting from 2:00–5:00 PM. To meet the deadline, you must schedule the report tomorrow morning from 09:30 AM to 12:30 PM. Would you like to schedule it then?"*
- **Expected Planning Constraints:**  
  Block morning 09:30–12:30 for Task 2. Flag critical warning if morning has other conflicts.

---

### Scenario 07: Strict Task Dependencies (DAG Pipeline)
- **Input (English):**  
  *"Before I can deploy the website to production on Friday afternoon, I have to run the regression test suite which takes 2 hours. But before running tests, Deepak needs to merge his backend PR. And after deployment, I need 30 minutes to verify DNS propagation."*
- **Expected Interpretation:**  
  Linear 4-stage dependency chain: Deepak merge $\rightarrow$ Regression tests (2h) $\rightarrow$ Production deployment (30m, Friday afternoon) $\rightarrow$ DNS verification (30m).
- **Expected Tasks:**
  1. *Task 1:* Follow up with Deepak to merge backend PR | Modality: CONDITIONAL_DEPENDENCY | Priority: P1.
  2. *Task 2:* Run Regression Test Suite | Duration: 2h | Dependency: [Task 1] | Priority: P1.
  3. *Task 3:* Deploy Website to Production | Duration: 30m | Deadline: Friday 15:00 | Dependency: [Task 2] | Priority: P1.
  4. *Task 4:* Verify DNS Propagation & Production Smoke Test | Duration: 30m | Dependency: [Task 3] | Priority: P2.
- **Non-Task Information:**  
  Deepak's backend context.
- **Ambiguities:**  
  When is Deepak expected to merge?
- **Clarification Required:**  
  *"When is Deepak expected to merge the backend PR? We need at least 2.5 hours before the Friday deployment."*
- **Expected Planning Constraints:**  
  Enforce strict DAG: $T_1 \prec T_2 \prec T_3 \prec T_4$.

---

### Scenario 08: Casual Ideas vs. Real Commitments
- **Input (Tanglish):**  
  *"Oru thought iruku... maybe next month oru tech podcast start pannalaam nu yosikiren. We should research mic prices sometime. Aana immediately inniku evening 4 PM kula auditor ku bank statement email pannanum, that's urgent."*
- **Expected Interpretation:**  
  Distinguish casual future idea (podcast brainstorming & mic research) from an urgent immediate compliance commitment (emailing auditor by 16:00).
- **Expected Tasks:**
  1. *Task 1:* Email Bank Statement to Auditor | Duration: 15m | Deadline: Today 16:00 | Modality: HARD_COMMITMENT | Priority: P1_CRITICAL.
- **Non-Task Information:**  
  Idea: Start a tech podcast next month | Modality: CASUAL_IDEA.  
  Subjunctive research: Research mic prices sometime | Modality: BACKBURNER_WISH.
- **Ambiguities:**  
  None.
- **Clarification Required:**  
  None for today’s schedule. System moves podcast ideas to the "Ideas / Backburner" archive without cluttering the daily plan.
- **Expected Planning Constraints:**  
  Schedule Task 1 before 16:00.

---

### Scenario 09: Conditional Commitments ("If-Then" Intentions)
- **Input (Tanglish):**  
  *"Suresh enaku call panni budget approve panna, udane vendor ku purchase order raise pannanum. Illana wait pannanum. Also, call varlana evening 5 PM-ku avanuku oru reminder message podanum."*
- **Expected Interpretation:**  
  Conditional workflow: Action depends on an external phone call trigger.
- **Expected Tasks:**
  1. *Task 1:* Raise Purchase Order to Vendor | Modality: CONDITIONAL_TASK (Condition: "If Suresh approves budget") | Duration: 30m.
  2. *Task 2:* Send Budget Follow-up Message to Suresh | Modality: HARD_COMMITMENT | Scheduled Time: Today 17:00 (Condition: "If no call received").
- **Non-Task Information:**  
  Vendor purchase order context.
- **Ambiguities:**  
  What is the vendor's turnaround time?
- **Clarification Required:**  
  None.
- **Expected Planning Constraints:**  
  Task 2 scheduled for 17:00 as an active reminder. Task 1 held in "Pending Triggers" list.

---

### Scenario 10: Retrospective & Completed Activities
- **Input (English):**  
  *"I already paid the electricity bill this morning and finished reviewing Rahul's resume. Now I just need to prepare the slides for tomorrow's demo and schedule an oil change for the bike."*
- **Expected Interpretation:**  
  Filter out historical completed actions; retain only pending action items.
- **Expected Tasks:**
  1. *Task 1:* Prepare Slides for Tomorrow's Demo | Duration: 2h | Deadline: Tomorrow morning | Priority: P1.
  2. *Task 2:* Schedule Bike Oil Change Appointment | Duration: 15m | Priority: P3_LOW.
- **Non-Task Information (Filtered Out):**  
  Completed: Electricity bill paid | Modality: COMPLETED_ACTION.  
  Completed: Reviewed Rahul's resume | Modality: COMPLETED_ACTION.
- **Ambiguities:**  
  None.
- **Clarification Required:**  
  None.
- **Expected Planning Constraints:**  
  Zero scheduling overhead for completed items. Schedule demo slides today.

---

### Scenario 11: Explicit Negations & Prohibitions
- **Input (English):**  
  *"Plan my week: Meet with the design agency, but do NOT schedule it on Wednesday or Friday because I'm out of office. And don't book anything before 10 AM on any day because of gym."*
- **Expected Interpretation:**  
  Scheduling request with negative boundary constraints.
- **Expected Tasks:**
  1. *Task 1:* Schedule Meeting with Design Agency | Duration: 1h | Allowed Days: Monday, Tuesday, Thursday | Allowed Window: After 10:00 AM.
- **Non-Task Information:**  
  Gym routine before 10:00 AM.
- **Ambiguities:**  
  Which specific day is preferred?
- **Clarification Required:**  
  *"I found open slots on Tuesday at 11:00 AM or Thursday at 2:00 PM for the design agency meeting. Which do you prefer?"*
- **Expected Planning Constraints:**  
  Hard negative constraints: Wednesday = BLOCKED, Friday = BLOCKED, All days $[00:00, 10:00] = \text{BLOCKED}$.

---

### Scenario 12: Mid-Stream User Corrections & Self-Repairs
- **Input (Tanglish):**  
  *"Book doctor appointment for Thursday 4 PM... wait, illa illa, Thursday leave iruken, make that Friday morning 10 AM. Actually, check if 11 AM is better because 10 AM traffic will be heavy."*
- **Expected Interpretation:**  
  Acoustic/semantic self-repair. Thursday 16:00 is cancelled $\rightarrow$ Friday 10:00 is revised $\rightarrow$ Final intent is Friday 11:00 AM.
- **Expected Tasks:**
  1. *Task 1:* Book Doctor Appointment | Target Time: Friday 11:00 AM | Priority: P2.
- **Non-Task Information:**  
  Thursday leave; traffic considerations. Cancelled intents: Thursday 16:00, Friday 10:00.
- **Ambiguities:**  
  Is the appointment already booked, or does the user need to call the clinic?
- **Clarification Required:**  
  *"Should I create a task to call the doctor's clinic to book for Friday 11:00 AM?"*
- **Expected Planning Constraints:**  
  Discard Thursday and Friday 10:00 AM. Target Friday 11:00 AM.

---

### Scenario 13: Ambiguous Colloquial Deadlines
- **Input (Tanglish):**  
  *"Praveen kitta project documentation update vaanganum sometime next week. Also end of month kula taxes settle pannanum."*
- **Expected Interpretation:**  
  Vague temporal markers: *"sometime next week"*, *"end of month kula"*.
- **Expected Tasks:**
  1. *Task 1:* Follow up with Praveen for Project Documentation | Deadline: Next Week (Tentative: Next Tuesday) | Priority: P3_LOW.
  2. *Task 2:* Settle Taxes | Deadline: Last working day of current month | Priority: P1.
- **Non-Task Information:**  
  None.
- **Ambiguities:**  
  Exact follow-up date for Praveen.
- **Clarification Required:**  
  *"For following up with Praveen next week, would you like me to set a reminder for Monday morning or mid-week Wednesday?"*
- **Expected Planning Constraints:**  
  Task 1 placed in general backlog / soft deadline. Task 2 anchored to month-end calendar date.

---

### Scenario 14: Complex Tamil-English Code-Mixing (High Tanglish Density)
- **Input (Tanglish):**  
  *"Naalaiki marunaal evening client presentation iruku pa. Tomorrow full-ah slide deck polish pannanum. Graphics designer kitta assets innum varala, avana call panni thitta poren. Aprom sayanthiram tea break-ku Vignesh-ah meet pannanum."*
- **Expected Interpretation:**  
  Temporal deduction: *"Naalaiki marunaal"* = Day after tomorrow (Friday). Client presentation on Friday evening. Tomorrow (Thursday) dedicated to slide deck polish, requiring follow-up with graphic designer for assets. Social break with Vignesh tomorrow evening.
- **Expected Tasks:**
  1. *Task 1:* Call Graphic Designer to Collect Missing Visual Assets | Duration: 15m | Scheduled: Tomorrow morning (09:30 AM) | Priority: P1_CRITICAL.
  2. *Task 2:* Polish Client Presentation Slide Deck | Duration: 3.5h | Dependency: [Task 1] | Deadline: Tomorrow end-of-day | Priority: P1_CRITICAL.
  3. *Task 3:* Meet Vignesh for Tea | Duration: 30m | Scheduled: Tomorrow 17:00 | Priority: P3_LOW.
  4. *Task 4:* Deliver Client Presentation | Fixed Event: Day after tomorrow evening.
- **Non-Task Information:**  
  Emotional venting (*"call panni thitta poren"*).
- **Ambiguities:**  
  None.
- **Clarification Required:**  
  None.
- **Expected Planning Constraints:**  
  Task 1 must precede Task 2. Task 3 placed at 17:00.

---

### Scenario 15: Sudden Urgent Emergency & Schedule Disruption
- **Input (English):**  
  *"It's 2 PM. A critical production database server just crashed and the CTO called an emergency war room right now. I had two tasks planned for this afternoon: writing unit tests (2 hours) and answering client emails (1 hour). What should happen to my afternoon?"*
- **Expected Interpretation:**  
  Immediate schedule shock. Emergency war room takes absolute precedence. Pre-scheduled tasks must be deferred.
- **Expected Tasks:**
  1. *Task 1:* Attend Production Database Emergency War Room | Fixed Event: Immediate (14:00 onwards, duration indefinite / 3h placeholder).
- **Rescheduling Proposals for Displaced Tasks:**
  - *Displaced Task A:* Write Unit Tests (2h) $\rightarrow$ Proposed postponement to tomorrow morning 09:30 AM.
  - *Displaced Task B:* Answer Client Emails (1h) $\rightarrow$ Proposed postponement to this evening 18:30 (or tomorrow).
- **Non-Task Information:**  
  CTO phone call context.
- **Ambiguities:**  
  When will the war room finish?
- **Clarification Required:**  
  **SCHEDULE SHOCK RESHOLDER:** *"Emergency War Room prioritized. I have paused your afternoon tasks. Proposed: Move Unit Tests (2h) to tomorrow 9:30 AM, and Client Emails (1h) to 6:30 PM today. Approve?"*
- **Expected Planning Constraints:**  
  Instantly clear afternoon schedule without deleting tasks.

---

### Scenario 16: Indefinite Subtasks & Executive Dysfunction
- **Input (English):**  
  *"I have to clean out my home office room this weekend. It's an absolute disaster and I've been avoiding it for 3 weeks. It feels impossible."*
- **Expected Interpretation:**  
  Vague, overwhelming chore triggering executive dysfunction. Requires micro-breakdown (Goblin Tools style).
- **Expected Tasks (Deconstructed Proposal):**
  1. *Step 1:* Clear trash and empty cups from the desk (15 min).
  2. *Step 2:* Sort paperwork into Keep vs. Shred piles (20 min).
  3. *Step 3:* Dust surfaces and organize cables (20 min).
  4. *Step 4:* Vacuum floor (15 min).
- **Non-Task Information:**  
  Emotional overwhelm / 3 weeks avoidance.
- **Ambiguities:**  
  Specific day of weekend preferred.
- **Clarification Required:**  
  *"Cleaning the office feels heavy. I've broken it down into 4 small 15-minute steps for Saturday morning. Would you like to start with just Step 1?"*
- **Expected Planning Constraints:**  
  Sequential micro-tasks with 5-minute buffer breaks.

---

### Scenario 17: Multi-Party Collaborative Commitments
- **Input (Tanglish):**  
  *"Me, Anitha and Praveen need to finalize the hackathon pitch deck together. Anitha is free only after 6 PM, Praveen is free between 4 PM and 7 PM. I need 1 hour with both of them today."*
- **Expected Interpretation:**  
  3-party calendar intersection constraint satisfaction problem:
  - Anitha: $[18:00, \infty)$
  - Praveen: $[16:00, 19:00]$
  - Duration needed: 1.0 hour.
  - Intersection: $[18:00, 19:00]$.
- **Expected Tasks:**
  1. *Task 1:* Finalize Hackathon Pitch Deck with Anitha & Praveen | Duration: 1h | Proposed Slot: Today 18:00–19:00 | Priority: P1.
- **Non-Task Information:**  
  Hackathon context.
- **Ambiguities:**  
  Does the user have other commitments between 18:00 and 19:00?
- **Clarification Required:**  
  *"The only overlapping time Anitha and Praveen share today is 6:00 PM to 7:00 PM. Shall I schedule your pitch sync for 6:00 PM?"*
- **Expected Planning Constraints:**  
  Exact mathematical interval intersection: $[18:00, 19:00]$.

---

### Scenario 18: Recursive Habit vs. One-Time Task Collision
- **Input (English):**  
  *"I have my daily French lesson on Duolingo every evening at 7:30 PM for 30 minutes. But tonight my mentor scheduled a 1-hour portfolio review at 7:30 PM. I don't want to break my 40-day French streak."*
- **Expected Interpretation:**  
  Habit vs. Hard Event collision. Hard mentor meeting takes precedence, but habit must be protected by shifting its slot earlier or later tonight.
- **Expected Tasks:**
  1. *Task 1:* Mentor Portfolio Review | Fixed Event: Tonight 19:30–20:30 | Priority: P1_CRITICAL.
  2. *Task 2:* Duolingo French Lesson (Protect Streak) | Duration: 30m | Proposed Shift: Tonight 20:45–21:15 (or 18:30–19:00) | Priority: P2.
- **Non-Task Information:**  
  40-day streak emotional context.
- **Ambiguities:**  
  Does user prefer doing French before or after the mentor review?
- **Clarification Required:**  
  *"To protect your 40-day streak without missing your mentor review, I can move Duolingo to 6:45 PM before the call, or 8:45 PM after. Which works better?"*
- **Expected Planning Constraints:**  
  Mentor review locked 19:30–20:30. French lesson shifted outside the conflict window.

