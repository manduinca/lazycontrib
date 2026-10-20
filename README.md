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

## How well it works

Everything below runs on a MacBook (M3 Pro, 18 GB) with Gemma 4 e4B on Ollama. Each evaluation has a `dev` set I
looked at while writing prompts and a `test` set I labelled before running anything and never tuned on. Raw results
are in `eval/results/`.

### Reading AI policies

Eight rules per project (welcome, discouraged, prohibited, disclose, test it yourself, own words, no agents,
beginner issues reserved), against a keyword baseline I wrote while reading the `dev` projects.

| Test set: 11 projects | lazycontrib | keywords |
| --- | ---: | ---: |
| Rules caught (recall) | **100%** | 67% |
| Rules flagged that are really there (precision) | 68% | 82% |
| F1 | **0.81** | 0.74 |
| Overall stance right | 10/11 | |

Missing a rule is the expensive mistake (you open a PR the project told you not to), so the caution rules keep every
grounded yes, and an extra one is a checklist item with its quote next to it. Only the three stance rules get a second
check, because they decide what you see first. How it got here, on the same test set:

| Version | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| One prompt for all rules (dev set only) | 0.57 | 0.63 | 0.60 |
| One question per rule | 0.60 | 1.00 | 0.75 |
| + second check on every rule | 0.74 | 0.81 | 0.77 |
| + second check on stance rules only (current) | 0.68 | 1.00 | 0.81 |

The one stance it gets wrong is sympy: "do not use AI-generated text to complete the PR description" reads to it as
"no AI at all". That's why a project that seems to refuse AI help is shown last with its quote, not hidden.

### Is the issue still free?

Threads where no open pull request is linked (those are read from the timeline, not the model).

| | dev, 17 threads | test, 15 threads |
| --- | ---: | ---: |
| lazycontrib: free vs taken right | 16/17 | 11/15 |
| claim regex: free vs taken right | 10/17 | 12/15 |
| lazycontrib: said free, but someone had claimed it | **0** | **0** |
| claim regex: said free, but someone had claimed it | 7 | 3 |

lazycontrib's misses on the test set are all the cheap kind: old, vague offers it reads as a stale claim, which only
lowers the issue in the list. The regex misses "May I try to contribute", "I can take the rest" and "can i  work on
this" with two spaces.

### Merge odds

1,595 pull requests that outside contributors opened in 39 repositories. The oldest 75% of each repository's pull
requests train, its newest 25% test.

| | ROC AUC | Brier |
| --- | ---: | ---: |
| The repo's merge rate alone | 0.739 | 0.143 |
| Logistic regression | 0.742 | 0.177 |
| **TabPFN 2.0** | **0.776** | **0.128** |

Five-fold cross-validation agrees (0.756, 0.768, **0.829**). A single global time split does not: its test set is the
last week across all repositories, mostly quick merges, because rejections take longer to close, and there the merge
rate alone wins (0.879 against TabPFN's 0.832). Both are in `eval/results/ranking.json`.

## Limits

- Policies that live only on a website (napari, numpy's full policy) are seen only as the link to them.
- Very long `CONTRIBUTING.md` files are read up to 20,000 characters.
- Merge odds are trained on a few hundred pull requests per run; treat them as a ranking signal, not a promise.

## License

Apache-2.0. Ranking uses TabPFN 2.0 open weights under the [Prior Labs License](https://github.com/PriorLabs/TabPFN/blob/main/LICENSE) (built with TabPFN).
