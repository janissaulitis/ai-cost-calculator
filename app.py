"""AI Cost Check: what an AI task really costs to run, and what it saves. Run: streamlit run app.py"""
import importlib

import streamlit as st

import costs as C
import kit

C = importlib.reload(C)  # Streamlit Cloud keeps old copies of imported files after an update; always use the latest
kit = importlib.reload(kit)

kit.page("AI Cost Check", "What an AI task really costs to run each month, and what it saves", mark="calculator", icon="💶",
         meta=f"Model prices checked {C.PRICES_CHECKED} · nothing you type is stored", badge="Free · no sign-up", theme="field")



def eur(x):
    if x < 1:
        return f"€{x:.2f}"
    return f"€{x:,.0f}"


def months(x):
    if x == float("inf"):
        return "never at this volume"
    return "under a month" if x < 1 else f"{x:.0f} month{'s' if round(x) != 1 else ''}"


layout = st.container(key="answer_first")  # on phones the answer column moves above the questions
left, right = layout.columns([5, 7], gap="large")

with left.container(border=True):
    st.markdown("#### The task")
    key = st.selectbox("What should the AI do?", list(C.TASKS), format_func=lambda k: C.TASKS[k][0])
    label, unit, vol0, tin0, tout0, min0, tier0, note = C.TASKS[key]
    volume = st.number_input(f"How many {unit}?", 1, 10_000_000, vol0, step=max(1, vol0 // 10), key=f"vol_{key}")
    minutes = st.number_input("Minutes a person spends on one today", 0.0, 600.0, float(min0), 0.5, key=f"min_{key}")
    hourly = st.number_input("Cost of one hour of staff time, €", 5.0, 200.0, 15.0, 1.0,
                             help="Salary plus taxes and overheads. Around €12–20 in the Baltics.")
    automated = st.slider("Share of the work the AI takes over", 0.1, 1.0, 0.6, 0.05,
                          help="Rarely 100%: some cases still go to a person.")
    review = st.number_input("Minutes a person spends checking each AI result", 0.0, 60.0,
                             round(min0 * 0.15, 1), 0.1, key=f"rev_{key}",
                             help="Usually the biggest running cost. Drops as trust grows and checks become spot checks.")
    with st.expander("Setup, tools and token sizes"):
        setup = st.number_input("One-off setup cost, €", 0.0, 200_000.0, 3000.0, 250.0,
                                help="Building, connecting to your systems and testing. A few weeks of work.")
        platform = st.number_input("Hosting and tools a month, €", 0.0, 10_000.0, 30.0, 5.0)
        tier = st.radio("Model needed", list(C.TIERS), index=list(C.TIERS).index(tier0), format_func=C.TIERS.get,
                        horizontal=True, key=f"tier_{key}",
                        help="Sorting and short replies work on fast models; reading long documents needs a stronger one.")
        a, b = st.columns(2)
        tin = a.number_input("Tokens in, per item", 10, 2_000_000, tin0, 50, key=f"tin_{key}")
        tout = b.number_input("Tokens out, per item", 1, 200_000, tout0, 50, key=f"tout_{key}")
        fx = st.number_input("Euros per US dollar", 0.5, 1.5, C.USD_TO_EUR, 0.01)
        st.caption(f"{note} One token is about ¾ of an English word; Latvian uses more.")

r = C.compare(volume, tin, tout, minutes, hourly, automated, tier, fx, review, platform, setup)


def knob(label, value, lo, hi, text):
    import math
    f = 0 if hi == lo else max(0.0, min(1.0, (value - lo) / (hi - lo)))
    ang = math.radians(-135 + 270 * f)
    x, y = 32 + 20 * math.sin(ang), 32 - 20 * math.cos(ang)
    return (f'<div class="k-knob"><svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="27" fill="var(--k-surface)" stroke="var(--k-ink)" stroke-width="2.5"/>'
            f'<circle cx="32" cy="32" r="21" fill="none" stroke="var(--k-line)" stroke-width="1.5" stroke-dasharray="2 4"/>'
            f'<line x1="32" y1="32" x2="{x:.1f}" y2="{y:.1f}" stroke="var(--k-go)" stroke-width="4" stroke-linecap="round"/></svg>'
            f'<span>{label}</span><b>{text}</b></div>')

pick = r["pick"]

with right:
    tiles = [("Time freed", f"{r['saved_hours']:,.0f} h"), ("Checking", eur(r["review"])),
             ("AI bill", eur(pick["cost"])), ("Tools", eur(r["platform"]))]
    if r["net"] > 0:
        kit.answer("Worth doing · you save", f"{eur(r['net'])} / mo",
                   f"Setup pays back in <b>{months(r['payback'])}</b>. The AI itself costs <b>{eur(pick['cost'])} a month</b> "
                   f"on {pick['model']}"
                   + (", under 1% of what it costs to run." if r["ai_share"] < 0.01
                      else f", {r['ai_share']:.0%} of what it costs to run.")
                   + (" Most of the cost is people checking its work." if r["review"] > r["platform"] + pick["cost"] else ""),
                   tiles)
    else:
        kit.answer("Not worth it yet · it costs", f"−{eur(-r['net'])} / mo",
                   "At this volume, checking the AI's work and running the tools cost more than the time it frees. "
                   "It starts to pay with more volume, less checking per item, or a task that takes longer by hand.",
                   tiles, tone="warn")

    st.markdown('<div class="k-knobs">' + knob(unit.split(" ")[0] + " / mo", volume, 0, max(5000, vol0 * 2), f"{volume:,}")
            + knob("min each", minutes, 0, 30, f"{minutes:g}") + knob("€ / hour", hourly, 5, 60, f"{hourly:g}")
            + knob("AI share", automated, 0, 1, f"{automated:.2f}") + knob("check min", review, 0, 5, f"{review:g}")
            + "</div>", unsafe_allow_html=True)
    st.markdown(f"#### The same {volume:,} {unit} on every model")
    kit.bars([{"label": x["model"], "value": x["cost"], "text": eur(x["cost"]), "pick": x is pick,
               "dim": not x["suited"], "note": None if x["suited"] else "may be too weak"} for x in r["rows"]])
    dearest = max(x["cost"] for x in r["rows"] if x["suited"])
    st.caption(f"A month on the dearest suitable model is {eur(dearest)}, against {eur(r['saved'])} of staff time freed. "
               "Picking the model matters less than how much checking the work needs.")

    with st.expander("Prices and where they come from"):
        st.markdown(f"Standard published rates per million tokens, checked **{C.PRICES_CHECKED}**, without batch or "
                    "cache discounts (both cut costs further).")
        kit.table([{"m": n, "p": p, "i": f"${pi:.2f}", "o": f"${po:.2f}", "n": nt or "—"} for n, p, t, pi, po, nt, s in C.MODELS],
                  [kit.col("Model", "m", "strong"), kit.col("Provider", "p", "chip", {"Anthropic": "warn", "Google": "info", "OpenAI": ""}),
                   kit.col("In, per 1M tokens", "i", "num"), kit.col("Out, per 1M tokens", "o", "num"), kit.col("Note", "n", "muted")])
        st.markdown(" · ".join(f"[{p} prices]({s})" for p, s in
                               dict((p, s) for n, p, t, pi, po, nt, s in C.MODELS).items()))

kit.footer("costs.py · prices checked " + C.PRICES_CHECKED)
