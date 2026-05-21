import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    api_url: str
    username: str
    password: str
    org_slug: str
    transport: str
    host: str
    port: int

    def __init__(self):
        self.api_url = os.environ.get("DALGO_API_URL", "http://localhost:8002").rstrip("/")
        self.username = os.environ.get("DALGO_USERNAME", "")
        self.password = os.environ.get("DALGO_PASSWORD", "")
        self.org_slug = os.environ.get("DALGO_ORG_SLUG", "")
        self.transport = os.environ.get("DALGO_TRANSPORT", "stdio")
        self.host = os.environ.get("DALGO_HOST", "0.0.0.0")
        self.port = int(os.environ.get("DALGO_PORT", "8079"))
        # Public URL when behind a reverse proxy or tunnel (e.g. Cloudflare Tunnel).
        # Used as OAuth issuer/resource URL in metadata. Falls back to http://localhost:<port>.
        self.public_url = os.environ.get("DALGO_PUBLIC_URL", "").rstrip("/")

    def validate(self):
        if self.transport not in ("stdio", "streamable-http"):
            raise ValueError(f"DALGO_TRANSPORT must be 'stdio' or 'streamable-http', got '{self.transport}'")

        if not self.api_url:
            raise ValueError("Missing required environment variable: DALGO_API_URL")

        if self.transport == "stdio":
            missing = []
            if not self.username:
                missing.append("DALGO_USERNAME")
            if not self.password:
                missing.append("DALGO_PASSWORD")
            if not self.org_slug:
                missing.append("DALGO_ORG_SLUG")
            if missing:
                raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


config = Config()
