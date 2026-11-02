<p align="center">
  <img src="docs/banner.svg" width="100%" alt="Oral Exam Prep banner" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1200&color=22C55E&center=true&vCenter=true&width=760&lines=Practise+the+oral+exam;Django+%2B+PostgreSQL;Accounts%2C+exams+%26+coaching" alt="Typing tagline" />
</p>

<p align="center">
  <img src="https://img.shields.io/github/languages/top/Skander-Bardaoui/lang-oral-exam-prep-app?style=flat-square&color=22C55E" alt="" />
  <img src="https://img.shields.io/github/stars/Skander-Bardaoui/lang-oral-exam-prep-app?style=flat-square&color=22C55E" alt="" />
  <img src="https://img.shields.io/github/last-commit/Skander-Bardaoui/lang-oral-exam-prep-app?style=flat-square&color=4ADE80" alt="" />
  <img src="https://img.shields.io/badge/status-Active-22C55E?style=flat-square" alt="" />
</p>

## Overview

A Django application for preparing language oral exams. It combines accounts, exam content, an oral practice flow and coaching context, with PostgreSQL persistence and Stripe for paid access.

## Highlights

- Account and learner profiles
- Structured oral-exam content and practice sessions
- Coaching context and feedback
- Stripe payment integration
- Django templates with a dedicated static pipeline

## Tech stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=django,python,postgres,git,githubactions&theme=dark&perline=8" alt="Tech stack" />
</p>

## Getting started

**Prerequisites:** Python 3.11+, PostgreSQL and Stripe test keys.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set database, SECRET_KEY and Stripe keys
python manage.py migrate
python manage.py runserver
```

## Project structure

```text
accounts/    authentication and profiles
exams/       exam content
oral_exam/   oral practice flow
context/     shared domain context
templates/   Django templates
static/      frontend assets
```

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:22C55E,100:0A0A0C&height=110&section=footer" alt="footer" width="100%" />
</p>

<p align="center">
  Built by <a href="https://github.com/Skander-Bardaoui"><b>Skander Bardaoui</b></a> ·
  <a href="https://skander-bardaoui.netlify.app/">Portfolio</a> ·
  <a href="https://github.com/Skander-Bardaoui?tab=repositories">All repositories</a>
</p>
