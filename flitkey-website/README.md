# FlitKey Website

This directory contains the landing page and interactive simulator for **FlitKey**, a local-first desktop text expander for Linux and Windows.

## Design Highlights

1. **Raycast Style Command Bar**: A sleek browser-based simulated prompt mimicking the desktop application's user interface.
2. **Interactive Editor Sandbox**: Try typing triggers (like `:date`, `:shrug`, `:ty`) on the left to see them instantly replaced by long text expansions, with live productivity stats tracking characters and time saved.
3. **Windows & Linux Synergy**: Highlighted feature set support for Windows 10/11 alongside Linux (X11 & Wayland).
4. **Light & Dark Mode**: Respects system theme preferences automatically and supports runtime toggling with smooth transitions.
5. **No Dependencies**: Powered by pure Semantic HTML5, CSS Variables, and Vanilla Javascript.

## Local Development

To run this website locally, open `index.html` in your browser or run a simple local web server:

```bash
# Using Python
python3 -m http.server 8000

# Using Node.js (npx)
npx -y serve
```

Then visit [http://localhost:8000](http://localhost:8000) or [http://localhost:3000](http://localhost:3000).

## Netlify Deployment

This folder is configured for zero-config Netlify hosting:
- Build folder is set to `.` (current folder).
- Security headers are pre-configured in `netlify.toml`.
- To deploy, connect your GitHub repository to Netlify and point the base directory to `flitkey-website`.
