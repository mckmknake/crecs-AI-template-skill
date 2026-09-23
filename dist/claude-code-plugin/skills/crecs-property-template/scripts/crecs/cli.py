"""Command line.

Every command has ``--help``. Every error says what to do next. Nothing writes to the
working document unless the change validates first, so a refused edit leaves the file
byte-identical.
"""

import argparse
import json
import os
import sys
import tempfile

from . import __version__, bindings as bindings_mod, coverage as coverage_mod
from . import export as export_mod
from . import validate as validate_mod
from .catalog import Catalog, CatalogError, DEFAULT_MANIFEST, REFERENCES_DIR
from .document import DocumentError
from .profile import Profile, ProfileError
from .state import StateError, Workspace

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_FINDINGS = 2

#: Environment variable that moves the default workspace somewhere the caller chooses.
WORKDIR_ENV = "CRECS_WORKDIR"


class CliError(Exception):
    """A problem the user can fix; printed without a traceback."""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _catalog():
    try:
        return Catalog.load_default()
    except CatalogError as exc:
        raise CliError(str(exc))


def default_workdir():
    """Where the workspace lives when nobody names a directory.

    It has to be the same path on every run, because `init`, `set` and `export` are
    separate processes that must find each other — so this is a fixed name under the
    system temp, not a fresh mkdtemp. One workspace at a time; `CRECS_WORKDIR` moves it
    for anyone who wants more than that.
    """
    override = os.environ.get(WORKDIR_ENV)
    if override:
        return os.path.abspath(override)
    return os.path.join(tempfile.gettempdir(), "crecs-property-template", "workspace")


def _resolve_workdir(args):
    """The given directory, or the default — announced, never silently assumed.

    The announcement goes to stderr so that `--json` output stays parseable.
    """
    given = getattr(args, "workdir", None)
    if given:
        return given
    path = default_workdir()
    sys.stderr.write("no --workdir given; using %s\n" % path)
    return path


def _workspace(args):
    try:
        return Workspace.open(_resolve_workdir(args))
    except StateError as exc:
        raise CliError(str(exc))


def _profile(args, workspace=None):
    path = getattr(args, "profile", None)
    if not path and workspace is not None:
        path = workspace.state.get("profile_path")
    if not path:
        return Profile.empty()
    try:
        return Profile.load(path)
    except ProfileError as exc:
        raise CliError(str(exc))


def _parse_value(raw):
    """JSON when it parses, otherwise the literal string.

    That keeps `--value ""` an empty string, `--value 0` the number zero and
    `--value '{"unit":"px"}'` an object, without a second flag to say which.
    """
    if raw is None:
        return None
    text = raw.strip()
    if text == "":
        return ""
    try:
        return json.loads(text)
    except ValueError:
        return raw


_STRING_STORING_TYPES = ("select", "select2", "switcher", "font", "color", "text",
                         "textarea", "popover_toggle", "choose", "wysiwyg")


def _coerce_to_control(value, control):
    """Honour the control's declared storage type when JSON guessed differently.

    `--value 700` parses as the number 700, but a font-weight select stores the
    string "700" and Elementor compares option values as strings. This narrows the
    JSON guess to what the control actually stores; it never changes a value's
    meaning, and it leaves anything without a declared string type alone.
    """
    if isinstance(value, bool) or value is None:
        return value, None
    if not isinstance(value, (int, float)):
        return value, None

    options = control.options
    if options and all(isinstance(o, str) for o in options):
        text = str(value)
        if text in options:
            return text, "the option list stores strings"
        # Leave it: the option check will report it with the real vocabulary.
        return value, None
    if control.type in _STRING_STORING_TYPES and not options:
        return str(value), "a %r control stores a string" % control.type
    return value, None


def _emit(payload, as_json, text_fn):
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        text_fn(payload)


def _validate_or_raise(document, catalog, profile, workspace, what):
    result = validate_mod.validate(document, catalog, profile,
                                   baseline_keys=workspace.baseline_keys())
    blocking = [f for f in result.by_severity(validate_mod.ERROR)]
    return result, blocking


def _element_summary(document, element):
    return {
        "id": element.id,
        "elType": element.el_type,
        "widgetType": element.widget_type,
        "path": document.path_of(element),
        "children": len(element.raw.get("elements") or []),
        "settings_count": len(element.settings),
    }


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------


def cmd_init(args):
    catalog = _catalog()
    if args.profile:
        _profile(args)  # fail fast on a bad profile
    workdir = _resolve_workdir(args)
    try:
        workspace = Workspace.init(workdir, getattr(args, "from"),
                                   profile_path=args.profile, force=args.force,
                                   catalog=catalog)
    except StateError as exc:
        raise CliError(str(exc))

    profile = _profile(args, workspace)
    document = workspace.load_document()

    # Apply the profile now, so the workspace starts with its site-specific values
    # resolved rather than carrying them as findings until export.
    applied = profile.apply(document)
    if applied:
        workspace.commit(
            document,
            "apply target profile (%d mapping(s))" % len(applied),
            decision="Target profile %s applied at init: %s."
                     % (profile.name or os.path.basename(args.profile or ""),
                        ", ".join("%s.%s -> %r" % (m["element_id"], m["key"], m["to"])
                                  for m in applied)),
            op="profile",
        )
        document = workspace.load_document()

    summary = workspace.resume_summary()
    result = validate_mod.validate(document, catalog, profile,
                                   baseline_keys=workspace.baseline_keys())
    payload = {
        "workdir": workspace.path,
        "revision": summary["revision"],
        "document_sha256": summary["document_sha256"],
        "base_template": summary["base_template"],
        "profile_path": summary["profile_path"],
        "catalog": summary["catalog"],
        "widgets": len(document.widgets()),
        "applied_profile_mappings": applied,
        "validation": result.counts,
    }

    def text(p):
        print("workspace ready: %s" % p["workdir"])
        print("  revision        %s" % p["revision"])
        print("  document        %s" % os.path.join(p["workdir"], "document.json"))
        print("  sha256          %s" % p["document_sha256"])
        print("  base template   %s" % p["base_template"])
        print("  profile         %s" % (p["profile_path"] or "(none — pass --profile "
                                                            "to resolve site ids)"))
        print("  widgets         %s" % p["widgets"])
        print("  validation      %s" % ", ".join("%s=%s" % kv
                                                 for kv in p["validation"].items()))

    _emit(payload, args.json, text)
    return EXIT_OK


def cmd_inspect(args):
    workspace = _workspace(args)
    catalog = _catalog()
    document = workspace.load_document(accept_external=True)

    if args.element:
        element = document.by_id(args.element)
        payload = _element_summary(document, element)
        payload["settings"] = element.settings
        payload["bindings"] = [
            {"control": b.control, "tag": b.tag.name if b.tag else None,
             "settings": b.tag.settings if b.tag else None, "error": b.error}
            for b in bindings_mod.read_element_bindings(element.settings)
        ]
        if element.el_type == "widget" and catalog.is_crecs_widget(element.widget_type):
            payload["catalog"] = {
                "title": catalog.widget_title(element.widget_type),
                "relevance": catalog.relevance(element.widget_type),
                "max_instances": catalog.max_instances(element.widget_type),
                "controls_declared": len(catalog.controls(element.widget_type)),
                "reference": "references/widgets/%s.md" % element.widget_type,
            }

        def text(p):
            print("%s  %s" % (p["id"], p.get("widgetType") or p["elType"]))
            print("  path %s" % p["path"])
            if "catalog" in p:
                print("  %s (%s), %d controls available, reference: %s"
                      % (p["catalog"]["title"], p["catalog"]["relevance"],
                         p["catalog"]["controls_declared"], p["catalog"]["reference"]))
            print("  settings (%d):" % len(p["settings"]))
            for key in sorted(p["settings"]):
                print("    %-46s %s" % (key, json.dumps(p["settings"][key])[:90]))
            for binding in p["bindings"]:
                print("  binding %s -> %s %s%s"
                      % (binding["control"], binding["tag"],
                         json.dumps(binding["settings"]),
                         "  ERROR: " + binding["error"] if binding["error"] else ""))

        _emit(payload, args.json, text)
        return EXIT_OK

    if args.widgets:
        widgets = [_element_summary(document, w) for w in document.widgets()]
        payload = {"widgets": widgets, "count": len(widgets)}

        def text(p):
            print("%d widgets, in document order:" % p["count"])
            for index, widget in enumerate(p["widgets"], 1):
                print("  %2d. %-8s %-32s %s"
                      % (index, widget["id"], widget["widgetType"] or "?",
                         widget["path"]))

        _emit(payload, args.json, text)
        return EXIT_OK

    elements = [_element_summary(document, e) for e in document.elements()]
    payload = {
        "elements": elements,
        "count": len(elements),
        "element_model": document.element_model(),
        "export_version": document.export_version,
        "revision": workspace.state.get("revision"),
    }

    def text(p):
        print("revision %s, %d elements, %s model, export version %s"
              % (p["revision"], p["count"], p["element_model"], p["export_version"]))
        for element in p["elements"]:
            depth = element["path"].count("/")
            print("  %s%-8s %-10s %s"
                  % ("  " * depth, element["id"], element["elType"],
                     element["widgetType"] or ""))

    _emit(payload, args.json, text)
    return EXIT_OK


def _resolve_control(catalog, element, key, device=None):
    """Return (control, effective_key) or raise CliError with a usable message."""
    owner = element.widget_type if element.el_type == "widget" else element.el_type
    if owner is None:
        raise CliError("element %s has no widget type" % element.id)
    if not (catalog.knows_widget(owner) or catalog.knows_element_type(owner)):
        raise CliError(
            "%s is a %r, which is not in this catalog, so its controls cannot be "
            "checked. Editing it blind is refused." % (element.id, owner)
        )
    el_kind = "widget" if element.el_type == "widget" else "element"
    control = catalog.control(owner, key, el_type=el_kind)
    if control is None:
        suggestion, why = catalog.suggest_control(owner, key)
        message = "%s (%s) has no control %r." % (element.id, owner, key)
        if suggestion:
            message += " Closest registered control: %r%s." % (
                suggestion, " — " + why if why else ""
            )
        message += ("\nRun `catalog --widget %s --controls` for the full list, or read "
                    "references/widgets/%s.md." % (owner, owner))
        raise CliError(message)

    if device:
        if device not in catalog.devices:
            raise CliError("device %r is not an active breakpoint here. Active: %s."
                           % (device, ", ".join(catalog.devices)))
        if not control.is_responsive:
            raise CliError(
                "%r on %s is not a responsive control (is_responsive is false), so "
                "Elementor never reads a %s variant of it. Set it once for all devices "
                "instead." % (key, owner, device)
            )
        return control, "%s_%s" % (key, device)
    return control, key


def cmd_set(args):
    workspace = _workspace(args)
    catalog = _catalog()
    profile = _profile(args, workspace)
    document = workspace.load_document(accept_external=args.accept_external)
    element = document.by_id(args.element)
    control, key = _resolve_control(catalog, element, args.key, args.device)
    value, coerced = _coerce_to_control(_parse_value(args.value), control)

    before = element.settings.get(key, "\0absent")
    element.settings[key] = value

    result, blocking = _validate_or_raise(document, catalog, profile, workspace, "set")
    relevant = [f for f in blocking if f.element_id == element.id and f.control == key]
    if relevant:
        raise CliError("refused, nothing was written:\n" + "\n".join(
            "  [%s] %s%s" % (f.code, f.message, "\n      hint: " + f.hint if f.hint else "")
            for f in relevant
        ))

    summary = "set %s.%s" % (element.id, key)
    workspace.commit(document, summary, decision=args.decision,
                     accept_external=args.accept_external)
    payload = {
        "element_id": element.id,
        "key": key,
        "value": value,
        "previous": None if before == "\0absent" else before,
        "was_absent": before == "\0absent",
        "revision": workspace.state["revision"],
        "control": {"type": control.type, "is_responsive": control.is_responsive,
                    "source": control.source_ref()},
        "validation": result.counts,
    }

    payload["coerced"] = coerced

    def text(p):
        print("r%s  %s.%s = %s" % (p["revision"], p["element_id"], p["key"],
                                   json.dumps(p["value"])))
        if p.get("coerced"):
            print("      stored as a string because %s" % p["coerced"])
        if not p["was_absent"]:
            print("      was %s" % json.dumps(p["previous"]))
        print("      control type %s%s, declared at %s"
              % (p["control"]["type"],
                 ", responsive" if p["control"]["is_responsive"] else "",
                 p["control"]["source"]))

    _emit(payload, args.json, text)
    return EXIT_OK


def cmd_unset(args):
    workspace = _workspace(args)
    catalog = _catalog()
    document = workspace.load_document(accept_external=args.accept_external)
    element = document.by_id(args.element)
    key = args.key
    if args.device:
        key = "%s_%s" % (key, args.device)
    try:
        document.unset_setting(element.id, key)
    except DocumentError as exc:
        raise CliError(str(exc))
    workspace.commit(document, "unset %s.%s" % (element.id, key),
                     decision=args.decision, accept_external=args.accept_external)
    payload = {"element_id": element.id, "key": key,
               "revision": workspace.state["revision"]}
    _emit(payload, args.json,
          lambda p: print("r%s  removed %s.%s" % (p["revision"], p["element_id"],
                                                  p["key"])))
    return EXIT_OK


def cmd_add_widget(args):
    workspace = _workspace(args)
    catalog = _catalog()
    profile = _profile(args, workspace)
    document = workspace.load_document(accept_external=args.accept_external)

    widget_type = args.widget
    if not catalog.knows_widget(widget_type):
        suggestion, note = catalog.suggest_widget(widget_type)
        message = "%r is not a widget this catalog knows." % widget_type
        if suggestion:
            message += " Did you mean %r?" % suggestion
        if note:
            message += " " + note
        message += "\nRun `catalog --list-widgets` to see what is available."
        raise CliError(message)

    limit = catalog.max_instances(widget_type)
    if limit is not None:
        existing = [w for w in document.widgets() if w.widget_type == widget_type]
        if len(existing) >= limit:
            raise CliError(
                "%s already appears %d time(s) and at most %d can work on one page.\n%s"
                % (widget_type, len(existing), limit,
                   catalog.cardinality_reason(widget_type) or "")
            )

    settings = _parse_value(args.settings) if args.settings else {}
    if not isinstance(settings, dict):
        raise CliError("--settings must be a JSON object")

    try:
        new_id = document.add_widget(args.into, widget_type, settings, index=args.index)
    except DocumentError as exc:
        raise CliError(str(exc))

    result, blocking = _validate_or_raise(document, catalog, profile, workspace, "add")
    own = [f for f in blocking if f.element_id == new_id]
    if own:
        raise CliError("refused, nothing was written:\n" + "\n".join(
            "  [%s] %s" % (f.code, f.message) for f in own
        ))

    workspace.commit(document, "add %s into %s" % (widget_type, args.into),
                     decision=args.decision, accept_external=args.accept_external)
    payload = {"element_id": new_id, "widgetType": widget_type, "into": args.into,
               "revision": workspace.state["revision"], "validation": result.counts,
               "reference": "references/widgets/%s.md" % widget_type}
    _emit(payload, args.json,
          lambda p: print("r%s  added %s as %s inside %s\n      reference: %s"
                          % (p["revision"], p["widgetType"], p["element_id"],
                             p["into"], p["reference"])))
    return EXIT_OK


def cmd_remove(args):
    workspace = _workspace(args)
    catalog = _catalog()
    document = workspace.load_document(accept_external=args.accept_external)
    element = document.by_id(args.element)

    if not args.reason:
        raise CliError(
            "removing an element needs --reason, so the decision is recorded in "
            "decisions.md. A property that happens to have no data for a block is not "
            "a reason to drop the block from the template shared by every property."
        )

    widget_type = element.widget_type
    if widget_type and catalog.relevance(widget_type) == "required" and not args.force:
        raise CliError(
            "%s is %s, which the page needs to function: it resolves the property and "
            "writes it into the PHP session ($_SESSION['property']) that every other "
            "property widget reads.\n%s\n"
            "Alternatives: move it instead of deleting it, or if this page really "
            "should carry no property data, remove the property widgets as well.\n"
            "To proceed anyway, add --force."
            % (element.id, widget_type, catalog.cardinality_reason(widget_type) or "")
        )

    removed = document.remove(element.id)
    workspace.commit(document,
                     "remove %s (%s)" % (element.id, widget_type or element.el_type),
                     decision=args.reason, accept_external=args.accept_external)
    payload = {"element_id": element.id, "widgetType": widget_type,
               "reason": args.reason, "revision": workspace.state["revision"],
               "descendants_removed": _count(removed) - 1}
    _emit(payload, args.json,
          lambda p: print("r%s  removed %s (%s) and %d descendant(s)\n      reason: %s"
                          % (p["revision"], p["element_id"],
                             p["widgetType"] or "element",
                             p["descendants_removed"], p["reason"])))
    return EXIT_OK


def _count(raw):
    return 1 + sum(_count(c) for c in (raw.get("elements") or []))


def cmd_move(args):
    workspace = _workspace(args)
    catalog = _catalog()
    profile = _profile(args, workspace)
    document = workspace.load_document(accept_external=args.accept_external)
    try:
        document.move(args.element, before=args.before, after=args.after,
                      into=args.into, index=args.index)
    except DocumentError as exc:
        raise CliError(str(exc))

    result, blocking = _validate_or_raise(document, catalog, profile, workspace, "move")
    order = [f for f in blocking if f.code in ("E-LOADER-ORDER", "E-NESTING")]
    if order:
        raise CliError("refused, nothing was written:\n" + "\n".join(
            "  [%s] %s" % (f.code, f.message) for f in order
        ))

    where = "before %s" % args.before if args.before else (
        "after %s" % args.after if args.after else "into %s" % args.into)
    workspace.commit(document, "move %s %s" % (args.element, where),
                     decision=args.decision, accept_external=args.accept_external)
    payload = {"element_id": args.element, "placement": where,
               "revision": workspace.state["revision"], "validation": result.counts}
    _emit(payload, args.json,
          lambda p: print("r%s  moved %s %s" % (p["revision"], p["element_id"],
                                                p["placement"])))
    return EXIT_OK


def _all_bindings(document, element_id=None):
    """Every dynamic binding in the document, in document order.

    The stored value travels with each row on purpose. A heading whose `title` reads
    "Add Your Heading Text Here" looks like a leftover until you can see that a binding
    replaces it at render time — that is the difference between deleting dead weight and
    deleting the property name from every page on the site.
    """
    out = []
    for element in document.elements():
        if element_id and element.id != element_id:
            continue
        for binding in bindings_mod.read_element_bindings(element.settings):
            tag = binding.tag
            row = {
                "element_id": element.id,
                "element_type": element.widget_type or element.el_type,
                "control": binding.control,
                "tag": tag.name if tag is not None else None,
                "param": None,
                "stored_value": element.settings.get(binding.control),
                "error": binding.error,
            }
            if tag is not None and tag.settings:
                # crecs-property carries param_name; popup carries popup.
                row["param"] = tag.settings.get("param_name") or tag.settings.get("popup")
                row["tag_settings"] = tag.settings
            out.append(row)
    return out


def cmd_bind_list(args):
    workspace = _workspace(args)
    document = workspace.load_document(accept_external=args.accept_external)
    if args.element:
        document.by_id(args.element)  # fail with the usual message if it is unknown
    found = _all_bindings(document, args.element)

    def render(p):
        rows = p["bindings"]
        if not rows:
            print("no dynamic bindings" + (" on %s" % args.element if args.element else ""))
            return
        print("%d binding(s):" % len(rows))
        for r in rows:
            head = "  %-10s %-28s %-24s" % (r["element_id"], r["element_type"] or "",
                                            r["control"])
            if r["error"]:
                print(head + " BROKEN: " + r["error"])
                continue
            print(head + " %s %s" % (r["tag"] or "?", r["param"] or ""))
            stored = r.get("stored_value")
            if isinstance(stored, str) and stored.strip():
                print("             stored value, shown only if the binding resolves to "
                      "nothing: %r" % stored[:60])

    _emit({"bindings": found}, args.json, render)
    return EXIT_OK


def cmd_bind(args):
    if getattr(args, "list", False):
        return cmd_bind_list(args)
    for required in ("element", "control", "param"):
        if not getattr(args, required, None):
            raise CliError("--%s is required to write a binding. To see what is already "
                           "bound, use `bind --list`." % required)

    workspace = _workspace(args)
    catalog = _catalog()
    profile = _profile(args, workspace)
    document = workspace.load_document(accept_external=args.accept_external)
    element = document.by_id(args.element)

    if args.tag != "crecs-property":
        raise CliError(
            "this command only writes crecs-property bindings. %r is outside the "
            "catalog; bind it in the Elementor editor if you need it." % args.tag
        )
    if args.param not in catalog.property_params():
        suggestion = catalog.suggest_param(args.param)
        message = ("%r is not a param_name that "
                   "Crecs_Functions::crecs_parse_property_data() produces."
                   % args.param)
        if suggestion:
            message += (" The real key is %r — keys are compared exactly, including "
                        "case." % suggestion)
        message += "\nRun `catalog --params` for the full list."
        raise CliError(message)

    detail = catalog.param_detail(args.param) or {}
    if not detail.get("bindable_scalar") and not args.force:
        raise CliError(
            "%r exists but holds a non-scalar value, and the tag renders only strings "
            "and numbers, so the binding would print nothing. %s\nUse --force if you "
            "know what you are doing." % (args.param, detail.get("note") or "")
        )

    bindings_mod.set_element_binding(element.settings, args.control,
                                     "crecs-property", {"param_name": args.param})
    result, blocking = _validate_or_raise(document, catalog, profile, workspace, "bind")
    own = [f for f in blocking
           if f.element_id == element.id and f.control == args.control]
    if own:
        raise CliError("refused, nothing was written:\n" + "\n".join(
            "  [%s] %s" % (f.code, f.message) for f in own
        ))

    workspace.commit(document,
                     "bind %s.%s -> %s" % (element.id, args.control, args.param),
                     decision=args.decision, accept_external=args.accept_external)
    payload = {"element_id": element.id, "control": args.control,
               "param_name": args.param, "revision": workspace.state["revision"],
               "shortcode": element.settings["__dynamic__"][args.control]}
    _emit(payload, args.json,
          lambda p: print("r%s  bound %s.%s to crecs-property param_name=%s"
                          % (p["revision"], p["element_id"], p["control"],
                             p["param_name"])))
    return EXIT_OK


def cmd_unbind(args):
    workspace = _workspace(args)
    document = workspace.load_document(accept_external=args.accept_external)
    element = document.by_id(args.element)
    if not bindings_mod.clear_element_binding(element.settings, args.control):
        raise CliError("%s has no dynamic binding on %r." % (element.id, args.control))
    workspace.commit(document, "unbind %s.%s" % (element.id, args.control),
                     decision=args.decision, accept_external=args.accept_external)
    payload = {"element_id": element.id, "control": args.control,
               "revision": workspace.state["revision"]}
    _emit(payload, args.json,
          lambda p: print("r%s  unbound %s.%s" % (p["revision"], p["element_id"],
                                                  p["control"])))
    return EXIT_OK


def _popup_bindings(document, profile):
    """Every Elementor Pro popup binding in the document, in document order."""
    out = []
    for element in document.elements():
        for binding in bindings_mod.read_element_bindings(element.settings):
            tag = binding.tag
            if tag is None or tag.name != "popup":
                continue
            popup_id = tag.settings.get("popup")
            popup_id = str(popup_id) if popup_id not in (None, "") else ""
            out.append({
                "element_id": element.id,
                "element_type": element.widget_type or element.el_type,
                "control": binding.control,
                "popup_id": popup_id,
                "declared_by_profile": bool(popup_id) and profile.knows_popup(popup_id),
            })
    return out


def cmd_popup(args):
    """List or retarget an Elementor Pro popup binding.

    The shipped template binds its contact buttons to the reference site's popup ids,
    and those ids mean nothing on anyone else's site. Nothing else in this tool could
    change them: `set --key __dynamic__` is refused because __dynamic__ is not a
    control, and it should stay refused. This is the supported way.

    The tool never renumbers an id on its own, and refuses an id the target profile
    does not declare, because declaring an id is how a person asserts that the popup
    exists on that site.
    """
    workspace = _workspace(args)
    profile = _profile(args, workspace)
    document = workspace.load_document(accept_external=args.accept_external)

    if args.list:
        found = _popup_bindings(document, profile)
        declared = sorted((profile.data.get("popups") or {}).keys()) \
            if not profile.is_empty() else []
        payload = {"bindings": found, "profile_declares": declared}

        def render(p):
            if not p["bindings"]:
                print("no popup bindings in this document")
                return
            header = "%-10s %-24s %-10s %-8s %s"
            print(header % ("ELEMENT", "TYPE", "CONTROL", "POPUP", "DECLARED"))
            for b in p["bindings"]:
                print(header % (b["element_id"], b["element_type"][:24], b["control"],
                                b["popup_id"] or "(none)",
                                "yes" if b["declared_by_profile"] else "NO"))
            undeclared = [b for b in p["bindings"] if not b["declared_by_profile"]]
            if undeclared:
                print("")
                print("%d binding(s) point at a popup this profile does not declare."
                      % len(undeclared))
                print("Retarget each one, with the id of a popup on the client's site:")
                for b in undeclared:
                    print("  popup --element %s --control %s --set <id> --decision ..."
                          % (b["element_id"], b["control"]))

        _emit(payload, args.json, render)
        return EXIT_OK

    if not args.element or not args.control:
        raise CliError("--element and --control are required unless you pass --list.\n"
                       "Run `popup --list` to see what this document binds.")
    if not args.set and not args.clear:
        raise CliError("pass --set <popup id> or --clear.")
    if args.set and args.clear:
        raise CliError("--set and --clear are mutually exclusive.")
    if not args.decision:
        raise CliError("--decision is required: retargeting a button is a decision "
                       "about the client's site, and it lands in decisions.md.")

    element = document.by_id(args.element)
    existing = [b for b in bindings_mod.read_element_bindings(element.settings)
                if b.control == args.control]
    if not existing:
        raise CliError("%s has no dynamic binding on %r. Run `popup --list` to see the "
                       "popup bindings this document has." % (element.id, args.control))
    tag = existing[0].tag
    if tag is None or tag.name != "popup":
        raise CliError("%s binds %r through the %r tag, not a popup. This command only "
                       "retargets popup bindings."
                       % (element.id, args.control,
                          tag.name if tag is not None else "unparseable"))

    was = str(tag.settings.get("popup") or "")

    if args.clear:
        bindings_mod.clear_element_binding(element.settings, args.control)
        workspace.commit(document,
                         "popup clear %s.%s (was %s)"
                         % (element.id, args.control, was or "none"),
                         decision=args.decision,
                         accept_external=args.accept_external)
        payload = {"element_id": element.id, "control": args.control,
                   "cleared": True, "was": was,
                   "revision": workspace.state["revision"]}
        _emit(payload, args.json,
              lambda p: print("r%s  cleared the popup binding on %s.%s (was %s)"
                              % (p["revision"], p["element_id"], p["control"],
                                 p["was"] or "none")))
        return EXIT_OK

    new_id = str(args.set).strip()
    if not new_id.isdigit():
        raise CliError("%r is not a post id. An Elementor Pro popup is a post, so its "
                       "id is a number." % new_id)
    if not profile.knows_popup(new_id):
        known = ", ".join(sorted((profile.data.get("popups") or {}).keys())) or "(nothing)"
        raise CliError(
            "the target profile does not declare popup %s, so this tool will not point "
            "a button at it.\n"
            "Declaring an id is how you assert the popup exists on the client's site. "
            "Add it to the profile's popups map with a label, then run this again.\n"
            "The profile currently declares: %s" % (new_id, known)
        )
    if new_id == was:
        raise CliError("%s.%s already points at popup %s."
                       % (element.id, args.control, new_id))

    tag_settings = dict(tag.settings)
    tag_settings["popup"] = new_id
    bindings_mod.set_element_binding(element.settings, args.control, "popup",
                                     tag_settings, instance_id=tag.instance_id)

    result, blocking = _validate_or_raise(document, _catalog(), profile, workspace,
                                          "popup")
    own = [f for f in blocking
           if f.element_id == element.id and f.control == args.control]
    if own:
        raise CliError("refused, nothing was written:\n" + "\n".join(
            "  [%s] %s" % (f.code, f.message) for f in own
        ))

    workspace.commit(document,
                     "popup %s.%s %s -> %s" % (element.id, args.control,
                                               was or "none", new_id),
                     decision=args.decision, accept_external=args.accept_external)
    payload = {"element_id": element.id, "control": args.control,
               "popup_id": new_id, "was": was,
               "revision": workspace.state["revision"],
               "shortcode": element.settings["__dynamic__"][args.control]}
    _emit(payload, args.json,
          lambda p: print("r%s  %s.%s now opens popup %s (was %s)"
                          % (p["revision"], p["element_id"], p["control"],
                             p["popup_id"], p["was"] or "none")))
    return EXIT_OK


def cmd_validate(args):
    workspace = _workspace(args)
    catalog = _catalog()
    profile = _profile(args, workspace)
    document = workspace.load_document(accept_external=True)
    result = validate_mod.validate(document, catalog, profile,
                                   baseline_keys=workspace.baseline_keys())

    wanted = {"error": [validate_mod.ERROR],
              "warning": [validate_mod.ERROR, validate_mod.WARNING],
              "info": [validate_mod.ERROR, validate_mod.WARNING, validate_mod.INFO]}
    levels = wanted[args.level]
    findings = [f for f in result.findings if f.severity in levels]

    payload = result.to_dict()
    payload["findings"] = [f.to_dict() for f in findings]
    payload["claim_level"] = ("static validation only; not imported into Elementor and "
                             "not rendered")

    def text(p):
        print("revision %s — ERROR=%d WARNING=%d INFO=%d  (%s)"
              % (workspace.state.get("revision"), p["counts"]["ERROR"],
                 p["counts"]["WARNING"], p["counts"]["INFO"],
                 "exportable" if p["exportable"] else "export blocked"))
        for finding in p["findings"]:
            print("  [%s] %s %s" % (finding["severity"], finding["code"],
                                    finding.get("element_id") or ""))
            print("      " + finding["message"].replace("\n", "\n      "))
            if finding.get("hint"):
                print("      hint: " + finding["hint"])
        print("  claim level: " + p["claim_level"])

    _emit(payload, args.json, text)
    return EXIT_FINDINGS if result.counts[validate_mod.ERROR] else EXIT_OK


def cmd_diff(args):
    workspace = _workspace(args)
    history = workspace.history()
    if not history:
        print("no revisions yet; nothing to compare")
        return EXIT_OK

    current = json.load(open(workspace.document_path, encoding="utf-8"))
    target_rev = args.rev if args.rev is not None else history[-1]["revision"]
    entry = next((h for h in history if h["revision"] == target_rev), None)
    if entry is None or not entry.get("snapshot"):
        raise CliError("no snapshot for revision %s. Run `history` to see what exists."
                       % target_rev)
    previous = json.load(open(os.path.join(workspace.path, entry["snapshot"]),
                              encoding="utf-8"))

    changes = _diff_documents(previous, current)
    payload = {"from_revision": target_rev - 1, "to_revision":
               workspace.state.get("revision"), "changes": changes}

    def text(p):
        print("diff r%s -> r%s (%d change(s))"
              % (p["from_revision"], p["to_revision"], len(p["changes"])))
        for change in p["changes"]:
            print("%s %s" % (change["op"], change["where"]))
            if change["op"] == "~":
                print("    - %s" % json.dumps(change["before"])[:160])
                print("    + %s" % json.dumps(change["after"])[:160])
            elif change["op"] == "+":
                print("    + %s" % json.dumps(change["after"])[:160])
            elif change["op"] == "-":
                print("    - %s" % json.dumps(change["before"])[:160])

    _emit(payload, args.json, text)
    return EXIT_OK


def _index_settings(payload):
    out = {}

    def walk(node):
        if isinstance(node, dict) and "elType" in node:
            element_id = node.get("id")
            settings = node.get("settings") or {}
            if isinstance(settings, dict):
                for key, value in settings.items():
                    out["%s.%s" % (element_id, key)] = value
            out["%s::__exists__" % element_id] = node.get("widgetType") or node["elType"]
            for child in node.get("elements") or []:
                walk(child)

    roots = payload["content"] if isinstance(payload, dict) else payload
    for root in roots:
        walk(root)
    return out


def _diff_documents(before, after):
    old, new = _index_settings(before), _index_settings(after)
    changes = []
    for key in sorted(set(old) | set(new)):
        if key.endswith("::__exists__"):
            if key in old and key not in new:
                changes.append({"op": "-", "where": "element " + key.split("::")[0],
                                "before": old[key], "after": None})
            elif key not in old and key in new:
                changes.append({"op": "+", "where": "element " + key.split("::")[0],
                                "before": None, "after": new[key]})
            continue
        if key in old and key not in new:
            changes.append({"op": "-", "where": key, "before": old[key], "after": None})
        elif key not in old and key in new:
            changes.append({"op": "+", "where": key, "before": None, "after": new[key]})
        elif old[key] != new[key]:
            changes.append({"op": "~", "where": key, "before": old[key],
                            "after": new[key]})
    return changes


def cmd_history(args):
    workspace = _workspace(args)
    payload = workspace.resume_summary()
    payload["history"] = workspace.history()
    payload["decisions"] = workspace.decisions_text()

    def text(p):
        print("workspace %s" % p["workdir"])
        print("  revision %s, updated %s" % (p["revision"], p["updated_at"]))
        print("  document %s" % p["document"])
        print("  sha256   %s" % p["document_sha256"])
        print("  profile  %s" % (p["profile_path"] or "(none)"))
        print("  catalog  %s @ %s" % (p["catalog"].get("crecs_plugin"),
                                      (p["catalog"].get("plugin_revision") or "")[:12]))
        print("  history:")
        for entry in p["history"]:
            print("    r%-3s %-6s %s" % (entry["revision"], entry["op"],
                                         entry["summary"]))
            if entry.get("decision"):
                print("          decision: %s" % entry["decision"])

    _emit(payload, args.json, text)
    return EXIT_OK


def cmd_undo(args):
    workspace = _workspace(args)
    try:
        revision = workspace.undo(steps=args.steps)
    except StateError as exc:
        raise CliError(str(exc))
    payload = {"revision": revision, "steps": args.steps}
    _emit(payload, args.json,
          lambda p: print("r%s  undid %d step(s); the document now holds the earlier "
                          "content" % (p["revision"], p["steps"])))
    return EXIT_OK


def cmd_export(args):
    to_stream = args.out == export_mod.STDOUT_PATH
    if to_stream and args.json:
        raise CliError(
            "--out - and --json both write to stdout, so they cannot be combined. "
            "Use --out - for the Elementor JSON, or --json with a real path for the "
            "report."
        )
    workspace = _workspace(args)
    catalog = _catalog()
    profile = _profile(args, workspace)
    if workspace.external_change_pending() and not args.accept_external:
        raise CliError(
            "document.json changed outside this tool since the last commit. Re-run "
            "with --accept-external to export the file as it is now."
        )
    report, written = export_mod.export(workspace, args.out, catalog, profile,
                                        allow_draft=args.allow_draft, title=args.title,
                                        accept_external=args.accept_external)
    if written is None:
        blocking = [f for f in report["findings"] if f["severity"] == "ERROR"]
        lines = ["export refused: %d blocking finding(s). Nothing was written."
                 % len(blocking)]
        for finding in blocking:
            lines.append("  [%s] %s %s" % (finding["code"],
                                           finding.get("element_id") or "",
                                           finding["message"]))
            if finding.get("hint"):
                lines.append("      hint: " + finding["hint"])
        lines.append("")
        lines.append("Use --allow-draft to save an incomplete draft anyway.")
        raise CliError("\n".join(lines))

    def text(p):
        # When the envelope went to stdout, every human line goes to stderr instead,
        # or the stream stops being a file.
        out = sys.stderr if to_stream else sys.stdout
        label = "DRAFT (incomplete)" if p.get("draft") else "ready"
        if to_stream:
            print("exported %s -> stdout" % label, file=out)
        else:
            print("exported %s -> %s" % (label, p["export_path"]), file=out)
            print("  report      %s.report.json" % p["export_path"], file=out)
        print("  counts      %s" % ", ".join("%s=%s" % kv for kv in p["counts"].items()),
              file=out)
        print("  claim level %s" % p["claim_level"], file=out)
        if p["applied_profile_mappings"]:
            print("  profile mappings applied:", file=out)
            for mapping in p["applied_profile_mappings"]:
                print("    %s.%s: %r -> %r (%s)"
                      % (mapping["element_id"], mapping["key"], mapping["from"],
                         mapping["to"], mapping["source"]), file=out)

    _emit(report, args.json, text)
    return EXIT_OK


def cmd_catalog(args):
    catalog = _catalog()

    if args.params:
        params = catalog.fields.get("params", [])
        payload = {"count": len(params), "params": params}

        def text(p):
            print("%d crecs-property param_name values (the editor dropdown shows a "
                  "per-property subset):" % p["count"])
            for entry in p["params"]:
                flag = "" if entry.get("bindable_scalar") else "  [not bindable]"
                print("  %-34s %s%s" % (entry["param_name"],
                                        ",".join(entry.get("reads") or []), flag))

        _emit(payload, args.json, text)
        return EXIT_OK

    if args.list_widgets:
        rows = []
        for name in catalog.relevant_widget_names():
            rows.append({
                "name": name,
                "title": catalog.widget_title(name),
                "relevance": catalog.relevance(name),
                "controls": len(catalog.controls(name)),
                "max_instances": catalog.max_instances(name),
            })
        payload = {"widgets": rows, "count": len(rows)}

        def text(p):
            print("%d widgets relevant to the property page:" % p["count"])
            for row in p["widgets"]:
                print("  %-30s %-11s %4d controls  max %s"
                      % (row["name"], row["relevance"], row["controls"],
                         row["max_instances"] if row["max_instances"] else "unlimited"))

        _emit(payload, args.json, text)
        return EXIT_OK

    if args.widget:
        name = args.widget
        if not catalog.knows_widget(name):
            suggestion, note = catalog.suggest_widget(name)
            message = "%r is not a widget in this catalog." % name
            if suggestion:
                message += " Did you mean %r?" % suggestion
            if note:
                message += " " + note
            raise CliError(message)
        controls = catalog.controls(name)
        payload = {
            "name": name,
            "title": catalog.widget_title(name),
            "relevance": catalog.relevance(name),
            "max_instances": catalog.max_instances(name),
            "cardinality_reason": catalog.cardinality_reason(name),
            "sections": catalog.sections(name),
            "legacy_aliases": catalog.legacy_aliases(name),
            "naming_hazards": catalog.naming_hazards(name) or [],
            "reference": "references/widgets/%s.md" % name,
            "control_count": len(controls),
        }
        if args.controls:
            payload["controls"] = {
                key: {
                    "type": c.type, "tab": c.tab, "section": c.section,
                    "serialized_as": c.data.get("serialized_as"),
                    "is_responsive": c.is_responsive,
                    "options": c.options,
                    "open_vocabulary": c.open_vocabulary,
                    "default": c.data.get("default"),
                    "source": c.source_ref(),
                }
                for key, c in sorted(controls.items())
                if not args.section or c.section == args.section
            }

        def text(p):
            print("%s — %s (%s)" % (p["name"], p["title"], p["relevance"]))
            print("  controls %d, max instances %s"
                  % (p["control_count"], p["max_instances"] or "unlimited"))
            if p["cardinality_reason"]:
                print("  cardinality: %s" % p["cardinality_reason"])
            for hazard in p["naming_hazards"]:
                print("  hazard: %s — %s" % (hazard["control"], hazard["note"]))
            if p["legacy_aliases"]:
                print("  keys from older exports:")
                for old, now in sorted(p["legacy_aliases"].items()):
                    print("    %-44s -> %s" % (old, now or "(no equivalent)"))
            print("  reference: %s" % p["reference"])
            if "controls" in p:
                for key, c in p["controls"].items():
                    print("    %-46s %-16s %s%s"
                          % (key, c["type"],
                             "responsive " if c["is_responsive"] else "",
                             ("options=" + ",".join(c["options"])) if c["options"]
                             else ("open vocabulary" if c["open_vocabulary"] else "")))

        _emit(payload, args.json, text)
        return EXIT_OK

    raise CliError("catalog needs one of --list-widgets, --widget or --params")


def cmd_selftest(args):
    """Offline package integrity: catalog present, manifest matches, assets parse."""
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL",
                       "detail": detail})

    try:
        catalog = Catalog.load_default()
        check("catalog loads", True,
              "CRECS %s, Elementor %s, revision %s"
              % (catalog.provenance.get("crecs_plugin"),
                 catalog.provenance.get("elementor"),
                 (catalog.provenance.get("plugin_revision") or "")[:12]))
    except CatalogError as exc:
        check("catalog loads", False, str(exc))
        catalog = None

    if catalog is not None:
        check("relevant widgets present", len(catalog.relevant_widget_names()) >= 16,
              "%d relevant widgets" % len(catalog.relevant_widget_names()))
        check("property params present", len(catalog.property_params()) >= 50,
              "%d params" % len(catalog.property_params()))
        check("responsive devices declared", bool(catalog.devices),
              ", ".join(catalog.devices))

    # manifest
    if os.path.isfile(DEFAULT_MANIFEST):
        import hashlib
        bad = []
        missing = []
        with open(DEFAULT_MANIFEST, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                digest, rel = line.split("  ", 1)
                path = os.path.join(REFERENCES_DIR, rel)
                if not os.path.isfile(path):
                    missing.append(rel)
                    continue
                actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
                if actual != digest:
                    bad.append(rel)
        check("reference manifest matches", not bad and not missing,
              "missing=%d changed=%d" % (len(missing), len(bad))
              + ("; " + ", ".join((missing + bad)[:5]) if (missing or bad) else ""))
    else:
        check("reference manifest matches", False, "MANIFEST.sha256 not found")

    # assets
    from .coverage import BASE_TEMPLATE, FIXTURES
    from .document import Document
    if os.path.isfile(BASE_TEMPLATE):
        try:
            document = Document(json.load(open(BASE_TEMPLATE, encoding="utf-8")))
            check("base template parses", True,
                  "%d elements, %d widgets"
                  % (len(document.elements()), len(document.widgets())))
        except Exception as exc:
            check("base template parses", False, str(exc))
    else:
        check("base template parses", False, "missing " + BASE_TEMPLATE)

    fixture_names = sorted(f for f in os.listdir(FIXTURES)) \
        if os.path.isdir(FIXTURES) else []
    fixture_bad = []
    for name in fixture_names:
        if not name.endswith(".json"):
            continue
        try:
            Document(json.load(open(os.path.join(FIXTURES, name), encoding="utf-8")))
        except Exception as exc:
            fixture_bad.append("%s (%s)" % (name, exc))
    check("fixtures parse", not fixture_bad,
          "%d fixture(s)" % len([n for n in fixture_names if n.endswith(".json")])
          + ("; bad: " + ", ".join(fixture_bad) if fixture_bad else ""))

    check("no network use", True, "the package imports only the standard library")

    failed = [c for c in checks if c["status"] == "FAIL"]
    payload = {"checks": checks, "passed": not failed, "version": __version__}

    def text(p):
        for entry in p["checks"]:
            print("%s  %-32s %s" % (entry["status"], entry["check"], entry["detail"]))
        print("\n%d/%d checks passed" % (len(p["checks"]) - len(failed),
                                         len(p["checks"])))

    _emit(payload, args.json, text)
    return EXIT_OK if not failed else EXIT_FINDINGS


def cmd_coverage(args):
    catalog = _catalog()
    payload = coverage_mod.report(catalog)

    def text(p):
        print("documents examined: %s" % ", ".join(p["documents_examined"]))
        print("widgets covered: %d/%d" % (p["widgets_covered"], p["widgets_relevant"]))
        if p["widgets_uncovered"]:
            print("  not covered: %s" % ", ".join(p["widgets_uncovered"]))
        print("control families exercised: %d/%d"
              % (p["families_exercised"], p["families_total"]))
        if p["families_not_exercised"]:
            print("  not exercised: %s" % ", ".join(p["families_not_exercised"]))
        print("method: %s" % p["method"])
        print("claim level: %s" % p["claim_level"])

    _emit(payload, args.json, text)
    return EXIT_OK


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="crecs_template.py",
        description="Inspect, edit, validate and export the shared CRECS Elementor "
                    "property template. Offline, standard library only.",
        epilog="Start with: init --from assets/property-template-all-widgets.json "
               "--workdir ./work --profile my-profile.json",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    def add(name, help_text, needs_workdir=True, mutating=False):
        sub = subparsers.add_parser(name, help=help_text, description=help_text)
        if needs_workdir:
            sub.add_argument("--workdir",
                             help="the workspace directory created by `init`; "
                                  "defaults to %s, or $%s"
                                  % (default_workdir(), WORKDIR_ENV))
        sub.add_argument("--json", action="store_true",
                         help="print machine-readable JSON instead of text")
        if mutating:
            sub.add_argument("--decision",
                             help="one line for decisions.md explaining why")
            sub.add_argument("--accept-external", action="store_true",
                             help="proceed even though document.json changed outside "
                                  "this tool (their edit is kept, yours is applied on "
                                  "top)")
        return sub

    p = add("init", "Create a workspace from a template file.", needs_workdir=False)
    p.add_argument("--workdir",
                   help="directory to create; defaults to %s, or $%s"
                        % (default_workdir(), WORKDIR_ENV))
    p.add_argument("--from", required=True, dest="from",
                   help="the Elementor JSON to start from")
    p.add_argument("--profile", help="target profile JSON (site host, preview slug, "
                                     "popup and media ids)")
    p.add_argument("--force", action="store_true",
                   help="discard an existing workspace at this path")
    p.set_defaults(func=cmd_init)

    p = add("inspect", "Show the tree, the widget list, or one element.")
    p.add_argument("--element", help="show just this element id")
    p.add_argument("--widgets", action="store_true",
                   help="list widgets in document order")
    p.add_argument("--tree", action="store_true", help="list every element (default)")
    p.set_defaults(func=cmd_inspect)

    p = add("set", "Set one control on one element.", mutating=True)
    p.add_argument("--element", required=True)
    p.add_argument("--key", required=True, help="control name, without a device suffix")
    p.add_argument("--value", required=True,
                   help="JSON when it parses (numbers, objects, \"\"), else a literal "
                        "string")
    p.add_argument("--device", choices=["tablet", "mobile"],
                   help="write the device variant; refused unless the control is "
                        "responsive")
    p.add_argument("--profile")
    p.set_defaults(func=cmd_set)

    p = add("unset", "Remove one control from one element.", mutating=True)
    p.add_argument("--element", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--device", choices=["tablet", "mobile"])
    p.set_defaults(func=cmd_unset)

    p = add("add-widget", "Add a widget into a column.", mutating=True)
    p.add_argument("--widget", required=True, help="technical widget name")
    p.add_argument("--into", required=True, help="target column id")
    p.add_argument("--index", type=int, help="position within the column")
    p.add_argument("--settings", help="JSON object of initial settings")
    p.add_argument("--profile")
    p.set_defaults(func=cmd_add_widget)

    p = add("remove", "Remove an element. Requires --reason.", mutating=True)
    p.add_argument("--element", required=True)
    p.add_argument("--reason", help="recorded in decisions.md")
    p.add_argument("--force", action="store_true",
                   help="remove even a functionally required widget")
    p.set_defaults(func=cmd_remove)

    p = add("move", "Move an element, keeping its id.", mutating=True)
    p.add_argument("--element", required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--before")
    group.add_argument("--after")
    group.add_argument("--into")
    p.add_argument("--index", type=int)
    p.add_argument("--profile")
    p.set_defaults(func=cmd_move)

    p = add("bind", "Bind a control to a crecs-property field, or list what is bound.",
            mutating=True)
    p.add_argument("--list", action="store_true", dest="list",
                   help="show every binding in the document instead of writing one; "
                        "with --element, only that element's")
    p.add_argument("--element")
    p.add_argument("--control", help="the control to bind, e.g. title")
    p.add_argument("--param", help="crecs-property param_name")
    p.add_argument("--tag", default="crecs-property")
    p.add_argument("--force", action="store_true",
                   help="bind even a non-scalar field")
    p.add_argument("--profile")
    p.set_defaults(func=cmd_bind)

    p = add("unbind", "Remove a dynamic binding from a control.", mutating=True)
    p.add_argument("--element", required=True)
    p.add_argument("--control", required=True)
    p.set_defaults(func=cmd_unbind)

    p = add("popup", "List or retarget Elementor Pro popup bindings.", mutating=True)
    p.add_argument("--list", action="store_true",
                   help="show every popup binding and whether the profile declares it")
    p.add_argument("--element", help="element id carrying the binding")
    p.add_argument("--control", help="control the binding sits on, usually 'link'")
    p.add_argument("--set", help="popup post id on the TARGET site; it must be declared "
                                 "in the profile")
    p.add_argument("--clear", action="store_true", help="remove the binding entirely")
    p.add_argument("--profile")
    p.set_defaults(func=cmd_popup)

    p = add("validate", "Check the document. ERROR blocks export; WARNING and INFO "
                        "do not.")
    p.add_argument("--profile")
    p.add_argument("--level", choices=["error", "warning", "info"], default="info",
                   help="lowest severity to print (default info, i.e. everything)")
    p.set_defaults(func=cmd_validate)

    p = add("diff", "Show what changed in a revision.")
    p.add_argument("--rev", type=int, help="revision to compare against (default: the "
                                           "most recent)")
    p.set_defaults(func=cmd_diff)

    p = add("history", "Show the revision history and the resume summary.")
    p.set_defaults(func=cmd_history)

    p = add("undo", "Restore the content from before a revision.")
    p.add_argument("--steps", type=int, default=1)
    p.set_defaults(func=cmd_undo)

    p = add("export", "Write importable Elementor JSON plus a report.")
    p.add_argument("--out", required=True,
                   help="path for the export, or - to write the Elementor JSON to "
                        "stdout when there is nowhere to save a file")
    p.add_argument("--profile")
    p.add_argument("--title", help="envelope title")
    p.add_argument("--allow-draft", action="store_true",
                   help="write an incomplete draft even though errors remain")
    p.add_argument("--accept-external", action="store_true")
    p.set_defaults(func=cmd_export)

    p = add("catalog", "Query the shipped control catalog.", needs_workdir=False)
    p.add_argument("--list-widgets", action="store_true")
    p.add_argument("--widget", help="describe one widget")
    p.add_argument("--controls", action="store_true", help="include its controls")
    p.add_argument("--section", help="only controls in this section")
    p.add_argument("--params", action="store_true",
                   help="list the crecs-property param_name universe")
    p.set_defaults(func=cmd_catalog)

    p = add("coverage", "Report which widgets and control families are exercised.",
            needs_workdir=False)
    p.set_defaults(func=cmd_coverage)

    p = add("selftest", "Check package integrity offline.", needs_workdir=False)
    p.set_defaults(func=cmd_selftest)

    return parser


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()

    if not argv:
        parser.print_help()
        return EXIT_USAGE

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse prints its own message; --help exits 0 and must stay 0.
        return int(exc.code or 0)

    if not getattr(args, "func", None):
        parser.print_help()
        return EXIT_USAGE

    # Errors belong on stderr: `export --out -` puts the Elementor JSON on stdout, and
    # a refusal printed there would be indistinguishable from a truncated file.
    try:
        return args.func(args)
    except CliError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE
    except (DocumentError, StateError, ProfileError, CatalogError) as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE
