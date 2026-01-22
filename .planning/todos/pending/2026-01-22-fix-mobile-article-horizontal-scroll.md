---
created: 2026-01-22T09:47
title: Fix mobile article horizontal scroll
area: ui
files:
  - web_frontend/src/components/module/ArticleEmbed.tsx
  - web_frontend/src/styles/globals.css
---

## Problem

On mobile viewport, the article view has a horizontal scrollbar. This breaks the mobile experience - users should not need to scroll horizontally on phone screens. Likely caused by content (images, code blocks, or wide elements) overflowing the container width.

## Solution

- Check for elements without `max-width: 100%` or `overflow-x: hidden`
- Ensure images have `max-width: 100%`
- Code blocks may need `overflow-x: auto` with `white-space: pre-wrap`
- Add `overflow-x: hidden` to article container as safety net
