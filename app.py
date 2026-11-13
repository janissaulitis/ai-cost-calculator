"""AI Cost Check: what an AI task really costs to run, and what it saves. Run: streamlit run app.py"""
import importlib

import streamlit as st

import costs as C
import kit

C = importlib.reload(C)  # Streamlit Cloud keeps old copies of imported files after an update; always use the latest
kit = importlib.reload(kit)

kit.page("AI Cost Check", "What an AI task really costs to run each month, and what it saves", mark="💶",
         meta=f"Model prices checked {C.PRICES_CHECKED} · nothing you type is stored", badge="Free · no sign-up")

st.markdown("""<style>
.bars { display: grid; gap: 7px; margin: 4px 0 8px; }
.bar { display: grid; grid-template-columns: minmax(130px, 34%) 1fr 84px; align-items: center; gap: 10px; font-size: 14px; }
.bar span { color: var(--k-ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar span small { color: var(--k-muted); }
.bar div { height: 12px; background: var(--k-line); border-radius: 6px; overflow: hidden; }
.bar i { display: block; height: 100%; min-width: 3px; background: var(--k-go); border-radius: 6px; }
.bar b { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; color: var(--k-ink); }
.bar.weak span, .bar.weak b { color: var(--k-muted); font-weight: 400; }
.bar.weak i { background: var(--k-muted); opacity: .45; }
.bar.pick span { font-weight: 600; }
</style>""", unsafe_allow_html=True)


def eur(x):
    if x < 1:
        return f"€{x:.2f}"
    return f"€{x:,.0f}"


def months(x):
    if x == float("inf"):
        return "never at this volume"
    return "under a month" if x < 1 else f"{x:.0f} month{'s' if round(x) != 1 else ''}"


left, right = st.columns([5, 7], gap="large")

with left:
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
pick = r["pick"]

with right:
    with st.container(border=True):
        if r["net"] > 0:
            st.markdown(f"### Saves about {eur(r['net'])} a month after every cost")
            st.markdown(f"Setup pays back in **{months(r['payback'])}**. The AI itself costs "
                        f"**{eur(pick['cost'])} a month** on {pick['model']}"
                        + (f", under 1% of what it costs to run." if r["ai_share"] < 0.01
                           else f", {r['ai_share']:.0%} of what it costs to run.")
                        + (" Most of the cost is people checking its work." if r["review"] > r["platform"] + pick["cost"]
                           else ""))
        else:
            st.markdown(f"### Costs {eur(-r['net'])} a month more than it saves")
            st.markdown("At this volume, checking the AI's work and running the tools cost more than the time it frees. "
                        "It starts to pay with more volume, less checking per item, or a task that takes longer by hand.")
        m = st.columns(4)
        m[0].metric("Time freed", f"{r['saved_hours']:,.0f} h", help=f"Worth {eur(r['saved'])} a month")
        m[1].metric("Checking", eur(r["review"]), help="Staff time spent reviewing AI results, in €")
        m[2].metric("AI bill", eur(pick["cost"]), help=f"{pick['model']}, {eur(pick['per_item'] * 1000)} per 1,000 items")
        m[3].metric("Tools", eur(r["platform"]))

    st.markdown(f"#### The same {volume:,} {unit} on every model")
    top = max(x["cost"] for x in r["rows"]) or 1
    st.markdown("<div class='bars'>" + "".join(
        f"<div class='bar{' pick' if x is pick else ''}{'' if x['suited'] else ' weak'}'>"
        f"<span>{x['model']}{' <small>· may be too weak</small>' if not x['suited'] else ''}</span>"
        f"<div><i style='width:{x['cost'] / top * 100:.1f}%'></i></div><b>{eur(x['cost'])}</b></div>"
        for x in r["rows"]) + "</div>", unsafe_allow_html=True)
    dearest = max(x["cost"] for x in r["rows"] if x["suited"])
    st.caption(f"A month on the dearest suitable model is {eur(dearest)}, against {eur(r['saved'])} of staff time freed. "
               "Picking the model matters less than how much checking the work needs.")

    with st.expander("Prices and where they come from"):
        st.markdown(f"Standard published rates per million tokens, checked **{C.PRICES_CHECKED}**, without batch or "
                    "cache discounts (both cut costs further).")
        st.dataframe([{"Model": n, "Provider": p, "In, $/1M": pi, "Out, $/1M": po, "Note": nt}
                      for n, p, t, pi, po, nt, s in C.MODELS], hide_index=True, width="stretch")
        st.markdown(" · ".join(f"[{p} prices]({s})" for p, s in
                               dict((p, s) for n, p, t, pi, po, nt, s in C.MODELS).items()))

kit.footer("costs.py · prices checked " + C.PRICES_CHECKED)
