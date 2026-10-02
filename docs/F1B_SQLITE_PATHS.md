# F1b SQLite paths

`cls_platform.sqlite_paths.sqlite_path` resolves a file name to `<bot>/db/<name>`. It does not create the file. Nightmode's `anti.db` and the no-prefix staff file `np.db` use it so a different working directory cannot open a second empty database.

These stores are still opened with a working-directory-relative path. They were not migrated in F1. Do not delete them.

- automod.db
- invc.db
- autoreact.db
- welcome.db
- autorole.db
- verification.db
- fastgreet.db
- ticket and logging databases

Retired routes and commands no longer write welcome.db, autorole.db, or the legacy ticket, reaction-role, and auto-react stores. The files stay where they are.
