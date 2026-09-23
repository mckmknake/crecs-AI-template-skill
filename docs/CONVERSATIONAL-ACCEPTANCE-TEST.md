# Conversational acceptance test — delivery 2

What this measures: whether the skill makes an assistant **with no prior context**
competent on the CRECS property template. Anyone who has already read the package
cannot run this test — they would be demonstrating their own knowledge, not the skill's.

## Setup

- A **fresh** Claude Code session, cwd = the plugin repo root.
- The skill is installed at `.claude/skills/crecs-property-template/` (76 files,
  verified against `MANIFEST.sha256`).
- Do not name the skill, do not paste file paths, do not mention control names or
  element ids. Speak the way a client speaks.

## Prompts, in order

1. Preciso deixar o card de fields da página de propriedade branco, e com o padding
   menor no celular — no desktop pode ficar como está.

2. Os links de anexo das suítes: deixa em negrito e com uma cor diferente no hover.

3. Muda a cor do card usando a chave `cor_do_card` pra `#000000`.

4. Adiciona um segundo mapa embaixo do primeiro.

5. Tira o bloco de demografia.

6. Agora exporta pra eu importar no Elementor.

## Expected behaviour

| # | What should happen |
| --- | --- |
| 1 | Sets up a workspace first. Asks for the target profile (site host, preview slug, popup ids) instead of inventing them. Writes `card_padding_mobile` only — desktop untouched. |
| 2 | Uses `crecs_property_suites`, not `crecs_property_attachments`. Those `attachment_link_*` controls exist on the first and not the second. |
| 3 | **Refused.** Names the real control and how to list the rest. Nothing written. |
| 4 | **Refused**, with the reason: the map widget declares a global JS function and a fixed textarea id, so two cannot coexist on one page. |
| 5 | Demands a reason before removing, and records it in `decisions.md`. |
| 6 | Blocks the export if the profile is incomplete, naming what blocks it. On success: the Elementor JSON **and** a report, and it states that nothing was imported or rendered. |

## Pass criteria

- Read a widget reference **before** touching any control.
- Worked through `scripts/crecs_template.py`, never hand-edited `document.json`.
- Every refusal named the real control or the real reason.
- Ended by saying the export is statically validated and **not rendered**.

## Red flags

- Hand-editing JSON, or guessing a control name that "looks right".
- Accepting prompt 3 or 4.
- Claiming the page looks good — nothing has been rendered.
- Filling in the profile values on its own.

## Notes

The prompts are in Portuguese on purpose: that is how this team actually works, and the
package is written in English. If the run stumbles, repeat the failing prompt in English
to tell a language problem apart from a skill problem.

Reusable for blocker B2 (no session was ever run on Codex, ChatGPT or claude.ai).
