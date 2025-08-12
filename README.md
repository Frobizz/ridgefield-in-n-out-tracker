# Ridgefield In‑N‑Out — Open Yet?

A tiny site that checks **once daily** whether the Ridgefield, WA In‑N‑Out has officially opened.  
Built for Vercel using a **Python Serverless Function** and **Vercel Cron**.

## How it works
- `api/check.py` fetches two official pages:
  - Grand openings: https://www.in-n-out.com/locations/grand-openings
  - Locations directory: https://www.in-n-out.com/locations
- It looks for signals that Ridgefield is listed with a date/hours.
- The result is written to **Vercel Blob** as `status.json` so your site can read it quickly.
- A **Vercel Cron** (9:00 AM PT daily) hits `/api/check` to refresh.

## Deploy (once)
1. Create a new **Vercel** project from this repo. No framework required (static site + Python function).
2. In **Vercel → Storage → Blob**, create a Blob Store and generate a **Read/Write token**.
3. In **Vercel → Project → Settings → Environment Variables**, add:
   - `VERCEL_BLOB_READ_WRITE_TOKEN = <your token>`
4. Deploy. Your site will be live at `https://<project>.vercel.app`.
5. Cron is configured in `vercel.json`:
   ```json
   {"crons":[{"path":"/api/check","schedule":"0 16 * * *"}]}
   ```

## Local testing
You can’t run the Vercel runtime locally without `vercel dev`, but you can still exercise the logic:
```bash
pip install -r requirements.txt
python -c "import api.check as c; print(c.run_check())"
```

## Notes
- Python handler uses **`BaseHTTPRequestHandler`** as required by Vercel’s Python runtime.
- Blob writes use the community `vercel_blob` package (unofficial wrapper). You can also hit the official REST endpoints if preferred.
- This is intentionally lightweight. Add more sources or a Next.js front‑end later if you want.
