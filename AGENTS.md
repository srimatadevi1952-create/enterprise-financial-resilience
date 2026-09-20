# V2 workspace boundaries

- This repository is the new V2 development foundation. Never run or mutate the recovered V1 source/database as a normal development step.
- Read the parent V2 architecture, data contracts, development plan and M0 report before extending the implementation.
- Keep `.local`, `.venv`, generated artifacts, backups and credentials out of Git. No external publishing or deployment is configured.
- Require explicit development/test profile selection. Use the identity guard and separate migration role. Do not weaken guards merely to make a test pass.
- M0 has only environment identity/version tables. M1 is not implemented; later milestones must satisfy their own acceptance gates.
- Test database writes are permitted for tests. Never route tests to development or recovery.
