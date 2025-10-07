AGENTS.md
=========

Overview
--------
This repository contains the files for the Cello project. It is a program for management of vials, plates and racks and boxes. These vials, plates and racks and boxes contain compounds for biological experients. Each compound has a set of properties, such as batch id, mol weight, and so on.

The program has a frontend built with python and PyQT5 and a backend that is built on python, tornado web, mysql, rdkit


Design principles
-----------------
- Small & focused: an agent should do one thing well and be easy to reason about.
- Observable: agents should print clear status messages and write outputs to predictable paths.
- Reproducible: where possible, behavior should be deterministic and idempotent.
- Safe: long-running operations (downloads/writes) should stream and provide progress/cancellation hooks.

Where to look
--------------
- `tools/` — CLI and helper scripts. These are the first place to check for data-processing utilities.
- `frontend/` — GUI features and UI agents. The launcher and update flows live here. Uses requests to communicate with the server.
- `backend/` — server-side code used by UI agents; useful for understanding APIs the launcher talks to.

