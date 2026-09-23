"""The target profile.

A template carries references that only mean something on one site: a preview slug,
popup post ids, media attachment ids, the site host. The profile is where those live,
so the template itself stays portable and no id from the source site is reused by
assumption.

A profile holds **no secrets**. It is a list of ids and names that are already public
on the client's own site.
"""

import json
import os

KNOWN_KEYS = (
    "name",
    "site_host",
    "preview_slug",
    "popups",
    "media",
    "templates",
    "fonts",
    "example_slugs",
    "forbidden_literals",
    "allow_hosts",
    "notes",
)

SECRET_HINTS = ("token", "password", "secret", "apikey", "api_key", "credential",
                "authorization", "auth_token", "private_key")


class ProfileError(Exception):
    pass


class Profile:
    def __init__(self, data=None):
        self.data = dict(data or {})
        self._applied = []
        self._validate()

    # -- construction --------------------------------------------------------

    @classmethod
    def empty(cls):
        return cls({})

    @classmethod
    def load(cls, path):
        if not os.path.isfile(path):
            raise ProfileError(
                "target profile not found: %s. Copy assets/target-profile.example.json "
                "and fill in the client's site host, preview slug and popup ids." % path
            )
        with open(path, encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except ValueError as exc:
                raise ProfileError("target profile %s is not valid JSON: %s"
                                   % (path, exc))
        if not isinstance(data, dict):
            raise ProfileError("target profile must be a JSON object, got %s"
                               % type(data).__name__)
        return cls(data)

    def _validate(self):
        unknown = [k for k in self.data if k not in KNOWN_KEYS and not k.startswith("_")]
        if unknown:
            raise ProfileError(
                "target profile has unrecognised key(s): %s. Known keys: %s"
                % (", ".join(sorted(unknown)), ", ".join(KNOWN_KEYS))
            )
        for key in ("popups", "media", "templates"):
            value = self.data.get(key)
            if value is not None and not isinstance(value, dict):
                raise ProfileError("profile '%s' must be an object mapping id -> "
                                   "description, got %s" % (key, type(value).__name__))
        for key in ("example_slugs", "forbidden_literals", "allow_hosts", "fonts"):
            value = self.data.get(key)
            if value is not None and not isinstance(value, list):
                raise ProfileError("profile '%s' must be an array, got %s"
                                   % (key, type(value).__name__))
        leaks = self.secret_like_keys()
        if leaks:
            raise ProfileError(
                "target profile looks like it contains credentials (%s). A profile "
                "holds only public ids and names; never put tokens or keys in it."
                % ", ".join(leaks)
            )

    def secret_like_keys(self):
        found = []

        def walk(node, trail):
            if isinstance(node, dict):
                for key, value in node.items():
                    lowered = str(key).lower()
                    if any(hint in lowered for hint in SECRET_HINTS):
                        found.append("/".join(trail + [str(key)]))
                    walk(value, trail + [str(key)])
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, trail + [str(index)])

        walk(self.data, [])
        return found

    # -- lookups -------------------------------------------------------------

    @property
    def name(self):
        return self.data.get("name")

    @property
    def site_host(self):
        return self.data.get("site_host")

    @property
    def preview_slug(self):
        return self.data.get("preview_slug")

    @property
    def example_slugs(self):
        return list(self.data.get("example_slugs") or [])

    @property
    def forbidden_literals(self):
        return list(self.data.get("forbidden_literals") or [])

    def allowed_hosts(self):
        hosts = list(self.data.get("allow_hosts") or [])
        if self.site_host:
            hosts.append(self.site_host)
        return hosts

    def knows_popup(self, popup_id):
        return str(popup_id) in (self.data.get("popups") or {})

    def knows_media(self, media_id):
        return str(media_id) in (self.data.get("media") or {})

    def knows_template(self, template_id):
        return str(template_id) in (self.data.get("templates") or {})

    def is_empty(self):
        return not self.data

    # -- application ---------------------------------------------------------

    def apply(self, document):
        """Write the profile's own values into the document, recording each change.

        Only explicit mappings are applied: the preview slug into the loader. Popup
        and media ids are *declarations* that the target site has them, never
        rewrites — silently renumbering someone else's ids is how a template ends up
        pointing at the wrong popup.
        """
        self._applied = []
        if not self.preview_slug:
            return self._applied
        for widget in document.widgets():
            if widget.widget_type != "crecs_property_data":
                continue
            before = widget.settings.get("slug")
            if before == self.preview_slug:
                continue
            widget.settings["slug"] = self.preview_slug
            self._applied.append({
                "element_id": widget.id,
                "key": "slug",
                "from": before,
                "to": self.preview_slug,
                "source": "profile.preview_slug",
            })
        return self._applied

    @property
    def applied_mappings(self):
        return list(self._applied)

    def describe(self):
        return {
            "name": self.name,
            "site_host": self.site_host,
            "preview_slug": self.preview_slug,
            "popups": sorted((self.data.get("popups") or {}).keys()),
            "media": sorted((self.data.get("media") or {}).keys()),
            "templates": sorted((self.data.get("templates") or {}).keys()),
            "example_slugs": self.example_slugs,
            "forbidden_literals_count": len(self.forbidden_literals),
        }
