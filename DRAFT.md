# AI Dev Tools & Security Watch — March 3, 2026

## 🔥 This Week in Spotlight

### [Anthropic Cowork feature creates 10GB VM bundle on macOS without warning](https://github.com/anthropics/claude-code/issues/22543)
**Security Alert for Local LLM Environments**  
Power users running the Anthropic Cowork toolchain on macOS may be facing unexpected storage consumption and potential security implications. Recent reports regarding issue #22543 indicate that a specific feature automatically generates a 10GB VM bundle without explicit user confirmation or warning during the session. This behavior contradicts standard sandboxing expectations for local LLM applications, raising concerns about how much system data is being bundled into the virtual environment by default.  
Developers are advised to check their repository permissions and review GitHub issue comments (specifically comment ID 47218288 on Hacker News) for community workarounds or official patches before bundling new projects.

## 🛠️ Tool Roundup: LLM Infrastructure & Privacy

- **[Show HN: Blindfold – PII protection for LLM apps (local regex and cloud NLP)](https://blindfold.dev)**
  A new utility designed to sanitize private data before it reaches a model. It combines local regex filtering with optional cloud NLP services to ensure sensitive information like emails or credit card numbers are masked within your workflow.

- **[Show HN: Axe – A CLI for running single-purpose LLM agents](https://github.com/jrswab/axe)**
  Streamline agent orchestration with a dedicated command-line interface. This tool simplifies the deployment of single-purpose agents, allowing developers to spin up specific functions without managing complex orchestration frameworks.

- **[FetchPrompt – Manage LLM prompts outside your code with a REST API](https://www.fetchprompt.dev/)**
  Separate your prompt engineering from your application code. This service provides a REST API for managing prompts centrally, making it easier to iterate on AI behavior without redeploying backend services.

- **[Continuum – CI drift guard for LLM workflows](https://github.com/Mofa1245/Continuum)**
  Ensure stability in automated pipelines. Continuum acts as a drift guard specifically designed for LLM-based Continuous Integration, detecting when model outputs deviate significantly from expected parameters during the build or deployment process.

- **[Ensu – Ente's Local LLM App](https://ente.io/blog/ensu/)**
  Prioritize privacy with this local-first application from Ente. The latest blog post discusses how ENSU keeps data on-premise, reducing reliance on external APIs and maintaining strict control over your proprietary training data.

- **[Strict Monospace Font for LLM-CLI users using Chinese Japanese Korean, CodexMono](https://www.npmjs.com/package/@monolex/codexmono)**