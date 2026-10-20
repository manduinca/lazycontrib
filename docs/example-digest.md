# Your lazycontrib digest, 2026-10-20

Looked at 40 open issues, read 20 closely, kept 10. Model: gemma4:e4b. Ranking: tabpfn on 369 outside pull requests. Took 150 s.

## 1. open-telemetry/opentelemetry.io#8450: Setup i18n entries for alert tags

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
1. Add 'caution: Caution', 'important: Important', 'note: Note', 'tip: Tip', and 'warning: Warning' entries to the appropriate i18n files to support internationalization for alert tags.

Risks: Missing the correct i18n file or key structure.

<details><summary>Policy quotes</summary>

- `must_disclose`: "I used AI and I have read and followed the [Generative AI Contribution Policy](https://opentelemetry.io/docs/contributing/pull-requests/#using-ai)."
- `own_words_only`: "Yes, I can answer maintainer questions about the content of this PR, without using AI."

</details>

Start: `lazycontrib start open-telemetry/opentelemetry.io#8450`

## 2. dapr/java-sdk#1655: Calling sdk's invokeMethod raise DaprException: UNKNOWN: HTTP status code: 400

<https://github.com/dapr/java-sdk/issues/1655>

- **Status:** free (nobody has claimed it and no pull request is linked)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 95% · the repo merges 94% of outside PRs
- **Policy:** no AI policy found; sign off commits (DCO)

**What it asks:** Investigate a 400 Bad Request error during service invocation in the Java SDK after upgrading Dapr, specifically when running in Kubernetes.

**A complete fix:**
- Determine if the 400 error is related to changes in Dapr 1.16.8 that affect HTTP request construction or validation from the Java SDK.
- Check if the issue is specific to the environment (e.g., Kubernetes networking, Dapr sidecar configuration) or the SDK usage itself.

**Plan:**
1. Change sdk/src/main/java/io/dapr/client/DaprHttp.java line 320 to use a switch expression or equivalent logic to handle HTTP methods instead of string comparison for GET and DELETE.
2. Change sdk/src/main/java/io/dapr/client/DaprHttp.java line 321 to handle other HTTP methods (PUT, POST, etc.) using the `HttpMethods` enum from `HttpExtension` if possible, or by extending the existing conditional structure to cover all methods defined in `HttpExtension`.
3. Review sdk/src/main/java/io/dapr/client/DaprHttp.java lines 319-321 to ensure that the HTTP method setting logic correctly utilizes the `HttpExtension` object passed into the method, rather than relying solely on `HttpMethods.GET.name().equals(method)` or similar string comparisons.
4. If the HTTP method logic needs to be generalized, introduce a helper method or modify the existing structure to correctly set the HTTP method on `HttpRequest.Builder` based on the `HttpExtension` provided to the method call.
5. Test the service invocation path with various HTTP methods (GET, POST, PUT, DELETE) to verify that the correct HTTP method is set on the `HttpRequest.Builder` when using the SDK's methods.

Files: `sdk/src/main/java/io/dapr/client/DaprHttp.java`, `sdk/src/main/java/io/dapr/client/domain/HttpExtension.java`

Start: `lazycontrib start dapr/java-sdk#1655`

## 3. dapr/java-sdk#1509: Support Native compilation for the Java SDK

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
- Test and ensure a Spring application can be compiled natively with the Java SDK.

**Plan:**
1. Investigate the current dependencies in the project to identify any that might prevent successful native compilation (e.g., those relying on reflection or dynamic class loading in a way that is incompatible with GraalVM).
2. If incompatible dependencies are found, propose and implement necessary workarounds or replacements to ensure compatibility with GraalVM.
3. Create a minimal Spring Boot application example that uses the Java SDK.
4. Attempt to compile this minimal Spring Boot application using GraalVM native image tooling.
5. If compilation fails, use the generated error logs to pinpoint the exact cause (e.g., missing reflection configuration, unsupported language feature).
6. Modify the build configuration (e.g., Maven/Gradle setup) or add necessary configuration files (like `reflect-config.json`) to address the identified issues, ensuring the SDK is correctly configured for native compilation.
7. Test the final setup by successfully building and running the minimal Spring Boot application as a native executable.


Start: `lazycontrib start dapr/java-sdk#1509`

## 4. fatiando/harmonica#586: harmonica.reduction_to_pole  flipping the output in north-south

<https://github.com/fatiando/harmonica/issues/586>

- **Status:** free (nobody has claimed it and no pull request is linked)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 92% · the repo merges 86% of outside PRs · maintainers reply in ~13 h
- **Policy:** AI help discouraged; say how you used AI; no agents opening PRs or commenting

**What it asks:** A bug where `harmonica.reduction_to_pole` flips the output data when processing North Hemisphere data.

**A complete fix:**
- Fix the data flipping issue in `harmonica.reduction_to_pole` for North-South data.
- Ensure the fix handles the loss of CRS information in the output correctly.

**Plan:**
1. Change the signature of `reduction_to_pole` in `src/harmonica/_transformations.py` to accept an optional `is_north_hemisphere` boolean argument, defaulting to `True`.
2. Inside `reduction_to_pole` in `src/harmonica/_transformations.py`, after the Fourier Transform and before the inverse Fourier Transform, check the value of `is_north_hemisphere`.
3. If `is_north_hemisphere` is `False` (indicating South Hemisphere data), negate the real and imaginary components of the resulting complex data array before the inverse Fourier Transform.
4. In `src/harmonica/_transformations.py`, update the docstring for `reduction_to_pole` to describe the new `is_north_hemisphere` parameter and its effect.
5. Update the call to `reduction_to_pole` in `src/harmonica/filters/_transformations.py` (line 451) to pass the necessary hemisphere information, assuming the calling context can determine it, or modify the function signature in `src/harmonica/filters/_transformations.py` to pass it through if it's relevant for the kernel application.
6. Add a test case in `test/filters/test_padding.py` to verify that the output of `reduction_to_pole` is correctly flipped when processing South Hemisphere data.

Files: `src/harmonica/_transformations.py`, `test/filters/test_padding.py`

<details><summary>Policy quotes</summary>

- `ai_welcome`: "Use of Generative AI (GenAI, including chatbots and coding agents) tools in contributions to Fatiando a Terra projects is strongly discouraged but not entirely prohibited."
- `ai_discouraged`: "Use of Generative AI (GenAI, including chatbots and coding agents) tools in contributions to Fatiando a Terra projects is strongly discouraged but not entirely prohibited."
- `must_disclose`: "1. **Declare if GenAI tools have been used** in the process and to what extent."
- `no_autonomous_agents`: "3. Do not use AI agents and bots to submit PRs, Issues, etc. on your behalf."

</details>

Start: `lazycontrib start fatiando/harmonica#586`

## 5. testcontainers/testcontainers-go#3871: [Bug]: basic clickhouse ping failed

<https://github.com/testcontainers/testcontainers-go/issues/3871>

- **Status:** free (nobody has claimed it and no pull request is linked)
- **They know you:** 1 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 71% · the repo merges 13% of outside PRs · maintainers reply in ~1 h
- **Policy:** AI help allowed, with conditions; say how you used AI

**What it asks:** A bug report regarding a basic ping failure with ClickHouse in `testcontainers-go`.

**A complete fix:**
- Investigate the reported failure of the basic ClickHouse ping.
- Ensure the fix works across different Docker/OS configurations.

<details><summary>Policy quotes</summary>

- `ai_welcome`: "Always include co-author footer when AI assists with changes"
- `must_disclose`: "Always include co-author footer when AI assists with changes"

</details>

Start: `lazycontrib start testcontainers/testcontainers-go#3871`

## 6. open-telemetry/opentelemetry.io#7932: [android] [registry] Add Android instrumentation to registry

<https://github.com/open-telemetry/opentelemetry.io/issues/7932>

- **Status:** stale claim (@breedx-splk said they would take it 382 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 95% · the repo merges 98% of outside PRs · maintainers reply in ~8 h
- **Policy:** AI help allowed, with conditions; say how you used AI; write the PR text and replies yourself

**What it asks:** Add Android instrumentation information to the OpenTelemetry registry.

**A complete fix:**
- Add 'android' as a language in the registry.
- Address the potential future need to rethink the 'android' categorization in relation to the collector and other labeling quirks.

<details><summary>Policy quotes</summary>

- `must_disclose`: "I used AI and I have read and followed the [Generative AI Contribution Policy](https://opentelemetry.io/docs/contributing/pull-requests/#using-ai)."
- `own_words_only`: "Yes, I can answer maintainer questions about the content of this PR, without using AI."

</details>

Start: `lazycontrib start open-telemetry/opentelemetry.io#7932`

## 7. open-telemetry/opentelemetry.io#7535: [es] Spanish folder localization blogs

<https://github.com/open-telemetry/opentelemetry.io/issues/7535>

- **Status:** stale claim (@immavalls said they would take it 131 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 94% · the repo merges 98% of outside PRs · maintainers reply in ~8 h
- **Policy:** AI help allowed, with conditions; say how you used AI; write the PR text and replies yourself

**What it asks:** This is a documentation translation task for the Spanish localization of the blogs section. It is a good fit for a contributor with documentation skills, although the specific technical domains (geophysics, etc.) are not directly relevant to the task itself.

**A complete fix:**
- Translate the remaining blog pages into Spanish.
- Open a unique Pull Request for each translated page.

<details><summary>Policy quotes</summary>

- `must_disclose`: "I used AI and I have read and followed the [Generative AI Contribution Policy](https://opentelemetry.io/docs/contributing/pull-requests/#using-ai)."
- `own_words_only`: "Yes, I can answer maintainer questions about the content of this PR, without using AI."

</details>

Start: `lazycontrib start open-telemetry/opentelemetry.io#7535`

## 8. open-telemetry/opentelemetry.io#7841: [es] Spanish folder localization zero-code

<https://github.com/open-telemetry/opentelemetry.io/issues/7841>

- **Status:** stale claim (@abalso0 said they would take it 370 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 94% · the repo merges 98% of outside PRs · maintainers reply in ~8 h
- **Policy:** AI help allowed, with conditions; say how you used AI; write the PR text and replies yourself

**What it asks:** This is a documentation translation task focused on the 'zero-code' section, specifically for Spanish localization. The contributor has a background in scientific/technical domains and has experience with documentation/localization.

**A complete fix:**
- Translate the remaining untranslated pages listed in the issue body (e.g., `zero-code/go/autosdk/`, `zero-code/dotnet/configuration`, `zero-code/Python/configuration`, etc.) into Spanish.
- Ensure each translation is submitted as a unique Pull Request, as requested in the original issue.
- Maintain the practice of keeping some English technical words for clarity, as noted by @abrahamVado.

<details><summary>Policy quotes</summary>

- `must_disclose`: "I used AI and I have read and followed the [Generative AI Contribution Policy](https://opentelemetry.io/docs/contributing/pull-requests/#using-ai)."
- `own_words_only`: "Yes, I can answer maintainer questions about the content of this PR, without using AI."

</details>

Start: `lazycontrib start open-telemetry/opentelemetry.io#7841`

## 9. OpenAPITools/openapi-generator#23274: Add scalafmt (plugin) to scala (client/server) generators

<https://github.com/OpenAPITools/openapi-generator/issues/23274>

- **Status:** stale claim (@YB0y said they would take it 213 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 88% · the repo merges 88% of outside PRs · maintainers reply in ~3 h
- **Policy:** no AI policy found

**What it asks:** The issue is about adding scalafmt support to Scala generators, and there are multiple contributors interested.

**A complete fix:**
- Implement the addition of scalafmt (plugin) to scala (client/server) generators.

Start: `lazycontrib start OpenAPITools/openapi-generator#23274`

## 10. fatiando/harmonica#646: Issue with xrft for next release

<https://github.com/fatiando/harmonica/issues/646>

- **Status:** stale claim (@santisoler said they would take it 175 days ago)
- **They know you:** 2 of your PRs merged here
- **Fit:** ok
- **Effort:** M · **clarity:** clear
- **Merge odds:** 91% · the repo merges 86% of outside PRs · maintainers reply in ~13 h
- **Policy:** AI help discouraged; say how you used AI; no agents opening PRs or commenting

**What it asks:** The issue is a dependency problem where `xrft` version 1.0.2 is not correctly recognized as installed (appearing as 0.0.0) during conda-forge builds, preventing the release of `harmonica`. Solutions discussed include changing the `xrft` recipe to fetch from PyPI or internalizing the necessary FFT functionality from `xrft`.

**A complete fix:**
- Investigate the suggestion to change the `xrft` feedstock to fetch from PyPI.
- Evaluate the feasibility of internalizing the required FFT functions from `xrft` to resolve the dependency issue.
- Address the dependency issue before the v0.8 release.

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
