# POSH Platform

## Current Implementation Status

- Microsoft Entra SSO now completes in the browser. The backend callback exchanges the Entra authorization code, sets the refresh-token cookie, and redirects to the React callback route. The React app stores the returned `access_token` and opens the correct dashboard for the user's role.
- User management follows the PDF role chain: Super Admin creates Admin, Admin creates Client / Management, Client / Management creates HR / IC, and HR / IC creates Employees.
- Video quality variants are supported through admin uploads. The platform can store and serve multiple quality files, but it does not yet run automatic FFmpeg transcoding from one source upload.
- Multi-language playback is supported through uploaded subtitle/audio tracks. The platform does not yet generate captions, translate subtitles, or synthesize dubbed audio automatically.

## Role Flow

| Role ID | Role | Can Create / Manage |
| --- | --- | --- |
| 1 | Super Admin | Admin |
| 2 | Admin | Client / Management |
| 5 | Client / Management | HR / IC |
| 3 | HR / IC | Employee |
| 4 | Employee | Own training, assessments, certificates |

## Entra SSO Redirect Flow

Configure Microsoft Entra to redirect to:

```text
http://localhost:8000/api/v1/auth/sso/entra/callback
```

Set `FRONTEND_URL` to the React app origin, for example:

```text
FRONTEND_URL=http://localhost:3000
```

After Microsoft redirects back to the API, the backend sends the browser to:

```text
/sso/entra/callback#access_token=...
```

The frontend consumes that fragment, stores auth state in `localStorage`, and removes the token from the visible route by navigating with `replace`.

## Remaining Automation Work

- Add a background FFmpeg transcoding worker if quality files should be generated automatically.
- Add speech-to-text, translation, and text-to-speech integrations if language tracks should be generated automatically.
