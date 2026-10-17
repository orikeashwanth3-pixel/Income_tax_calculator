from flask import Flask, request, redirect, session, url_for, render_template_string, flash
import sqlite3, os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key-before-deployment')
DATABASE = os.environ.get('DATABASE_PATH', 'tax.db')

TEXT = {
 'English': {'title':'Income Tax & Expenditure Manager','login':'Login','register':'Create account','username':'Username','password':'Password','new_password':'New password','confirm':'Confirm password','reset':'Reset password','forgot':'Forgot password?','logout':'Logout','income':'Annual income (₹)','name':'Name','calculate':'Calculate tax','result':'Tax calculation explanation','tax_before':'Tax before cess','cess':'Health & Education cess (4%)','total_tax':'Total tax including cess','monthly':'Monthly income after tax','slabs':'Tax slabs','dashboard':'Dashboard','expenses':'Monthly expenditure','year':'Year','month':'Month','rent':'House rent','electricity':'Electricity','medical':'Medical / hospital','travel':'Travel','food':'Food','shopping':'Shopping','education':'Education','mobile':'Mobile / internet','entertainment':'Entertainment','others':'Others','save_expense':'Save expenditure','saved':'Saved successfully.','graph':'Expenditure breakdown','records':'Saved tax calculations','delete':'Delete','error':'Something went wrong. Check your details.','reset_note':'Demo password reset: enter your username and set a new password. For a public website, use verified email/OTP recovery.'},
 'Telugu': {'title':'ఆదాయపు పన్ను & ఖర్చుల నిర్వహణ','login':'లాగిన్','register':'ఖాతా సృష్టించండి','username':'యూజర్ పేరు','password':'పాస్‌వర్డ్','new_password':'కొత్త పాస్‌వర్డ్','confirm':'పాస్‌వర్డ్ నిర్ధారించండి','reset':'పాస్‌వర్డ్ మార్చండి','forgot':'పాస్‌వర్డ్ మర్చిపోయారా?','logout':'లాగ్ అవుట్','income':'వార్షిక ఆదాయం (₹)','name':'పేరు','calculate':'పన్ను లెక్కించండి','result':'పన్ను లెక్కింపు వివరాలు','tax_before':'సెస్‌కు ముందు పన్ను','cess':'హెల్త్ & ఎడ్యుకేషన్ సెస్ (4%)','total_tax':'సెస్‌తో కలిపి మొత్తం పన్ను','monthly':'పన్ను తర్వాత నెలవారీ ఆదాయం','slabs':'పన్ను స్లాబులు','dashboard':'డ్యాష్‌బోర్డ్','expenses':'నెలవారీ ఖర్చులు','year':'సంవత్సరం','month':'నెల','rent':'ఇంటి అద్దె','electricity':'విద్యుత్','medical':'వైద్యం / ఆసుపత్రి','travel':'ప్రయాణం','food':'ఆహారం','shopping':'షాపింగ్','education':'విద్య','mobile':'మొబైల్ / ఇంటర్నెట్','entertainment':'వినోదం','others':'ఇతర ఖర్చులు','save_expense':'ఖర్చులను సేవ్ చేయండి','saved':'విజయవంతంగా సేవ్ అయ్యాయి.','graph':'ఖర్చుల గ్రాఫ్','records':'సేవ్ చేసిన పన్ను వివరాలు','delete':'తొలగించు','error':'వివరాలు సరిచూసి మళ్లీ ప్రయత్నించండి.','reset_note':'డెమో పాస్‌వర్డ్ రీసెట్: యూజర్ పేరు ఇచ్చి కొత్త పాస్‌వర్డ్ పెట్టండి. పబ్లిక్ వెబ్‌సైట్‌లో ఇమెయిల్/OTP ధృవీకరణ అవసరం.'},
 'Hindi': {'title':'आयकर और खर्च प्रबंधक','login':'लॉगिन','register':'खाता बनाएं','username':'यूज़रनेम','password':'पासवर्ड','new_password':'नया पासवर्ड','confirm':'पासवर्ड की पुष्टि करें','reset':'पासवर्ड रीसेट करें','forgot':'पासवर्ड भूल गए?','logout':'लॉगआउट','income':'वार्षिक आय (₹)','name':'नाम','calculate':'टैक्स की गणना करें','result':'टैक्स गणना विवरण','tax_before':'सेस से पहले टैक्स','cess':'स्वास्थ्य और शिक्षा सेस (4%)','total_tax':'सेस सहित कुल टैक्स','monthly':'टैक्स के बाद मासिक आय','slabs':'टैक्स स्लैब','dashboard':'डैशबोर्ड','expenses':'मासिक खर्च','year':'वर्ष','month':'महीना','rent':'घर का किराया','electricity':'बिजली','medical':'चिकित्सा / अस्पताल','travel':'यात्रा','food':'भोजन','shopping':'खरीदारी','education':'शिक्षा','mobile':'मोबाइल / इंटरनेट','entertainment':'मनोरंजन','others':'अन्य','save_expense':'खर्च सेव करें','saved':'सफलतापूर्वक सेव हुआ।','graph':'खर्च का ग्राफ','records':'सेव किए गए टैक्स रिकॉर्ड','delete':'हटाएं','error':'विवरण जांचकर फिर कोशिश करें।','reset_note':'डेमो पासवर्ड रीसेट: यूज़रनेम देकर नया पासवर्ड सेट करें। सार्वजनिक वेबसाइट पर सत्यापित ईमेल/OTP का उपयोग करें.'}
}
EXPENSE_FIELDS = ['rent','electricity','medical','travel','food','shopping','education','mobile','entertainment','others']
SLABS = [('Up to ₹4,00,000',0),('₹4,00,001–₹8,00,000',5),('₹8,00,001–₹12,00,000',10),('₹12,00,001–₹16,00,000',15),('₹16,00,001–₹20,00,000',20),('₹20,00,001–₹24,00,000',25),('Above ₹24,00,000',30)]

def db():
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)')
        con.execute('CREATE TABLE IF NOT EXISTS tax_records (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, income TEXT NOT NULL, tax TEXT NOT NULL, tax_before TEXT NOT NULL, cess TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        con.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, year INTEGER NOT NULL, month TEXT NOT NULL, income REAL DEFAULT 0, rent REAL DEFAULT 0, electricity REAL DEFAULT 0, medical REAL DEFAULT 0, travel REAL DEFAULT 0, food REAL DEFAULT 0, shopping REAL DEFAULT 0, education REAL DEFAULT 0, mobile REAL DEFAULT 0, entertainment REAL DEFAULT 0, others REAL DEFAULT 0, UNIQUE(user_id, year, month))''')

def current_user():
    if 'user_id' not in session: return None
    with db() as con: return con.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()

def tax_breakdown(value):
    income = Decimal(str(value))
    if income < 0: raise ValueError('negative income')
    if income <= Decimal('400000'): tax = Decimal('0')
    elif income <= Decimal('800000'): tax = (income-Decimal('400000'))*Decimal('0.05')
    elif income <= Decimal('1200000'): tax = Decimal('20000')+(income-Decimal('800000'))*Decimal('0.10')
    elif income <= Decimal('1600000'): tax = Decimal('60000')+(income-Decimal('1200000'))*Decimal('0.15')
    elif income <= Decimal('2000000'): tax = Decimal('120000')+(income-Decimal('1600000'))*Decimal('0.20')
    elif income <= Decimal('2400000'): tax = Decimal('200000')+(income-Decimal('2000000'))*Decimal('0.25')
    else: tax = Decimal('300000')+(income-Decimal('2400000'))*Decimal('0.30')
    tax = tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    cess = (tax*Decimal('0.04')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return tax, cess, tax+cess

BASE = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ t.title }}</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:linear-gradient(135deg,#edf4ff,#f8faff);color:#172033}.top{background:#172554;color:white;padding:18px 5%;display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}.top h1{font-size:22px;margin:0}.top a{color:white;text-decoration:none;margin-left:12px}.wrap{max-width:1000px;margin:24px auto;padding:0 14px}.card{background:white;padding:22px;border-radius:16px;box-shadow:0 8px 26px #17255412;margin-bottom:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}.field{display:flex;flex-direction:column;gap:7px;margin:12px 0}input,select{padding:12px;border:1px solid #cbd5e1;border-radius:9px;font-size:15px;width:100%}button,.btn{border:0;background:#2563eb;color:white;padding:12px 17px;border-radius:9px;cursor:pointer;text-decoration:none;display:inline-block;font-size:15px}button:hover,.btn:hover{background:#1d4ed8}.muted{color:#64748b;font-size:13px}.alert{background:#fff1f2;color:#9f1239;padding:12px;border-radius:9px;margin-bottom:12px}.metric{background:#eff6ff;border-radius:12px;padding:15px}.metric strong{font-size:22px;display:block;margin-top:8px}.table{width:100%;border-collapse:collapse}.table th,.table td{padding:10px;border-bottom:1px solid #e2e8f0;text-align:left}.table-wrap{overflow:auto}.positive{color:#047857;font-weight:bold}.expense-grid{display:grid;grid-template-columns:1fr;gap:0}.actions{display:flex;gap:10px;flex-wrap:wrap}.danger{background:#dc2626}canvas{max-height:340px}footer{text-align:center;color:#64748b;padding:18px}@media(max-width:600px){.card{padding:16px}.top h1{font-size:18px}}
</style></head><body><header class="top"><h1>{{ t.title }}</h1><div>{% if user %}<a href="{{ url_for('home') }}">Income</a><a href="{{ url_for('expenditure') }}">Expenditure</a><a href="{{ url_for('logout') }}">{{ t.logout }}</a>{% endif %}<form style="display:inline-block;margin-left:10px" method="get"><select name="lang" onchange="this.form.submit()" aria-label="Language"><option {% if lang=='English' %}selected{% endif %}>English</option><option {% if lang=='Telugu' %}selected{% endif %}>Telugu</option><option {% if lang=='Hindi' %}selected{% endif %}>Hindi</option></select></form></div></header><main class="wrap">{% with messages=get_flashed_messages() %}{% for message in messages %}<div class="alert">{{ message }}</div>{% endfor %}{% endwith %}{{ content|safe }}</main><footer>Final Year CSE Project · Verify tax rules with an official tax professional before filing.</footer></body></html>'''

def page(content):
    lang = request.args.get('lang') or session.get('lang','English')
    if lang not in TEXT: lang='English'
    session['lang']=lang
    return render_template_string(BASE, t=TEXT[lang], lang=lang, user=current_user(), content=content)

def money(x): return '₹' + format(float(x), ',.2f')

@app.route('/register', methods=['GET','POST'])
def register():
    t=TEXT.get(session.get('lang','English'),TEXT['English'])
    if request.method=='POST':
        username=request.form.get('username','').strip()
        password=request.form.get('password','')
        if len(username)<3 or len(password)<6: flash('Username must be 3+ characters and password 6+ characters.')
        else:
            try:
                with db() as con: con.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',(username,generate_password_hash(password)))
                flash('Account created. Please log in.'); return redirect(url_for('login',lang=session.get('lang','English')))
            except sqlite3.IntegrityError: flash('Username already exists.')
    c=f'''<section class="card"><h2>{t['register']}</h2><form method="post"><label class="field">{t['username']}<input name="username" required minlength="3"></label><label class="field">{t['password']}<input type="password" name="password" required minlength="6"></label><button>{t['register']}</button></form><p><a href="{url_for('login')}">{t['login']}</a></p></section>'''
    return page(c)

@app.route('/login', methods=['GET','POST'])
def login():
    t=TEXT.get(session.get('lang','English'),TEXT['English'])
    if request.method=='POST':
        with db() as con: user=con.execute('SELECT * FROM users WHERE username=?',(request.form.get('username','').strip(),)).fetchone()
        if user and check_password_hash(user['password_hash'],request.form.get('password','')):
            session['user_id']=user['id']; return redirect(url_for('home',lang=session.get('lang','English')))
        flash(t['error'])
    c=f'''<section class="card" style="max-width:520px;margin:auto"><h2>{t['login']}</h2><form method="post"><label class="field">{t['username']}<input name="username" required></label><label class="field">{t['password']}<input type="password" name="password" required></label><button>{t['login']}</button></form><p><a href="{url_for('register')}">{t['register']}</a> · <a href="{url_for('reset_password')}">{t['forgot']}</a></p></section>'''
    return page(c)

@app.route('/reset-password', methods=['GET','POST'])
def reset_password():
    t=TEXT.get(session.get('lang','English'),TEXT['English'])
    if request.method=='POST':
        username=request.form.get('username','').strip(); new=request.form.get('new_password',''); confirm=request.form.get('confirm','')
        if len(new)<6 or new!=confirm: flash('Passwords must match and contain at least 6 characters.')
        else:
            with db() as con: cur=con.execute('UPDATE users SET password_hash=? WHERE username=?',(generate_password_hash(new),username))
            flash('Password updated. Please log in.' if cur.rowcount else 'Username not found.')
            if cur.rowcount: return redirect(url_for('login',lang=session.get('lang','English')))
    c=f'''<section class="card" style="max-width:560px;margin:auto"><h2>{t['reset']}</h2><p class="muted">{t['reset_note']}</p><form method="post"><label class="field">{t['username']}<input name="username" required></label><label class="field">{t['new_password']}<input type="password" name="new_password" minlength="6" required></label><label class="field">{t['confirm']}<input type="password" name="confirm" minlength="6" required></label><button>{t['reset']}</button></form><p><a href="{url_for('login')}">{t['login']}</a></p></section>'''
    return page(c)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/', methods=['GET','POST'])
def home():
    user=current_user()
    if not user: return redirect(url_for('login',lang=request.args.get('lang','English')))
    t=TEXT.get(session.get('lang','English'),TEXT['English']); result=''
    if request.method=='POST' and request.form.get('form_type')=='tax':
        try:
            income=Decimal(request.form.get('income',''))
            if income<0: raise ValueError()
            before,cess,total=tax_breakdown(income)
            result=f'''<section class="card"><h2>{t['result']}</h2><div class="grid"><div class="metric">{t['income']}<strong>{money(income)}</strong></div><div class="metric">{t['tax_before']}<strong>{money(before)}</strong></div><div class="metric">{t['cess']}<strong>{money(cess)}</strong></div><div class="metric">{t['total_tax']}<strong>{money(total)}</strong></div><div class="metric">{t['monthly']}<strong>{money((income-total)/Decimal(12))}</strong></div></div><p class="muted">Calculation: slab tax = {money(before)}; cess = {money(before)} × 4% = {money(cess)}; total = {money(total)}. Section 87A rebate is not applied.</p></section>'''
        except (ValueError,InvalidOperation): flash(t['error'])
    slabrows=''.join(f'<tr><td>{label}</td><td>{rate}%</td></tr>' for label,rate in SLABS)
    c=f'''<section class="card"><h2>{t['dashboard']}</h2><form method="post"><input type="hidden" name="form_type" value="tax"><label class="field">{t['income']}<input name="income" type="number" min="0" step="0.01" required placeholder="Enter annual income"></label><button>{t['calculate']}</button></form></section>{result}{('<section class="card"><h2>'+t['slabs']+' · New tax regime (illustrative)</h2><div class="table-wrap"><table class="table"><tr><th>Annual taxable income range</th><th>Rate</th></tr>'+slabrows+'</table></div><p class="muted">Configured illustrative slabs; Section 87A rebate is not applied. Verify current official rules before filing.</p></section>') if result else ''}'''
    return page(c)

@app.route('/expenditure')
def expenditure():
    user=current_user()
    if not user: return redirect(url_for('login',lang=request.args.get('lang','English')))
    t=TEXT.get(session.get('lang','English'),TEXT['English'])
    return page(expense_html(user['id'],t))

@app.route('/delete-tax/<int:rid>',methods=['POST'])
def delete_tax(rid):
    user=current_user()
    if not user: return redirect(url_for('login'))
    with db() as con: con.execute('DELETE FROM tax_records WHERE id=? AND user_id=?',(rid,user['id']))
    return redirect(url_for('home',lang=session.get('lang','English')))

@app.route('/save-expense',methods=['POST'])
def save_expense():
    user=current_user()
    if not user: return redirect(url_for('login'))
    try:
        year=int(request.form.get('year','2026')); month=request.form.get('month','January')
        income=float(request.form.get('expense_income') or 0)
        vals=[]
        for f in EXPENSE_FIELDS:
            v=float(request.form.get(f) or 0)
            if v<0: raise ValueError()
            vals.append(v)
        if income<0: raise ValueError()
        columns=', '.join(['user_id','year','month','income']+EXPENSE_FIELDS)
        placeholders=', '.join(['?']*(4+len(EXPENSE_FIELDS)))
        updates=', '.join([f'{f}=excluded.{f}' for f in ['income']+EXPENSE_FIELDS])
        with db() as con: con.execute(f'INSERT INTO expenses ({columns}) VALUES ({placeholders}) ON CONFLICT(user_id,year,month) DO UPDATE SET {updates}',[user['id'],year,month,income]+vals)
        flash(TEXT.get(session.get('lang','English'),TEXT['English'])['saved'])
    except (ValueError,sqlite3.Error): flash(TEXT.get(session.get('lang','English'),TEXT['English'])['error'])
    return redirect(url_for('expenditure',lang=session.get('lang','English'))+'#expenses')

def expense_html(uid,t):
    with db() as con:
        rows=con.execute("SELECT * FROM expenses WHERE user_id=? ORDER BY year DESC, CASE month WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 END DESC LIMIT 24",(uid,)).fetchall()
    labels=[t[f] for f in EXPENSE_FIELDS]
    inputs=''.join(f'<label class="field">{t[f]} (₹)<input name="{f}" type="number" min="0" step="0.01" placeholder="Enter amount"></label>' for f in EXPENSE_FIELDS)
    options=''.join(f'<option>{m}</option>' for m in ['January','February','March','April','May','June','July','August','September','October','November','December'])
    def row_total(r): return sum(float(r[f] or 0) for f in EXPENSE_FIELDS)
    latest=rows[0] if rows else None
    previous=rows[1] if len(rows)>1 else None
    data=[float(latest[f] or 0) for f in EXPENSE_FIELDS] if latest else [0]*len(EXPENSE_FIELDS)
    total=sum(data); income=float(latest['income'] or 0) if latest else 0
    prev_total=row_total(previous) if previous else 0
    records=[]
    for r in rows:
        for f in EXPENSE_FIELDS:
            amount=float(r[f] or 0)
            if amount>0: records.append(f'<tr><td>{r["month"]} {r["year"]}</td><td>{t[f]}</td><td>{money(amount)}</td></tr>')
    record_table=''.join(records) or '<tr><td colspan="3">No saved expense items yet. Add expenses below.</td></tr>'
    history=''.join(f'<tr><td>{r["month"]} {r["year"]}</td><td>{money(row_total(r))}</td><td>{money(r["income"] or 0)}</td><td>{money(float(r["income"] or 0)-row_total(r))}</td></tr>' for r in rows) or '<tr><td colspan="4">No saved records yet</td></tr>'
    if latest:
        pct=(total/income*100) if income>0 else 0
        comparison=f'<div class="grid"><div class="metric">Latest month expenditure<strong>{money(total)}</strong></div><div class="metric">Income<strong>{money(income)}</strong></div><div class="metric">Income remaining<strong>{money(income-total)}</strong></div><div class="metric">Expenditure / income<strong>{pct:.1f}%</strong></div></div>'
        if previous:
            diff=total-prev_total
            comparison+=f'<p>Compared with previous saved record ({previous["month"]} {previous["year"]}): expenditure {"increased by" if diff>0 else "decreased by" if diff<0 else "is unchanged at"} <b>{money(abs(diff))}</b>.</p>'
        nonzero=sorted([(t[f],float(latest[f] or 0)) for f in EXPENSE_FIELDS if float(latest[f] or 0)>0],key=lambda x:x[1],reverse=True)
        suggestions=[]
        if income>0 and total>income: suggestions.append('Your expenses exceed income. Review optional spending and set a monthly limit.')
        elif income>0 and pct>=70: suggestions.append('Expenses use at least 70% of income. Try setting aside a savings amount first.')
        if nonzero: suggestions.append(f'Your highest expense is {nonzero[0][0]} ({money(nonzero[0][1])}). Compare prices or set a category budget.')
        if not suggestions: suggestions.append('Save a few months of records to get more useful comparisons and suggestions.')
        suggestions_html=''.join(f'<li>{x}</li>' for x in suggestions)
    else:
        comparison='<p class="muted">Save your first month of expenditure to see income comparison and suggestions.</p>'; suggestions_html='<li>Enter real amounts, then save the record to get suggestions.</li>'
    return f'''<section class="card"><h2>Previously saved expenditure records</h2><div class="table-wrap"><table class="table"><tr><th>Month / Year</th><th>Expense item</th><th>Amount</th></tr>{record_table}</table></div></section><section class="card" id="expenses"><h2>{t['expenses']}</h2><p class="muted">Leave any field blank if you did not spend money in that category. Saving the same month/year updates that record.</p><form method="post" action="{url_for('save_expense')}"><div class="grid"><label class="field">{t['year']}<input name="year" type="number" min="2000" max="2100" value="{__import__('datetime').date.today().year}" required></label><label class="field">{t['month']}<select name="month">{options}</select></label><label class="field">{t['income']}<input name="expense_income" type="number" min="0" step="0.01" placeholder="Enter monthly income"></label></div><h3>Enter each bill or expense</h3><div class="expense-grid">{inputs}</div><button>{t['save_expense']}</button></form></section><section class="card"><h2>Income and expenditure comparison</h2>{comparison}</section><section class="card"><h2>Saving suggestions</h2><ul>{suggestions_html}</ul></section><section class="card"><h2>Expenditure history</h2><div class="table-wrap"><table class="table"><tr><th>Month / Year</th><th>Total expenditure</th><th>Income</th><th>Income after expenses</th></tr>{history}</table></div></section><section class="card"><h2>{t['graph']} — bar graph</h2><canvas id="expenseChart"></canvas><p class="muted">Each bar shows spending by category for the latest saved month.</p></section><script>new Chart(document.getElementById('expenseChart'),{{type:'bar',data:{{labels:{labels!r},datasets:[{{label:'Expense amount (₹)',data:{data!r},borderWidth:1}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}},title:{{display:true,text:'Monthly expenditure by category'}}}},scales:{{y:{{beginAtZero:true}}}}}}}});</script>'''

@app.route('/health')
def health(): return {'status':'ok'}

init_db()
if __name__=='__main__':
    port=int(os.environ.get('PORT','5000'))
    app.run(host='0.0.0.0',port=port,debug=False)
