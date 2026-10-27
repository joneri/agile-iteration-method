<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/local-runtime-access.md
-->

# AIM local runtime access

These capabilities support the requested repository workflow; they are not
permission to inspect unrelated files, collect credentials or run arbitrary
commands. Planning and local evidence inspection do not require an AIM account,
API key or external AIM service. Start the UI only when requested or needed for
the user's authorized work. Installation/update downloads are separate from
ordinary local runtime operation.

### Local communication endpoints

- The optional UI launcher starts `http://127.0.0.1:<port>/` on an available
  local port. Direct server invocation defaults to port `4177`; its bind-address
  allowlist is `127.0.0.1`, `localhost` and `::1`. It rejects non-loopback binds.
  Do not expose or forward this listener to a LAN or public network.
- `GET /` and packaged static assets serve the local interface.
  `GET /api/board` reads the selected repository's Story/decision view;
  `GET /api/health` checks the repository-bound process identity/version.
  `GET /api/evidence?path=...` reads a requested contained `.aim/` file; absolute
  paths, traversal and symlink components are rejected. These files can contain
  project information and are displayed locally, not uploaded to AIM.
- `GET /api/actions/latest` and `GET /api/actions/status?id=...` report local
  dispatch progress. The only POST route, `/api/actions/dispatch`, submits an
  exact currently eligible activate/approve action to the already-bound Codex
  task. It is not a shell-command endpoint or a direct repository writer.
  Host checks reject unexpected authorities; POST requires the listener's exact
  same Origin. The UI's content policy limits connections to its own origin.
- Browser `fetch` calls use relative paths on that local listener. Timers poll
  board/action status; they do not schedule uploads. The launcher's HTTP health
  probe also uses the recorded `127.0.0.1` listener.
- The optional Codex bridge starts `codex app-server --listen stdio://` and
  exchanges JSON messages through local stdin/stdout pipes, not a TCP service.
  It verifies the bound task before resuming it and sending the reviewed action.
  `codex://new?...` links are local application handoffs for visible prompts.
  Codex itself can communicate with its configured provider under its existing
  login, settings and permissions. A dispatched prompt contains repository/action
  context; this is distinct from the local UI HTTP traffic.
- There is no AIM telemetry, hosted learning sync or runtime upload endpoint.
  OWASP/NIST reference links and JSON Schema identifiers in the package identify
  documentation or schemas; the helpers do not fetch them automatically.
  User-requested installation/update through the skills CLI can contact npm and
  GitHub as documented in `version-and-installation.md`. Other network
  use for product work requires the user's task authority and host permissions.

### Environment variables

The bundled helpers explicitly read these three configuration variables:

| Variable | Purpose and default |
| --- | --- |
| `CODEX_THREAD_ID` | Existing host task identity, used only to bind and verify optional UI dispatch. It is not an API credential; without it, background dispatch is unavailable. |
| `AIM_UI_STATE_DIR` | Override the local UI instance/dispatch metadata and log directory; default `~/.aim/ui/instances/`. |
| `AIM_LEARNING_REGISTRY` | Override the shared local SQLite learning registry; default `~/.aim/learning/registry.sqlite3`. A command's explicit `--registry` can select another local path. |

Standard home-directory, executable lookup and browser-launch behavior can also
use the operating system's normal environment. Child processes inherit the
launching environment; the helpers do not enumerate it or extract credentials.
Do not print environment contents or request new secrets for these local features.
The installed Codex executable manages its own authentication.

### Local file access and process execution

Read the selected repository's profile, requirements, code and referenced
evidence to plan, validate and explain the requested work. Authorized delivery
helpers write the repository's `.aim/` ledger, decisions, observations, evidence
and locks using their bounded runtime contracts. Product edits, configured
project-agent files and profile updates follow the user's approved task scope.
The UI serves read-only repository views; its dispatch bookkeeping is stored in
the local UI state directory. The local learning helper reads/writes generalized
lessons and proof references in the selected SQLite registry, not a remote server.
Do not place raw secrets or identifying project content in shared lesson text.
Credential/private-key/path expressions in `scripts/aim_quality/learning.py`
are rejection rules for submitted lesson text, not embedded credentials or keys.

The launcher executes the installed Python interpreter with packaged
`scripts/aim_ui.py` and explicit repository/loopback/port arguments. The optional
bridge executes the installed Codex command described above. Both use argument
lists without `shell=True`; browser requests cannot choose executables or command
strings. Opening the local URL uses the operating system's browser handler.
Stopping/replacing a UI instance checks its recorded identity before signaling
that process and removing its instance metadata. Explicit legacy cleanup removes
only artifacts classified by its documented cleanup contract. Repository-specific
build/test commands run only as required by authorized product work; preserve host
approval controls. No download-and-execute shell pipeline is needed for UI use.
