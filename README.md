GitAI turns messy AI chats into a living developer memory. It ingests conversations from coding sessions, auto-summarizes them with Gemini, classifies each message, extracts code blocks, and saves everything as clean JSON you can search and surface later. In minutes, a team gets instant “why/how we fixed this” context, commit-ready summaries, and keywords—without writing a single retro note.

Why now? AI coding is everywhere; institutional memory isn’t. This bridges the gap.

Demo flow (30s): POST a raw chat -> get back a title, one-paragraph summary, per-message types, code snippets, and semantic keywords -> front-end lists projects with updates.

Edge: Code-aware extraction + semantic enrichment (MiniLM + KeyBERT) yields searchable, convention-ready insights—cheap, fast, and portable (plain JSON).