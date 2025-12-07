from flask import Flask, render_template_string, jsonify, request
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from lumina.hardware.lamp import LampController
from lumina.utils.config import load_config

app = Flask(__name__)
lamp = LampController(load_config())
lamp.start_automation()

HTML = """<!DOCTYPE html>
<html><head><title>Lumina</title>
<style>body{font-family:sans-serif;max-width:600px;margin:50px auto;padding:20px}
.btn{padding:15px 30px;margin:10px;font-size:16px;cursor:pointer;border:none;border-radius:5px}
.on{background:#4CAF50;color:white}.off{background:#f44336;color:white}
.color{background:#2196F3;color:white}.mode{background:#FF9800;color:white}
input[type=range]{width:100%}
.status{background:#f0f0f0;padding:15px;border-radius:5px;margin:20px 0}
.color-btn{width:50px;height:50px;border-radius:50%;margin:5px;border:2px solid #ddd;cursor:pointer;display:inline-block}
</style></head><body>
<h1>🏮 Lumina Control</h1>
<div class="status" id="status">Loading...</div>
<button class="btn on" onclick="power()">Power</button>
<button class="btn mode" onclick="mode()">Mode</button>
<button class="btn color" onclick="cycle()">Next Color</button>
<h3>Brightness: <span id="bright">50</span>%</h3>
<input type="range" min="0" max="100" value="50" oninput="brightness(this.value)">
<h3>Colors</h3>
<div id="colors"></div>
<script>
const colors = [[255,0,0],[0,255,0],[0,0,255],[255,255,0],[255,0,255],[0,255,255],[255,255,255]];
colors.forEach(c => {
    const div = document.createElement('div');
    div.className = 'color-btn';
    div.style.background = `rgb(${c[0]},${c[1]},${c[2]})`;
    div.onclick = () => setColor(c[0],c[1],c[2]);
    document.getElementById('colors').appendChild(div);
});
async function power(){await fetch('/power');update();}
async function mode(){await fetch('/mode');update();}
async function cycle(){await fetch('/cycle');update();}
async function brightness(v){document.getElementById('bright').innerText=v;await fetch('/brightness/'+v);update();}
async function setColor(r,g,b){await fetch(`/color/${r}/${g}/${b}`);update();}
async function update(){
    const r = await fetch('/status');
    const s = await r.json();
    const l = s.lamp;
    document.getElementById('status').innerHTML = 
        `Power: ${l.is_on?'ON':'OFF'} | Mode: ${l.mode} | Color: RGB(${l.current_color}) | Brightness: ${l.current_brightness}%`;
    document.getElementById('bright').innerText = l.current_brightness;
}
setInterval(update, 2000);
update();
</script></body></html>"""

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/status')
def status(): return jsonify(lamp.get_status())

@app.route('/power')
def power(): lamp._on_power(); return 'ok'

@app.route('/mode')
def mode(): lamp._on_mode(); return 'ok'

@app.route('/cycle')
def cycle(): lamp.cycle_color(); return 'ok'

@app.route('/brightness/<int:value>')
def brightness(value): lamp.set_brightness(value); return 'ok'

@app.route('/color/<int:r>/<int:g>/<int:b>')
def color(r,g,b): lamp.set_color(r,g,b); return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
