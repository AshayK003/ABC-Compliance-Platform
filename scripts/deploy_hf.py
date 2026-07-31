"""Deploy the backend to a Hugging Face Spaces Docker space.

Uploads the Space card, Dockerfile, and app code to the configured Space.
The Space rebuilds automatically on every upload.

Requires two environment variables:
  HF_TOKEN     - Hugging Face access token with write access to Spaces
  HF_SPACE_ID  - target Space in "owner/name" form (e.g. "AshayK003/abc-compliance")

The Space must exist before the first deploy (create it at
https://huggingface.co/new-space with SDK "Docker").

Run from the repository root:
  HF_TOKEN=... HF_SPACE_ID=... python scripts/deploy_hf.py
"""

from __future__ import annotations

import os

from huggingface_hub import HfApi

SPACE_ID = os.environ["HF_SPACE_ID"]
CARD_FILE = "deploy/hf/README.md"
ROOT_FILES = ["Dockerfile", "pyproject.toml", "alembic.ini"]
FOLDERS = ["src", "migrations"]


def main() -> None:
    api = HfApi(token=os.environ["HF_TOKEN"])

    # Space card (README.md with frontmatter is what HF reads for SDK config).
    api.upload_file(
        path_or_fileobj=CARD_FILE,
        path_in_repo="README.md",
        repo_id=SPACE_ID,
        repo_type="space",
    )

    # Files and folders the Dockerfile copies at build time.
    for filename in ROOT_FILES:
        api.upload_file(
            path_or_fileobj=filename,
            path_in_repo=filename,
            repo_id=SPACE_ID,
            repo_type="space",
        )
    for folder in FOLDERS:
        api.upload_folder(
            folder_path=folder,
            repo_id=SPACE_ID,
            repo_type="space",
        )

    print(f"Deployed to https://huggingface.co/spaces/{SPACE_ID}")


if __name__ == "__main__":
    main()
