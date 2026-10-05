# Source Ledger: Personalized And Agent Memory Research

## Snapshot

- Reviewed: 2026-10-05.
- Subject: external memory, long-term dialogue, and language-model personalization.
- Evidence class: primary papers and proceedings records.
- Verification method: title, version, abstract, authorship, and publication
  metadata checked against arXiv or the ACL Anthology.

## Verified Sources

| Source | Verified contribution | Relevance boundary |
|---|---|---|
| [Generative Agents](https://arxiv.org/abs/2304.03442v2) | Stores natural-language experience records, synthesizes reflections, retrieves memories for planning, and evaluates the architecture in an interactive-agent simulation. | Agent believability and simulation are not evidence for explicit user-preference adherence. |
| [Reflexion](https://arxiv.org/abs/2303.11366v4) | Stores linguistic feedback in an episodic buffer to influence later trials without weight updates. | Self-reflection from task feedback differs from user-approved durable preferences. |
| [MemGPT](https://arxiv.org/abs/2310.08560v2) | Uses OS-inspired memory tiers and virtual context management for document analysis and multi-session chat. | Context-window management does not establish Memory Loom's consent or deletion properties. |
| [MemoryBank](https://arxiv.org/abs/2305.10250v3) | Proposes long-term conversational memory with retrieval, updates, and time/significance-based forgetting. | Anthropomorphic forgetting and inferred personality are outside the first study. |
| [LoCoMo](https://arxiv.org/abs/2402.17753v1) | Introduces very long-term conversational data and evaluation covering information extraction, multi-hop reasoning, temporal reasoning, and open-domain generation. | The benchmark targets conversational recall, not scoped coding preferences or approval. |
| [LOCCO](https://aclanthology.org/2025.findings-acl.1014/) | Introduces Long-term Chronological Conversations and measures retention, decay, rehearsal, and category-specific memory behavior. | Its retention findings do not validate a particular external-memory policy. |
| [Reflective Memory Management](https://arxiv.org/abs/2503.08026v2) | Combines multi-granularity prospective summaries with retrospectively refined retrieval for long-term dialogue. | Its adaptive summarization and reinforcement mechanisms remain deferred here. |
| [PREMem](https://arxiv.org/abs/2509.10852v1) | Moves cross-session reasoning into construction of categorized episodic memories before response time. | Automated memory construction is outside the explicit-only admission boundary. |
| [PRIME](https://arxiv.org/abs/2507.04607v3) | Uses dual memory and personalized thought processes, and introduces a long-context personalization benchmark based on Change My View. | It studies broader opinion personalization rather than approved coding-workflow rules. |
| [Hello Again!](https://arxiv.org/abs/2406.05925v2) | Separates event perception, persona extraction, memory retrieval, and response generation in a long-term dialogue agent. | Dynamic persona modeling is explicitly excluded from the first study. |
| [Persona-Plug](https://arxiv.org/abs/2409.11901v2) | Builds a user embedding from historical contexts and attaches it to task inputs without tuning the base LLM. | Learned user embeddings are not inspectable, correctable records and are not a baseline in this study. |
| [Learning to Remember User Conversations](https://arxiv.org/abs/2411.13405v1) | Uses temporally ordered conversations to build parameter-efficient per-user adapters and compares them with retrieval baselines. | Per-user fine-tuning is intentionally excluded from Memory Loom's first study. |

## Supported Design Lessons

These papers support treating external memory, retrieval, summarization,
reflection, and parameter-efficient personalization as distinct mechanisms that
must not be conflated in one claim. They also support evaluating temporal
updates, long-horizon recall, and abstention separately.

They do **not** establish that Memory Loom improves coding-assistant behavior,
that explicit memory is superior to learned personalization, or that synthetic
results transfer to real users.

## Resolution Of The Original Queue

Every named item in the original design brief is now linked to a primary paper
or proceedings record. `LOCCO` refers to the dataset introduced by Jia et al.,
not to `LoCoMo`; the two are kept separate. No empirical value from these papers
is promoted into the Memory Loom claim register without a directly applicable
study decision.

