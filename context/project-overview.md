# Project Overview

## About the Project

Oral Exam Prep is a voice-first web application that simulates real oral language certification exams. The user speaks to an AI examiner in real time, the examiner reacts, asks follow-up questions, pushes back, and steers the conversation exactly as a human examiner would. At the end of the session the user receives a structured feedback report scored against the real exam's rubric. The MVP targets English learners preparing for IELTS and Cambridge B2 First, at B1–C1 levels, with a freemium subscription model.

## The Problem It Solves

Oral exam preparation is either expensive (private tutors, language schools) or passive (YouTube videos, sample question PDFs). There is no affordable way to practice the actual experience of a reactive, evaluative oral exam conversation at any hour, as many times as needed. Students go into IELTS and Cambridge speaking tests having never experienced the real pressure and format of the exam, and they underperform as a result.

## Pages / Screens

```
/                        Landing page
/setup                   Exam configuration (language → exam → level → exercise)
/session                 The exam room — live voice session
/feedback/[sessionId]    Post-session structured feedback report
/login                   Email auth + Google OAuth
/register                Account creation
/account                 Subscription status, billing, session history count
```

## Core User Flow

**Onboarding**
1. User lands on homepage, sees what the product does
2. Clicks "Start practicing" — redirected to /login or /register if not authenticated
3. Creates account (email or Google)

**Setup**
1. User selects language (English for MVP)
2. Selects exam type (IELTS or Cambridge B2 First)
3. Selects proficiency level (B1, B2, or C1)
4. Selects exercise type (Topic Discussion or Debate) or picks random
5. Clicks "Start session"

**Session**
1. AI examiner introduces itself and the task (TTS audio)
2. User speaks — Deepgram VAD detects voice activity
3. User finishes turn — orchestration layer decides response type
4. AI examiner responds in character (Groq LLM → OpenAI TTS)
5. Loop continues for the fixed exam duration
6. Session ends — evaluation triggered automatically

**Feedback**
1. Full transcript sent to Groq for structured evaluation
2. Feedback report displayed: scores per dimension, specific examples, recommendations
3. User can retry the same configuration, start fresh, or save and exit

## Features In Scope

- English language only
- IELTS and Cambridge B2 First oral formats
- B1, B2, C1 proficiency levels
- Topic Discussion exercise type
- Debate exercise type
- Real-time voice conversation with AI examiner via Deepgram STT + OpenAI TTS
- Reactive examiner behavior: follow-up questions, pushback, steering, interventions
- Pause classification: mid-utterance / end of turn / hesitation / stuck
- Level-adjusted intervention logic (more hand-holding at B1, less at C1)
- Post-session structured feedback report (5 dimensions)
- Pronunciation flagging via Deepgram word confidence scores
- Live audio waveform visualization (user voice + examiner voice, different colors)
- Transcript toggle (hidden by default, user can reveal)
- Fixed session duration per exam type (IELTS ~14 min, Cambridge B2 ~15 min)
- User accounts via Supabase Auth (email + Google OAuth)
- 3 free lifetime sessions → subscription paywall
- Monthly ($9.99) and annual ($59.99) subscription tiers via Stripe
- Web app only

## Features Out of Scope

- Mobile app (iOS or Android)
- French, Spanish, or any language other than English
- DELF, DALF, TCF, DELE, SIELE, or any non-English exam
- A2 and C2 proficiency levels
- Structured Monologue exercise type
- Selectable examiner voice/persona
- Session audio recording and playback
- Progress tracking dashboard
- Pronunciation model (Speechace or similar)
- Offline mode
- Tutor marketplace
- Team or institutional accounts
- In-app purchases (no App Store / Play Store)

## Target User

A university student or young professional, 18–30, preparing for an IELTS or Cambridge B2 exam for university admission or visa purposes. They know they need to practice the speaking component but can't afford regular tutor sessions. They're comfortable with web apps and will find the product through organic search or Reddit.

## Success Criteria

- A user can complete a full simulated IELTS speaking session from setup to feedback without errors
- The examiner never breaks character during a session
- The feedback report contains specific examples from the user's transcript, not generic advice
- End-to-end latency from user finishing speaking to examiner responding is under 2 seconds
- 3 free sessions enforce correctly — 4th session triggers paywall for unsubscribed users
- Stripe subscription gate works: subscribed users have unlimited sessions, free users are blocked after 3
