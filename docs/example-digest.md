# Your lazycontrib digest, 2026-10-20

Looked at 40 open issues, read 20 closely, kept 10. Model: gemma4:e4b. Ranking: tabpfn on 369 outside pull requests. Took 161 s.

## 1. open-telemetry/opentelemetry.io#7841: [es] Spanish folder localization zero-code

<https://github.com/open-telemetry/opentelemetry.io/issues/7841>

- **Status:** stale claim (@immavalls said they would take it 79 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** strong
- **Effort:** M · **clarity:** clear
- **Merge odds:** 94% · the repo merges 98% of outside PRs · maintainers reply in ~8 h
- **Policy:** AI help allowed, with conditions; say how you used AI; write the PR text and replies yourself

**What it asks:** This is a documentation translation task focused on the 'zero-code' section, primarily requiring translation into Spanish. The contributor has skills in documentation and has experience with multiple languages (Python, Java, etc.), making them a good fit for this task.

**A complete fix:**
- Translate the remaining untranslated pages listed in the issue body (e.g., `zero-code/go/autosdk/`, `zero-code/dotnet/configuration`, `zero-code/Python/configuration`, etc.) into Spanish.
- Ensure each translation is submitted as a unique Pull Request, as requested in the original issue body.

**Plan:**
1. The task requires translating specific documentation pages into Spanish, as indicated by the issue summary and 'must_do' list.
2. The provided code snippets do not contain the documentation files that need translation (e.g., `zero-code/go/autosdk/`, `zero-code/dotnet/configuration`, etc.).
3. The existing files (`LICENSE-CODE`, `.github/component-owners.yml`, `.github/CODEOWNERS`, `.github/component-label-map.yml`, `content/en/blog/2024/spring-starter-stable/index.md`, `assets/js/dcConverter.js`) are configuration or code files and do not contain the content to be translated.
4. Therefore, the implementation plan focuses on the *process* required to fulfill the 'must_do' items, assuming the contributor will perform the translation in the correct file structure.

Build on: `No existing helper files were found that directly assist in the translation process, as the task is purely content translation.`
Risks: The contributor must ensure that each translation is submitted as a unique Pull Request, as specified in the 'must_do' list, to avoid merging multiple translations into one PR.

<details><summary>Policy quotes</summary>

- `must_disclose`: "I used AI and I have read and followed the [Generative AI Contribution Policy](https://opentelemetry.io/docs/contributing/pull-requests/#using-ai)."
- `own_words_only`: "Yes, I can answer maintainer questions about the content of this PR, without using AI."

</details>

Start: `lazycontrib start open-telemetry/opentelemetry.io#7841`

## 2. open-telemetry/opentelemetry.io#8450: Setup i18n entries for alert tags

<https://github.com/open-telemetry/opentelemetry.io/issues/8450>

- **Status:** free (nobody has claimed it and no pull request is linked)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 96% · the repo merges 98% of outside PRs · maintainers reply in ~8 h
- **Policy:** AI help allowed, with conditions; say how you used AI; write the PR text and replies yourself

**What it asks:** This issue is about adding internationalization (i18n) entries for alert tags, which seems to be a follow-up to previous work.

**A complete fix:**
- Create i18n entries for alert tags (e.g., caution: Caution, important: Important, note: Note, tip: Tip, warning: Warning) in the relevant i18n files.

**Plan:**
1. The contributor needs to add i18n entries for specific alert tags into the relevant i18n files.
2. The required tags are: 'caution', 'important', 'note', 'tip', and 'warning'.
3. The corresponding English translations are: 'Caution', 'Important', 'Note', 'Tip', and 'Warning'.

Risks: Without the structure of the i18n files, the exact location for modification cannot be determined, potentially leading to incorrect file changes.

<details><summary>Policy quotes</summary>

- `must_disclose`: "I used AI and I have read and followed the [Generative AI Contribution Policy](https://opentelemetry.io/docs/contributing/pull-requests/#using-ai)."
- `own_words_only`: "Yes, I can answer maintainer questions about the content of this PR, without using AI."

</details>

Start: `lazycontrib start open-telemetry/opentelemetry.io#8450`

## 3. dapr/java-sdk#1655: Calling sdk's invokeMethod raise DaprException: UNKNOWN: HTTP status code: 400

<https://github.com/dapr/java-sdk/issues/1655>

- **Status:** free (nobody has claimed it and no pull request is linked)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 95% · the repo merges 94% of outside PRs
- **Policy:** no AI policy found; sign off commits (DCO)

**What it asks:** Investigate a 400 Bad Request error during service invocation in the Java SDK after upgrading Dapr, specifically when running in Kubernetes.

**A complete fix:**
- Determine if the 400 error is related to changes in Dapr 1.16.8 that affect HTTP request construction or payload handling in the Java SDK.
- Check if the issue is specific to the environment (e.g., Kubernetes networking, configuration) or the SDK usage itself.

**Plan:**
1. Investigate the potential cause of the 400 Bad Request error during service invocation in the Java SDK, focusing on changes related to Dapr 1.16.8.
2. Examine `sdk/src/main/java/io/dapr/client/DaprHttp.java` to see how HTTP requests are constructed and headers are added.
3. Review `sdk/src/main/java/io/dapr/client/domain/HttpExtension.java` to understand the structure of HTTP extensions.
4. The 400 error often relates to incorrect request structure or payload. I will focus on how `DaprHttp` builds the request.
5. If the issue is related to how HTTP methods are used or how headers are set, I will look for places where the HTTP method is determined and used in `DaprHttp.java`.

Files: `sdk/src/main/java/io/dapr/client/DaprHttp.java`, `sdk/src/main/java/io/dapr/client/domain/HttpExtension.java`
Risks: Modifying request building logic in `DaprHttp.java` without a clear specification of the 1.16.8 change might introduce regressions.; The provided snippets do not show the full context of the `invokeMethod` call or the error handling path, limiting the scope of the fix.

Start: `lazycontrib start dapr/java-sdk#1655`

## 4. dapr/java-sdk#1509: Support Native compilation for the Java SDK

<https://github.com/dapr/java-sdk/issues/1509>

- **Status:** free (nobody has claimed it and no pull request is linked)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 91% · the repo merges 94% of outside PRs
- **Policy:** no AI policy found; sign off commits (DCO)

**What it asks:** Investigate and fix issues preventing native compilation (GraalVM) for the Java SDK, specifically focusing on Spring Boot applications.

**A complete fix:**
- Investigate dependency issues preventing native compilation.
- Ensure Spring applications using the Java SDK can be compiled natively.

**Plan:**
1. Investigate dependency issues preventing native compilation by reviewing the current `pom.xml` and related build configurations for potential incompatibilities with GraalVM.
2. Focus the investigation on dependencies that might require runtime reflection or dynamic loading, as these are common blockers for native compilation.
3. If specific dependencies are identified as problematic, propose necessary adjustments (e.g., using specific versions, providing native-friendly alternatives, or adding required build-time configuration).

Files: `pom.xml`
Risks: The investigation might reveal that the issue is outside the scope of the Java SDK's direct control (e.g., a dependency's design), requiring external coordination.

Start: `lazycontrib start dapr/java-sdk#1509`

## 5. fatiando/harmonica#586: harmonica.reduction_to_pole  flipping the output in north-south

<https://github.com/fatiando/harmonica/issues/586>

- **Status:** free (nobody has claimed it and no pull request is linked)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 92% · the repo merges 86% of outside PRs · maintainers reply in ~13 h
- **Policy:** AI help discouraged; say how you used AI; no agents opening PRs or commenting

**What it asks:** A bug where `harmonica.reduction_to_pole` flips the output data when processing North-South data, which has been reproduced by another contributor.

**A complete fix:**
- Fix the data flipping issue in `harmonica.reduction_to_pole` for North-South data.
- Ensure the fix maintains correct spatial attributes, especially when the CRS is dropped in the output.

<details><summary>Policy quotes</summary>

- `ai_welcome`: "Use of Generative AI (GenAI, including chatbots and coding agents) tools in contributions to Fatiando a Terra projects is strongly discouraged but not entirely prohibited."
- `ai_discouraged`: "Use of Generative AI (GenAI, including chatbots and coding agents) tools in contributions to Fatiando a Terra projects is strongly discouraged but not entirely prohibited."
- `must_disclose`: "1. **Declare if GenAI tools have been used** in the process and to what extent."
- `no_autonomous_agents`: "3. Do not use AI agents and bots to submit PRs, Issues, etc. on your behalf."

</details>

Start: `lazycontrib start fatiando/harmonica#586`

## 6. testcontainers/testcontainers-go#3871: [Bug]: basic clickhouse ping failed

<https://github.com/testcontainers/testcontainers-go/issues/3871>

- **Status:** free (nobody has claimed it and no pull request is linked)
- **They know you:** 1 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 71% · the repo merges 13% of outside PRs · maintainers reply in ~1 h
- **Policy:** AI help allowed, with conditions; say how you used AI

**What it asks:** A bug report regarding a basic ping failure with ClickHouse in `testcontainers-go`.

**A complete fix:**
- Investigate the reported failure of the ClickHouse ping.
- Verify if the issue is reproducible given the provided environment details (Testcontainers 0.44.0, Go 1.26, Docker 29.1.3 on Windows/x86).
- Ensure the fix maintains compatibility with the Go ecosystem and Docker interaction patterns.

<details><summary>Policy quotes</summary>

- `ai_welcome`: "Always include co-author footer when AI assists with changes"
- `must_disclose`: "Always include co-author footer when AI assists with changes"

</details>

Start: `lazycontrib start testcontainers/testcontainers-go#3871`

## 7. open-telemetry/opentelemetry.io#7932: [android] [registry] Add Android instrumentation to registry

<https://github.com/open-telemetry/opentelemetry.io/issues/7932>

- **Status:** stale claim (@breedx-splk said they would take it 382 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 95% · the repo merges 98% of outside PRs · maintainers reply in ~8 h
- **Policy:** AI help allowed, with conditions; say how you used AI; write the PR text and replies yourself

**What it asks:** This issue requires defining how to categorize Android-specific OpenTelemetry instrumentations within the existing registry structure, specifically whether to create a new 'Android' language category.

**A complete fix:**
- Implement the addition of Android instrumentation information to the registry.
- Decide on the correct categorization strategy (e.g., creating an 'Android' language tag) as discussed in the comments.

<details><summary>Policy quotes</summary>

- `must_disclose`: "I used AI and I have read and followed the [Generative AI Contribution Policy](https://opentelemetry.io/docs/contributing/pull-requests/#using-ai)."
- `own_words_only`: "Yes, I can answer maintainer questions about the content of this PR, without using AI."

</details>

Start: `lazycontrib start open-telemetry/opentelemetry.io#7932`

## 8. open-telemetry/opentelemetry.io#7535: [es] Spanish folder localization blogs

<https://github.com/open-telemetry/opentelemetry.io/issues/7535>

- **Status:** stale claim (@immavalls said they would take it 131 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 94% · the repo merges 98% of outside PRs · maintainers reply in ~8 h
- **Policy:** AI help allowed, with conditions; say how you used AI; write the PR text and replies yourself

**What it asks:** This is a documentation translation task for the Spanish localization of the blogs section. It is low-risk and fits well with a contributor who has experience with documentation or Spanish.

**A complete fix:**
- Translate the remaining blog pages listed in the issue body.
- Open a unique PR for each translated page.

<details><summary>Policy quotes</summary>

- `must_disclose`: "I used AI and I have read and followed the [Generative AI Contribution Policy](https://opentelemetry.io/docs/contributing/pull-requests/#using-ai)."
- `own_words_only`: "Yes, I can answer maintainer questions about the content of this PR, without using AI."

</details>

Start: `lazycontrib start open-telemetry/opentelemetry.io#7535`

## 9. OpenAPITools/openapi-generator#23274: Add scalafmt (plugin) to scala (client/server) generators

<https://github.com/OpenAPITools/openapi-generator/issues/23274>

- **Status:** stale claim (@YB0y said they would take it 213 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 88% · the repo merges 88% of outside PRs · maintainers reply in ~3 h
- **Policy:** no AI policy found

**What it asks:** The issue is about adding a 'scalafmt' plugin to Scala generators for OpenAPI, and there are multiple contributors interested.

**A complete fix:**
- Implement the addition of the scalafmt plugin to both client and server Scala generators.

Start: `lazycontrib start OpenAPITools/openapi-generator#23274`

## 10. fatiando/harmonica#646: Issue with xrft for next release

<https://github.com/fatiando/harmonica/issues/646>

- **Status:** stale claim (@santisoler said they would take it 175 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 91% · the repo merges 86% of outside PRs · maintainers reply in ~13 h
- **Policy:** AI help discouraged; say how you used AI; no agents opening PRs or commenting

**What it asks:** The issue is a dependency problem where `xrft` version 1.0.2 is not correctly recognized as installed (appearing as 0.0.0) during conda-forge builds, preventing the release of `harmonica`. Solutions discussed include changing the `xrft` feedstock to use PyPI instead of GitHub, or internalizing the necessary FFT functionality from `xrft` into `harmonica`.

**A complete fix:**
- Investigate the suggestion to change the `xrft` feedstock to fetch from PyPI instead of GitHub.
- Evaluate the feasibility of internalizing the required FFT functions from `xrft` into `harmonica` to resolve the dependency issue.
- Determine if the issue is critical for the next release or if a temporary workaround (like version pinning) is sufficient.

<details><summary>Policy quotes</summary>

- `ai_welcome`: "Use of Generative AI (GenAI, including chatbots and coding agents) tools in contributions to Fatiando a Terra projects is strongly discouraged but not entirely prohibited."
- `ai_discouraged`: "Use of Generative AI (GenAI, including chatbots and coding agents) tools in contributions to Fatiando a Terra projects is strongly discouraged but not entirely prohibited."
- `must_disclose`: "1. **Declare if GenAI tools have been used** in the process and to what extent."
- `no_autonomous_agents`: "3. Do not use AI agents and bots to submit PRs, Issues, etc. on your behalf."

</details>

Start: `lazycontrib start fatiando/harmonica#646`

## Skipped, and why

- [[pt] Localize content/en/docs/zero-code/agent/configuration.md](https://github.com/open-telemetry/opentelemetry.io/issues/7114): @reetig said they would take it 7 days ago
- [[pt] Localize content/en/docs/zero-code/java/spring-boot-starter/_index.md](https://github.com/open-telemetry/opentelemetry.io/issues/7117): open pull request: https://github.com/open-telemetry/opentelemetry.io/pull/11905
- [[pt] Localize content/en/docs/zero-code/agent/performance.md](https://github.com/open-telemetry/opentelemetry.io/issues/7115): open pull request: https://github.com/open-telemetry/opentelemetry.io/pull/11850
- [[Docs]: Community Meeting Records links unusable](https://github.com/open-telemetry/opentelemetry.io/issues/11927): open pull request: https://github.com/open-telemetry/opentelemetry.io/pull/11947
- [[pt] Localize content/en/docs/demo pages](https://github.com/open-telemetry/opentelemetry.io/issues/7544): open pull request: https://github.com/open-telemetry/opentelemetry.io/pull/11770
- [Add new test for TLS on durable task module after merging DT to SDK](https://github.com/dapr/java-sdk/issues/1604): open pull request: https://github.com/dapr/java-sdk/pull/1802
- [[pt] Localize content/en/docs/collector pages](https://github.com/open-telemetry/opentelemetry.io/issues/9427): open pull request: https://github.com/open-telemetry/opentelemetry.io/pull/11349
- [Simplify DaprContainer with default values for Spring Boot apps](https://github.com/dapr/java-sdk/issues/1583): open pull request: https://github.com/dapr/java-sdk/pull/1842
- [Go language docs: Add documentation for how to test instrumentation](https://github.com/open-telemetry/opentelemetry.io/issues/6899): open pull request: https://github.com/open-telemetry/opentelemetry.io/pull/11675
- [[pt] Localize content/en/docs/platforms pages](https://github.com/open-telemetry/opentelemetry.io/issues/7545): @reetig said they would take it 7 days ago
