# Screen Recording Walkthrough Script (3-Minute Cap)

**Candidate Instructions:** Use this script to record a 3-minute screen walkthrough. Phone recording of your monitor or a screen recording (Loom/OBS) is fine. **No slides.** Show the code, terminal, and dashboard directly.

---

### Timing & Sequence Overview

| Timecode | Section | Visual Focus | Key Message |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:40** | **1. The Prompts Used** | Open `src/classifier.py` & Dashboard Sandbox | Show the structured JSON prompt, evidence extraction, and few-shot disambiguation rules. |
| **0:40 – 1:50** | **2. Version Iterations** | Terminal & Comparison Charts | Explain shifting from raw intake counting (V1) to resolving workload & timezone normalization (V2). |
| **1:50 – 2:40** | **3. What Was Discarded** | Terminal CLI & Git Diff / Scratch | Explain why multi-agent systems and unadjusted legacy metrics were discarded. |
| **2:40 – 3:00** | **4. Final Synthesis** | Dashboard Decision Banner | Close with the Rs 1.22L/quarter savings and the decision: 2 hires to Logistics. |

---

### Detailed Spoken Script & Screen Actions

#### Minute 0:00 – 0:40 | Part 1: The Prompts Used
- **Screen Action:** Open `src/classifier.py` at line 140 and show the prompt function `_build_prompt()`. Then toggle to the browser dashboard at `http://127.0.0.1:8000` and click the "Paid 5 days ago" sample in the AI Sandbox.
- **Spoken Audio:**
  > *"Hi everyone. Here is our working AI ticket triage tool for Vireo Audio. 
  > 
  > Let's look at the prompts first. Our initial naive prompt simply asked an LLM: 'Classify this ticket into 11 categories.' It failed on edge cases because customers often use payment words when complaining about missing deliveries. 
  > 
  > In our production prompt in `src/classifier.py`, we engineered two explicit instructions: 
  > First, we established domain disambiguation: if a customer says 'I paid X days ago and nothing arrived', the issue is strictly Delivery & Shipping, not Billing. 
  > Second, we forced a strict Pydantic JSON schema returning not just the category, but the confidence score, suggested routing team, and an exact evidence quote. Notice in the sandbox, when I test 'Paid 5 days ago, nothing in hand', the classifier extracts '5 days and counting', assigns 92% confidence, and automatically suggests routing to Logistics instead of Billing."*

---

#### Minute 0:40 – 1:50 | Part 2: What Changed Between Versions
- **Screen Action:** Switch to the browser dashboard's **"Team Workload: Assigned vs Resolved"** tab. Hover over the Billing bar (showing 2,425 dropping to 1,798) and Logistics bar (showing 1,905 surging to 2,574). Then open `src/pipeline.py` at lines 35-44 (showing the UTC+5.5h adjustment).
- **Spoken Audio:**
  > *"Now, what changed between our versions? 
  > 
  > In Version 1, we took Priya Raman's initial assumption at face value: Billing appeared to be 20.8% of tickets, so we initially modeled hiring into Billing. But when we inspected resolving agent IDs in `agents.csv`, our pipeline discovered the 'Billing Illusion': 696 tickets assigned to Billing were actually delivery tracking complaints transferred to Logistics! 
  > 
  > In Version 2, we completely restructured the pipeline to compare **Intake Assigned Volume** versus **Actually Resolved Workload**. Billing's workload drops by 26% down to 15.4%, while Logistics surges by 35% to 22.1%. Logistics agents were resolving 515 tickets per agent with a median resolution time of 25.1 hours! 
  > 
  > We also caught a major data integrity flaw: 2,379 legacy Freshdesk tickets had negative resolution times. We discovered that event logs were exported in UTC while helpdesk creation was in IST (+5:30). In Version 2, we added automatic timezone normalization (+5.5 hours), completely eliminating negative durations and restoring valid SLA metrics."*

---

#### Minute 1:50 – 2:40 | Part 3: What We Threw Away & Why
- **Screen Action:** Switch to VS Code terminal. Show `python run.py --evaluate` terminal output with 80% accuracy and the 83% Billing F1 score.
- **Spoken Audio:**
  > *"Next: what did we throw away? 
  > 
  > First, we completely threw away a complex multi-agent LangGraph workflow. It was non-deterministic, slow, racked up unnecessary API costs, and violated the core requirement that a solution must run reliably on a clean machine from README without external dependencies. Instead, we built a hybrid engine: a zero-dependency deterministic semantic classifier that runs offline in milliseconds, with an optional LLM toggle.
  > 
  > Second, we threw away naive keyword regex classification that attempted to classify all 11 categories from scratch. We saw in evaluation benchmarks that it caused false positives in technical frontline queues. We replaced it with a precision-targeted override model: it strictly intervenes on misclassified billing-delivery tickets where the chatbot fails, boosting Billing F1 score from 63.8% to 83.4% and Delivery F1 from 57.2% to 80.6%."*

---

#### Minute 2:40 – 3:00 | Part 4: Conclusion & Business Decision
- **Screen Action:** Scroll to the Executive Banner and Arjun Mehta's Financial Case on the Dashboard.
- **Spoken Audio:**
  > *"To conclude: Priya’s proposed two hires must not go to Billing. They must go to Logistics. 
  > 
  > This solves the 25-hour delivery bottleneck, while our AI auto-routing eliminates 1,200+ avoidable internal transfers, saving Vireo Rs 1.22 Lakh per quarter in administrative friction and SLA penalties. Thank you."*
