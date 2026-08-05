import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Liquidity Monitor",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "liquidity-monitor",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    updated = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Liquidity Monitor</title>
        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background: #f3f5f7;
                color: #17202a;
            }}

            header {{
                background: #14213d;
                color: white;
                padding: 28px 8%;
            }}

            header h1 {{
                margin: 0 0 6px;
                font-size: 30px;
            }}

            header p {{
                margin: 0;
                color: #cbd5e1;
            }}

            main {{
                width: min(1100px, 90%);
                margin: 32px auto;
            }}

            .status {{
                background: white;
                border-left: 6px solid #2e7d32;
                border-radius: 8px;
                padding: 22px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.07);
                margin-bottom: 24px;
            }}

            .status-label {{
                color: #68737d;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}

            .status h2 {{
                margin: 8px 0;
                color: #2e7d32;
            }}

            .cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                gap: 18px;
            }}

            .card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            }}

            .card h3 {{
                margin: 0;
                color: #68737d;
                font-size: 14px;
                font-weight: 600;
            }}

            .value {{
                font-size: 30px;
                font-weight: 700;
                margin: 12px 0 5px;
            }}

            .placeholder {{
                color: #87929d;
                font-size: 13px;
            }}

            .commentary {{
                background: white;
                border-radius: 8px;
                padding: 24px;
                margin-top: 24px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.07);
                line-height: 1.6;
            }}

            footer {{
                width: min(1100px, 90%);
                margin: 30px auto;
                color: #68737d;
                font-size: 13px;
            }}
        </style>
    </head>

    <body>
        <header>
            <h1>U.S. Cash Market Liquidity Monitor</h1>
            <p>Funding, reserves, repo and Treasury-market conditions</p>
        </header>

        <main>
            <section class="status">
                <div class="status-label">Current assessment</div>
                <h2>Normal</h2>
                <p>
                    This is the first test deployment. Live market data and
                    calculated liquidity signals will be added next.
                </p>
            </section>

            <section class="cards">
                <article class="card">
                    <h3>SOFR</h3>
                    <div class="value">—</div>
                    <div class="placeholder">Awaiting data connection</div>
                </article>

                <article class="card">
                    <h3>EFFR</h3>
                    <div class="value">—</div>
                    <div class="placeholder">Awaiting data connection</div>
                </article>

                <article class="card">
                    <h3>IORB</h3>
                    <div class="value">—</div>
                    <div class="placeholder">Awaiting data connection</div>
                </article>

                <article class="card">
                    <h3>SOFR − EFFR</h3>
                    <div class="value">—</div>
                    <div class="placeholder">Calculated spread</div>
                </article>
            </section>

            <section class="commentary">
                <h2>Market Commentary</h2>
                <p>
                    Funding conditions commentary will appear here after the
                    application is connected to official market data.
                </p>
            </section>
        </main>

        <footer>
            Last application refresh: {updated}
        </footer>
    </body>
    </html>
    """
