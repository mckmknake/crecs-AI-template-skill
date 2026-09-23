# Opening instruction

Paste this as your first message, with the files attached, when the skill cannot be
installed natively. It replaces the automatic discovery that a real skill install
gives you.

---

You are helping me design the shared Elementor property-page template for a CRE Cloud
Solutions (CRECS) WordPress site. I have attached a skill bundle. Before doing anything
else:

1. Read `SKILL.md` in full. It is the operating manual — follow it, including the
   rules about the loader being first, per-widget control names, and responsiveness.
2. Read `references/INDEX.md` so you know which widget reference to open later.
3. Do **not** guess a control name. Open `references/widgets/<widget>.md` and use the
   exact keys it lists. If a control is not there, it does not exist in the installed
   plugin version — tell me instead of inventing a key.
4. If you can run files, use `scripts/crecs_template.py`. Start with:
   `python3 scripts/crecs_template.py selftest`, then
   `python3 scripts/crecs_template.py init --from assets/property-template-all-widgets.json --workdir ./work --profile ./my-profile.json`.
   Every change goes through `set`/`move`/`add-widget`/`remove`/`bind`, then
   `validate`, then `export`.
5. If you **cannot** run files in this conversation, say so up front. You can still use
   the references to propose changes, but you must label the result as unvalidated:
   reading the rules is not the same as running the validator. Do not claim a template
   is correct, and do not claim it looks right — nothing here renders anything.

Reply in my language. Do not translate the site's own content.

---

## Attach these

Minimum, for reference-only work:

- `SKILL.md`
- `references/INDEX.md`
- `references/catalog/crecs-property-fields.json`
- the `references/widgets/*.md` files for the widgets you are changing

Add these when file execution is available:

- `assets/property-template-all-widgets.json`
- `assets/target-profile.example.json`
- `references/catalog/crecs-controls.min.json`
- the whole `scripts/` folder

`references/catalog/crecs-controls.min.json` is about 1.8 MB. It is what the scripts
read; you do not need to read it yourself, and you should not paste it into the
conversation. Use the per-widget Markdown files for reading — they are 1–30 KB each.
