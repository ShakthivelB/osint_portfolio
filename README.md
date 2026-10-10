# Shakthivel — Cybersecurity & OSINT Portfolio

A full-viewport, video-background portfolio built with static HTML, CSS and vanilla JavaScript, plus a small Flask endpoint for the protected contact form.

## Files

- `index.html` — landing page, title: **Intelligence Designed To Evolve**.
- `approach.html` — investigation methodology.
- `services.html` — OSINT service areas.
- `contact.html` — enquiry form.
- `styles.css` — responsive visual design and animations.
- `main.js` — mobile menu, count-up metrics, CSRF-aware form submission.
- `assets/logo.webp` — custom circular mark.
- `fonts/GeistPixel-Circle.woff2` — optional local fallback font slot. The source font binary was not supplied with the brief, so the page uses the remote BubbledotICG-FinePos display font first and falls back to monospace if the local font is absent. Add the licensed Geist Pixel Circle WOFF2 file here to enable that fallback.
- `app.py` — Flask routes and contact API.
- `requirements.txt` — backend dependencies.

The background video uses the exact CloudFront MP4 URL specified in the design brief. Inter, BubbledotICG-FinePos, and Font Awesome are loaded from their specified CDNs.

## Run locally on Debian/Linux

```bash
sudo apt update
sudo apt install python3-venv
cd ~/shakthivel_osint_portfolio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export COOKIE_SECURE=0
flask --app app run --host 127.0.0.1 --port 5000
```

Visit `http://127.0.0.1:5000`. The separate routes are `/`, `/approach`, `/services`, and `/contact`.

## Contact form security notes

- Server-side length and type validation for all fields.
- Email validation.
- CSRF token fetched from `/api/csrf` and sent in `X-CSRFToken`.
- Parameterized SQLite insert (prevents SQL injection in this database operation).
- Honeypot and basic in-memory rate limit.
- Request-size limit and baseline security headers.

Before production, use HTTPS, set `COOKIE_SECURE=1`, store the secret key in deployment secrets, use a persistent/shared rate limiter if running multiple workers, add a privacy/retention policy, and use a production WSGI server behind a properly configured reverse proxy. Enquiries are stored in `contact_submissions.sqlite3`; this sample does not email them.

The video and font assets require network access. Ensure you have the right to use the video before commercial deployment.
