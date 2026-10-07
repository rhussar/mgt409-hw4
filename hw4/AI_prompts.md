# Homework 4 prompt log

## Problem 1 — Vibe coder prompts

**Initial prompt:** Create `AI_prompts.md` now and use it as a running record of the instructions I give you for each problem. Give every problem its own section with the title and the prompt I used. If I need to correct or extend a result, record that follow-up and what was missing.

## Problem 2 — Analyze the database

**Initial prompt:** Open the supplied SQLite database and inspect its real tables and columns. Start `output/harness.md` with a plain English field guide: what each column stores and why the shop or chatbot needs it. Cover the catalogue, inventory, and users, and include any other table that's actually there.

## Problem 3 — Build the Campus Customs website

**Initial prompt:** Build the first Campus Customs storefront with React, Vite, and TypeScript. Add navigation for Home, Products, About Us, Log in, and Create account. Use original Yale themed copy inspired by the reference shop. Show real products and images from the supplied database, make cards open detail pages with price, description, and size stock, and put a chat panel in the bottom right. A simple FastAPI read API is fine for now; the chat can be a stub until the later agent problem.

**Follow-up prompt:** The first browser run is blank because of a React effect error. Fix that, rebuild, and check that the catalogue, images, and product details actually render.

**What was lacking:** The initial version compiled, but a runtime effect cleanup error stopped the page from rendering in the browser.

## Problem 4 — Create account and login

**Initial prompt:** Replace the account previews with working registration and login. Save new users in the database, protect passwords with a salted slow hash, support the supplied test account, and verify that a new account can log in. Document the authentication flow in the harness.

## Problem 5 — Wire the chat agent

**Initial prompt:** Connect the chat widget to a PydanticAI agent behind FastAPI. Keep the prompt, agent wiring, tools, and typed models in separate backend files, load the model key from the environment, and document how a message reaches the agent.

## Problem 6 — Ground product facts

**Initial prompt:** Give the assistant database tools to look up real product descriptions, prices, and stock by size. Make it state zero stock honestly and ask for a clearer product name when a match is ambiguous. Record the tool inputs and outputs in the harness.

## Problem 7 — Show product cards from chat

**Initial prompt:** When I ask about a category such as hoodies, search the actual catalogue and return structured matches from the API. Render those matches as clickable product cards in the chat and document the result shape.

## Problem 8 — Remember logged-in shoppers

**Initial prompt:** Save and reload chat history for logged-in users, while letting guests chat without saving their conversation. Give the agent the shopper's name and the product currently open on the page so it can understand questions like “Does this come in XL?” Document the flow.

## Problem 9 — Improve usability

**Initial prompt:** Add two shopping controls to the Products page: filter by sizes that are actually in stock, and sort by price or name. Improve backend answers with better catalogue matching and a database-checked response for product-page price and size questions. Write down why each change helps.

## Problem 10 — Creative styling

**Initial prompt:** Give the shop a distinctive but usable Campus Customs look. Refine the navy, cream, and gold palette, type hierarchy, product presentation, and chat panel, add restrained motion, and explain the design choices in `output/design.md`.

## Problem 11 — Site testing

**Initial prompt:** Test the live shop and make `output/app_check.html` with labeled screenshots of a real inventory-level chat answer, category search-result cards, and one of the usability features from Problem 9. Link the screenshots with short captions so I can open the page locally.

## Problem 12 — Audit and safety

**Initial prompt:** Keep `output/audit_trail.json` append-only with the time, tool name, short arguments and result, and stop reason for agent activity. Add practical safety rules to the agent prompt and finish `output/harness.md` with the fields, tools, safety choices, and run specifications.

## Problem 13 — GitHub and Canvas

**Initial prompt:** Put the finished code in a folder named `hw4`, publish it to a public GitHub repository, and submit the repository URL on Canvas. Keep the real `.env`, SQLite database, and product images out of Git; include a placeholder `.env.example` and clear run instructions.

**Follow-up:** I’ll submit it myself.

**Submission handoff:** The public repository is `https://github.com/rhussar/mgt409-hw4`. Canvas submission is for me to complete.
