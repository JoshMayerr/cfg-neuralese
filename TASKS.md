# tasks.md

## Today (P1: MVP loop)

- [ ] `env/scenes.py`: scene generator (K=4; ensure unique objects).
- [ ] `env/scoring.py`: metrics (acc, len, complexity, collisions, parse-fail stub).
- [ ] `grammar/base_grammar.lark`: human-readable starter grammar.
- [ ] `agents/openai_client.py`: thin wrapper (env var model name; CFG tool payload).
- [ ] `agents/speaker.py` & `agents/listener.py`: single-call functions (no proposer yet).
- [ ] `loop/evaluate.py`: run N scenes with current grammar → metrics dict.
- [ ] `main.py`: CLI to eval baseline grammar once.
- [ ] Seed prompts in `prompts/`.

## Next (P2: Proposer + mutations)

- [ ] `grammar/patch_schema.json`: strict JSON schema for mutations.
- [ ] `grammar/mutations.py`: ops (rename_terminal, restrict_terminal, remove_separators, replace_rule, add_rule, drop_rule, fix_length, map_vocab, add_checksum).
- [ ] `agents/proposer.py`: returns JSON patch + optional few-shots.
- [ ] `loop/search.py`: Top-K evolutionary loop (K=5, 2 children/parent).
- [ ] `loop/guards.py`: parse-validity, diversity floor, collision penalty.

## Later (P3: robustness + polish)

- [ ] Add noise injection + robustness metric.
- [ ] Add checksum mutation support and acceptance rule.
- [ ] `dashboards/plots.py`: Accuracy vs Length, Robustness vs Length.
- [ ] `scripts/quick_demo.py`: run 5–10 rounds and print before/after messages.

## Stretch

- [ ] Multi-seed experiments & comparison.
- [ ] Token-length measurement (in addition to chars).
- [ ] Optional local parser to sanity-check messages beyond model tool parse.
- [ ] Export run logs to CSV/JSON for analysis.
