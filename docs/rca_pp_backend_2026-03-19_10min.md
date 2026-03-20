# RCA: ai_videos_backend-pp — 2026-03-19 (10-minute window)

**Container:** `ai_videos_backend-pp`
**Image:** `creator-media-gen-backend-pp-backend:latest`
**Observation window:** `2026-03-19 18:56:59` – `2026-03-19 19:12:39 UTC` (~16 min captured)
**Environment:** Pre-Production (pp)
**User:** `siddharth.raja@jiostar.com`
**Frontend version:** `27022026_1`
**Total log lines analyzed:** 2,228

---

## Executive Summary

The 10-minute window was **high-traffic**: multiple concurrent keyframe and video generation jobs were active across several episodes and shows. The following distinct issues were identified:

| # | Issue | Severity | Count |
|---|---|---|---|
| 1 | **Keyframe FAILURE — Face recognition evaluation** | CRITICAL | 2 jobs failed (scenes 2450, 2890) |
| 2 | **Keyframe FAILURE — Gemini empty response (AI-007)** | CRITICAL | Scene 2427 failed twice |
| 3 | **ValueError: Reference image does not contain a face** | HIGH | 4 occurrences |
| 4 | **Storage 404 — GCS object not found** | HIGH | 3 hits (same video object) |
| 5 | **Gemini invalid JSON in object consistency pipeline** | MEDIUM | 2 occurrences |
| 6 | **Long-running video jobs not completing within window** | INFO | Scenes 1895, 2981 |

3 video generations completed successfully. 2 keyframe jobs succeeded. 1 new episode was created end-to-end (safety check, title extraction, breakdown, location extraction — all passed).

---

## Timeline of Events

### 18:56:59 – 18:57:12 | Video Generation Completion — Scene 2426 (Job 1)

| Time (UTC) | Event | Details |
|---|---|---|
| 18:56:59 | Polling `/v2/scene/2426/video/result/37c4406b` → `GENERATING` | Carry-over from prior session |
| 18:57:08 | Polling again → `GENERATING` | |
| 18:57:12 | **VIDEO GENERATION COMPLETED SUCCESSFULLY** | Trace `05dd36f8`, model: `veo-3.1-generate-001` |
| 18:57:12 | GCS URI: `gs://jc-prd-mum-gcs-vod-ai-microdrama/pp/generated_videos/37c4406b.../12728572572685999966/sample_0.mp4` | |

> Job `37c4406b` for Scene 2426 started at 18:54:03 (previous session), completed in **~3m 9s**.

---

### 19:02:53 – 19:03:42 | Keyframe Jobs Launched — Scenes 2450 & 2427 (Concurrent)

| Time (UTC) | Event | Scene | Job ID | Trace |
|---|---|---|---|---|
| 19:02:53 | POST `/v2/scene/2450/generate` → `GENERATING` | 2450 | `5d920659` | `540cb8de` |
| 19:02:59 | POST `/v2/scene/2427/generate` → `GENERATING` | 2427 | `3627efce` | `ad185ea5` |
| 19:03:09 | **[ERROR]** `GenAI returned empty response on attempt 1` | 2427 | `3627efce` | `ad185ea5` |
| 19:03:15 | GET result → **FAILURE** `{"code":"AI-007","message":"Unable to generate keyframe","statusCode":424}` | 2427 | `3627efce` | — |
| 19:03:17 | **[WARNING]** Evaluation failed on attempt 1, regenerating | 2450 | `5d920659` | `540cb8de` |
| 19:03:26 | POST `/v2/scene/2426/generate/video` → `GENERATING` (2nd video job) | 2426 | `88faf23a` | `e579b188` |
| 19:03:35 | **[ERROR]** Evaluation failed on attempt 2, all retries exhausted — **FAILURE** | 2450 | `5d920659` | `540cb8de` |
| 19:03:38 | POST `/v2/scene/2427/generate` (retry) → `GENERATING` | 2427 | `fa8f4dbd` | `39547800` |
| 19:03:42 | PATCH Scene 2450 → `imageUrl: 5d920659..._retry_2.png`, status: `"Not Generated"` | 2450 | — | — |
| 19:03:48 | **[ERROR]** `GenAI returned empty response on attempt 1` (again) | 2427 | `fa8f4dbd` | `39547800` |
| 19:03:56 | GET result → **FAILURE** `AI-007` + `ValueError: Reference image doesnot contain a face` (×2) | 2427 | `fa8f4dbd` | — |

#### Scene 2450 — Face Recognition Failure Detail

**Characters:** `AncientKing`, `AncientWarrior`

| Attempt | AncientKing (best score) | AncientWarrior (best score) | Overall |
|---|---|---|---|
| 1 | **0.283** (Facenet512: 0.513) → **PASS** | **0.335** (Facenet512: 0.444) → **FAIL** (threshold: 0.45) | **FAIL** |
| 2 | **0.306** (Facenet512: 0.462) → **FAIL** (threshold: 0.45) | **0.124** (Facenet512: 0.117) → **FAIL** | **FAIL** |

Event `b9a5bcca-9d48-4467-beef-366c0817e86a` marked FAILURE.

> Note: AncientKing passed on attempt 1 but failed on attempt 2. AncientWarrior failed both. The system requires ALL characters to pass simultaneously for a single image.

#### Scene 2427 — Gemini Empty Response + Reference Image Error

- Gemini (`gemini-2.5-flash-image`) returned an **empty response** on both independent job attempts.
- `ValueError: Reference image doesnot contain a face` was raised **twice** (one per character) — indicating that the **reference images for scene 2427's characters do not have detectable faces** by the face recognition pipeline.
- Both jobs returned `AI-007` (HTTP 424) to the client.

---

### 19:04:35 – 19:05:57 | New Session + Keyframe Jobs — Scenes 2889, 2890, 2891

| Time (UTC) | Event |
|---|---|
| 19:04:35 | Session start recorded for `siddharth.raja@jiostar.com` |
| 19:04:56 | POST `/v2/scene/2889/generate/video` → GENERATING (job `c1658637`) |
| 19:05:03 | POST `/v2/scene/2890/generate` (keyframe) → GENERATING (job `820ba2b8`, trace `a87e3fc2`) — character: `Ramu` |
| 19:05:09 | POST `/v2/scene/2891/generate` (keyframe) → GENERATING (job `f0f76ef1`, trace `101c3fb9`) — characters: `Siddharth`, `Ramu` |
| 19:05:19 | **[WARNING]** Evaluation failed on attempt 1, regenerating (Scene 2890, Ramu) |
| 19:05:33 | **[ERROR]** Evaluation failed on attempt 2, marking as FAILURE (Scene 2890) |
| 19:05:34 | **VIDEO GENERATION COMPLETED SUCCESSFULLY** — Scene 2426 job `88faf23a` |
| 19:05:57 | **KEYFRAME GENERATION COMPLETED SUCCESSFULLY** — Scene 2891 |

#### Scene 2890 — Keyframe Failure Detail

**Character:** `Ramu`

| Attempt | Best Similarity Score | Models | Result |
|---|---|---|---|
| 1 | 0.307 (Facenet512 only; antelopev2=None, buffalo_l=None) | 1 vote only | **FAIL** |
| 2 | 0.307 (Facenet512 only; antelopev2=None, buffalo_l=None) | 1 vote only | **FAIL** |

Event `56800d9c-4a2e-4791-a652-a45fbf831744` marked FAILURE.

> `antelopev2` and `buffalo_l` return `None` for both attempts — only Facenet512 provides a score. The pose comparison falls back to `Looking Down Slightly` vs FRONTAL reference (no exact pose match). With only 1 vote, the threshold of 0.45 is not met.

#### Scene 2891 — Keyframe SUCCESS Detail

**Characters:** `Siddharth`, `Ramu`

| Character | Best Similarity | Pose | Models (F512 / ante / buf) | Result |
|---|---|---|---|---|
| Siddharth | 0.284 | Right profile → Right Semi-profile | 0.576 / 0.130 / 0.147 | **PASS** |
| Ramu | 0.428 | Right profile → Right Semi-profile | 0.669 / 0.316 / 0.300 | **PASS** |

> Both characters passed via profile pose matching (pose not exactly matched, but cross-pose similarity was sufficient). This is notable: **Ramu passed on 2891 but failed on 2890** — the scene prompt/image context or angle differed between the two jobs.

---

### 19:05:57 – 19:07:07 | New Session + Scene 2889 Video Completion

| Time (UTC) | Event |
|---|---|
| 19:07:04 | **VIDEO GENERATION COMPLETED SUCCESSFULLY** — Scene 2889 (job `c1658637`) |
| 19:07:06 | New session start recorded for `siddharth.raja@jiostar.com` (3rd session in window) |
| 19:07:10 | GET `/v2/show/113/characters` → `data: []` (show 113 has no characters defined) |

---

### 19:07:43 – 19:08:19 | Keyframe Successes + Video Completion — Scene 2891

| Time (UTC) | Event | Trace | Character | Best Score |
|---|---|---|---|---|
| 19:07:44 | Keyframe event `abd47e9f` updated — `RaghavSharma` passed | `bef0d953` | RaghavSharma | 0.513 (Left profile) |
| 19:07:45 | Keyframe event `8da18c97` updated — `RaghavSharma` passed | `7e16e688` | RaghavSharma | **0.748** FRONTAL (F512: 0.881) |
| 19:08:19 | **VIDEO GENERATION COMPLETED SUCCESSFULLY** — Scene 2891 (job `1946e8ce`) | `d434b203` | — | — |

> `RaghavSharma` achieved the highest face recognition score in this window: **0.748** ensemble (Facenet512: 0.881, antelopev2: 0.689, buffalo_l: 0.675) — a strong FRONTAL match.

---

### 19:08:07 – 19:08:48 | New Video Jobs + Storage 404 Cluster

| Time (UTC) | Event |
|---|---|
| 19:08:07 | POST `/v2/scene/1933/generate/video` → GENERATING (job `d5f67f38`, trace `29cf3c52`) |
| 19:08:10 | Polling Scene 1895 (job `68bfa784`) → GENERATING (long-running, started before window) |
| 19:08:48 | **[ERROR] ×3** `Failed to get blob metadata for pp/generated_videos/399eac75-b8aa-4728-9596-f6dfed0057e3: Storage object not found` |
| 19:08:48 | 3× GET `/creator-api-pp/object` → **404** `ERR-001: Object not found: Failed to download from storage` |

> The video object `399eac75-b8aa-4728-9596-f6dfed0057e3` does not exist in GCS. Three concurrent requests hit the same missing object simultaneously, suggesting the UI sent parallel range requests for a video that was never successfully written to storage (or was deleted). No retry or fallback was triggered on the client side.

---

### 19:08:55 – 19:10:15 | New Episode Creation — Episode 298 "The Jungle Kand" Ep 3

A full episode creation flow was traced end-to-end:

| Time (UTC) | Step | Duration | Result |
|---|---|---|---|
| 19:08:55 | POST `/v2/episode` → Created Episode 298 "Untitled", Show 131 "The Jungle Kand" Ep 3 | 12ms | `DRAFT` |
| 19:09:12 | PATCH episode — script: `"Siddharth plays badminton in the park."` | 18ms | `APPROVED` |
| 19:09:16 | POST `/v2/safety/check` → passed, no violations | **3,877ms** | eligible: true |
| 19:09:23 | POST `/v2/episode/298/extract-title` → `"Siddharth's Smash in the Park"` | **6,497ms** | Success |
| 19:09:47 | POST `/v2/episode/298/breakdown` → job `4c301e83` | 13ms | GENERATING |
| 19:10:03 | Breakdown job `4c301e83` → **SUCCESS** | ~16s total | — |
| 19:10:11 | POST `/v2/episode/298/extract-locations` → "Public Park Badminton Court" | **7,188ms** | 1 location |
| 19:10:11 | POST `/v2/show/131/locations` → location ID 507 saved | 29ms | — |

> Total episode creation latency (script to breakdown): **~1m 15s**. LLM-heavy steps dominate: safety check (3.9s), title extraction (6.5s), location extraction (7.2s). All passed cleanly.

---

### 19:10:15 – 19:10:45 | Video Completion + Keyframe Success

| Time (UTC) | Event |
|---|---|
| 19:10:15 | **VIDEO GENERATION COMPLETED SUCCESSFULLY** — Scene 1933 (job `d5f67f38`) |
| 19:10:16 | POST `/v2/scene/2981/generate` → GENERATING (job `db89ebad`, trace `3c7410bb`) — character: `Siddharth` |
| 19:10:30 | **[WARNING]** Evaluation failed on attempt 1, regenerating (Scene 2981, Siddharth) |
| 19:10:45 | **KEYFRAME GENERATION COMPLETED SUCCESSFULLY** — Scene 2981 |

#### Scene 2981 — Keyframe SUCCESS after retry

| Character | Attempt 2 Best Score | Models (F512 / ante / buf) | Result |
|---|---|---|---|
| Siddharth | **0.462** FRONTAL | 0.607 / 0.402 / 0.377 | **PASS** |

Event `04ee67ee` updated with SUCCESS.

---

### 19:10:23 – 19:11:21 | Gemini Invalid JSON (Consistency Pipeline)

| Time (UTC) | Trace | Event |
|---|---|---|
| 19:10:23 | `29cf3c52` | `Video consistency: invalid JSON` — Gemini returned malformed snippet |
| 19:11:21 | `08e98dd3` | `Video consistency: invalid JSON` — second occurrence |

Both are warnings; the pipeline appears to continue via retry/fallback. No downstream failures observed tied directly to these.

---

### 19:11:12 – 19:12:39 | Video Generation Started — Scene 2981 (Still Running at Window End)

| Time (UTC) | Event |
|---|---|
| 19:11:12 | POST `/v2/scene/2981/generate/video` → GENERATING (job `3f4c59ee`) |
| 19:11:12 | **VIDEO GENERATION COMPLETED SUCCESSFULLY** — Scene 1895 job `08e98dd3`... wait — no. Scene 1895 job `68bfa784` was still GENERATING. Scene completion at 19:11:12 was for scene 1895, trace `08e98dd3` — this is VideoServiceV2, a different trace |
| 19:12:39 | Scene 2981 (job `3f4c59ee`) still → `GENERATING` at window end |
| 19:12:39 | Scene 1895 (job `68bfa784`) → status unclear, last seen GENERATING at 19:10:53 |

---

## Job Completion Summary

### Keyframe Jobs

| Scene | Job ID | Characters | Result | Duration | Failure Reason |
|---|---|---|---|---|---|
| 2450 | `5d920659` | AncientKing, AncientWarrior | **FAILURE** | ~41s | Face eval: AncientWarrior failed both attempts |
| 2427 | `3627efce` | Unknown | **FAILURE** | ~6s | Gemini empty response (AI-007) |
| 2427 | `fa8f4dbd` (retry) | Unknown | **FAILURE** | ~8s | Gemini empty response + `ValueError: Reference image has no face` |
| 2890 | `820ba2b8` | Ramu | **FAILURE** | ~30s | Face eval: only Facenet512 returned scores; score 0.307 < threshold 0.45 |
| 2891 | `f0f76ef1` | Siddharth, Ramu | **SUCCESS** | ~48s | — |
| 2981 | `db89ebad` | Siddharth | **SUCCESS** (on retry 2) | ~29s | — |
| (prev) RaghavSharma events | `abd47e9f`, `8da18c97` | RaghavSharma | **SUCCESS** | — | — |

### Video Jobs

| Scene | Job ID | Result | Duration |
|---|---|---|---|
| 2426 | `37c4406b` | **COMPLETED** ✅ | ~3m 9s (Veo 3.1) |
| 2426 | `88faf23a` | **COMPLETED** ✅ | ~1m 31s |
| 2889 | `c1658637` | **COMPLETED** ✅ | ~2m 8s |
| 2891 | `1946e8ce` | **COMPLETED** ✅ | ~3m 9s |
| 1933 | `d5f67f38` | **COMPLETED** ✅ | ~2m 8s |
| 1895 | `68bfa784` | **GENERATING** ⏳ (>4m at window end) | — |
| 2981 | `3f4c59ee` | **GENERATING** ⏳ at window end | — |

---

## Issues Deep Dive

### Issue 1 — Gemini Empty Response for Scene 2427 (AI-007, HTTP 424) [CRITICAL]

- **What:** `gemini-2.5-flash-image` returned an empty response on **two separate jobs** for the same scene (2427), both on attempt 1.
- **Root cause:** Unknown — could be model-side rate limiting, token quota, or an invalid/too-large input payload. Compounded by `ValueError: Reference image doesnot contain a face` on both character reference images for this scene.
- **Impact:** Scene 2427 has **no keyframe** and cannot progress to video generation. Two job attempts consumed quota with no output.
- **Note:** The `ValueError` suggests the root cause is upstream — the reference images uploaded for scene 2427's characters don't contain detectable faces, causing the face-recognition pipeline to throw before the model can even be evaluated. This may also be what causes Gemini to return empty if the validation runs before the model call.

### Issue 2 — Face Recognition Failures: AncientKing/AncientWarrior (Persistent) [CRITICAL]

- **What:** `AncientKing` and `AncientWarrior` face recognition scores are consistently below the 0.45 threshold across all retry attempts for scenes 2450 (this window) and 2450 (prior window).
- **Pattern:** `antelopev2` and `buffalo_l` frequently return `None` for these characters' FRONTAL poses, indicating the models **cannot detect faces** in the generated images — possibly because the generated characters are non-photorealistic (ancient/fantasy characters) or are rendered at low resolution.
- **Impact:** Scene 2450 has failed across **two independent sessions** (prior 3-min window and this 10-min window). The scene is stuck in `"Not Generated"` state with retry images uploaded to GCS but not promoted.
- **Affected events:** `724f174d` (prior session), `b9a5bcca` (this session).

### Issue 3 — ValueError: Reference Image Has No Face [HIGH]

```
Traceback (most recent call last):
    raise ValueError("Reference image doesnot contain a face")
ValueError: Reference image doesnot contain a face
```

- Raised **4 times** (2 per character) for scene 2427.
- This is a pre-evaluation check in the face recognition pipeline.
- **Root cause:** The reference character images for scene 2427 do not contain detectable faces. These may be images of objects, backgrounds, or non-face entities.
- **Impact:** All keyframe generations for scene 2427 will fail as long as the reference images are not corrected. The error is silent from the API response perspective (only `AI-007` is returned to the client).

### Issue 4 — GCS Object Not Found (HTTP 404) [HIGH]

- **Object:** `pp/generated_videos/399eac75-b8aa-4728-9596-f6dfed0057e3`
- **Time:** 19:08:48 (3 simultaneous requests)
- **Error:** `ERR-001: Object not found: Failed to download from storage`
- **Root cause:** A video result object referenced in the UI does not exist in GCS. The video generation job for this job ID likely failed silently or the object was deleted.
- **Impact:** UI shows a broken/missing video for the user. 3 simultaneous 404 requests suggest the video player sends parallel range requests without checking existence first.

### Issue 5 — Gemini Invalid JSON in Object Consistency Pipeline [MEDIUM]

- Occurred at 19:10:23 and 19:11:21.
- Same recurring issue observed in the prior 3-min window (14:53:59).
- Model `gemini-3-flash-preview` intermittently returns malformed/partial JSON.
- No crashes observed — pipeline continues. But consistency check data is dropped for those frames.

---

## Observations

| # | Observation | Severity |
|---|---|---|
| 1 | Scene 2427 permanently blocked: reference images have no detectable faces | **Critical** |
| 2 | Scene 2450 has now failed across 2 separate sessions — AncientKing/AncientWarrior systematically fail face evaluation | **Critical** |
| 3 | `antelopev2`/`buffalo_l` returning `None` on FRONTAL comparisons for fantasy characters — models cannot detect faces | **High** |
| 4 | `Ramu` passed in scene 2891 but failed in scene 2890 — face eval is non-deterministic per image; consistent retry behavior needed | **High** |
| 5 | GCS object `399eac75` referenced in UI but missing from storage — no graceful degradation for missing video | **High** |
| 6 | Scene 1895 video has been GENERATING for >4 minutes with no completion — potential stuck job | **Medium** |
| 7 | Scene 2981 video GENERATING at window end — no timeout or escalation mechanism visible in logs | **Medium** |
| 8 | `gemini-3-flash-preview` returning malformed JSON in consistency pipeline — 3 occurrences across both observation windows | **Medium** |
| 9 | Show 113 has no characters defined (`data: []`) — navigation to this show may produce misleading UI state | **Low** |
| 10 | LLM step latencies are significant: safety check ~3.9s, title extraction ~6.5s, location extraction ~7.2s — acceptable but monitor | **Informational** |
| 11 | `RaghavSharma` achieved highest face recognition score (0.748 ensemble, 0.881 Facenet512) — FRONTAL reference images are well-calibrated for this character | **Positive** |
| 12 | Episode creation pipeline (safety → title → breakdown → locations) completed cleanly end-to-end in ~1m 15s | **Positive** |
| 13 | Video generation with `veo-3.1-generate-001` completing in 2–3 minutes consistently | **Positive** |

---

## Recommendations

1. **[URGENT] Fix reference images for scene 2427** — Run a pre-flight face detectability check before allowing reference images to be saved. Reject images where no face is detected and surface a user-friendly error at upload time.

2. **[URGENT] Investigate scene 2450 / AncientKing character reference** — This character has failed across 2 sessions (4+ attempts). Audit the reference images for `AncientKing` and `AncientWarrior`. Consider whether fantasy/non-photorealistic characters need alternative evaluation strategies (e.g., CLIP-based or embedding similarity instead of face recognition).

3. **[HIGH] Pre-flight face detection before keyframe evaluation** — Before calling `VoteBasedFaceRecognizer`, validate that all character reference images have a detectable face. If not, fail fast with a clear error (not AI-007 which is opaque) and block job submission rather than consuming Gemini quota.

4. **[HIGH] GCS object existence check before serving video URLs** — Add a pre-check for GCS blob existence before returning video result URLs to the client. Return a clear `VIDEO_NOT_FOUND` state instead of letting the client hit 3 parallel 404s.

5. **[HIGH] Add job timeout + alerting for long-running video jobs** — Scene 1895 was GENERATING for >4 minutes with no log of completion. Implement a configurable timeout (e.g., 5 minutes for `veo-3.1`) after which the job is marked TIMED_OUT and retried or surfaced to the user.

6. **[MEDIUM] Tune face recognition for non-photorealistic characters** — When `antelopev2` and `buffalo_l` return `None` (no detection), consider this a detection failure rather than a similarity failure. Log separately and either skip those models from the vote or use a single-model fallback path.

7. **[MEDIUM] Fix Gemini JSON parse in consistency pipeline** — Wrap Gemini response parsing in a try/except with structured retry logic. After 2 failed parses, log an alert rather than silently swallowing the error.

8. **[LOW] Surface character-less shows** — When a show has no characters (`data: []`), the UI should warn the user that keyframe generation requiring face evaluation will not work.
