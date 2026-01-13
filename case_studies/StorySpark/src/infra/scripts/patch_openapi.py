#!/usr/bin/env python3
"""
infra/scripts/patch_openapi.py

Usage:
  python3 infra/scripts/patch_openapi.py input_openapi.json output_openapi.yaml --audience "AUD1,AUD2" [--public-paths /health,/openapi.json,/docs]

Reads an OpenAPI JSON file (FastAPI /openapi.json), injects a Google OIDC security scheme
(with x-google fields and x-google-audiences), sets a global security requirement if
one is not present, marks configured public paths as unauthenticated (security: []),
and writes the result as YAML suitable for Google API Gateway's api_config.

The script is idempotent and accepts audiences via CLI (pass OAuth client ID and/or
service URL). It does not embed secrets in the repo; pass sensitive values via CI secrets.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import List
import yaml

DEFAULT_PUBLIC_PATHS = ["/health", "/openapi.json", "/docs"]

def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_yaml(obj: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, sort_keys=False, allow_unicode=True)


def ensure_google_oidc(doc: dict, audience: str) -> dict:
    """
    Ensure components.securitySchemes.google_id_token exists and contains the
    Google OIDC fields required by API Gateway. Update x-google-audiences to the
    provided audience string.
    """
    components = doc.setdefault("components", {})
    sec_schemes = components.setdefault("securitySchemes", {})

    scheme = {
        "type": "openIdConnect",
        "openIdConnectUrl": "https://accounts.google.com/.well-known/openid-configuration",
        "x-google-issuer": "https://accounts.google.com",
        "x-google-jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
        "x-google-audiences": audience,
    }

    existing = sec_schemes.get("google_id_token")
    if existing:
        # Merge/overwrite relevant fields while preserving other keys
        existing.update(scheme)
        sec_schemes["google_id_token"] = existing
    else:
        sec_schemes["google_id_token"] = scheme

    # Ensure global security requires the scheme unless explicitly present
    if "security" not in doc:
        doc["security"] = [{"google_id_token": []}]

    return doc


def mark_public_paths(doc: dict, public_paths: List[str]) -> dict:
    """
    For each path in public_paths, if it exists in doc['paths'], ensure the GET
    operation has security: [] so it is unauthenticated.
    """
    paths = doc.get("paths", {})
    for p in public_paths:
        if p in paths:
            op = paths[p].setdefault("get", {})
            op["security"] = []
    return doc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Patch OpenAPI JSON for Google API Gateway.")
    p.add_argument("input", type=Path, help="Path to input openapi.json")
    p.add_argument("output", type=Path, help="Path to output openapi.yaml")
    p.add_argument(
        "--audience",
        required=True,
        help="Comma-separated audience(s) to accept (e.g., OAUTH_CLIENT_ID,service-url)",
    )
    p.add_argument(
        "--public-paths",
        default=",".join(DEFAULT_PUBLIC_PATHS),
        help=f"Comma-separated list of paths to mark public (default: {','.join(DEFAULT_PUBLIC_PATHS)})",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    inp: Path = args.input
    outp: Path = args.output
    audience: str = args.audience
    public_paths = [p.strip() for p in args.public_paths.split(",") if p.strip()]

    if not inp.exists():
        print(f"ERROR: input file not found: {inp}", file=sys.stderr)
        return 2

    try:
        doc = load_json(inp)
    except Exception as e:
        print(f"ERROR: failed to load JSON from {inp}: {e}", file=sys.stderr)
        return 3

    if not isinstance(doc, dict):
        print("ERROR: OpenAPI document root must be a JSON object", file=sys.stderr)
        return 4

    doc = ensure_google_oidc(doc, audience)
    doc = mark_public_paths(doc, public_paths)

    # Ensure a servers entry exists so Swagger UI and tooling have a default; do not overwrite if present
    if "servers" not in doc:
        doc["servers"] = [{"url": "https://REPLACE_WITH_GATEWAY_HOST"}]

    try:
        outp.parent.mkdir(parents=True, exist_ok=True)
        write_yaml(doc, outp)
    except Exception as e:
        print(f"ERROR: failed to write YAML to {outp}: {e}", file=sys.stderr)
        return 5

    print(f"Wrote patched OpenAPI YAML to {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
