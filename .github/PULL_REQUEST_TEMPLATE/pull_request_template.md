## Summary

<!-- Describe the changes introduced by this PR in 2-3 sentences. -->

## Type of change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactor / tech debt
- [ ] CI / infra change

## Related issues

Closes #<!-- issue number -->

## Changes

<!-- List the key files / areas changed and why. -->

- 
- 

## Testing

<!-- Describe how you tested these changes. -->

- [ ] Unit tests added / updated
- [ ] Integration tests pass locally
- [ ] Manually tested (describe steps below)

<details>
<summary>Manual test steps</summary>

1. 
2. 

</details>

## Screenshots (if UI changes)

<!-- Before / after screenshots or screen recording. -->

## Positioning gate (required for PRs that change public surface)

> **Required if this PR touches:** landing pages (`apps/web/src/app/`), README,
> marketing copy, blog, taglines, meta descriptions, pricing, or any narrative
> the customer sees. Internal positioning brief is held by the maintainer.
>
> Skip this section for mechanical changes (refactors, tests, infra, deps).

- **Target customer this serves:** <!-- which segment? -->
- **Moat pillar reinforced:** <!-- name one of the three pillars -->
- **Defensibility:** would the moat survive a major adjacent player shipping this tomorrow? <!-- yes/no + 1 sentence -->
- [ ] Not applicable — internal/mechanical change

## Checklist

- [ ] My code follows the style guidelines of this project (`ruff`, `eslint`, `gofmt`)
- [ ] I have performed a self-review of my own code
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally
- [ ] I have updated documentation as needed (README, CHANGELOG, CONTRIBUTING)
- [ ] My changes do not introduce new linter warnings
- [ ] I have checked for sensitive data / credentials in my diff

## Eval harness (required for substrate / playbook / detection changes)

> **Required if this PR touches:** `services/agents/`, `services/api/app/orchestrator/`,
> `playbooks/packs/`, `detections/`, `services/agents/tests/eval_data/`,
> `scripts/generate_eval_incidents.py`, `scripts/run_evals.py`, or any prompt /
> RAG corpus / response template under those trees.
>
> Run `python3 scripts/run_evals.py --json --out /tmp/report.json` before and
> after your change and paste both summary blocks below. Any axis that
> regresses must be called out explicitly. Playbook-touching PRs must include
> the `playbook_completion_rate` block — orphan playbooks / templates fail CI.

<details>
<summary><strong>Before</strong> (paste <code>scripts/run_evals.py</code> output on base branch)</summary>

```text

```

</details>

<details>
<summary><strong>After</strong> (paste <code>scripts/run_evals.py</code> output on this branch)</summary>

```text

```

</details>

- [ ] Not applicable — this PR does not touch substrate, playbooks, detections, or eval inputs
- [ ] No axis regressed
- [ ] An axis regressed; rationale and follow-up are described in the Summary above
