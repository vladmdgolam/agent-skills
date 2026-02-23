
# The Complete Guide to Building Skills for Claude

---

## Contents

- [Introduction](#introduction)
- [Chapter 1: Fundamentals](#chapter-1-fundamentals)
- [Chapter 2: Planning and Design](#chapter-2-planning-and-design)
- [Chapter 3: Testing and Iteration](#chapter-3-testing-and-iteration)
- [Chapter 4: Distribution and Sharing](#chapter-4-distribution-and-sharing)
- [Chapter 5: Patterns and Troubleshooting](#chapter-5-patterns-and-troubleshooting)
- [Chapter 6: Resources and References](#chapter-6-resources-and-references)
- [Reference A: Quick Checklist](#reference-a-quick-checklist)
- [Reference B: YAML Frontmatter](#reference-b-yaml-frontmatter)
- [Reference C: Complete Skill Examples](#reference-c-complete-skill-examples)

---

## Introduction

A skill is a set of instructions - packaged as a simple folder - that teaches Claude how to handle specific tasks or workflows. Skills are one of the most powerful ways to customize Claude for your specific needs. Instead of re-explaining your preferences, processes, and domain expertise in every conversation, skills let you teach Claude once and benefit every time.

Skills are powerful when you have repeatable workflows: generating frontend designs from specs, conducting research with consistent methodology, creating documents that follow your team's style guide, or orchestrating multi-step processes. They work well with Claude's built-in capabilities like code execution and document creation. For those building MCP integrations, skills add another powerful layer helping turn raw tool access into reliable, optimized workflows.

This guide covers everything you need to know to build effective skills - from planning and structure to testing and distribution. Whether you're building a skill for yourself, your team, or for the community, you'll find practical patterns and real-world examples throughout.

**What you'll learn:**

- Technical requirements and best practices for skill structure
- Patterns for standalone skills and MCP-enhanced workflows
- Patterns we've seen work well across different use cases
- How to test, iterate, and distribute your skills

**Who this is for:**

- Developers who want Claude to follow specific workflows consistently
- Power users who want Claude to follow specific workflows
- Teams looking to standardize how Claude works across their organization

### Two Paths Through This Guide

Building standalone skills? Focus on Fundamentals, Planning and Design, and category 1-2. Enhancing an MCP integration? The "Skills + MCP" section and category 3 are for you. Both paths share the same technical requirements, but you choose what's relevant to your use case.

**What you'll get out of this guide:** By the end, you'll be able to build a functional skill in a single sitting. Expect about 15-30 minutes to build and test your first working skill using the skill-creator.

Let's get started.

---

## Chapter 1: Fundamentals

### What is a skill?

A skill is a folder containing:

- **SKILL.md** (required): Instructions in Markdown with YAML frontmatter
- **scripts/** (optional): Executable code (Python, Bash, etc.)
- **references/** (optional): Documentation loaded as needed
- **assets/** (optional): Templates, fonts, icons used in output

### Core design principles

#### Progressive Disclosure

Skills use a three-level system:

- **First level (YAML frontmatter):** Always loaded in Claude's system prompt. Provides just enough information for Claude to know when each skill should be used without loading all of it into context.
- **Second level (SKILL.md body):** Loaded when Claude thinks the skill is relevant to the current task. Contains the full instructions and guidance.
- **Third level (Linked files):** Additional files bundled within the skill directory that Claude can choose to navigate and discover only as needed.

This progressive disclosure minimizes token usage while maintaining specialized expertise.

#### Composability

Claude can load multiple skills simultaneously. Your skill should work well alongside others, not assume it's the only capability available.

#### Portability

Skills work identically across Claude.ai, Claude Code, and API. Create a skill once and it works across all surfaces without modification, provided the environment supports any dependencies the skill requires.

### For MCP Builders: Skills + Connectors

> 💡 Building standalone skills without MCP? Skip to [Planning and Design](#chapter-2-planning-and-design) - you can always return here later.

If you already have a working MCP server, you've done the hard part. Skills are the knowledge layer on top - capturing the workflows and best practices you already know, so Claude can apply them consistently.

#### The kitchen analogy

MCP provides the professional kitchen: access to tools, ingredients, and equipment.

Skills provide the recipes: step-by-step instructions on how to create something valuable.

Together, they enable users to accomplish complex tasks without needing to figure out every step themselves.

#### How they work together:

| MCP (Connectivity) | Skills (Knowledge) |
|---|---|
| Connects Claude to your service (Notion, Asana, Linear, etc.) | Teaches Claude how to use your service effectively |
| Provides real-time data access and tool invocation | Captures workflows and best practices |
| What Claude can do | How Claude should do it |

#### Why this matters for your MCP users

**Without skills:**

- Users connect your MCP but don't know what to do next
- Support tickets asking "how do I do X with your integration"
- Each conversation starts from scratch
- Inconsistent results because users prompt differently each time
- Users blame your connector when the real issue is workflow guidance

**With skills:**

- Pre-built workflows activate automatically when needed
- Consistent, reliable tool usage
- Best practices embedded in every interaction
- Lower learning curve for your integration

---

## Chapter 2: Planning and Design

### Start with use cases

Before writing any code, identify 2-3 concrete use cases your skill should enable.

**Good use case definition:**

```
Use Case: Project Sprint Planning
Trigger: User says "help me plan this sprint" or "create sprint tasks"
Steps:
1. Fetch current project status from Linear (via MCP)
2. Analyze team velocity and capacity
3. Suggest task prioritization
4. Create tasks in Linear with proper labels and estimates
Result: Fully planned sprint with tasks created
```

**Ask yourself:**

- What does a user want to accomplish?
- What multi-step workflows does this require?
- Which tools are needed (built-in or MCP?)
- What domain knowledge or best practices should be embedded?

### Common skill use case categories

At Anthropic, we've observed three common use cases:

#### Category 1: Document & Asset Creation

**Used for:** Creating consistent, high-quality output including documents, presentations, apps, designs, code, etc.

**Real example:** frontend-design skill (also see skills for docx, pptx, xlsx, and ppt)

> "Create distinctive, production-grade frontend interfaces with high design quality. Use when building web components, pages, artifacts, posters, or applications."

**Key techniques:**

- Embedded style guides and brand standards
- Template structures for consistent output
- Quality checklists before finalizing
- No external tools required - uses Claude's built-in capabilities

#### Category 2: Workflow Automation

**Used for:** Multi-step processes that benefit from consistent methodology, including coordination across multiple MCP servers.

**Real example:** skill-creator skill

> "Interactive guide for creating new skills. Walks the user through use case definition, frontmatter generation, instruction writing, and validation."

**Key techniques:**

- Step-by-step workflow with validation gates
- Templates for common structures
- Built-in review and improvement suggestions
- Iterative refinement loops

#### Category 3: MCP Enhancement

**Used for:** Workflow guidance to enhance the tool access an MCP server provides.

**Real example:** sentry-code-review skill (from Sentry)

> "Automatically analyzes and fixes detected bugs in GitHub Pull Requests using Sentry's error monitoring data via their MCP server."

**Key techniques:**

- Coordinates multiple MCP calls in sequence
- Embeds domain expertise
- Provides context users would otherwise need to specify
- Error handling for common MCP issues

### Define success criteria

How will you know your skill is working?

These are aspirational targets - rough benchmarks rather than precise thresholds. Aim for rigor but accept that there will be an element of vibes-based assessment. We are actively developing more robust measurement guidance and tooling.

**Quantitative metrics:**

- **Skill triggers on 90% of relevant queries**
  - How to measure: Run 10-20 test queries that should trigger your skill. Track how many times it loads automatically vs. requires explicit invocation.
- **Completes workflow in X tool calls**
  - How to measure: Compare the same task with and without the skill enabled. Count tool calls and total tokens consumed.
- **0 failed API calls per workflow**
  - How to measure: Monitor MCP server logs during test runs. Track retry rates and error codes.

**Qualitative metrics:**

- **Users don't need to prompt Claude about next steps**
  - How to assess: During testing, note how often you need to redirect or clarify. Ask beta users for feedback.
- **Workflows complete without user correction**
  - How to assess: Run the same request 3-5 times. Compare outputs for structural consistency and quality.
- **Consistent results across sessions**
  - How to assess: Can a new user accomplish the task on first try with minimal guidance?

### Technical requirements

#### File structure

```
your-skill-name/
├── SKILL.md              # Required - main skill file
├── scripts/              # Optional - executable code
│   ├── process_data.py   # Example
│   └── validate.sh       # Example
├── references/           # Optional - documentation
│   ├── api-guide.md      # Example
│   └── examples/         # Example
└── assets/               # Optional - templates, etc.
    └── report-template.md # Example
```

#### Critical rules

**SKILL.md naming:**

- Must be exactly `SKILL.md` (case-sensitive)
- No variations accepted (`SKILL.MD`, `skill.md`, etc.)

**Skill folder naming:**

- Use kebab-case: `notion-project-setup` ✅
- No spaces: `Notion Project Setup` ❌
- No underscores: `notion_project_setup` ❌
- No capitals: `NotionProjectSetup` ❌

**No README.md:**

- Don't include `README.md` inside your skill folder
- All documentation goes in `SKILL.md` or `references/`
- Note: when distributing via GitHub, you'll still want a repo-level README for human users — see [Distribution and Sharing](#chapter-4-distribution-and-sharing).

### YAML frontmatter: The most important part

The YAML frontmatter is how Claude decides whether to load your skill. Get this right.

#### Minimal required format

```yaml
---
name: your-skill-name
description: What it does. Use when user asks to [specific phrases].
---
```

That's all you need to start.

#### Field requirements

**name** (required):

- kebab-case only
- No spaces or capitals
- Should match folder name

**description** (required):

- MUST include BOTH:
  - What the skill does
  - When to use it (trigger conditions)
- Under 1024 characters
- No XML tags (`<` or `>`)
- Include specific tasks users might say
- Mention file types if relevant

**license** (optional):

- Use if making skill open source
- Common: MIT, Apache-2.0

**compatibility** (optional):

- 1-500 characters
- Indicates environment requirements: e.g. intended product, required system packages, network access needs, etc.

**metadata** (optional):

- Any custom key-value pairs
- Suggested: author, version, mcp-server
- Example:

```yaml
metadata:
  author: ProjectHub
  version: 1.0.0
  mcp-server: projecthub
```

#### Security restrictions

**Forbidden in frontmatter:**

- XML angle brackets (`<` `>`)
- Skills with "claude" or "anthropic" in name (reserved)

**Why:** Frontmatter appears in Claude's system prompt. Malicious content could inject instructions.

### Writing effective skills

#### The description field

According to Anthropic's engineering blog: "This metadata...provides just enough information for Claude to know when each skill should be used without loading all of it into context." This is the first level of progressive disclosure.

**Structure:**

```
[What it does] + [When to use it] + [Key capabilities]
```

**Examples of good descriptions:**

```yaml
# Good - specific and actionable
description: Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for "design specs", "component documentation", or "design-to-code handoff".

# Good - includes trigger phrases
description: Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions "sprint", "Linear tasks", "project planning", or asks to "create tickets".

# Good - clear value proposition
description: End-to-end customer onboarding workflow for PayFlow. Handles account creation, payment setup, and subscription management. Use when user says "onboard new customer", "set up subscription", or "create PayFlow account".
```

**Examples of bad descriptions:**

```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.

# Too technical, no user triggers
description: Implements the Project entity model with hierarchical relationships.
```

#### Writing the main instructions

After the frontmatter, write the actual instructions in Markdown.

**Recommended structure:**

Adapt this template for your skill. Replace bracketed sections with your specific content.

```markdown
---
name: your-skill
description: [.]
---

# Your Skill Name

# Instructions

# Step 1: [First Major Step]
Clear explanation of what happens.

Example:
```bash
python scripts/fetch_data.py --project-id PROJECT_ID
```
Expected output: [describe what success looks like]

(Add more steps as needed)

# Examples

## Example 1: [common scenario]
User says: "Set up a new marketing campaign"
Actions:
1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters
Result: Campaign created with confirmation link

(Add more examples as needed)

# Troubleshooting

## Error: [Common error message]
Cause: [Why it happens]
Solution: [How to fix]

(Add more error cases as needed)
```

#### Best Practices for Instructions

**Be Specific and Actionable**

✅ Good:

```
Run `python scripts/validate.py --input {filename}` to check data format.
If validation fails, common issues include:
- Missing required fields (add them to the CSV)
- Invalid date formats (use YYYY-MM-DD)
```

❌ Bad:

```
Validate the data before proceeding.
```

**Include error handling**

```markdown
# Common Issues

# MCP Connection Failed
If you see "Connection refused":
1. Verify MCP server is running: Check Settings > Extensions
2. Confirm API key is valid
3. Try reconnecting: Settings > Extensions > [Your Service] > Reconnect
```

**Reference bundled resources clearly**

```
Before writing queries, consult `references/api-patterns.md` for:
- Rate limiting guidance
- Pagination patterns
- Error codes and handling
```

**Use progressive disclosure**

Keep SKILL.md focused on core instructions. Move detailed documentation to `references/` and link to it. (See [Core Design Principles](#core-design-principles) for how the three-level system works.)

---

## Chapter 3: Testing and Iteration

Skills can be tested at varying levels of rigor depending on your needs:

- **Manual testing in Claude.ai** - Run queries directly and observe behavior. Fast iteration, no setup required.
- **Scripted testing in Claude Code** - Automate test cases for repeatable validation across changes.
- **Programmatic testing via skills API** - Build evaluation suites that run systematically against defined test sets.

Choose the approach that matches your quality requirements and the visibility of your skill. A skill used internally by a small team has different testing needs than one deployed to thousands of enterprise users.

> **Pro Tip: Iterate on a single task before expanding**
>
> We've found that the most effective skill creators iterate on a single challenging task until Claude succeeds, then extract the winning approach into a skill. This leverages Claude's in-context learning and provides faster signal than broad testing. Once you have a working foundation, expand to multiple test cases for coverage.

### Recommended Testing Approach

Based on early experience, effective skills testing typically covers three areas:

#### 1. Triggering tests

**Goal:** Ensure your skill loads at the right times.

**Test cases:**

- ✅ Triggers on obvious tasks
- ✅ Triggers on paraphrased requests
- ❌ Doesn't trigger on unrelated topics

**Example test suite:**

```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"
- "Initialize a ProjectHub project for Q4 planning"

Should NOT trigger:
- "What's the weather in San Francisco?"
- "Help me write Python code"
- "Create a spreadsheet" (unless ProjectHub skill handles sheets)
```

#### 2. Functional tests

**Goal:** Verify the skill produces correct outputs.

**Test cases:**

- Valid outputs generated
- API calls succeed
- Error handling works
- Edge cases covered

**Example:**

```
Test: Create project with 5 tasks
Given: Project name "Q4 Planning", 5 task descriptions
When: Skill executes workflow
Then:
  - Project created in ProjectHub
  - 5 tasks created with correct properties
  - All tasks linked to project
  - No API errors
```

#### 3. Performance comparison

**Goal:** Prove the skill improves results vs. baseline.

Use the metrics from [Define Success Criteria](#define-success-criteria). Here's what a comparison might look like.

**Baseline comparison:**

```
Without skill:
- User provides instructions each time
- 15 back-and-forth messages
- 3 failed API calls requiring retry
- 12,000 tokens consumed

With skill:
- Automatic workflow execution
- 2 clarifying questions only
- 0 failed API calls
- 6,000 tokens consumed
```

### Using the skill-creator skill

The skill-creator skill - available in Claude.ai via plugin directory or download for Claude Code - can help you build and iterate on skills. If you have an MCP server and know your top 2–3 workflows, you can build and test a functional skill in a single sitting - often in 15–30 minutes.

**Creating skills:**

- Generate skills from natural language descriptions
- Produce properly formatted SKILL.md with frontmatter
- Suggest trigger phrases and structure

**Reviewing skills:**

- Flag common issues (vague descriptions, missing triggers, structural problems)
- Identify potential over/under-triggering risks
- Suggest test cases based on the skill's stated purpose

**Iterative improvement:**

- After using your skill and encountering edge cases or failures, bring those examples back to skill-creator
- Example: "Use the issues & solution identified in this chat to improve how the skill handles [specific edge case]"

**To use:**

```
"Use the skill-creator skill to help me build a skill for [your use case]"
```

> **Note:** skill-creator helps you design and refine skills but does not execute automated test suites or produce quantitative evaluation results.

### Iteration based on feedback

Skills are living documents. Plan to iterate based on:

**Undertriggering signals:**

- Skill doesn't load when it should
- Users manually enabling it
- Support questions about when to use it

**Solution:** Add more detail and nuance to the description - this may include keywords particularly for technical terms

**Overtriggering signals:**

- Skill loads for irrelevant queries
- Users disabling it
- Confusion about purpose

**Solution:** Add negative triggers, be more specific

**Execution issues:**

- Inconsistent results
- API call failures
- User corrections needed

**Solution:** Improve instructions, add error handling

---

## Chapter 4: Distribution and Sharing

Skills make your MCP integration more complete. As users compare connectors, those with skills offer a faster path to value, giving you an edge over MCP-only alternatives.

### Current distribution model (January 2026)

**How individual users get skills:**

1. Download the skill folder
2. Zip the folder (if needed)
3. Upload to Claude.ai via Settings > Capabilities > Skills
4. Or place in Claude Code skills directory

**Organization-level skills:**

- Admins can deploy skills workspace-wide (shipped December 18, 2025)
- Automatic updates
- Centralized management

### An open standard

We've published Agent Skills as an open standard. Like MCP, we believe skills should be portable across tools and platforms - the same skill should work whether you're using Claude or other AI platforms. That said, some skills are designed to take full advantage of a specific platform's capabilities; authors can note this in the skill's compatibility field. We've been collaborating with members of the ecosystem on the standard, and we're excited by early adoption.

### Using skills via API

For programmatic use cases - such as building applications, agents, or automated workflows that leverage skills - the API provides direct control over skill management and execution.

**Key capabilities:**

- `/v1/skills` endpoint for listing and managing skills
- Add skills to Messages API requests via the `container.skills` parameter
- Version control and management through the Claude Console
- Works with the Claude Agent SDK for building custom agents

**When to use skills via the API vs. Claude.ai:**

| Use Case | Best Surface |
|---|---|
| End users interacting with skills directly | Claude.ai / Claude Code |
| Manual testing and iteration during development | Claude.ai / Claude Code |
| Individual, ad-hoc workflows | Claude.ai / Claude Code |
| Applications using skills programmatically | API |
| Production deployments at scale | API |
| Automated pipelines and agent systems | API |

> **Note:** Skills in the API require the Code Execution Tool beta, which provides the secure environment skills need to run.

**For implementation details, see:**

- Skills API Quickstart
- Create Custom skills
- Skills in the Agent SDK

### Recommended approach today

Start by hosting your skill on GitHub with a public repo, clear README (for human visitors — this is separate from your skill folder, which should not contain a README.md), and example usage with screenshots. Then add a section to your MCP documentation that links to the skill, explains why using both together is valuable, and provides a quick-start guide.

1. **Host on GitHub**
   - Public repo for open-source skills
   - Clear README with installation instructions
   - Example usage and screenshots

2. **Document in Your MCP Repo**
   - Link to skills from MCP documentation
   - Explain the value of using both together
   - Provide quick-start guide

3. **Create an Installation Guide**

```markdown
# Installing the [Your Service] skill

1. Download the skill:
   - Clone repo: `git clone https://github.com/yourcompany/skills`
   - Or download ZIP from Releases

2. Install in Claude:
   - Open Claude.ai > Settings > Skills
   - Click "Upload skill"
   - Select the skill folder (zipped)

3. Enable the skill:
   - Toggle on the [Your Service] skill
   - Ensure your MCP server is connected

4. Test:
   - Ask Claude: "Set up a new project in [Your Service]"
```

### Positioning your skill

How you describe your skill determines whether users understand its value and actually try it. When writing about your skill—in your README, documentation, or marketing—keep these principles in mind.

**Focus on outcomes, not features:**

✅ Good:

```
"The ProjectHub skill enables teams to set up complete project workspaces in seconds — including pages, databases, and templates — instead of spending 30 minutes on manual setup."
```

❌ Bad:

```
"The ProjectHub skill is a folder containing YAML frontmatter and Markdown instructions that calls our MCP server tools."
```

**Highlight the MCP + skills story:**

```
"Our MCP server gives Claude access to your Linear projects. Our skills teach Claude your team's sprint planning workflow. Together, they enable AI-powered project management."
```

---

## Chapter 5: Patterns and Troubleshooting

These patterns emerged from skills created by early adopters and internal teams. They represent common approaches we've seen work well, not prescriptive templates.

### Choosing your approach: Problem-first vs. tool-first

Think of it like Home Depot. You might walk in with a problem - "I need to fix a kitchen cabinet" - and an employee points you to the right tools. Or you might pick out a new drill and ask how to use it for your specific job.

Skills work the same way:

- **Problem-first:** "I need to set up a project workspace" → Your skill orchestrates the right MCP calls in the right sequence. Users describe outcomes; the skill handles the tools.
- **Tool-first:** "I have Notion MCP connected" → Your skill teaches Claude the optimal workflows and best practices. Users have access; the skill provides expertise.

Most skills lean one direction. Knowing which framing fits your use case helps you choose the right pattern below.

### Pattern 1: Sequential workflow orchestration

**Use when:** Your users need multi-step processes in a specific order.

**Example structure:**

```markdown
# Workflow: Onboard New Customer

# Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

# Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

# Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

# Step 4: Send Welcome Email
Call MCP tool: `send_email`
Template: welcome_email_template
```

**Key techniques:**

- Explicit step ordering
- Dependencies between steps
- Validation at each stage
- Rollback instructions for failures

### Pattern 2: Multi-MCP coordination

**Use when:** Workflows span multiple services.

**Example: Design-to-development handoff**

```markdown
# Phase 1: Design Export (Figma MCP)
1. Export design assets from Figma
2. Generate design specifications
3. Create asset manifest

# Phase 2: Asset Storage (Drive MCP)
1. Create project folder in Drive
2. Upload all assets
3. Generate shareable links

# Phase 3: Task Creation (Linear MCP)
1. Create development tasks
2. Attach asset links to tasks
3. Assign to engineering team

# Phase 4: Notification (Slack MCP)
1. Post handoff summary to #engineering
2. Include asset links and task references
```

**Key techniques:**

- Clear phase separation
- Data passing between MCPs
- Validation before moving to next phase
- Centralized error handling

### Pattern 3: Iterative refinement

**Use when:** Output quality improves with iteration.

**Example: Report generation**

```markdown
# Iterative Report Creation

# Initial Draft
1. Fetch data via MCP
2. Generate first draft report
3. Save to temporary file

# Quality Check
1. Run validation script: `scripts/check_report.py`
2. Identify issues:
   - Missing sections
   - Inconsistent formatting
   - Data validation errors

# Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

# Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

**Key techniques:**

- Explicit quality criteria
- Iterative improvement
- Validation scripts
- Know when to stop iterating

### Pattern 4: Context-aware tool selection

**Use when:** Same outcome, different tools depending on context.

**Example: File storage**

```markdown
# Smart File Storage

# Decision Tree
1. Check file type and size
2. Determine best storage location:
   - Large files (>10MB): Use cloud storage MCP
   - Collaborative docs: Use Notion/Docs MCP
   - Code files: Use GitHub MCP
   - Temporary files: Use local storage

# Execute Storage
Based on decision:
- Call appropriate MCP tool
- Apply service-specific metadata
- Generate access link

# Provide Context to User
Explain why that storage was chosen
```

**Key techniques:**

- Clear decision criteria
- Fallback options
- Transparency about choices

### Pattern 5: Domain-specific intelligence

**Use when:** Your skill adds specialized knowledge beyond tool access.

**Example: Financial compliance**

```markdown
# Payment Processing with Compliance

# Before Processing (Compliance Check)
1. Fetch transaction details via MCP
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction allowances
   - Assess risk level
3. Document compliance decision

# Processing
IF compliance passed:
  - Call payment processing MCP tool
  - Apply appropriate fraud checks
  - Process transaction
ELSE:
  - Flag for review
  - Create compliance case

# Audit Trail
- Log all compliance checks
- Record processing decisions
- Generate audit report
```

**Key techniques:**

- Domain expertise embedded in logic
- Compliance before action
- Comprehensive documentation
- Clear governance

### Troubleshooting

#### Skill won't upload

**Error: "Could not find SKILL.md in uploaded folder"**

Cause: File not named exactly `SKILL.md`

Solution:

- Rename to `SKILL.md` (case-sensitive)
- Verify with: `ls -la` should show `SKILL.md`

**Error: "Invalid frontmatter"**

Cause: YAML formatting issue

Common mistakes:

```yaml
# Wrong - missing delimiters
name: my-skill
description: Does things

# Wrong - unclosed quotes
name: my-skill
description: "Does things

# Correct
---
name: my-skill
description: Does things
---
```

**Error: "Invalid skill name"**

Cause: Name has spaces or capitals

```yaml
# Wrong
name: My Cool Skill

# Correct
name: my-cool-skill
```

#### Skill doesn't trigger

**Symptom:** Skill never loads automatically

**Fix:** Revise your description field. See [The Description Field](#the-description-field) for good/bad examples.

Quick checklist:

- Is it too generic? ("Helps with projects" won't work)
- Does it include trigger phrases users would actually say?
- Does it mention relevant file types if applicable?

**Debugging approach:**

Ask Claude: "When would you use the [skill name] skill?" Claude will quote the description back. Adjust based on what's missing.

#### Skill triggers too often

**Symptom:** Skill loads for unrelated queries

**Solutions:**

1. **Add negative triggers**

```yaml
description: Advanced data analysis for CSV files. Use for statistical modeling, regression, clustering. Do NOT use for simple data exploration (use data-viz skill instead).
```

2. **Be more specific**

```yaml
# Too broad
description: Processes documents

# More specific
description: Processes PDF legal documents for contract review
```

3. **Clarify scope**

```yaml
description: PayFlow payment processing for e-commerce. Use specifically for online payment workflows, not for general financial queries.
```

#### MCP connection issues

**Symptom:** Skill loads but MCP calls fail

**Checklist:**

1. **Verify MCP server is connected**
   - Claude.ai: Settings > Extensions > [Your Service]
   - Should show "Connected" status

2. **Check authentication**
   - API keys valid and not expired
   - Proper permissions/scopes granted
   - OAuth tokens refreshed

3. **Test MCP independently**
   - Ask Claude to call MCP directly (without skill)
   - "Use [Service] MCP to fetch my projects"
   - If this fails, issue is MCP not skill

4. **Verify tool names**
   - Skill references correct MCP tool names
   - Check MCP server documentation
   - Tool names are case-sensitive

#### Instructions not followed

**Symptom:** Skill loads but Claude doesn't follow instructions

**Common causes:**

1. **Instructions too verbose**
   - Keep instructions concise
   - Use bullet points and numbered lists
   - Move detailed reference to separate files

2. **Instructions buried**
   - Put critical instructions at the top
   - Use `## Important` or `## Critical` headers
   - Repeat key points if needed

3. **Ambiguous language**

```markdown
# Bad
Make sure to validate things properly

# Good
CRITICAL: Before calling create_project, verify:
- Project name is non-empty
- At least one team member assigned
- Start date is not in the past
```

> **Advanced technique:** For critical validations, consider bundling a script that performs the checks programmatically rather than relying on language instructions. Code is deterministic; language interpretation isn't. See the Office skills for examples of this pattern.

4. **Model "laziness"** — Add explicit encouragement:

```markdown
# Performance Notes
- Take your time to do this thoroughly
- Quality is more important than speed
- Do not skip validation steps
```

> **Note:** Adding this to user prompts is more effective than in SKILL.md

#### Large context issues

**Symptom:** Skill seems slow or responses degraded

**Causes:**

- Skill content too large
- Too many skills enabled simultaneously
- All content loaded instead of progressive disclosure

**Solutions:**

1. **Optimize SKILL.md size**
   - Move detailed docs to `references/`
   - Link to references instead of inline
   - Keep SKILL.md under 5,000 words

2. **Reduce enabled skills**
   - Evaluate if you have more than 20-50 skills enabled simultaneously
   - Recommend selective enablement
   - Consider skill "packs" for related capabilities

---

## Chapter 6: Resources and References

If you're building your first skill, start with the Best Practices Guide, then reference the API docs as needed.

### Official Documentation

**Anthropic Resources:**

- Best Practices Guide
- Skills Documentation
- API Reference
- MCP Documentation

**Blog Posts:**

- Introducing Agent Skills
- Engineering Blog: Equipping Agents for the Real World
- Skills Explained
- How to Create Skills for Claude
- Building Skills for Claude Code
- Improving Frontend Design through Skills

### Example skills

**Public skills repository:**

- GitHub: [anthropics/skills](https://github.com/anthropics/skills)
- Contains Anthropic-created skills you can customize

### Tools and Utilities

**skill-creator skill:**

- Built into Claude.ai and available for Claude Code
- Can generate skills from descriptions
- Reviews and provides recommendations
- Use: "Help me build a skill using skill-creator"

**Validation:**

- skill-creator can assess your skills
- Ask: "Review this skill and suggest improvements"

### Getting Support

**For Technical Questions:**

- General questions: Community forums at the Claude Developers Discord

**For Bug Reports:**

- GitHub Issues: anthropics/skills/issues
- Include: Skill name, error message, steps to reproduce

---

## Reference A: Quick Checklist

Use this checklist to validate your skill before and after upload. If you want a faster start, use the skill-creator skill to generate your first draft, then run through this list to make sure you haven't missed anything.

### Before you start

- [ ] Identified 2-3 concrete use cases
- [ ] Tools identified (built-in or MCP)
- [ ] Reviewed this guide and example skills
- [ ] Planned folder structure

### During development

- [ ] Folder named in kebab-case
- [ ] SKILL.md file exists (exact spelling)
- [ ] YAML frontmatter has `---` delimiters
- [ ] name field: kebab-case, no spaces, no capitals
- [ ] description includes WHAT and WHEN
- [ ] No XML tags (`<` `>`) anywhere
- [ ] Instructions are clear and actionable
- [ ] Error handling included
- [ ] Examples provided
- [ ] References clearly linked

### Before upload

- [ ] Tested triggering on obvious tasks
- [ ] Tested triggering on paraphrased requests
- [ ] Verified doesn't trigger on unrelated topics
- [ ] Functional tests pass
- [ ] Tool integration works (if applicable)
- [ ] Compressed as .zip file

### After upload

- [ ] Test in real conversations
- [ ] Monitor for under/over-triggering
- [ ] Collect user feedback
- [ ] Iterate on description and instructions
- [ ] Update version in metadata

---

## Reference B: YAML Frontmatter

### Required fields

```yaml
---
name: skill-name-in-kebab-case
description: What it does and when to use it. Include specific trigger phrases.
---
```

### All optional fields

```yaml
name: skill-name
description: [required description]
license: MIT                          # Optional: License for open-source
allowed-tools: "Bash(python:*) Bash(npm:*) WebFetch"  # Optional: Restrict tool access
metadata:                             # Optional: Custom fields
  author: Company Name
  version: 1.0.0
  mcp-server: server-name
  category: productivity
  tags: [project-management, automation]
  documentation: https://example.com/docs
  support: support@example.com
```

### Security notes

**Allowed:**

- Any standard YAML types (strings, numbers, booleans, lists, objects)
- Custom metadata fields
- Long descriptions (up to 1024 characters)

**Forbidden:**

- XML angle brackets (`<` `>`) - security restriction
- Code execution in YAML (uses safe YAML parsing)
- Skills named with "claude" or "anthropic" prefix (reserved)

---

## Reference C: Complete Skill Examples

For full, production-ready skills demonstrating the patterns in this guide:

- **Document Skills** - PDF, DOCX, PPTX, XLSX creation
- **Example Skills** - Various workflow patterns
- **Partner Skills Directory** - View skills from various partners such as Asana, Atlassian, Canva, Figma, Sentry, Zapier, and more

These repositories stay up-to-date and include additional examples beyond what's covered here. Clone them, modify them for your use case, and use them as templates.


> [A complete guide to building skills for Claude | Claude Blog](https://claude.com/blog/complete-guide-to-building-skills-for-claude)에서 공개한 [PDF](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)를 마크다운 기반으로 변경한 파일입니다.
> Cladue Opus 4.5를 사용해 번역하였습니다.

----

# Claude를 위한 스킬 구축 완벽 가이드

---

## 목차

- [소개](#소개)
- [1장: 기본 개념](#1장-기본-개념)
- [2장: 계획 및 설계](#2장-계획-및-설계)
- [3장: 테스트 및 반복](#3장-테스트-및-반복)
- [4장: 배포 및 공유](#4장-배포-및-공유)
- [5장: 패턴 및 문제 해결](#5장-패턴-및-문제-해결)
- [6장: 리소스 및 참고 자료](#6장-리소스-및-참고-자료)
- [참고 A: 빠른 체크리스트](#참고-a-빠른-체크리스트)
- [참고 B: YAML 프론트매터](#참고-b-yaml-프론트매터)
- [참고 C: 완전한 스킬 예제](#참고-c-완전한-스킬-예제)

---

## 소개

스킬은 Claude에게 특정 작업이나 워크플로우를 처리하는 방법을 가르치는 일련의 지침으로, 간단한 폴더 형태로 패키징됩니다. 스킬은 Claude를 사용자의 특정 요구에 맞게 커스터마이징하는 가장 강력한 방법 중 하나입니다. 매번 대화할 때마다 선호 사항, 프로세스, 도메인 전문 지식을 다시 설명하는 대신, 스킬을 통해 한 번만 가르치면 매번 그 효과를 누릴 수 있습니다.

스킬은 반복 가능한 워크플로우가 있을 때 강력합니다: 사양서로부터 프론트엔드 디자인 생성, 일관된 방법론으로 리서치 수행, 팀 스타일 가이드를 따르는 문서 작성, 또는 다단계 프로세스 조율 등이 해당됩니다. 스킬은 코드 실행 및 문서 생성과 같은 Claude의 기본 기능과 잘 연동됩니다. MCP 통합을 구축하는 분들에게 스킬은 원시 도구 접근을 신뢰할 수 있고 최적화된 워크플로우로 전환하는 데 도움이 되는 강력한 추가 레이어를 제공합니다.

이 가이드는 효과적인 스킬을 구축하는 데 필요한 모든 것을 다룹니다 - 계획 및 구조부터 테스트 및 배포까지. 자신, 팀 또는 커뮤니티를 위한 스킬을 구축하든, 전반에 걸쳐 실용적인 패턴과 실제 사례를 확인할 수 있습니다.

**학습 내용:**

- 스킬 구조에 대한 기술 요구 사항 및 모범 사례
- 독립형 스킬과 MCP 강화 워크플로우를 위한 패턴
- 다양한 사용 사례에서 효과적인 것으로 확인된 패턴
- 스킬 테스트, 반복 및 배포 방법

**대상 독자:**

- Claude가 특정 워크플로우를 일관되게 따르도록 하려는 개발자
- Claude가 특정 워크플로우를 따르도록 하려는 파워 유저
- 조직 전체에서 Claude의 작동 방식을 표준화하려는 팀

### 이 가이드를 읽는 두 가지 경로

독립형 스킬을 구축하시나요? 기본 개념, 계획 및 설계, 카테고리 1-2에 집중하세요. MCP 통합을 강화하시나요? "스킬 + MCP" 섹션과 카테고리 3이 적합합니다. 두 경로 모두 동일한 기술 요구 사항을 공유하지만, 사용 사례에 맞는 것을 선택하시면 됩니다.

**이 가이드에서 얻을 수 있는 것:** 가이드를 마치면 한 번의 작업 세션에서 기능적인 스킬을 구축할 수 있게 됩니다. skill-creator를 사용하여 첫 번째 작동하는 스킬을 구축하고 테스트하는 데 약 15-30분이 소요됩니다.

시작해 봅시다.

---

## 1장: 기본 개념

### 스킬이란 무엇인가?

스킬은 다음을 포함하는 폴더입니다:

- **SKILL.md** (필수): YAML 프론트매터가 포함된 마크다운 형식의 지침
- **scripts/** (선택): 실행 가능한 코드 (Python, Bash 등)
- **references/** (선택): 필요 시 로드되는 문서
- **assets/** (선택): 출력에 사용되는 템플릿, 폰트, 아이콘

### 핵심 설계 원칙

#### 점진적 공개(Progressive Disclosure)

스킬은 세 단계 시스템을 사용합니다:

- **첫 번째 단계 (YAML 프론트매터):** 항상 Claude의 시스템 프롬프트에 로드됩니다. 전체를 컨텍스트에 로드하지 않고도 각 스킬이 언제 사용되어야 하는지 Claude가 알 수 있을 만큼의 충분한 정보를 제공합니다.
- **두 번째 단계 (SKILL.md 본문):** Claude가 해당 스킬이 현재 작업에 관련이 있다고 판단할 때 로드됩니다. 전체 지침과 안내를 포함합니다.
- **세 번째 단계 (연결된 파일):** 스킬 디렉토리 내에 번들된 추가 파일로, Claude가 필요할 때만 탐색하고 발견할 수 있습니다.

이 점진적 공개는 전문적 역량을 유지하면서 토큰 사용량을 최소화합니다.

#### 조합 가능성(Composability)

Claude는 여러 스킬을 동시에 로드할 수 있습니다. 스킬은 다른 스킬과 함께 잘 작동해야 하며, 유일한 기능이라고 가정해서는 안 됩니다.

#### 이식성(Portability)

스킬은 Claude.ai, Claude Code, API 전반에서 동일하게 작동합니다. 한 번 스킬을 생성하면 환경이 스킬이 요구하는 종속성을 지원하는 한, 수정 없이 모든 플랫폼에서 작동합니다.

### MCP 빌더를 위한: 스킬 + 커넥터

> 💡 MCP 없이 독립형 스킬을 구축하시나요? [계획 및 설계](#2장-계획-및-설계)로 건너뛰세요 - 나중에 언제든 돌아올 수 있습니다.

이미 작동하는 MCP 서버가 있다면, 어려운 부분은 완료된 것입니다. 스킬은 그 위에 올라가는 지식 레이어로, 이미 알고 있는 워크플로우와 모범 사례를 캡처하여 Claude가 일관되게 적용할 수 있도록 합니다.

#### 주방 비유

MCP는 전문 주방을 제공합니다: 도구, 재료, 장비에 대한 접근.

스킬은 레시피를 제공합니다: 가치 있는 것을 만드는 단계별 지침.

함께 사용하면, 사용자가 모든 단계를 직접 파악할 필요 없이 복잡한 작업을 수행할 수 있습니다.

#### 함께 작동하는 방식:

| MCP (연결성) | 스킬 (지식) |
|---|---|
| Claude를 사용자 서비스에 연결 (Notion, Asana, Linear 등) | Claude에게 서비스를 효과적으로 사용하는 방법을 교육 |
| 실시간 데이터 접근 및 도구 호출 제공 | 워크플로우 및 모범 사례 캡처 |
| Claude가 할 수 있는 것 | Claude가 어떻게 해야 하는지 |

#### MCP 사용자에게 중요한 이유

**스킬 없이:**

- 사용자가 MCP를 연결하지만 다음에 무엇을 해야 할지 모름
- "통합으로 X를 어떻게 하나요"라는 지원 티켓 발생
- 매 대화가 처음부터 시작
- 사용자마다 다르게 프롬프트하여 일관되지 않은 결과
- 실제 문제가 워크플로우 안내인데 사용자가 커넥터를 탓함

**스킬과 함께:**

- 사전 구축된 워크플로우가 필요할 때 자동으로 활성화
- 일관되고 신뢰할 수 있는 도구 사용
- 모든 상호작용에 모범 사례가 내장
- 통합에 대한 학습 곡선 감소

---

## 2장: 계획 및 설계

### 사용 사례부터 시작하기

코드를 작성하기 전에, 스킬이 가능하게 해야 할 2-3개의 구체적인 사용 사례를 식별하세요.

**좋은 사용 사례 정의:**

```
사용 사례: 프로젝트 스프린트 계획
트리거: 사용자가 "이 스프린트 계획 도와줘" 또는 "스프린트 작업 만들어줘"라고 말함
단계:
1. Linear에서 현재 프로젝트 상태 가져오기 (MCP 통해)
2. 팀 속도 및 역량 분석
3. 작업 우선순위 제안
4. 적절한 라벨과 예상치로 Linear에 작업 생성
결과: 작업이 생성된 완전한 스프린트 계획
```

**스스로에게 물어보세요:**

- 사용자가 무엇을 달성하고 싶어 하는가?
- 이것이 어떤 다단계 워크플로우를 필요로 하는가?
- 어떤 도구가 필요한가 (내장 또는 MCP?)
- 어떤 도메인 지식이나 모범 사례가 내장되어야 하는가?

### 일반적인 스킬 사용 사례 카테고리

Anthropic에서 세 가지 일반적인 사용 사례를 관찰했습니다:

#### 카테고리 1: 문서 및 에셋 생성

**용도:** 문서, 프레젠테이션, 앱, 디자인, 코드 등 일관되고 고품질의 출력 생성.

**실제 예시:** frontend-design 스킬 (docx, pptx, xlsx, ppt 스킬도 참조)

> "독특하고 프로덕션 수준의 프론트엔드 인터페이스를 높은 디자인 품질로 생성합니다. 웹 컴포넌트, 페이지, 아티팩트, 포스터 또는 애플리케이션을 구축할 때 사용하세요."

**핵심 기법:**

- 내장된 스타일 가이드 및 브랜드 표준
- 일관된 출력을 위한 템플릿 구조
- 최종 완료 전 품질 체크리스트
- 외부 도구 불필요 - Claude의 내장 기능 사용

#### 카테고리 2: 워크플로우 자동화

**용도:** 일관된 방법론의 이점을 얻는 다단계 프로세스, 여러 MCP 서버 간의 조율 포함.

**실제 예시:** skill-creator 스킬

> "새로운 스킬을 만들기 위한 대화형 가이드. 사용 사례 정의, 프론트매터 생성, 지침 작성 및 검증을 안내합니다."

**핵심 기법:**

- 검증 게이트가 있는 단계별 워크플로우
- 일반적인 구조를 위한 템플릿
- 내장된 검토 및 개선 제안
- 반복적 개선 루프

#### 카테고리 3: MCP 강화

**용도:** MCP 서버가 제공하는 도구 접근을 향상시키기 위한 워크플로우 안내.

**실제 예시:** sentry-code-review 스킬 (Sentry 제공)

> "Sentry의 MCP 서버를 통한 에러 모니터링 데이터를 사용하여 GitHub Pull Request에서 감지된 버그를 자동으로 분석하고 수정합니다."

**핵심 기법:**

- 여러 MCP 호출을 순서대로 조율
- 도메인 전문 지식 내장
- 사용자가 별도로 지정해야 할 컨텍스트 제공
- 일반적인 MCP 문제에 대한 에러 처리

### 성공 기준 정의

스킬이 잘 작동하는지 어떻게 알 수 있을까요?

이것은 목표치입니다 - 정확한 임계값이 아닌 대략적인 벤치마크입니다. 엄격함을 목표로 하되 감각 기반 평가의 요소가 있을 것임을 받아들이세요. 보다 견고한 측정 가이드 및 도구를 적극적으로 개발 중입니다.

**정량적 지표:**

- **관련 쿼리의 90%에서 스킬 트리거**
  - 측정 방법: 스킬이 트리거되어야 할 10-20개의 테스트 쿼리를 실행합니다. 자동으로 로드된 횟수와 명시적 호출이 필요했던 횟수를 추적합니다.
- **X회의 도구 호출로 워크플로우 완료**
  - 측정 방법: 스킬 활성화 유무로 동일한 작업을 비교합니다. 도구 호출 횟수와 총 토큰 소비량을 계산합니다.
- **워크플로우당 API 호출 실패 0회**
  - 측정 방법: 테스트 실행 중 MCP 서버 로그를 모니터링합니다. 재시도율과 에러 코드를 추적합니다.

**정성적 지표:**

- **사용자가 Claude에게 다음 단계를 프롬프트할 필요 없음**
  - 평가 방법: 테스트 중 리디렉션이나 명확화가 필요한 빈도를 기록합니다. 베타 사용자에게 피드백을 요청합니다.
- **사용자 수정 없이 워크플로우 완료**
  - 평가 방법: 동일한 요청을 3-5회 실행합니다. 구조적 일관성과 품질에 대해 출력을 비교합니다.
- **세션 간 일관된 결과**
  - 평가 방법: 새 사용자가 최소한의 안내로 첫 시도에서 작업을 완료할 수 있는가?

### 기술 요구 사항

#### 파일 구조

```
your-skill-name/
├── SKILL.md              # 필수 - 메인 스킬 파일
├── scripts/              # 선택 - 실행 가능한 코드
│   ├── process_data.py   # 예시
│   └── validate.sh       # 예시
├── references/           # 선택 - 문서
│   ├── api-guide.md      # 예시
│   └── examples/         # 예시
└── assets/               # 선택 - 템플릿 등
    └── report-template.md # 예시
```

#### 중요 규칙

**SKILL.md 네이밍:**

- 정확히 `SKILL.md`여야 함 (대소문자 구분)
- 변형 불가 (`SKILL.MD`, `skill.md` 등)

**스킬 폴더 네이밍:**

- 케밥 케이스 사용: `notion-project-setup` ✅
- 공백 불가: `Notion Project Setup` ❌
- 언더스코어 불가: `notion_project_setup` ❌
- 대문자 불가: `NotionProjectSetup` ❌

**README.md 금지:**

- 스킬 폴더 내에 `README.md`를 포함하지 마세요
- 모든 문서는 `SKILL.md` 또는 `references/`에 작성
- 참고: GitHub를 통해 배포할 때는 인간 사용자를 위한 저장소 수준의 README가 여전히 필요합니다 — [배포 및 공유](#4장-배포-및-공유) 참조.

### YAML 프론트매터: 가장 중요한 부분

YAML 프론트매터는 Claude가 스킬을 로드할지 결정하는 방법입니다. 이것을 정확히 작성하세요.

#### 최소 필수 형식

```yaml
---
name: your-skill-name
description: 무엇을 하는지. 사용자가 [특정 문구]를 요청할 때 사용.
---
```

시작하는 데 이것만 있으면 됩니다.

#### 필드 요구 사항

**name** (필수):

- 케밥 케이스만 가능
- 공백이나 대문자 불가
- 폴더 이름과 일치해야 함

**description** (필수):

- 반드시 두 가지를 모두 포함:
  - 스킬이 하는 것
  - 언제 사용하는지 (트리거 조건)
- 1024자 미만
- XML 태그 (`<` 또는 `>`) 불가
- 사용자가 실제로 말할 수 있는 특정 작업 포함
- 관련 파일 유형이 있으면 언급

**license** (선택):

- 스킬을 오픈 소스로 만들 때 사용
- 일반적: MIT, Apache-2.0

**compatibility** (선택):

- 1-500자
- 환경 요구 사항 표시: 예) 대상 제품, 필요한 시스템 패키지, 네트워크 접근 요구 등

**metadata** (선택):

- 모든 커스텀 키-값 쌍
- 권장: author, version, mcp-server
- 예시:

```yaml
metadata:
  author: ProjectHub
  version: 1.0.0
  mcp-server: projecthub
```

#### 보안 제한

**프론트매터에서 금지:**

- XML 꺾쇠 괄호 (`<` `>`)
- 이름에 "claude" 또는 "anthropic"이 포함된 스킬 (예약됨)

**이유:** 프론트매터는 Claude의 시스템 프롬프트에 나타납니다. 악의적인 콘텐츠가 지침을 주입할 수 있습니다.

### 효과적인 스킬 작성

#### description 필드

Anthropic 엔지니어링 블로그에 따르면: "이 메타데이터는... Claude가 전체를 컨텍스트에 로드하지 않고도 각 스킬이 언제 사용되어야 하는지 알 수 있을 만큼의 충분한 정보를 제공합니다." 이것이 점진적 공개의 첫 번째 단계입니다.

**구조:**

```
[하는 것] + [언제 사용하는지] + [주요 기능]
```

**좋은 설명 예시:**

```yaml
# 좋음 - 구체적이고 실행 가능
description: Figma 디자인 파일을 분석하고 개발자 핸드오프 문서를 생성합니다. 사용자가 .fig 파일을 업로드하거나, "디자인 사양", "컴포넌트 문서화", "디자인-코드 핸드오프"를 요청할 때 사용합니다.

# 좋음 - 트리거 문구 포함
description: 스프린트 계획, 작업 생성, 상태 추적을 포함한 Linear 프로젝트 워크플로우를 관리합니다. 사용자가 "스프린트", "Linear 작업", "프로젝트 계획"을 언급하거나 "티켓 만들어줘"를 요청할 때 사용합니다.

# 좋음 - 명확한 가치 제안
description: PayFlow를 위한 엔드투엔드 고객 온보딩 워크플로우. 계정 생성, 결제 설정 및 구독 관리를 처리합니다. 사용자가 "새 고객 온보딩", "구독 설정", "PayFlow 계정 생성"이라고 말할 때 사용합니다.
```

**나쁜 설명 예시:**

```yaml
# 너무 모호
description: 프로젝트를 도와줍니다.

# 트리거 누락
description: 정교한 다중 페이지 문서 시스템을 생성합니다.

# 너무 기술적, 사용자 트리거 없음
description: 계층적 관계를 가진 Project 엔티티 모델을 구현합니다.
```

#### 메인 지침 작성

프론트매터 이후에 마크다운으로 실제 지침을 작성합니다.

**권장 구조:**

이 템플릿을 스킬에 맞게 조정하세요. 괄호 안의 섹션을 구체적인 내용으로 교체하세요.

```markdown
---
name: your-skill
description: [.]
---

# 스킬 이름

# 지침

# 단계 1: [첫 번째 주요 단계]
무엇이 일어나는지 명확한 설명.

예시:
```bash
python scripts/fetch_data.py --project-id PROJECT_ID
```
예상 출력: [성공이 어떻게 보이는지 설명]

(필요에 따라 더 많은 단계 추가)

# 예시

## 예시 1: [일반적인 시나리오]
사용자가 말함: "새 마케팅 캠페인 설정해줘"
동작:
1. MCP를 통해 기존 캠페인 가져오기
2. 제공된 매개변수로 새 캠페인 생성
결과: 확인 링크와 함께 캠페인 생성

(필요에 따라 더 많은 예시 추가)

# 문제 해결

## 오류: [일반적인 에러 메시지]
원인: [왜 발생하는지]
해결: [어떻게 수정하는지]

(필요에 따라 더 많은 에러 사례 추가)
```

#### 지침 작성 모범 사례

**구체적이고 실행 가능하게**

✅ 좋음:

```
`python scripts/validate.py --input {filename}`을 실행하여 데이터 형식을 확인합니다.
검증이 실패하면, 일반적인 문제는 다음과 같습니다:
- 필수 필드 누락 (CSV에 추가하세요)
- 잘못된 날짜 형식 (YYYY-MM-DD 사용)
```

❌ 나쁨:

```
진행하기 전에 데이터를 검증하세요.
```

**에러 처리 포함**

```markdown
# 일반적인 문제

# MCP 연결 실패
"Connection refused"가 표시되면:
1. MCP 서버가 실행 중인지 확인: 설정 > 확장 기능 확인
2. API 키가 유효한지 확인
3. 재연결 시도: 설정 > 확장 기능 > [서비스] > 재연결
```

**번들된 리소스를 명확히 참조**

```
쿼리를 작성하기 전에 `references/api-patterns.md`를 참조하세요:
- 속도 제한 안내
- 페이지네이션 패턴
- 에러 코드 및 처리
```

**점진적 공개 사용**

SKILL.md를 핵심 지침에 집중하세요. 상세한 문서는 `references/`로 이동하고 링크하세요. (세 단계 시스템이 어떻게 작동하는지는 [핵심 설계 원칙](#핵심-설계-원칙) 참조.)

---

## 3장: 테스트 및 반복

스킬은 필요에 따라 다양한 수준의 엄격함으로 테스트할 수 있습니다:

- **Claude.ai에서 수동 테스트** - 쿼리를 직접 실행하고 동작을 관찰합니다. 빠른 반복, 설정 불필요.
- **Claude Code에서 스크립트 테스트** - 변경 사항에 대해 반복 가능한 검증을 위해 테스트 케이스를 자동화합니다.
- **스킬 API를 통한 프로그래밍 방식 테스트** - 정의된 테스트 세트에 대해 체계적으로 실행되는 평가 스위트를 구축합니다.

품질 요구 사항과 스킬의 가시성에 맞는 접근 방식을 선택하세요. 소규모 팀이 내부적으로 사용하는 스킬은 수천 명의 기업 사용자에게 배포되는 스킬과 다른 테스트 요구 사항을 가집니다.

> **프로 팁: 확장하기 전에 단일 작업에서 반복하세요**
>
> 가장 효과적인 스킬 제작자는 Claude가 성공할 때까지 단일 도전적인 작업에서 반복한 다음, 성공한 접근 방식을 스킬로 추출하는 것을 발견했습니다. 이는 Claude의 인컨텍스트 학습을 활용하며 광범위한 테스트보다 빠른 신호를 제공합니다. 작동하는 기반이 생기면, 커버리지를 위해 여러 테스트 케이스로 확장하세요.

### 권장 테스트 접근 방식

초기 경험을 바탕으로, 효과적인 스킬 테스트는 일반적으로 세 가지 영역을 다룹니다:

#### 1. 트리거 테스트

**목표:** 스킬이 적절한 시점에 로드되는지 확인.

**테스트 케이스:**

- ✅ 명확한 작업에서 트리거
- ✅ 다른 표현의 요청에서 트리거
- ❌ 관련 없는 주제에서 트리거되지 않음

**테스트 스위트 예시:**

```
트리거되어야 함:
- "새 ProjectHub 워크스페이스 설정 도와줘"
- "ProjectHub에서 프로젝트를 만들어야 해"
- "Q4 계획을 위한 ProjectHub 프로젝트 초기화"

트리거되지 않아야 함:
- "샌프란시스코 날씨가 어때?"
- "Python 코드 작성 도와줘"
- "스프레드시트 만들어줘" (ProjectHub 스킬이 시트를 처리하지 않는 한)
```

#### 2. 기능 테스트

**목표:** 스킬이 올바른 출력을 생성하는지 검증.

**테스트 케이스:**

- 유효한 출력 생성
- API 호출 성공
- 에러 처리 작동
- 엣지 케이스 커버

**예시:**

```
테스트: 5개 작업이 있는 프로젝트 생성
주어진 것: 프로젝트 이름 "Q4 Planning", 5개 작업 설명
실행 시: 스킬이 워크플로우 실행
결과:
  - ProjectHub에 프로젝트 생성
  - 올바른 속성으로 5개 작업 생성
  - 모든 작업이 프로젝트에 연결
  - API 에러 없음
```

#### 3. 성능 비교

**목표:** 스킬이 기준선 대비 결과를 개선하는지 증명.

[성공 기준 정의](#성공-기준-정의)의 지표를 사용하세요. 비교가 어떻게 보일 수 있는지 아래와 같습니다.

**기준선 비교:**

```
스킬 없이:
- 사용자가 매번 지침 제공
- 15번의 왕복 메시지
- 재시도가 필요한 3번의 API 호출 실패
- 12,000 토큰 소비

스킬과 함께:
- 자동 워크플로우 실행
- 2번의 명확화 질문만
- API 호출 실패 0회
- 6,000 토큰 소비
```

### skill-creator 스킬 사용

skill-creator 스킬은 - Claude.ai에서 플러그인 디렉토리를 통해 또는 Claude Code용으로 다운로드하여 사용 가능 - 스킬을 구축하고 반복하는 데 도움을 줄 수 있습니다. MCP 서버가 있고 상위 2-3개 워크플로우를 알고 있다면, 한 번의 작업 세션에서 기능적인 스킬을 구축하고 테스트할 수 있습니다 - 보통 15-30분 내에.

**스킬 생성:**

- 자연어 설명으로부터 스킬 생성
- 프론트매터가 포함된 올바른 형식의 SKILL.md 생성
- 트리거 문구 및 구조 제안

**스킬 검토:**

- 일반적인 문제 표시 (모호한 설명, 누락된 트리거, 구조적 문제)
- 잠재적 과다/과소 트리거 위험 식별
- 스킬의 명시된 목적에 기반한 테스트 케이스 제안

**반복적 개선:**

- 스킬을 사용하고 엣지 케이스나 실패를 만난 후, 해당 사례를 skill-creator에 가져오세요
- 예시: "이 채팅에서 식별된 문제와 해결책을 사용하여 스킬이 [특정 엣지 케이스]를 처리하는 방식을 개선하세요"

**사용 방법:**

```
"skill-creator 스킬을 사용하여 [사용 사례]를 위한 스킬을 만들도록 도와주세요"
```

> **참고:** skill-creator는 스킬을 설계하고 개선하는 데 도움을 주지만 자동화된 테스트 스위트를 실행하거나 정량적 평가 결과를 생성하지는 않습니다.

### 피드백 기반 반복

스킬은 살아있는 문서입니다. 다음을 기반으로 반복할 계획을 세우세요:

**과소 트리거 신호:**

- 스킬이 로드되어야 할 때 로드되지 않음
- 사용자가 수동으로 활성화
- 언제 사용해야 하는지에 대한 지원 문의

**해결:** description에 더 많은 세부 사항과 뉘앙스를 추가 - 특히 기술 용어에 대한 키워드 포함

**과다 트리거 신호:**

- 관련 없는 쿼리에 스킬이 로드
- 사용자가 비활성화
- 목적에 대한 혼란

**해결:** 부정 트리거 추가, 더 구체적으로

**실행 문제:**

- 일관되지 않은 결과
- API 호출 실패
- 사용자 수정 필요

**해결:** 지침 개선, 에러 처리 추가

---

## 4장: 배포 및 공유

스킬은 MCP 통합을 더 완전하게 만듭니다. 사용자가 커넥터를 비교할 때, 스킬이 있는 것은 가치에 더 빠른 경로를 제공하여 MCP만 있는 대안보다 우위를 제공합니다.

### 현재 배포 모델 (2026년 1월)

**개별 사용자가 스킬을 얻는 방법:**

1. 스킬 폴더 다운로드
2. 폴더를 압축 (필요한 경우)
3. 설정 > 기능 > 스킬을 통해 Claude.ai에 업로드
4. 또는 Claude Code 스킬 디렉토리에 배치

**조직 수준 스킬:**

- 관리자가 워크스페이스 전체에 스킬 배포 가능 (2025년 12월 18일 출시)
- 자동 업데이트
- 중앙 집중식 관리

### 오픈 표준

에이전트 스킬을 오픈 표준으로 발표했습니다. MCP와 마찬가지로, 스킬은 도구와 플랫폼 간에 이식 가능해야 한다고 믿습니다 - Claude를 사용하든 다른 AI 플랫폼을 사용하든 동일한 스킬이 작동해야 합니다. 그렇지만 일부 스킬은 특정 플랫폼의 기능을 최대한 활용하도록 설계되었습니다; 작성자는 스킬의 compatibility 필드에 이를 기록할 수 있습니다. 생태계 구성원들과 표준에 대해 협력해 왔으며, 초기 채택에 대해 기대하고 있습니다.

### API를 통한 스킬 사용

프로그래밍 방식의 사용 사례 - 스킬을 활용하는 애플리케이션, 에이전트 또는 자동화된 워크플로우 구축 등 - 를 위해 API는 스킬 관리 및 실행에 대한 직접적인 제어를 제공합니다.

**주요 기능:**

- 스킬 나열 및 관리를 위한 `/v1/skills` 엔드포인트
- `container.skills` 매개변수를 통해 Messages API 요청에 스킬 추가
- Claude Console을 통한 버전 관리 및 관리
- 커스텀 에이전트 구축을 위한 Claude Agent SDK와 연동

**API vs. Claude.ai에서 스킬을 사용할 때:**

| 사용 사례 | 최적 플랫폼 |
|---|---|
| 최종 사용자가 스킬과 직접 상호작용 | Claude.ai / Claude Code |
| 개발 중 수동 테스트 및 반복 | Claude.ai / Claude Code |
| 개별적이고 임시적인 워크플로우 | Claude.ai / Claude Code |
| 프로그래밍 방식으로 스킬을 사용하는 애플리케이션 | API |
| 대규모 프로덕션 배포 | API |
| 자동화된 파이프라인 및 에이전트 시스템 | API |

> **참고:** API에서의 스킬은 스킬이 실행하는 데 필요한 보안 환경을 제공하는 코드 실행 도구 베타가 필요합니다.

**구현 세부 사항은 다음을 참조:**

- Skills API 퀵스타트
- 커스텀 스킬 생성
- Agent SDK에서의 스킬

### 현재 권장 접근 방식

공개 저장소, 명확한 README (인간 방문자용 — 이것은 README.md를 포함하면 안 되는 스킬 폴더와는 별도), 스크린샷이 포함된 사용 예시가 있는 GitHub에서 스킬을 호스팅하는 것부터 시작하세요. 그런 다음 MCP 문서에 스킬로의 링크, 함께 사용하는 것이 왜 가치 있는지 설명, 빠른 시작 가이드를 제공하는 섹션을 추가하세요.

1. **GitHub에 호스팅**
   - 오픈 소스 스킬을 위한 공개 저장소
   - 설치 지침이 포함된 명확한 README
   - 사용 예시 및 스크린샷

2. **MCP 저장소에 문서화**
   - MCP 문서에서 스킬로 링크
   - 함께 사용하는 가치 설명
   - 빠른 시작 가이드 제공

3. **설치 가이드 작성**

```markdown
# [서비스] 스킬 설치

1. 스킬 다운로드:
   - 저장소 클론: `git clone https://github.com/yourcompany/skills`
   - 또는 Releases에서 ZIP 다운로드

2. Claude에 설치:
   - Claude.ai > 설정 > 스킬 열기
   - "스킬 업로드" 클릭
   - 스킬 폴더 선택 (압축된)

3. 스킬 활성화:
   - [서비스] 스킬 토글 켜기
   - MCP 서버가 연결되었는지 확인

4. 테스트:
   - Claude에게: "[서비스]에서 새 프로젝트 설정해줘"
```

### 스킬 포지셔닝

스킬을 어떻게 설명하느냐가 사용자가 그 가치를 이해하고 실제로 시도하는지를 결정합니다. README, 문서 또는 마케팅에서 스킬에 대해 작성할 때 — 이러한 원칙을 염두에 두세요.

**기능이 아닌 결과에 집중:**

✅ 좋음:

```
"ProjectHub 스킬을 사용하면 팀이 수동 설정에 30분을 소비하는 대신, 페이지, 데이터베이스, 템플릿을 포함한 완전한 프로젝트 워크스페이스를 몇 초 만에 설정할 수 있습니다."
```

❌ 나쁨:

```
"ProjectHub 스킬은 MCP 서버 도구를 호출하는 YAML 프론트매터와 마크다운 지침을 포함하는 폴더입니다."
```

**MCP + 스킬 스토리 강조:**

```
"MCP 서버는 Claude에게 Linear 프로젝트에 대한 접근을 제공합니다. 스킬은 Claude에게 팀의 스프린트 계획 워크플로우를 가르칩니다. 함께 사용하면 AI 기반 프로젝트 관리가 가능합니다."
```

---

## 5장: 패턴 및 문제 해결

이러한 패턴은 초기 채택자와 내부 팀이 만든 스킬에서 나타났습니다. 잘 작동하는 것으로 확인된 일반적인 접근 방식을 나타내며, 규범적인 템플릿이 아닙니다.

### 접근 방식 선택: 문제 우선 vs. 도구 우선

홈디포(Home Depot)를 생각해 보세요. 문제를 가지고 들어갈 수 있습니다 - "주방 캐비닛을 수리해야 해" - 그러면 직원이 적절한 도구를 안내합니다. 또는 새 드릴을 골라서 특정 작업에 어떻게 사용하는지 물어볼 수 있습니다.

스킬도 같은 방식으로 작동합니다:

- **문제 우선:** "프로젝트 워크스페이스를 설정해야 해" → 스킬이 올바른 순서로 적절한 MCP 호출을 조율합니다. 사용자는 결과를 설명하고; 스킬이 도구를 처리합니다.
- **도구 우선:** "Notion MCP를 연결했어" → 스킬이 Claude에게 최적의 워크플로우와 모범 사례를 가르칩니다. 사용자는 접근권이 있고; 스킬이 전문 지식을 제공합니다.

대부분의 스킬은 한쪽으로 기울어집니다. 어떤 프레이밍이 사용 사례에 맞는지 알면 아래의 적절한 패턴을 선택하는 데 도움이 됩니다.

### 패턴 1: 순차적 워크플로우 조율

**사용 시기:** 사용자가 특정 순서의 다단계 프로세스를 필요로 할 때.

**예시 구조:**

```markdown
# 워크플로우: 신규 고객 온보딩

# 단계 1: 계정 생성
MCP 도구 호출: `create_customer`
매개변수: name, email, company

# 단계 2: 결제 설정
MCP 도구 호출: `setup_payment_method`
대기: 결제 수단 확인

# 단계 3: 구독 생성
MCP 도구 호출: `create_subscription`
매개변수: plan_id, customer_id (단계 1에서)

# 단계 4: 환영 이메일 발송
MCP 도구 호출: `send_email`
템플릿: welcome_email_template
```

**핵심 기법:**

- 명시적 단계 순서
- 단계 간 종속성
- 각 단계에서 검증
- 실패 시 롤백 지침

### 패턴 2: 다중 MCP 조율

**사용 시기:** 워크플로우가 여러 서비스에 걸쳐 있을 때.

**예시: 디자인-개발 핸드오프**

```markdown
# 1단계: 디자인 내보내기 (Figma MCP)
1. Figma에서 디자인 에셋 내보내기
2. 디자인 사양 생성
3. 에셋 매니페스트 생성

# 2단계: 에셋 저장 (Drive MCP)
1. Drive에 프로젝트 폴더 생성
2. 모든 에셋 업로드
3. 공유 가능한 링크 생성

# 3단계: 작업 생성 (Linear MCP)
1. 개발 작업 생성
2. 작업에 에셋 링크 첨부
3. 엔지니어링 팀에 할당

# 4단계: 알림 (Slack MCP)
1. #engineering에 핸드오프 요약 게시
2. 에셋 링크 및 작업 참조 포함
```

**핵심 기법:**

- 명확한 단계 구분
- MCP 간 데이터 전달
- 다음 단계로 이동하기 전 검증
- 중앙 집중식 에러 처리

### 패턴 3: 반복적 개선

**사용 시기:** 반복을 통해 출력 품질이 향상될 때.

**예시: 보고서 생성**

```markdown
# 반복적 보고서 생성

# 초안
1. MCP를 통해 데이터 가져오기
2. 첫 번째 초안 보고서 생성
3. 임시 파일에 저장

# 품질 검사
1. 검증 스크립트 실행: `scripts/check_report.py`
2. 문제 식별:
   - 누락된 섹션
   - 일관되지 않은 서식
   - 데이터 검증 에러

# 개선 루프
1. 식별된 각 문제 해결
2. 영향받은 섹션 재생성
3. 재검증
4. 품질 임계값을 충족할 때까지 반복

# 최종화
1. 최종 서식 적용
2. 요약 생성
3. 최종 버전 저장
```

**핵심 기법:**

- 명시적 품질 기준
- 반복적 개선
- 검증 스크립트
- 반복을 멈출 시점 파악

### 패턴 4: 컨텍스트 인식 도구 선택

**사용 시기:** 동일한 결과, 컨텍스트에 따라 다른 도구.

**예시: 파일 저장**

```markdown
# 스마트 파일 저장

# 의사결정 트리
1. 파일 유형 및 크기 확인
2. 최적의 저장 위치 결정:
   - 대용량 파일 (>10MB): 클라우드 스토리지 MCP 사용
   - 협업 문서: Notion/Docs MCP 사용
   - 코드 파일: GitHub MCP 사용
   - 임시 파일: 로컬 스토리지 사용

# 저장 실행
결정에 따라:
- 적절한 MCP 도구 호출
- 서비스별 메타데이터 적용
- 접근 링크 생성

# 사용자에게 컨텍스트 제공
해당 저장소가 선택된 이유 설명
```

**핵심 기법:**

- 명확한 결정 기준
- 대안 옵션
- 선택에 대한 투명성

### 패턴 5: 도메인 특화 인텔리전스

**사용 시기:** 스킬이 도구 접근 이상의 전문 지식을 추가할 때.

**예시: 금융 컴플라이언스**

```markdown
# 컴플라이언스를 갖춘 결제 처리

# 처리 전 (컴플라이언스 검사)
1. MCP를 통해 거래 세부 사항 가져오기
2. 컴플라이언스 규칙 적용:
   - 제재 목록 확인
   - 관할권 허용 여부 확인
   - 위험 수준 평가
3. 컴플라이언스 결정 문서화

# 처리
컴플라이언스 통과 시:
  - 결제 처리 MCP 도구 호출
  - 적절한 사기 검사 적용
  - 거래 처리
그렇지 않으면:
  - 검토를 위해 표시
  - 컴플라이언스 케이스 생성

# 감사 추적
- 모든 컴플라이언스 검사 기록
- 처리 결정 기록
- 감사 보고서 생성
```

**핵심 기법:**

- 도메인 전문 지식이 로직에 내장
- 행동 전 컴플라이언스
- 포괄적 문서화
- 명확한 거버넌스

### 문제 해결

#### 스킬이 업로드되지 않음

**오류: "Could not find SKILL.md in uploaded folder"**

원인: 파일 이름이 정확히 `SKILL.md`가 아님

해결:

- `SKILL.md`로 이름 변경 (대소문자 구분)
- `ls -la`로 확인하면 `SKILL.md`가 표시되어야 함

**오류: "Invalid frontmatter"**

원인: YAML 서식 문제

일반적인 실수:

```yaml
# 잘못됨 - 구분자 누락
name: my-skill
description: Does things

# 잘못됨 - 닫히지 않은 따옴표
name: my-skill
description: "Does things

# 올바름
---
name: my-skill
description: Does things
---
```

**오류: "Invalid skill name"**

원인: 이름에 공백이나 대문자가 있음

```yaml
# 잘못됨
name: My Cool Skill

# 올바름
name: my-cool-skill
```

#### 스킬이 트리거되지 않음

**증상:** 스킬이 자동으로 로드되지 않음

**수정:** description 필드를 수정하세요. 좋은/나쁜 예시는 [description 필드](#description-필드)를 참조하세요.

빠른 체크리스트:

- 너무 일반적인가? ("프로젝트를 도와줍니다"는 작동하지 않음)
- 사용자가 실제로 말할 트리거 문구를 포함하는가?
- 해당되는 경우 관련 파일 유형을 언급하는가?

**디버깅 접근:**

Claude에게 물어보세요: "[스킬 이름] 스킬은 언제 사용하시겠습니까?" Claude가 description을 인용합니다. 누락된 것에 따라 조정하세요.

#### 스킬이 너무 자주 트리거됨

**증상:** 관련 없는 쿼리에 스킬이 로드됨

**해결:**

1. **부정 트리거 추가**

```yaml
description: CSV 파일을 위한 고급 데이터 분석. 통계 모델링, 회귀, 클러스터링에 사용. 단순 데이터 탐색에는 사용하지 마세요 (data-viz 스킬을 대신 사용).
```

2. **더 구체적으로**

```yaml
# 너무 광범위
description: 문서를 처리합니다

# 더 구체적
description: 계약 검토를 위한 PDF 법률 문서를 처리합니다
```

3. **범위 명확화**

```yaml
description: 전자상거래를 위한 PayFlow 결제 처리. 온라인 결제 워크플로우에 특별히 사용하며, 일반적인 금융 질의에는 사용하지 마세요.
```

#### MCP 연결 문제

**증상:** 스킬은 로드되지만 MCP 호출이 실패

**체크리스트:**

1. **MCP 서버 연결 확인**
   - Claude.ai: 설정 > 확장 기능 > [서비스]
   - "연결됨" 상태가 표시되어야 함

2. **인증 확인**
   - API 키가 유효하고 만료되지 않았는지
   - 적절한 권한/스코프가 부여되었는지
   - OAuth 토큰이 갱신되었는지

3. **MCP 독립적으로 테스트**
   - Claude에게 스킬 없이 직접 MCP를 호출하도록 요청
   - "[서비스] MCP를 사용해서 내 프로젝트를 가져와"
   - 이것이 실패하면 문제는 스킬이 아닌 MCP

4. **도구 이름 확인**
   - 스킬이 올바른 MCP 도구 이름을 참조하는지
   - MCP 서버 문서 확인
   - 도구 이름은 대소문자 구분

#### 지침이 따라지지 않음

**증상:** 스킬은 로드되지만 Claude가 지침을 따르지 않음

**일반적인 원인:**

1. **지침이 너무 장황함**
   - 지침을 간결하게 유지
   - 불릿 포인트와 번호 매긴 목록 사용
   - 상세한 참조는 별도 파일로 이동

2. **지침이 묻혀 있음**
   - 중요 지침을 상단에 배치
   - `## 중요` 또는 `## 핵심` 헤더 사용
   - 필요시 핵심 포인트 반복

3. **모호한 언어**

```markdown
# 나쁨
제대로 검증해야 합니다

# 좋음
핵심: create_project를 호출하기 전에 다음을 확인하세요:
- 프로젝트 이름이 비어 있지 않은지
- 최소 한 명의 팀 멤버가 할당되었는지
- 시작 날짜가 과거가 아닌지
```

> **고급 기법:** 중요한 검증의 경우, 언어 지침에 의존하기보다 프로그래밍 방식으로 검사를 수행하는 스크립트를 번들하는 것을 고려하세요. 코드는 결정적이고; 언어 해석은 그렇지 않습니다. 이 패턴의 예시는 Office 스킬을 참조하세요.

4. **모델 "게으름"** — 명시적 격려 추가:

```markdown
# 성능 참고 사항
- 시간을 들여 철저하게 수행하세요
- 품질이 속도보다 중요합니다
- 검증 단계를 건너뛰지 마세요
```

> **참고:** 이것은 SKILL.md보다 사용자 프롬프트에 추가하는 것이 더 효과적입니다

#### 대규모 컨텍스트 문제

**증상:** 스킬이 느리거나 응답 품질이 저하됨

**원인:**

- 스킬 콘텐츠가 너무 큼
- 너무 많은 스킬이 동시에 활성화
- 점진적 공개 대신 모든 콘텐츠가 로드됨

**해결:**

1. **SKILL.md 크기 최적화**
   - 상세 문서를 `references/`로 이동
   - 인라인 대신 참조로 링크
   - SKILL.md를 5,000단어 이하로 유지

2. **활성화된 스킬 줄이기**
   - 동시에 20-50개 이상의 스킬이 활성화되어 있는지 평가
   - 선택적 활성화 권장
   - 관련 기능을 위한 스킬 "팩" 고려

---

## 6장: 리소스 및 참고 자료

첫 번째 스킬을 구축하는 경우, 모범 사례 가이드부터 시작한 후 필요에 따라 API 문서를 참조하세요.

### 공식 문서

**Anthropic 리소스:**

- 모범 사례 가이드
- 스킬 문서
- API 레퍼런스
- MCP 문서

**블로그 게시물:**

- 에이전트 스킬 소개
- 엔지니어링 블로그: 실제 세계를 위한 에이전트 장비
- 스킬 설명
- Claude를 위한 스킬 만드는 방법
- Claude Code를 위한 스킬 구축
- 스킬을 통한 프론트엔드 디자인 개선

### 예시 스킬

**공개 스킬 저장소:**

- GitHub: [anthropics/skills](https://github.com/anthropics/skills)
- 커스터마이징할 수 있는 Anthropic 제작 스킬 포함

### 도구 및 유틸리티

**skill-creator 스킬:**

- Claude.ai에 내장되어 있으며 Claude Code에서도 사용 가능
- 설명으로부터 스킬 생성 가능
- 검토 및 권장 사항 제공
- 사용: "skill-creator를 사용해서 스킬 만들기 도와줘"

**검증:**

- skill-creator가 스킬을 평가할 수 있음
- 질문: "이 스킬을 검토하고 개선 사항을 제안해줘"

### 지원 받기

**기술 질문:**

- 일반 질문: Claude Developers Discord 커뮤니티 포럼

**버그 보고:**

- GitHub Issues: anthropics/skills/issues
- 포함 사항: 스킬 이름, 에러 메시지, 재현 단계

---

## 참고 A: 빠른 체크리스트

이 체크리스트를 사용하여 업로드 전후에 스킬을 검증하세요. 더 빠르게 시작하려면 skill-creator 스킬을 사용하여 첫 번째 초안을 생성한 후, 이 목록을 통해 누락된 것이 없는지 확인하세요.

### 시작 전

- [ ] 2-3개의 구체적인 사용 사례 식별
- [ ] 도구 식별 (내장 또는 MCP)
- [ ] 이 가이드 및 예시 스킬 검토
- [ ] 폴더 구조 계획

### 개발 중

- [ ] 폴더가 케밥 케이스로 명명
- [ ] SKILL.md 파일 존재 (정확한 철자)
- [ ] YAML 프론트매터에 `---` 구분자
- [ ] name 필드: 케밥 케이스, 공백 없음, 대문자 없음
- [ ] description에 무엇(WHAT)과 언제(WHEN) 포함
- [ ] 어디에도 XML 태그 (`<` `>`) 없음
- [ ] 지침이 명확하고 실행 가능
- [ ] 에러 처리 포함
- [ ] 예시 제공
- [ ] 참조가 명확히 연결

### 업로드 전

- [ ] 명확한 작업에서 트리거 테스트 완료
- [ ] 다른 표현의 요청에서 트리거 테스트 완료
- [ ] 관련 없는 주제에서 트리거되지 않는지 확인
- [ ] 기능 테스트 통과
- [ ] 도구 통합 작동 (해당되는 경우)
- [ ] .zip 파일로 압축

### 업로드 후

- [ ] 실제 대화에서 테스트
- [ ] 과소/과다 트리거 모니터링
- [ ] 사용자 피드백 수집
- [ ] description 및 지침 반복 개선
- [ ] metadata에서 버전 업데이트

---

## 참고 B: YAML 프론트매터

### 필수 필드

```yaml
---
name: skill-name-in-kebab-case
description: 무엇을 하고 언제 사용하는지. 구체적인 트리거 문구를 포함.
---
```

### 모든 선택 필드

```yaml
name: skill-name
description: [필수 설명]
license: MIT                          # 선택: 오픈 소스 라이선스
allowed-tools: "Bash(python:*) Bash(npm:*) WebFetch"  # 선택: 도구 접근 제한
metadata:                             # 선택: 커스텀 필드
  author: Company Name
  version: 1.0.0
  mcp-server: server-name
  category: productivity
  tags: [project-management, automation]
  documentation: https://example.com/docs
  support: support@example.com
```

### 보안 참고

**허용:**

- 모든 표준 YAML 유형 (문자열, 숫자, 불리언, 리스트, 객체)
- 커스텀 메타데이터 필드
- 긴 설명 (최대 1024자)

**금지:**

- XML 꺾쇠 괄호 (`<` `>`) - 보안 제한
- YAML에서의 코드 실행 (안전한 YAML 파싱 사용)
- "claude" 또는 "anthropic" 접두사가 있는 스킬 이름 (예약됨)

---

## 참고 C: 완전한 스킬 예제

이 가이드의 패턴을 시연하는 완전한 프로덕션 수준의 스킬:

- **문서 스킬** - PDF, DOCX, PPTX, XLSX 생성
- **예시 스킬** - 다양한 워크플로우 패턴
- **파트너 스킬 디렉토리** - Asana, Atlassian, Canva, Figma, Sentry, Zapier 등 다양한 파트너의 스킬 확인

이 저장소들은 최신 상태를 유지하며 여기에서 다루는 것 이상의 추가 예시를 포함합니다. 클론하고, 사용 사례에 맞게 수정하고, 템플릿으로 사용하세요.
