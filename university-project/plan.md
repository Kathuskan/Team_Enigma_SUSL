# PaddyGuard MAS build plan

PaddyGuard helps a Sri Lankan paddy farmer answer questions such as “Can I spray tomorrow morning?” The answer depends on the field, the crop, the forecast and the advice in official rice manuals. Sometimes the right next step is to ask the farmer one question or refer the case to an Agricultural Instructor.

This plan follows `docs/Proposal.docx`. The local build now includes five agents, cloud speech and photo service connections, and hybrid search over official sources. Real-device and field accuracy checks remain open. The steps below describe the full target. See README.md for the features available today. Start with one complete text conversation on a local computer. Then add photos, speech and the phone interface. This order makes it easier to find which part caused a wrong answer.

## Phase 1 — Agree on the inputs and the first working example

1. **Select the manuals.** The first collection uses RRDI’s 2013 Sinhala paddy fertilizer booklet and IRRI’s *Safeguarding Plant Health for Sustainable Rice*. The source links are in `project/rag/sources.json`. Check the edition, coverage and current local rules before approving any treatment.
2. **Use cloud transcription.** With the updated audio decision, the farmer can record a clip for cloud transcription in the selected language. Put the returned words in the composer for review. Keep service keys on the server.
3. **Choose the first place to run the app.** Use a local computer for development. Before setting up a shared site, agree on the host, who manages the service keys and who may see test records. Keep real farmer photos out of demonstrations unless the team has permission.
4. **Prepare a fixed example.** Use a verified field in Polonnaruwa, a 3.5-month variety, crop day 40 and the Maha season. The farmer asks in Tamil about brown spots and spraying tomorrow morning. Save an example photo with permission and a sample forecast showing heavy rain at 11 a.m. Label the forecast as sample data.
5. **Write down what success looks like.** The app should remember the field, notice the rain conflict, explain its decision in Tamil and show which evidence it used. Write a second ending for an unclear photo so the team can also demonstrate a referral.

**Phase check.** A teammate can read the two example endings and say what the farmer should see in each. The initial sources and the cloud speech decision are recorded above.

## Phase 2 — Build the server and farm memory

1. **Create the project layout.** Start the FastAPI server from `project/main.py`. Put the five agents in `project/agents/`, manual loading in `project/rag/`, the phone app in `project/frontend/` and evaluation scripts in `project/eval/`. Keep setup and design notes in `project/docs/`. Provide an example settings file with blank values. Read real keys from a local, Git-ignored environment file.
2. **Create an anonymous farm session.** Give the browser a private session identifier. Use it on the server to find the right farm. A farmer should be able to return using the same browser without giving a name, phone number or home address.
3. **Save the field and crop separately.** In SQLite, keep the verified district or division with the farm. Keep the variety duration, planting date, irrigation method, last fertilizer date and Yala or Maha season with the current crop. An unknown value stays empty. Store chat turns and unanswered questions with the season they belong to.
4. **Set a crop-day rule.** Document how planting day is counted, use the Sri Lankan local date and test a date change at midnight. If the farmer gives a crop age instead of a planting date, save the date on which they gave that age. Tomorrow's answer must use tomorrow's crop age.
5. **Define the requests the screen can make.** Support confirming a field, reading My Farm, sending a message with an optional photo, starting a season, reading progress and preparing a referral. Use Pydantic to check dates, units, identifiers and allowed values. Explain invalid entries in a way the farmer can correct.
6. **Protect updates.** Give every sent message an identifier. If the phone retries the same message, return its existing result. Save related changes together so a lost connection cannot leave a new season with the old season's pending question.
7. **Test a return visit.** Open two browser sessions for different farms. Correct the variety in one, reload it and check both farms. Start a new season in the first farm and check that its field stays verified while its old crop details are no longer used for advice.

**Phase check.** A developer can send a message, refresh, correct a farm detail and start a new season through the server. A second session cannot read the first farm's profile, chat, trace or referral.

## Phase 3 — Build the searchable manual collection

1. **Make a source list.** Give each approved manual a stable identifier. Record the edition and the pages that cover crop stage, water supply, pests and treatment limits. Record which districts or growing zones each recommendation covers.
2. **Read each PDF with PyPDF.** Keep its page numbers and headings. Compare extracted text with the printed page, especially tables. A number copied without its column heading, unit or footnote can change the meaning. Hold unreadable pages out for review.
3. **Split the text into useful pieces.** Keep a recommendation together with its heading, units and exceptions. Attach the manual identifier, page and growing conditions to each piece. This lets the app show where an answer came from.
4. **Build the local search index with ChromaDB.** Save the index version, source file versions and the settings used to build it. Provide one command that a teammate can use to rebuild it. The running app searches this local collection for crop advice.
5. **Review rules before using them.** Ask a qualified reviewer to check crop stages, dose limits, restricted products and the required wait between treatment and harvest. Keep a reference to the page behind each rule. Record gaps for later review.
6. **Check retrieval with similar questions.** Try the same question for an irrigated field and a rainfed field. Inspect the passages returned. Then try a question outside the collection. The app should report the gap and withhold any unsupported chemical advice.

**Phase check.** A reviewer can follow a sample answer back to the exact page, check its units and see why it applies to that farm. Rebuilding from the same source list makes the same reviewed passages available.

## Phase 4 — Connect the five agents

An agent is one part of the server with a specific job. Use LangGraph to pass a shared case record between agents. Use Gemini 2.5 Flash through a replaceable model connection for language and image tasks. Keep weather measurements, manual pages and decisions in separate fields so a reviewer can follow the case.

### Step 4.1 — Orchestrator and memory agent

1. Read the current farm profile, recent messages and any unanswered question. Decide whether the farmer is asking about fertilizer, symptoms, spraying or another supported topic.
2. Extract details the farmer actually supplied. For example, “It is rainfed, and I planted on 2 November” updates two fields. If the year or date is unclear and it affects the answer, ask for the missing detail.
3. List the facts needed for this request. Use known facts first. Ask one or two short questions in the farmer's language when a needed fact is missing. Save the original request so “rainfed” can continue the conversation without the farmer having to repeat it.
4. Start weather, image review and manual search together when their inputs are ready. Collect their results before the critic reviews the advice. If a specialist fails, carry that failure into the decision.

### Step 4.2 — Weather agent

1. Look up the coordinates for the verified field area. Ask the farmer to confirm the area if two places have similar names. Fetch 48 hours of hourly data from Open-Meteo and save the time of the forecast.
2. Translate “tomorrow morning” into a local time window. Check that the forecast covers the proposed time and the following 12 hours. Keep the hourly rain probability separate from the total predicted rain.
3. Apply the proposal's thresholds. Flag wash-off if rain probability exceeds 40% or expected rain exceeds 2 mm in 12 hours. Flag spray drift above 15 km/h wind and fungal risk above 85% relative humidity. Show the relevant time and measurement with each flag.
4. Use a timeout and limited retries with Tenacity. If required hours are missing or the forecast is too old, mark weather unavailable. Tell the farmer to check local conditions and withhold weather-dependent approval.

### Step 4.3 — Vision agent

1. Check that the upload opens as an image and shows a relevant plant or pest. Inspect whether the subject is clear enough to assess.
2. Return visible signs, possible causes, uncertainty and a confidence score. Choose the score needed to accept a result using reviewed examples. The score alone cannot establish a diagnosis.
3. For an unclear image, ask once for a better view and explain what needs to be visible. Remember that request. If the second image is still unclear or the possible causes need different treatments, prepare a referral.

### Step 4.4 — Agronomy and pest agent

1. Search the approved passages using the farmer's question, crop age, variety, growing zone and water supply. Keep the page references attached to the draft.
2. Start with supported field checks and integrated pest management, which includes ways to manage pests without immediately using a chemical. Use generic ingredient names when the reviewed source supports chemical advice.
3. Include the conditions that make the advice valid. When a needed limit, stage or source is missing, say what is missing. If the critic returns a conflict, change the affected action and submit the draft again with its evidence.

### Step 4.5 — Safety and feasibility critic

1. Compare each proposed action with the forecast, image result, crop stage and cited manual. For a chemical action, check restrictions, dose limits and the waiting time before harvest. Route restricted or high-toxicity cases covered by the proposal to an instructor.
2. Return one decision. Approve a supported action, request a change and explain the conflict, or refer the case. Allow at most two revised drafts. If the second revision still fails, end the loop with a referral.
3. Send the farmer the approved next action or referral in their language. Write a short record of which agents ran, which rules applied and what changed. Save one JSON record per line in `project/logs/`. Leave raw photos, secrets and personal details out of these logs.

**Phase check.** Run the fixed rain example through the graph. Follow the trace from the original draft to the rain conflict and the revised result. Run the unclear-photo example and confirm that repeated uncertainty ends in a referral.

## Phase 5 — Build the farmer's phone and desktop screens

1. **Start with field confirmation.** Let the farmer select Sinhala, Tamil or English. Ask whether the field is here or elsewhere. Allow area selection even if location permission is denied. Show the chosen district or division and save it only after confirmation.
2. **Build My Farm and chat.** Use React and Tailwind for a readable phone layout. Pin the farm summary above the messages. Show known values such as “Polonnaruwa • 3.5 months • Day 40 • Maha”. After a correction in chat, update the bar so the farmer can check the result.
3. **Make New Season deliberate.** Explain which crop details will start fresh and show Confirm and Cancel. Test Cancel first. On confirmation, open the new season, retain the verified field and ask only for details needed for the next question.
4. **Add voice input and playback.** Show when the microphone is listening and let the farmer stop it. Put the transcript in the message box in the selected language. Let the farmer edit or discard it before sending. Add Play Audio to each reply. If speech is unavailable, explain the problem in that language and keep chat usable.
5. **Add photos.** Show the selected photo before sending. Let the farmer replace or remove it. Compress it to below 1 MB on the phone, check the final size and preserve enough detail to inspect the leaf. Check size and image type again on the server.
6. **Build the instructor handoff.** Prepare a short summary with the verified area, crop details, relevant messages, photo and reason for referral. Show a preview. The farmer chooses whether to share and who receives it. Provide a way to save or copy the summary when device sharing is unavailable.
7. **Support weak connections.** Package the app as an installable Progressive Web App (PWA). Cache the files needed to open the screen. Show whether a message is waiting, sent or failed. A cached screen must never present an old forecast as a fresh answer.
8. **Build the desktop view.** Put chat on one side and a live trace on the other. Show plain events such as “Forecast received”, “Rain conflict found” and “Revised answer approved”. A farmer on a small screen should still be able to read the complete answer.

**Phase check.** On a phone, complete onboarding, correct a spoken question, add a photo, hear a reply and preview a referral. On desktop, follow the same conversation and see the trace update. Repeat the main actions in all three languages.

## Phase 6 — Test whole conversations and failures

| Test | What to do | What should happen |
| --- | --- | --- |
| Polonnaruwa walkthrough | Use the Tamil day-40 case with 85% rain probability, 14 mm rain at 11 a.m. and 89% humidity. | The original spray plan is rejected. The reply explains the delay. Any suggested later window must have forecast coverage. |
| Farm memory | Supply a planting date, close the app, return the next day and correct the date. | The crop age advances with the local date and changes after the correction. The agent uses the updated age. |
| Short follow-up | Ask about fertilizer with an incomplete profile, then answer the agent's question. | It asks at most two relevant questions at once and continues the original request. |
| Weather boundaries | Try values exactly at each threshold and just above it. Remove one forecast hour, then simulate a timeout. | The strict “above” rules behave as written. Missing data never becomes a zero-risk reading. |
| Evidence gaps | Remove the matching page or give the agent two conflicting recommendations. | The final reply contains no unsupported dose. The trace identifies the missing or conflicting evidence. |
| Two unclear photos | Send a blurry image and then another unclear image. | The first reply requests a clearer photo. The second offers instructor review. |
| Revision limit | Supply a draft that still fails after two changes. | The graph stops and prepares a referral. It never delivers the rejected action. |
| Shared phone or interrupted send | Retry the same message, cancel a season reset, then switch to a separate test session. | No duplicate turn appears, Cancel preserves the crop and the other session cannot see the case. |
| Device and language | Test installation, outdoor readability, denied microphone access, slow uploads and missing playback voices. | Each failure has a clear message. A native speaker can understand the available next action. |

Run repeatable tests with fixed inputs first. Then run a separate live check with the real model and weather service. Keep a record of device, language, input, expected result, actual result and any fix. Repeat affected tests after each fix.

**Phase check.** A teammate can reproduce the walkthrough from a clean setup. Record any check that still needs a device, key, native speaker or qualified reviewer as pending.

## Phase 7 — Measure results and hand over the system

1. **Write 30 test cases before scoring.** Use 12 safety conflicts, eight uncertain or failed-input cases and ten routine or multi-turn cases. Give each an identifier, starting profile, conversation, forecast, manual references and expected action. Have a reviewer check the expected answers.
2. **Run the two software versions fairly.** Compare the full graph with a single-agent version using the same model, manual collection, photos and recorded weather. The single agent gets one prompt and the same tools without a separate critic. Record versions so a later run can be compared.
3. **Collect the human comparison.** Give knowledgeable reviewers the same case details, manuals and forecasts. Record their answers and time taken. If a reviewer has not completed a case, mark it pending and give the number actually reviewed.
4. **Calculate the measures.** Divide conflicts caught by total conflict cases. Score manual accuracy, crop memory and follow-up questions on a written 0–5 scale. For referral precision, divide justified referrals by all referrals made and also count cases that needed referral but were missed. Report average response time and P95, the time within which about 95% of requests finished. Use recorded token counts and dated prices to estimate cost per 1,000 requests.
5. **Explain failures.** For each missed conflict, find the first wrong step in the trace. Record whether the cause was the profile, forecast, image, manual search or critic. Keep the original score when reporting the first run and label results from later fixes separately.
6. **Write the run guides.** In the README give exact install, configuration, index build, start and test commands. In `Workflow.md` show the paths for a normal reply, revision and referral. In `PROJECT_DETAILS.md` record data sources, supported devices, known gaps and benchmark results. Link the original proposal from the guides.
7. **Prepare the shared deployment.** Configure HTTPS for phone installation and microphone use. Keep the database on persistent storage. Decide who can access records, how long photos and logs are kept and how to delete them. Back up a test database and restore it into a clean instance.
8. **Hand over and demonstrate.** Have another teammate follow the README on a clean checkout. Demonstrate one approved reply, one weather conflict and one instructor referral. Record which language, agricultural and live-service checks have passed before describing the system as ready for field use. Keep optional market-price and irrigation agents for a later phase.

**Final deliverables.** The team should have a runnable app, an approved manual list and rebuildable index, setup and workflow guides, reproducible test cases, a benchmark report and a list of remaining field checks with owners. The report should make clear which results came from fixed examples, live services and human review.

