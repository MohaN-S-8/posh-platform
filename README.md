Entra SSO is backend/API-level only. I don’t see frontend callback handling that stores the returned access_token, so after Microsoft redirects to /api/v1/auth/sso/entra/callback, the user likely gets JSON instead of being logged into the React app.
Video quality still depends on admin uploading each quality file. There is no automatic transcoding.
Multi-language is now supported by uploaded tracks, but not automatic generation/translation.
Backend tests still cannot run: pytest is not installed in the active Python environment.

pendings...
