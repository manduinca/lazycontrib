# lazycontrib 🦥

**Finds open source issues that fit you while you rest, reads them for you, and leaves a briefing you can act on. You stay the author.**

Looking for a good first contribution is slow work: search, open twenty tabs, read every thread to see if someone already took it, find the contributing guide, check whether the project even wants AI-assisted work, then figure out where in the code the fix goes. lazycontrib does that reading with an open-weight model running on your own machine, and hands you a short list with the receipts.

It never opens a pull request, posts a comment or pushes a commit. That part is yours.

## What you get

For each issue it keeps, a briefing with:

- **Is it free?** Linked open pull requests come from the GitHub timeline. Claims in the comments ("can I take this?", "I'm working on it") come from the model, but only count if the code finds the quoted words in that person's comment. Old claims are marked stale.
- **Does the project want your kind of help?** lazycontrib reads `AI_POLICY.md`, `AGENTS.md`, `CONTRIBUTING.md`, PR templates and organization-wide policies, and asks one question per rule: must you disclose AI use, test it yourself, write replies in your own words, keep agents away? Every yes comes with the sentence that says it, verified against the file. Projects that refuse AI-assisted work are skipped. Beginner issues stay with beginners if you already contribute there.
- **What a complete fix looks like**, including the parts a thread adds later, so you don't ship half of it.
- **Where the change goes.** A shallow clone, a search for the names the issue mentions, and a draft plan that may only cite files and helpers that exist in the code. Reusing the helper that already does the job beats patching three call sites.
- **Merge odds.** A [TabPFN](https://github.com/PriorLabs/TabPFN) classifier trained on the recent pull requests outside contributors opened in those same repositories, with features known before you write any code: stars, how often the repo merges outsiders, whether you've been merged there before, the issue's labels, age and discussion.
- **Skipped, and why**, so you can see what it decided not to show you.

`lazycontrib start owner/repo#123` clones the project, creates a branch with a normal name (`fix/123-short-title`) and drops the briefing in `.lazycontrib/BRIEF.md`, which git ignores, with a checklist for the project's rules. Forking and pushing stay manual.

## Quick start

```bash
pip install -e '.[rank]'
ollama pull gemma4:e4b
lazycontrib init --github <your-username>    # builds ~/.lazycontrib/profile.yaml from your merged PRs
$EDITOR ~/.lazycontrib/profile.yaml          # add domains, skills, repos to watch or avoid
lazycontrib scan                             # writes ~/.lazycontrib/digests/<date>.html and .md
lazycontrib start owner/repo#123
```

GitHub access is read-only and uses `GITHUB_TOKEN` or your `gh` login. Responses are cached for six hours.

Any OpenAI-compatible endpoint works instead of Ollama:

```bash
LAZYCONTRIB_LLM_URL=http://my-vllm:8000/v1 LAZYCONTRIB_LLM_API=openai LAZYCONTRIB_MODEL=google/gemma-4-12b lazycontrib scan
```

## Why an open-weight model

lazycontrib reads your history, your interests and a lot of other people's threads every night. That shouldn't need a paid API or leave your laptop. With Gemma on Ollama it costs nothing to run, works offline once the data is cached, and you can swap the model when a better one ships.

## How it decides

The model drafts; the code decides.

- Data comes from the GitHub API, deterministically.
- The model only extracts: summaries, scope, claims, policy sentences, a plan.
- Every claim and every policy rule must quote its source, and the code checks the quote is really there. A second pass asks whether the quoted sentence, on its own, states that rule.
- Files and helpers in a plan are checked against the clone.

Project files sometimes contain instructions aimed at AI agents. lazycontrib treats them as data: the model is only asked whether they state a rule.

## How well it reads policies

`eval/run_policy_eval.py` compares lazycontrib against a keyword baseline on hand-labelled AI policies. The `dev` set (16 projects) was used to write the prompts and keywords; the `test` set (11 other projects) was labelled before running anything and never tuned on.

EVAL_TABLE

## Limits

- Policies that live only on a website (napari, numpy's full policy) are seen only as the link to them.
- Very long `CONTRIBUTING.md` files are read up to 20,000 characters.
- Merge odds are trained on a few hundred pull requests per run; treat them as a ranking signal, not a promise.

## License

Apache-2.0. Ranking uses TabPFN 2.0 open weights under the [Prior Labs License](https://github.com/PriorLabs/TabPFN/blob/main/LICENSE) (built with TabPFN).
