# Sports apps redesign: hand-off

The redesign for the three sports apps was built and approved, but the chat that built it could not push to their repos.
Apply it in a fresh chat that has these repos attached: janissaulitis/court-finish, janissaulitis/caption-checker,
janissaulitis/delivery-report.

For each app folder here (court-finish, caption-checker, delivery-report):

1. Clone the app's repo (main branch).
2. Apply the patches in order: `git am <this folder>/<app>/patches/*.patch`
   If `git am` fails, copy everything under `<app>/files/` over the repo instead (same paths) and commit.
3. Push to main. Streamlit redeploys automatically within a minute or two.
4. Check the live app opens without errors, in light and dark, and on a phone width:
   - court-finish → https://court-finish.streamlit.app/ (split-flap departures board at the top)
   - caption-checker → https://caption-checker.streamlit.app/ (red CAPTIONS score bug, "11 READY")
   - delivery-report → https://tournament-report.streamlit.app/ (press "Build the sample report"; paper list with FIXED / HELD BACK / FLAGGED stamps)

Each app gets its own `kit.py` (shared design kit) and `.streamlit/config.toml` (fonts and colours) from the patches.
The keep-awake job for these three runs from janissaulitis/ai-opportunity-finder (.github/workflows/keep-awake.yml).
