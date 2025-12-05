# app.py
import streamlit as st
from datetime import datetime
import json

st.set_page_config(page_title="CED: Managed Services Pricign Calcualtor", layout="wide")

# ---------- PRICING DATA (from the PDF) ----------
PRICING_DATA = {
  "oneTime": {
    "Standard Listings (Product Uploads)": {
      "Amazon":[ {"min":1,"max":100,"price":5}, {"min":101,"max":500,"price":3}, {"min":501,"max":float("inf"),"price":3} ],
      "TikTok":[ {"min":1,"max":100,"price":4}, {"min":101,"max":500,"price":2.5}, {"min":501,"max":float("inf"),"price":2} ],
      "eBay":[ {"min":1,"max":100,"price":4}, {"min":101,"max":500,"price":2.5}, {"min":501,"max":float("inf"),"price":2} ],
      "Walmart":[ {"min":1,"max":100,"price":5}, {"min":101,"max":500,"price":3.5}, {"min":501,"max":float("inf"),"price":3} ],
      "Etsy":[ {"min":1,"max":100,"price":4}, {"min":101,"max":500,"price":2.5}, {"min":501,"max":float("inf"),"price":2} ],
      "Shein":[ {"min":1,"max":100,"price":5}, {"min":101,"max":500,"price":3.5}, {"min":501,"max":float("inf"),"price":3} ],
      "Temu":[ {"min":1,"max":100,"price":5}, {"min":101,"max":500,"price":3.5}, {"min":501,"max":float("inf"),"price":3} ]
    },
    "Advanced Listings (Optimized Content)": {
      "Amazon":[ {"min":1,"max":10,"price":60}, {"min":11,"max":50,"price":50}, {"min":51,"max":100,"price":50}, {"min":101,"max":float("inf"),"price":40} ],
      "TikTok":[ {"min":1,"max":50,"price":45}, {"min":51,"max":float("inf"),"price":35} ],
      "eBay":[ {"min":1,"max":float("inf"),"price":40} ],
      "Walmart":[ {"min":1,"max":float("inf"),"price":42} ],
      "Etsy":[ {"min":1,"max":float("inf"),"price":40} ],
      "Shein":[ {"min":1,"max":float("inf"),"price":45} ],
      "Temu":[ {"min":1,"max":float("inf"),"price":45} ]
    },
    "Enhanced Listings (Rich Media + Optimized)": {
      "Amazon":[ {"min":1,"max":float("inf"),"price":75,"label":"Basic A+"}, {"min":1,"max":float("inf"),"price":100,"label":"Premium A+"} ],
      "TikTok":[ {"min":1,"max":float("inf"),"price":45} ],
      "eBay":[ {"min":1,"max":float("inf"),"price":55} ],
      "Walmart":[ {"min":1,"max":float("inf"),"price":62} ],
      "Etsy":[ {"min":1,"max":float("inf"),"price":45} ],
      "Shein":[ {"min":1,"max":float("inf"),"price":45} ],
      "Temu":[ {"min":1,"max":float("inf"),"price":45} ]
    },
    "Brand Storefront / Brand Story": {
      "any":[ {"type":"storefront","priceRange":[500,1000],"note":"500 basic (5 categories); 1000 advanced (10+ collections)"}, {"type":"brandstory","priceRange":[200,400],"note":"per story"} ]
    },
    "Advertising Strategy (Ads Setup)": {
      "any":[ {"type":"ads","priceRange":[500,1500],"note":"setup fee varies by ad budget"} ]
    }
  },
  "recurring": {
    "presets": [
      { "key":"starter","label":"Starter (No Ads)","monthly":299,"effective":{"quarterly":259,"halfyear":199,"yearly":None},"eligiblePlatforms":["Amazon","TikTok","Walmart","Shein","eBay","Etsy","Temu"] },
      { "key":"enterprise","label":"Enterprise (With Ads)","monthly":499,"effective":{"quarterly":459,"halfyear":399,"yearly":359},"eligiblePlatforms":["Amazon","TikTok","Walmart","Shein","eBay","Etsy","Temu"] },
      { "key":"growth_basic","label":"Growth Basic (No Ads)","monthly":699,"effective":{"quarterly":599,"halfyear":499,"yearly":499},"eligiblePlatforms":["Amazon","TikTok","Walmart","Shein","eBay","Etsy","Temu"] },
      { "key":"growth_enterprise","label":"Growth Enterprise (With Ads)","monthly":1099,"effective":{"quarterly":999,"halfyear":899,"yearly":799},"eligiblePlatforms":["Amazon","TikTok","Walmart","Shein","eBay","Etsy","Temu"] },
      { "key":"enhanced_basic","label":"Enhanced Basic (No Ads)","monthly":699,"effective":{"quarterly":599,"halfyear":499,"yearly":399},"eligiblePlatforms":["Amazon","TikTok","Walmart","Shein"] },
      { "key":"enhanced_enterprise","label":"Enhanced Enterprise (With Ads)","monthly":1099,"effective":{"quarterly":999,"halfyear":899,"yearly":799},"eligiblePlatforms":["Amazon","TikTok","Walmart","Shein"] },
      { "key":"enterprise_large","label":"Enterprise Large","monthly":1499,"effective":{"quarterly":1299,"halfyear":1099,"yearly":899},"eligiblePlatforms":["Amazon","TikTok","Walmart","Shein","eBay","Etsy","Temu"] }
    ],
    "adBands": [
      { "bracket":"0-5000","monthly":500 },
      { "bracket":"5000-10000","monthly":800 },
      { "bracket":"10000-25000","monthly":1000 },
      { "bracket":"25000-50000","monthly":1500 }
    ]
  }
}

# ---------- helper functions ----------
def find_one_time_unit(service, platform, count, extras=None):
    extras = extras or {}
    svc = PRICING_DATA["oneTime"].get(service)
    if not svc:
        return {"error": "Unknown service"}
    if service in ("Brand Storefront / Brand Story", "Advertising Strategy (Ads Setup)"):
        return {"special": svc["any"]}
    tiers = svc.get(platform)
    if not tiers:
        return {"error": "Unknown platform for this service"}
    if service.startswith("Enhanced") and platform == "Amazon" and extras.get("aplusLevel"):
        for t in tiers:
            if t.get("label") and ((extras["aplusLevel"] == "premium" and t["label"] == "Premium A+") or (extras["aplusLevel"] == "basic" and t["label"]=="Basic A+")):
                return {"unit": t["price"], "unitLabel": t.get("label")}
    for t in tiers:
        if count >= t.get("min",1) and count <= t.get("max", float("inf")):
            return {"unit": t["price"], "tier": t}
    # fallback
    for t in tiers:
        if t.get("price") is not None:
            return {"unit": t["price"]}
    return {"error":"No matching tier found"}

def compute_ad_one_time(ad_bracket):
    band = next((b for b in PRICING_DATA["recurring"]["adBands"] if b["bracket"]==ad_bracket), None)
    if not band:
        return {"error":"Unknown ad bracket"}
    recommended = band["monthly"]
    return {"recommendedOneTime": recommended, "range":[round(recommended*0.6), round(recommended*1.5)], "monthlyBand": recommended}

def compute_recurring_quote(preset_key, frequency, platform):
    preset = next((p for p in PRICING_DATA["recurring"]["presets"] if p["key"]==preset_key), None)
    if not preset:
        return {"error":"Unknown preset"}
    if preset.get("eligiblePlatforms") and platform not in preset["eligiblePlatforms"]:
        return {"error": f"Preset not eligible for {platform}"}
    monthly_base = preset["monthly"]
    effective = preset.get("effective", {}).get(frequency)
    if effective is None:
        if frequency=="quarterly":
            monthly_effective = round(monthly_base * 0.86)
        elif frequency=="halfyear":
            monthly_effective = round(monthly_base * 0.66)
        elif frequency=="yearly":
            monthly_effective = round(monthly_base * 0.9)
        else:
            monthly_effective = monthly_base
    else:
        monthly_effective = effective
    months = {"monthly":1,"quarterly":3,"halfyear":6,"yearly":12}.get(frequency,1)
    total = monthly_effective * months
    saving = max(0, (monthly_base * months) - total)
    return {"monthlyBase": monthly_base, "monthlyEffective": monthly_effective, "months": months, "total": total, "saving": saving, "presetLabel": preset["label"]}

# ---------- UI ----------
st.markdown("<h2 style='margin-bottom:6px'>CED: Managed Services Pricign Calcualtor</h2>", unsafe_allow_html=True)
st.write("")  # spacing

col1, col2 = st.columns([1,1.4])

with col1:
    billing = st.radio("Billing cycle", options=["Monthly","Yearly"], index=0, horizontal=True)
    service = st.selectbox("Service Category", [
        "Standard Listings (Product Uploads)",
        "Advanced Listings (Optimized Content)",
        "Enhanced Listings (Rich Media + Optimized)",
        "Brand Storefront / Brand Story",
        "Advertising Strategy (Ads Setup)"
    ])
    platform = st.selectbox("Platform", ["Amazon","TikTok","eBay","Walmart","Etsy","Shein","Temu"])
    count = st.number_input("Product count (or enter 1 for storefront/one-off)", min_value=1, value=20, step=1)

    # conditional fields
    ad_budget = None
    storefront_size = None
    aplus_level = "basic"
    if service == "Advertising Strategy (Ads Setup)":
        ad_budget = st.selectbox("Ad budget bracket (used for ad setup bands)", ["0-5000","5000-10000","10000-25000","25000-50000"])
    if service == "Brand Storefront / Brand Story":
        storefront_size = st.selectbox("Storefront complexity", ["basic","advanced"])
    if service.startswith("Enhanced") and platform=="Amazon":
        aplus_level = st.selectbox("A+ Content level", ["basic","premium"])

    st.write("")  # spacing
    st.write("")  # spacing
    if st.button("Calculate"):
        # compute depending on selections
        extras = {"aplusLevel": aplus_level, "storefrontSize": storefront_size, "adBudgetBracket": ad_budget}
        # special service handling
        if service == "Brand Storefront / Brand Story":
            special = PRICING_DATA["oneTime"][service]["any"]
            storefront = next(s for s in special if s["type"]=="storefront")
            brandstory = next(s for s in special if s["type"]=="brandstory")
            if count >=5:
                low, high = storefront["priceRange"]
                quote = {"type":"storefront","low":low,"high":high,"note":shop_note:=storefront["note"]}
                st.success(f"Estimated storefront price: **{low} — {high} USD**")
                st.caption(f"{shop_note}")
            else:
                low, high = brandstory["priceRange"]
                st.success(f"Brand story estimate: **{low} — {high} USD**")
                st.caption(brandstory["note"])
        elif service == "Advertising Strategy (Ads Setup)":
            band = compute_ad_one_time(ad_budget)
            if "error" in band:
                st.error(band["error"])
            else:
                low, high = band["range"]
                recommended = band["recommendedOneTime"]
                st.success(f"Ad setup estimate: **{low} — {high} USD** (recommended: {recommended} USD)")
                st.caption(f"Ad budget bracket: {ad_budget}")
        else:
            unit_res = find_one_time_unit(service, platform, int(count), extras)
            if "error" in unit_res:
                st.error(unit_res["error"])
            else:
                unit = unit_res["unit"]
                total_one_time = unit * int(count)
                # check recurring preset selection (allow user to choose below)
                st.info(f"One-time total: **{total_one_time:,} USD** — ({count} × {unit} USD/product)")
                # we will show recurring calc in right column on click below (or here)
                # store lastQuote in session_state
                st.session_state["last_quote"] = {"mode":"computed","service":service,"platform":platform,"count":int(count),"unit":unit,"total_one_time":total_one_time}

with col2:
    # Right column: Recurring preset + result card
    st.subheader("Recurring (optional)")
    preset_options = {p["label"]:p["key"] for p in PRICING_DATA["recurring"]["presets"]}
    preset_label = st.selectbox("Recurring preset (choose for subscription quote)", list(preset_options.keys()))
    preset_key = preset_options[preset_label]
    # allowed frequencies for presets - show monthly/yearly only as requested, but include quarters/halfyear in calculation if needed
    billing_choice = billing.lower()  # "monthly" or "yearly"
    frequency_to_use = "monthly"
    if billing_choice == "yearly":
        frequency_to_use = "yearly"
    else:
        frequency_to_use = "monthly"
    # compute recurring
    recurring = compute_recurring_quote(preset_key, frequency_to_use, platform)
    if "error" in recurring:
        st.error(recurring["error"])
    else:
        # show result card (styled)
        def card_html(title, value, subtitle):
            return f"""
            <div style="background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
                        padding:18px; border-radius:10px; border:1px solid rgba(255,255,255,0.04);
                        box-shadow: rgba(3,6,20,0.6) 0px 18px 40px;">
              <div style="font-weight:900; font-size:28px; color:#fff;">{value}</div>
              <div style="color: #b8c7d9; margin-top:6px; font-size:14px;">{subtitle}</div>
            </div>
            """
        # recurring values
        monthly_eff = recurring["monthlyEffective"]
        total_term = recurring["total"]
        months = recurring["months"]
        saving = recurring["saving"]
        st.markdown(card_html("Recurring (effective)", f"{monthly_eff:,} USD / mo", f"{recurring['presetLabel']} — {months} month term • Total {total_term:,} USD"), unsafe_allow_html=True)

        # show one-time if present in session_state
        if st.session_state.get("last_quote"):
            jq = st.session_state["last_quote"]
            st.markdown("---")
            st.markdown(f"**Last computed one-time**: {jq['total_one_time']:,} USD")
            st.markdown(f"{jq['count']} × {jq['unit']} USD / product — {jq['service']} on {jq['platform']}")

    # export / copy actions
    st.markdown("---")
    if st.button("Copy quote JSON (to clipboard)"):
        payload = {
            "generatedAt": datetime.utcnow().isoformat(),
            "service": st.session_state.get("last_quote")
        }
        st.write("JSON (copy from below):")
        st.code(json.dumps(payload, indent=2))
        # Note: Streamlit clipboard not available on backend; user can copy from code block.

    if st.button("Download quote (.txt)"):
        # generate text
        jq = st.session_state.get("last_quote", {})
        lines = [
            "CED Quote",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            f"Service: {jq.get('service')}",
            f"Platform: {jq.get('platform')}",
            f"Count: {jq.get('count')}",
            f"One-time total: {jq.get('total_one_time')}",
        ]
        text_blob = "\n".join(lines)
        st.download_button("Download .txt", data=text_blob, file_name="ced-quote.txt", mime="text/plain")
