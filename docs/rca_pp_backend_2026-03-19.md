# RCA: ai_videos_backend-pp — 2026-03-19

**Container:** `ai_videos_backend-pp`
**Image:** `creator-media-gen-backend-pp-backend:latest`
**Observation window:** `2026-03-19 14:53:51` – `2026-03-19 18:55:03 UTC`
**Environment:** Pre-Production (pp)
**User active:** `siddharth.raja@jiostar.com`
**Frontend version:** `27022026_1`

---

## Executive Summary

Two distinct issues were observed during the monitoring window:

1. **[CRITICAL] Keyframe generation FAILURE** — Scene 2450 keyframe generation failed both retry attempts due to face recognition evaluation (`VoteBasedFaceRecognizer`) consistently rejecting the generated images for character `AncientKing`. Character `AncientWarrior` passed on attempt 1 but failed on attempt 2, causing the overall evaluation to fail.
2. **[WARNING] GCS connection pool exhaustion** — `urllib3` discarded connections to `storage.googleapis.com` three times (~18:53:04–18:53:20) due to the pool being full (size: 10), indicating concurrent GCS reads exceed the pool capacity.
3. **[WARNING] Invalid JSON from Gemini (object consistency pipeline)** — At 14:53:59, `gemini-3-flash-preview` returned a partial/plain-array JSON fragment instead of the expected structured object, causing a parse failure in the consistency pipeline.

---

## Timeline of Events

### Phase 1 — Background Activity (14:53:51 – 14:54:37)

| Time (UTC) | Event | Trace ID |
|---|---|---|
| 14:53:51 | `generation_iteration` tracker updated LLM metrics for event `c1065f6f` | `c1ed7dd0` |
| 14:53:57 | GET `/v2/scene/917/video/result/17d43ad6` → 200 (8.53ms) | `6c5f40a4` |
| 14:53:57 | PATCH `/v2/episode/107/scene/917` → 200 (18.45ms) — DB commit in 0.011s | `befa74f6` |
| 14:53:57–14:53:58 | GET `/object` (sample_0.mp4 video) → 206/200 (75–134ms, 4.5MB) | multiple |
| 14:53:59 | **[WARNING]** `object_consistency_pipeline`: Gemini (`gemini-3-flash-preview`) returned invalid JSON — plain object list instead of structured response | `07f74d5e` |
| 14:54:08 | Gemini retry succeeded; `generation_iteration` tracker updated for event `7803d8ef` | `07f74d5e` |
| 14:54:35–14:54:37 | GET `/object` (video `cf65696d`, ~12.5MB) → 206 (79–256ms) | multiple |

---

### Phase 2 — Session Start & Navigation (18:52:54 – 18:53:04)

| Time (UTC) | Event | Trace ID |
|---|---|---|
| 18:52:54 | User `siddharth.raja@jiostar.com` logged in; `lastLoginAt` updated | `48b89cfa` |
| 18:52:54 | POST `/review-request/search` → 200 (130ms) — 0 review requests found | `b22c1fc2` |
| 18:52:54 | GET `/v2/show` → 200 (129ms, 30KB) | `c0356f4a` |
| 18:53:03 | GET `/v2/episode/232` → 200 (21ms) | `01795857` |
| 18:53:03 | GET `/v2/show/143/characters` → 200 (18ms, 42KB — 11 characters) | `ebc8ed55` |
| 18:53:03 | GET `/v2/episode/232/scene` → 200 (14ms, 70KB) | `95ba448f` |
| 18:53:03 | 11 parallel GET `/object` for character front images (178–310ms each) | multiple |
| 18:53:04 | GET `/v2/show/143/locations` → 200 (48ms) | `e2d2c763` |
| 18:53:04 | **[WARNING]** GCS connection pool full (size: 10) — connection to `storage.googleapis.com` discarded | `efbe7388` |
| 18:53:10 | **[WARNING]** GCS connection pool full — second discard | `19a11647` |
| 18:53:20 | **[WARNING]** GCS connection pool full — third discard | `c65199e3` |

---

### Phase 3 — Keyframe Generation & Evaluation Failure (18:53:35 – 18:54:42)

#### Setup
| Time (UTC) | Event |
|---|---|
| 18:53:35 | `KeyframeServiceV2` begins generation for **Scene 2450** (trace `60c67b3c`, fe: `27022026_1`) |
| 18:53:35 | Model: `gemini-2.5-flash-image`, temperature=1, top_p=0.95, aspect_ratio=9:16 |
| 18:53:35 | Request: 5 parts (2 images + 2 descriptions + 1 prompt) for characters: `AncientKing`, `AncientWarrior` |
| 18:53:35 | `GenerationEventService` created event `724f174d-c36f-4093-8ab7-f001825d0c0b` |

#### Attempt 1
| Time (UTC) | Event |
|---|---|
| 18:53:35 | Generation attempt 1/2 started |
| 18:53:48 | Gemini returned image successfully (`image/png`) in **~13s** |
| 18:53:50–18:54:05 | `VoteBasedFaceRecognizer` evaluates image against all character reference poses |

**Attempt 1 — Face Recognition Results:**

| Character | overall_eval | matching_face_found | Best Similarity Score | Notes |
|---|---|---|---|---|
| `AncientKing` | **False** | False | 0.183 (Facenet512: 0.362) | Below threshold (0.45) across all models |
| `AncientWarrior` | **True** | True | **0.364** (Facenet512: 0.515) | Passed — best match FRONTAL→FRONTAL |

- `AncientKing` failed all 5 comparisons (scores: -0.117, -0.269, -0.184, 0.131, 0.183).
- `AncientWarrior` passed on comparison 5 (Facenet512: 0.515, antelopev2: 0.321, buffalo_l: 0.256).
- **Overall eval = False** (requires ALL characters to pass).
- Retry image uploaded to GCS: `pp/keyframe_images/a01a5902-7368-4f03-bfbc-28364e56ad52_retry_1.png`
- `18:54:05` — **[WARNING]** "Evaluation failed on attempt 1, regenerating..."

#### Attempt 2
| Time (UTC) | Event |
|---|---|
| 18:54:05 | Generation attempt 2/2 started |
| ~18:54:10 | Gemini returned second image |
| 18:54:24–18:54:34 | `VoteBasedFaceRecognizer` evaluates second image |

**Attempt 2 — Face Recognition Results:**

| Character | overall_eval | matching_face_found | Scores (Facenet512 / antelopev2 / buffalo_l) | Notes |
|---|---|---|---|---|
| `AncientKing` | **False** | False | 0.201 / 0.021 / 0.025 (best) | Below threshold 0.45 |
| `AncientWarrior` | **False** | False | 0.403 / 0.215 / 0.115 (best) | Below threshold 0.45 / 0.49 / 0.43 |

- `AncientWarrior` regressed from attempt 1 (best score dropped from 0.364 to 0.244).
- Both characters failed. antelopev2 and buffalo_l returning `None` on exact-pose FRONTAL comparisons (possible model unavailability or low-confidence detection).
- **18:54:34** — **[ERROR]** "Evaluation failed on attempt 2, all retry images uploaded, marking as FAILURE"
- Retry image 2 uploaded: `pp/keyframe_images/a01a5902-7368-4f03-bfbc-28364e56ad52_retry_2.png`
- Event `724f174d` updated to FAILURE in DB.
- Scene 2450 PATCH'd with `imageUrl: retry_2.png`, status: `"Not Generated"`.

---

### Phase 4 — Video Generation (Ongoing at window end)

| Time (UTC) | Event | Trace ID |
|---|---|---|
| 18:54:02 | PATCH `/v2/episode/232/scene/2426` → 200 (scene last updated 2026-02-19, ~1 month stale) | `c0fe550a` |
| 18:54:03 | POST `/v2/scene/2426/generate/video` by `siddharth.raja@jiostar.com` | `05dd36f8` |
| 18:54:03 | `VideoServiceV2` started job `37c4406b-2e58-42fc-aa3d-33a46d84e816` for Scene 2426, duration=6s | `05dd36f8` |
| 18:54:03 | Scene metadata: Wide Shot, "Dynamic tracking shot", Dusk/Twilight, Intense orchestral score | |
| 18:54:03 | Start keyframe: `pp/keyframe_images/3383eccb-899a-4c7b-8c0e-ef16b5dffe71.png` | |
| 18:54:03–18:55:03 | 7x polling of `/v2/scene/2426/video/result/37c4406b` → all returned `{"status":"GENERATING"}` | multiple |
| **18:55:03** | **Video generation still in progress at observation window end** | |

---

## Issues Summary

### Issue 1 — Keyframe Face Recognition Failure (CRITICAL)
- **Affected:** Scene 2450, Event `724f174d`, Trace `60c67b3c`
- **Root Cause:** `AncientKing` face consistently failed recognition across both attempts and all 3 models (Facenet512, antelopev2, buffalo_l). antelopev2 and buffalo_l return `None` scores for FRONTAL exact-pose matches — suggesting the generated image may not contain a detectable face at the expected pose, or the character reference images lack enough FRONTAL coverage for ensemble matching. AncientWarrior passed on attempt 1 but failed on attempt 2.
- **Impact:** Keyframe marked FAILURE; scene 2450 left in "Not Generated" state. Retry image (`_retry_2.png`) is stored but not promoted to primary keyframe.
- **Contributing factors:**
  - `antelopev2` and `buffalo_l` returning `None` on FRONTAL poses (models yielding no match detection).
  - Low vote count (1) for exact-pose comparisons vs. 3 for fallback poses — exact FRONTAL matching appears unreliable for these characters.
  - Similarity scores for `AncientKing` remain negative even with Facenet512 on most comparisons, suggesting the generated character doesn't visually resemble the reference.

### Issue 2 — GCS Connection Pool Exhaustion (WARNING)
- **Affected:** Requests to `storage.googleapis.com` at ~18:53:04–18:53:20
- **Root Cause:** 11 concurrent character image GETs were issued after episode load, saturating the urllib3 connection pool (max size: 10).
- **Impact:** 3 connections discarded; affected requests may have been delayed or required reconnection overhead. No request failures observed.
- **Contributing factor:** No explicit connection pool tuning for burst parallel GCS reads during UI load.

### Issue 3 — Gemini JSON Parse Failure in Object Consistency Pipeline (WARNING)
- **Affected:** Trace `07f74d5e`, event `7803d8ef`
- **Root Cause:** `gemini-3-flash-preview` returned a partial/plain JSON array (list of object names) instead of the expected structured consistency check response. The pipeline retried and succeeded ~9s later.
- **Impact:** Minor — self-healed on retry. No downstream failure observed.

---

## Observations

| # | Observation | Severity |
|---|---|---|
| 1 | `AncientKing` face recognition consistently fails (negative Facenet512 scores indicate low similarity to reference) | High |
| 2 | `antelopev2` and `buffalo_l` returning `None` on FRONTAL exact-pose comparisons — only 1 vote, models not detecting faces | Medium |
| 3 | GCS connection pool (size 10) insufficient for burst UI loads triggering 11+ parallel image requests | Medium |
| 4 | `gemini-3-flash-preview` returned malformed JSON in consistency pipeline; no retry/fallback guard | Low |
| 5 | Scene 2426 was untouched for ~1 month before this session (last updated 2026-02-19) | Informational |
| 6 | Video generation for scene 2426 was still `GENERATING` at window end — no completion observed | Informational |
| 7 | API response times are healthy — DB commits: 8–24ms, scene fetches: 14–21ms, object fetches: 75–377ms | Healthy |

---

## Recommendations

1. **Keyframe face evaluation** — Investigate reference images for `AncientKing`: the consistently negative Facenet512 scores suggest the reference face images may be low quality, occluded, or not representative of the generated character's appearance. Consider auditing reference coverage.
2. **antelopev2/buffalo_l returning None** — Add detection-confidence logging before the recognizer vote step. If the model fails to detect any face, it should be surfaced as a separate failure mode from "face detected but similarity too low".
3. **Retry limit** — 2 retries may be insufficient for complex multi-character scenes. Consider making retry count configurable per character count or scene complexity.
4. **GCS connection pool** — Increase urllib3 pool size or add a connection pool multiplier to `client.py` / Docker SDK config to handle burst parallel reads without discards.
5. **Gemini JSON validation** — Add a try/except around Gemini response parsing in `object_consistency_pipeline` with a structured retry before logging WARNING.
