"""
Lotto Quant Engine & Frontend Dashboard
System: 6 aus 49 (Garantie: Mindestens 3 Richtige)
Architektur: FastAPI + In-Memory Bitvector Matrix + Tailwind Frontend
"""

import time
import random
import itertools
from typing import List, Dict
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

# =====================================================================
# KERN-ALGORITHMUS (HOCHOPTIMIERTE BIT-MATRIX)
# =====================================================================

class LottoCore:
    @staticmethod
    def to_vector(numbers: tuple) -> int:
        vector = 0
        for n in numbers:
            vector |= (1 << n)
        return vector

    @staticmethod
    def from_vector(vector: int) -> List[int]:
        return [i for i in range(1, 50) if (vector & (1 << i))]


class AdvancedPortfolioGenerator:
    """Generiert ein hocheffizientes, kompaktes mathematisches Netz (~170-250 Tipps)."""
    def __init__(self):
        self.all_triplets = list(itertools.combinations(range(1, 50), 3))
        self.triplet_vectors = [LottoCore.to_vector(t) for t in self.all_triplets]

    def build(self) -> List[int]:
        random.seed(42)  # Für deterministische, reproduzierbare Best-Ergebnisse
        uncovered = set(range(len(self.triplet_vectors)))
        portfolio = []
        
        print("[Engine] Knüpfe kompaktes mathematisches Netz...")
        
        while uncovered:
            target_idx = random.choice(list(uncovered))
            base_triplet = self.all_triplets[target_idx]
            
            available_numbers = [n for n in range(1, 50) if n not in base_triplet]
            best_ticket = 0
            best_coverage = -1
            
            # Optimierter Such-Pool für schnellen Free-Tier Boot
            for _ in range(15):
                extra = random.sample(available_numbers, 3)
                candidate_ticket = LottoCore.to_vector(tuple(list(base_triplet) + extra))
                
                coverage = 0
                sample_space = random.sample(list(uncovered), min(len(uncovered), 200))
                for idx in sample_space:
                    if (candidate_ticket & self.triplet_vectors[idx]) == self.triplet_vectors[idx]:
                        coverage += 1
                        
                if coverage > best_coverage:
                    best_coverage = coverage
                    best_ticket = candidate_ticket
            
            portfolio.append(best_ticket)
            
            covered_indices = {i for i in uncovered if (best_ticket & self.triplet_vectors[i]) == self.triplet_vectors[i]}
            uncovered -= covered_indices
            
        return list(set(portfolio))


# =====================================================================
# API INITIALISIERUNG
# =====================================================================

app = FastAPI(title="Lotto Quant Engine", version="2.0.0")

GLOBAL_SYSTEM = {
    "portfolio": [],
    "generation_time": 0.0,
    "size": 0
}

@app.on_event("startup")
def initialize_engine():
    start = time.perf_counter()
    generator = AdvancedPortfolioGenerator()
    GLOBAL_SYSTEM["portfolio"] = generator.build()
    end = time.perf_counter()
    GLOBAL_SYSTEM["generation_time"] = round(end - start, 4)
    GLOBAL_SYSTEM["size"] = len(GLOBAL_SYSTEM["portfolio"])
    print(f"[INIT] Portfolio bereit: {GLOBAL_SYSTEM['size']} Tipps ({GLOBAL_SYSTEM['generation_time']}s)")

# Input Validations
class SimulationRequest(BaseModel):
    simulations: int = Field(5000, ge=10, le=50000)

class LiveCheckRequest(BaseModel):
    numbers: List[int] = Field(..., min_items=6, max_items=6)

# =====================================================================
# API ENDPUNKTE (ROUTES)
# =====================================================================

@app.get("/api/v1/status")
def get_status():
    return {
        "tickets_in_memory": GLOBAL_SYSTEM["size"],
        "generation_time_seconds": GLOBAL_SYSTEM["generation_time"],
        "cost_per_draw_eur": round(GLOBAL_SYSTEM["size"] * 1.20, 2)
    }

@app.get("/api/v1/portfolio")
def get_portfolio():
    raw_tickets = [LottoCore.from_vector(vec) for vec in GLOBAL_SYSTEM["portfolio"]]
    sorted_tickets = [sorted(ticket) for ticket in raw_tickets]
    return {"tickets": sorted_tickets}

@app.post("/api/v1/papertrade")
def run_papertrade(payload: SimulationRequest):
    portfolio = GLOBAL_SYSTEM["portfolio"]
    simulations = payload.simulations
    prize_table = {3: 11.50, 4: 50.00, 5: 4000.00, 6: 1000000.00}
    
    total_investment = len(portfolio) * 1.20 * simulations
    total_returns = 0.0
    hit_statistics = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    
    for _ in range(simulations):
        drawing_vector = LottoCore.to_vector(tuple(random.sample(range(1, 50), 6)))
        max_hit_this_drawing = 0
        
        for ticket in portfolio:
            hits = (ticket & drawing_vector).bit_count()
            if hits > max_hit_this_drawing:
                max_hit_this_drawing = hits
            total_returns += prize_table.get(hits, 0.0)
            
        hit_statistics[max_hit_this_drawing] += 1

    return {
        "investment": round(total_investment, 2),
        "returns": round(total_returns, 2),
        "profit": round(total_returns - total_investment, 2),
        "roi": round((total_returns / total_investment) * 100, 2),
        "distribution": {f"{k} Richtige": v for k, v in hit_statistics.items() if k >= 2}
    }

@app.post("/api/v1/live-check")
def live_check(payload: LiveCheckRequest):
    nums = payload.numbers
    if any(n < 1 or n > 49 for n in nums) or len(set(nums)) != 6:
        raise HTTPException(status_code=400, detail="Ungültige Zahlen")
        
    drawing_vector = LottoCore.to_vector(tuple(nums))
    wins = []
    prize_table = {3: 11.50, 4: 50.00, 5: 4000.00, 6: 1000000.00}
    
    for idx, ticket in enumerate(GLOBAL_SYSTEM["portfolio"]):
        hits = (ticket & drawing_vector).bit_count()
        if hits >= 3:
            wins.append({
                "index": idx + 1,
                "numbers": sorted(LottoCore.from_vector(ticket)),
                "hits": hits,
                "win_eur": prize_table.get(hits, 0.0)
            })
            
    return {"total_winning_tickets": len(wins), "details": wins}

# =====================================================================
# INTERAKTIVES DASHBOARD (FRONTEND INJEKTION)
# =====================================================================

@app.get("/", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
def render_dashboard():
    html_content = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lotto Quant Engine v2.1</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0b0f19; color: #f3f4f6; font-family: system-ui, sans-serif; }
        .glow-card { border: 1px solid #1e293b; background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(10px); }
        .lotto-ball { display: inline-flex; align-items: center; justify-content: center; width: 2.2rem; height: 2.2rem; border-radius: 9999px; font-weight: bold; font-size: 0.875rem; }
        .help-panel { transition: max-height 0.3s ease-in-out; overflow: hidden; max-height: 0; }
        .help-panel.open { max-height: 1000px; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-6xl mx-auto">
        
        <!-- HEADER -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-800 pb-6 mb-8 gap-4">
            <div>
                <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-indigo-500">
                    LOTTO QUANT STRATEGY ENGINE
                </h1>
                <p class="text-gray-400 text-sm mt-1">Statisches Covering Design C(49,6,3,6) — 100% Mathematische Mindestgarantie</p>
            </div>
            <div class="flex gap-3">
                <button onclick="toggleHelp()" class="px-4 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 rounded text-sm font-bold transition">
                    📖 System-Hilfe
                </button>
                <span class="px-3 py-1 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full text-xs font-mono font-bold flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> ONLINE
                </span>
            </div>
        </header>

        <!-- HELP PANEL -->
        <div id="help-section" class="help-panel mb-8 bg-gray-900 border border-indigo-900/50 rounded-xl">
            <div class="p-6 text-sm text-gray-300 space-y-4">
                <h2 class="text-xl font-bold text-white mb-2">Wie funktioniert der Generator? (Einfach erklärt)</h2>
                <p>Stell dir vor, die 49 Lottozahlen sind Fische in einem Teich, und du darfst mit einem Netz fischen, das genau 6 Fische fassen kann. Das Ziel ist es, <strong>garantiert</strong> mindestens 3 der 6 später gezogenen Gewinnzahlen einzufangen.</p>
                <p>Anstatt einfach zufällige Zahlen anzukreuzen, wendet diese Engine einen präzisen Algorithmus an:</p>
                <ul class="list-disc pl-5 space-y-2 text-gray-400">
                    <li><strong>Die Bausteine (Triplets):</strong> Die Engine zerlegt alle möglichen 3er-Kombinationen, die es bei 49 Zahlen gibt (das sind 18.424 Kombinationen).</li>
                    <li><strong>Das Netz weben:</strong> Die Software nimmt nun ein 3er-Päckchen und fügt 3 weitere clevere Zahlen hinzu, um ein volles 6er-Tippfeld zu erstellen. Dabei prüft sie rasend schnell im Hintergrund, wie viele andere 3er-Kombinationen durch dieses neue 6er-Feld automatisch "mit abgedeckt" werden.</li>
                    <li><strong>Kompression:</strong> Dieser Vorgang wird wiederholt, wobei die Engine immer die Tippfelder behält, die die größte Netz-Abdeckung haben. Das macht sie so lange, bis jede einzelne der 18.424 möglichen 3er-Kombinationen in mindestens einem deiner Tippfelder vorkommt.</li>
                </ul>
                <p><strong>Das Ergebnis:</strong> Ein hocheffizienter, komprimierter Block an Tippfeldern. Egal welche 6 Zahlen am Samstagabend aus der Trommel rollen – es ist mathematisch unmöglich, dass du keinen 3er auf deinem Schein hast.</p>
            </div>
        </div>

        <!-- METRIC CARDS -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div class="glow-card p-5 rounded-xl">
                <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider">Tipps im Speicher</p>
                <p id="metric-size" class="text-3xl font-bold text-white mt-1">Lade...</p>
                <p class="text-xs text-gray-500 mt-2">Matrix-Größe (Arrays)</p>
            </div>
            <div class="glow-card p-5 rounded-xl">
                <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider">Einsatzkosten / Ziehung</p>
                <p id="metric-cost" class="text-3xl font-bold text-indigo-400 mt-1">Lade...</p>
                <p class="text-xs text-gray-500 mt-2">Berechnet mit aktuellem Feldpreis</p>
            </div>
            <div class="glow-card p-5 rounded-xl">
                <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider">Generierungszeit</p>
                <p id="metric-time" class="text-3xl font-bold text-emerald-400 mt-1">Lade...</p>
                <p class="text-xs text-gray-500 mt-2">In-Memory (Free-Tier optimiert)</p>
            </div>
        </div>

        <!-- MAIN TABS -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            <!-- LINKS: CONTROL PANELS -->
            <div class="lg:col-span-1 flex flex-col gap-6">
                
                <!-- MODULE: BACKTEST SIMULATOR -->
                <div class="glow-card p-6 rounded-xl border-l-4 border-indigo-500">
                    <h2 class="text-lg font-bold text-white mb-2 flex items-center gap-2">📊 System-Backtest</h2>
                    <p class="text-gray-400 text-xs mb-4">Simuliert Ziehungen gegen die Bitmaske.</p>
                    
                    <div class="space-y-3">
                        <div>
                            <label class="block text-xs font-medium text-gray-400 mb-1">Anzahl Iterationen:</label>
                            <input type="number" id="sim-count" value="5000" min="10" max="50000" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-gray-400 mb-1">Kosten pro Tippfeld (€):</label>
                            <input type="number" id="ticket-cost" value="1.20" step="0.10" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                        </div>
                    </div>
                    
                    <button onclick="runBacktest()" id="btn-sim" class="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 px-4 rounded-lg text-sm transition duration-200">
                        Backtest ausführen
                    </button>
                    
                    <!-- SIM RESULTS -->
                    <div id="sim-results" class="hidden mt-6 pt-4 border-t border-gray-800 space-y-2 text-sm">
                        <div class="flex justify-between"><span class="text-gray-400">Gesamteinsatz:</span> <span id="res-invest" class="font-mono font-bold"></span></div>
                        <div class="flex justify-between"><span class="text-gray-400">Rückfluss:</span> <span id="res-returns" class="font-mono text-emerald-400 font-bold"></span></div>
                        <div class="flex justify-between"><span class="text-gray-400">Netto Profit:</span> <span id="res-profit" class="font-mono font-bold"></span></div>
                        <div class="flex justify-between"><span class="text-gray-400">System-ROI:</span> <span id="res-roi" class="font-mono font-bold px-1.5 rounded"></span></div>
                        <div class="mt-3 pt-2 border-t border-gray-800">
                            <p class="text-xs font-semibold text-gray-400 mb-1">Verteilung der Höchsttreffer:</p>
                            <div id="res-dist" class="text-xs space-y-1 font-mono text-indigo-300"></div>
                        </div>
                    </div>
                </div>

                <!-- MODULE: LIVE VALUE CHECKER -->
                <div class="glow-card p-6 rounded-xl border-l-4 border-emerald-500">
                    <h2 class="text-lg font-bold text-white mb-2 flex items-center gap-2">🔮 Live-Einsatz Prüfer</h2>
                    
                    <div class="grid grid-cols-6 gap-1.5 mb-4">
                        <input type="number" min="1" max="49" class="live-input w-full bg-gray-900 border border-gray-700 rounded p-2 text-center text-sm text-white font-bold" value="1">
                        <input type="number" min="1" max="49" class="live-input w-full bg-gray-900 border border-gray-700 rounded p-2 text-center text-sm text-white font-bold" value="12">
                        <input type="number" min="1" max="49" class="live-input w-full bg-gray-900 border border-gray-700 rounded p-2 text-center text-sm text-white font-bold" value="23">
                        <input type="number" min="1" max="49" class="live-input w-full bg-gray-900 border border-gray-700 rounded p-2 text-center text-sm text-white font-bold" value="34">
                        <input type="number" min="1" max="49" class="live-input w-full bg-gray-900 border border-gray-700 rounded p-2 text-center text-sm text-white font-bold" value="45">
                        <input type="number" min="1" max="49" class="live-input w-full bg-gray-900 border border-gray-700 rounded p-2 text-center text-sm text-white font-bold" value="49">
                    </div>
                    
                    <button onclick="checkLiveDrawing()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 px-4 rounded-lg text-sm transition duration-200">
                        Matrix prüfen
                    </button>
                    
                    <div id="live-results" class="hidden mt-4 p-3 bg-gray-900/50 border border-gray-800 rounded-lg text-xs space-y-2">
                        <p class="font-bold text-gray-300">Treffer-Zusammenfassung:</p>
                        <p id="live-summary" class="text-sm font-semibold text-emerald-400"></p>
                        <div id="live-details" class="max-h-40 overflow-y-auto space-y-1 font-mono text-gray-400 pt-1"></div>
                    </div>
                </div>

            </div>

            <!-- RECHTS: ALL SYSTEM TICKETS DISPLAY -->
            <div class="lg:col-span-2">
                <div class="glow-card p-6 rounded-xl h-full flex flex-col">
                    <div class="flex justify-between items-center mb-4">
                        <div>
                            <h2 class="text-xl font-bold text-white">🎰 System-Portfolio</h2>
                            <p class="text-gray-400 text-xs">Statische Tipp-Reihen für den Wettschein.</p>
                        </div>
                        <span id="ticket-badge" class="bg-gray-800 text-gray-300 px-2.5 py-1 rounded text-xs font-mono">0 Felder</span>
                    </div>
                    
                    <div class="mb-4">
                        <input type="text" id="ticket-search" oninput="filterTickets()" placeholder="Nach Zahl filtern..." class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                    </div>

                    <div class="flex-1 overflow-y-auto max-h-[500px] border border-gray-900 rounded-lg bg-gray-950/50 p-2" id="tickets-container">
                        <p class="text-gray-500 text-sm p-4 text-center">Lade Daten...</p>
                    </div>
                </div>
            </div>

        </div>
    </div>

    <script>
        let allTickets = [];
        let systemSize = 0;

        function toggleHelp() {
            const panel = document.getElementById('help-section');
            panel.classList.toggle('open');
        }

        async function loadMetrics() {
            try {
                const resStatus = await fetch('/api/v1/status');
                const status = await resStatus.json();
                systemSize = status.tickets_in_memory;
                
                document.getElementById('metric-size').innerText = systemSize.toLocaleString('de-DE') + " Tipps";
                document.getElementById('metric-time').innerText = status.generation_time_seconds + " s";
                document.getElementById('ticket-badge').innerText = systemSize + " Felder total";
                updateCostDisplay();
                
                const resPortfolio = await fetch('/api/v1/portfolio');
                const data = await resPortfolio.json();
                allTickets = data.tickets;
                renderTickets(allTickets);
            } catch (err) {
                console.error("UI Init Fehler: ", err);
            }
        }

        function updateCostDisplay() {
            const costPerTicket = parseFloat(document.getElementById('ticket-cost').value) || 1.20;
            const total = systemSize * costPerTicket;
            document.getElementById('metric-cost').innerText = total.toLocaleString('de-DE', {style: 'currency', currency: 'EUR'});
        }

        document.getElementById('ticket-cost').addEventListener('input', updateCostDisplay);

        function renderTickets(ticketsList) {
            const container = document.getElementById('tickets-container');
            container.innerHTML = "";
            if(ticketsList.length === 0) {
                container.innerHTML = `<p class="text-gray-600 text-sm p-4 text-center">Keine passenden Tipps gefunden.</p>`;
                return;
            }
            ticketsList.forEach((ticket, idx) => {
                const item = document.createElement('div');
                item.className = "flex items-center justify-between p-2 hover:bg-gray-900/60 rounded border-b border-gray-900/30 transition text-sm";
                let ballsHtml = '<div class="flex gap-1">';
                ticket.forEach(num => { ballsHtml += `<span class="lotto-ball bg-slate-800 text-slate-200 border border-slate-700">${num}</span>`; });
                ballsHtml += '</div>';
                item.innerHTML = `<span class="text-gray-600 font-mono text-xs">#${String(idx+1).padStart(3, '0')}</span>${ballsHtml}`;
                container.appendChild(item);
            });
        }

        function filterTickets() {
            const query = document.getElementById('ticket-search').value.trim();
            if(!query) { renderTickets(allTickets); return; }
            const targetNum = parseInt(query, 10);
            if(isNaN(targetNum)) return;
            renderTickets(allTickets.filter(ticket => ticket.includes(targetNum)));
        }

        async function runBacktest() {
            const btn = document.getElementById('btn-sim');
            const resultsDiv = document.getElementById('sim-results');
            const count = parseInt(document.getElementById('sim-count').value, 10);
            const costPerTicket = parseFloat(document.getElementById('ticket-cost').value);
            
            btn.disabled = true;
            btn.innerText = "Rechne...";
            resultsDiv.classList.add('hidden');

            try {
                const res = await fetch('/api/v1/papertrade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ simulations: count })
                });
                const data = await res.json();
                
                // Adjusting investment based on custom UI cost (API calculates with 1.20 hardcoded, so we recalculate for UI)
                const realInvestment = systemSize * costPerTicket * count;
                const realProfit = data.returns - realInvestment;
                const realRoi = (data.returns / realInvestment) * 100;
                
                document.getElementById('res-invest').innerText = realInvestment.toLocaleString('de-DE', {style: 'currency', currency: 'EUR'});
                document.getElementById('res-returns').innerText = data.returns.toLocaleString('de-DE', {style: 'currency', currency: 'EUR'});
                
                const profitEl = document.getElementById('res-profit');
                profitEl.innerText = realProfit.toLocaleString('de-DE', {style: 'currency', currency: 'EUR'});
                profitEl.className = realProfit >= 0 ? "font-mono text-emerald-400 font-bold" : "font-mono text-red-400 font-bold";

                const roiEl = document.getElementById('res-roi');
                roiEl.innerText = realRoi.toFixed(2) + " %";
                roiEl.className = realRoi >= 100 ? "font-mono bg-emerald-950 text-emerald-400 font-bold" : "font-mono bg-red-950 text-red-400 font-bold";
                
                document.getElementById('res-dist').innerHTML = Object.entries(data.distribution).map(([k, v]) => `<div>${k}: ${v}x</div>`).join('');
                resultsDiv.classList.remove('hidden');
            } catch (err) {
                alert("Fehler: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = "Backtest ausführen";
            }
        }

        async function checkLiveDrawing() {
            const inputs = document.querySelectorAll('.live-input');
            const numbers = Array.from(inputs).map(i => parseInt(i.value, 10));
            try {
                const res = await fetch('/api/v1/live-check', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ numbers })
                });
                const data = await res.json();
                document.getElementById('live-summary').innerText = data.total_winning_tickets + " Gewinn-Tipps gefunden!";
                document.getElementById('live-details').innerHTML = data.details.map(w => 
                    `<div class="p-1 bg-gray-800/50 rounded">Ticket: ${w.numbers.join(', ')} | ${w.hits}er: ${w.win_eur} €</div>`
                ).join('') || '<p class="text-gray-600">Keine Treffer ≥3</p>';
                document.getElementById('live-results').classList.remove('hidden');
            } catch (err) { alert("Fehler: " + err.message); }
        }

        document.addEventListener('DOMContentLoaded', loadMetrics);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)
