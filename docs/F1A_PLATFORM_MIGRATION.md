# F1a platform migration

Shared primitives live under `dashboard/components/platform`, `dashboard/lib`, and `bot/cls_platform/health/contract.py`. Later phases consume them. They do not replace Automod, Security, Logging, or Commands in this phase.

## Save bar

`SaveBar` is the write path for a form that is not an immediate switch.

- Keep local `saved` and draft state.
- `dirty` is true only when the draft differs from `saved`.
- Pass field messages as `fieldErrors`. The bar and the field both show them before the request is sent.
- Cmd/Ctrl+S, `beforeunload`, and in-app link clicks are attached while the form is dirty.
- An immediate switch may still save on change when the control is obviously instant. Do not put that switch behind the bar.

Adopted now: Bot settings (field errors on the existing bar) and Voice role (bar was already present; the role picker now reports health before save).

Leave Logging, Automod, Commands, and ticket editors for their own phases.

## Errors

A failed load uses `LoadError`. It shows a human sentence, a Retry button, and the technical message as a reference. Do not `catch(() => null)` and then render an empty list.

Adopted now: Welcome home, Custom roles configuration.

## Tables

`DataTable` renders one server page. The parent owns `page`, `size` (25, 50, or 100), and the filter query. `serverPage` is the slice contract. Filters belong in the URL when the view is shareable. The foundation example is `/dashboard/primitives`.

## Health

`GET /api/v1/guilds/{id}/runtime-health` is one cached pass. Role and channel pickers take that snapshot plus the already loaded role or channel list. They do not request Discord once per option. Pass `intent="mutate"` only on forms that will save the selection. Read-only displays omit it.

## Drag

Decorative `img`, `svg`, and `video` elements do not start a native drag. A real drag source sets `draggable="true"` or `data-drag-handle`. The config transfer drop zone is marked `data-dropzone` and still receives file drops.
