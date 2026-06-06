#!/usr/bin/env python3
"""
Show Me Turkiye - Cookie consent injector (KVKK uyumlu, GA always-on)
=====================================================================
Tum HTML sayfalara (kok + cities/ routes/ blog/ alt klasorler) cookie
consent banner'ini ekler. Banner her sayfada </body> etiketinden hemen
once, tek bir blok olarak yer alir.

DEGISIKLIK NOTU (6 Haziran 2026):
- GA artik sayfa yuklenir yuklenmez calisir (consent beklemeden).
- IP anonimlestirme acik (anonymize_ip:true), KVKK mesru menfaat kapsami.
- Banner yine gosterilir; kullanici reddederse ileride eklenecek marketing/
  advertising cerezleri yuklenmez. Analytics ise her durumda calisir.

GA_ID: Script'i calistirmadan once asagidaki GA_ID degerini gercek
Measurement ID'nle degistir (G-XXXXXXXXXX formatinda). Canli sayfa
kaynak kodundan bulabilirsin (view-source > 'gtag/js?id=' ara).

Kullanim:   python build-consent.py
"""

import re
from pathlib import Path

START = "<!-- SMT-CONSENT-START -->"
END   = "<!-- SMT-CONSENT-END -->"

# === BURAYI DEGISTIR ===
# Canli sayfadan gercek GA Measurement ID'ni al ve asagiya yaz.
# Ornek: GA_ID = 'G-ABC123XYZ'
GA_ID = "G-Q7E5XWC6GR"

CONSENT_BLOCK = START + """
<style>
.cc-banner{position:fixed;left:24px;right:24px;bottom:24px;z-index:2147483000;max-width:560px;margin:0 auto;background:#FAF5EA;color:#2A1410;border:1px solid rgba(42,20,16,0.12);border-radius:14px;box-shadow:0 18px 50px rgba(42,20,16,0.22);font-family:'Poppins',-apple-system,sans-serif;padding:26px 28px 22px;transform:translateY(140%);opacity:0;transition:transform .55s cubic-bezier(.16,1,.3,1),opacity .4s ease;pointer-events:none;}
.cc-banner.cc-show{transform:translateY(0);opacity:1;pointer-events:auto;}
.cc-eyebrow{font-size:10.5px;font-weight:600;letter-spacing:.34em;text-transform:uppercase;color:#C9A75D;margin:0 0 10px;}
.cc-title{font-family:'Playfair Display',serif;font-size:21px;font-weight:600;margin:0 0 8px;line-height:1.25;}
.cc-text{font-size:13.5px;line-height:1.6;color:#5C3530;margin:0 0 18px;}
.cc-text a{color:#C0392B;text-decoration:none;border-bottom:1px solid rgba(192,57,43,.3);}
.cc-text a:hover{border-color:#C0392B;}
.cc-actions{display:flex;flex-wrap:wrap;gap:10px;}
.cc-btn{font-family:'Poppins',sans-serif;font-size:12.5px;font-weight:500;letter-spacing:.04em;border-radius:9px;padding:12px 20px;cursor:pointer;border:1px solid transparent;transition:all .25s ease;flex:1 1 auto;min-width:120px;}
.cc-btn-accept{background:#2A1410;color:#F4EFE5;}
.cc-btn-accept:hover{background:#C0392B;}
.cc-btn-reject{background:transparent;color:#2A1410;border-color:rgba(42,20,16,0.25);}
.cc-btn-reject:hover{border-color:#2A1410;background:rgba(42,20,16,0.04);}
.cc-btn-prefs{background:none;border:none;color:#5C3530;font-size:12px;letter-spacing:.04em;text-decoration:underline;cursor:pointer;flex:0 0 auto;padding:12px 8px;font-family:'Poppins',sans-serif;}
.cc-btn-prefs:hover{color:#2A1410;}
.cc-modal-bg{position:fixed;inset:0;background:rgba(10,10,10,.55);z-index:2147483001;display:none;align-items:center;justify-content:center;padding:24px;}
.cc-modal-bg.cc-show{display:flex;}
.cc-modal{background:#FAF5EA;color:#2A1410;border-radius:16px;max-width:520px;width:100%;max-height:86vh;overflow-y:auto;padding:34px 32px 28px;font-family:'Poppins',sans-serif;box-shadow:0 24px 70px rgba(10,10,10,.4);}
.cc-modal h3{font-family:'Playfair Display',serif;font-size:24px;font-weight:600;margin:0 0 6px;}
.cc-modal>p{font-size:13.5px;color:#5C3530;line-height:1.6;margin:0 0 22px;}
.cc-row{border-top:1px solid rgba(42,20,16,.1);padding:18px 0;display:flex;justify-content:space-between;align-items:flex-start;gap:16px;}
.cc-row-info h4{font-size:14px;font-weight:600;margin:0 0 5px;}
.cc-row-info p{font-size:12.5px;color:#5C3530;line-height:1.55;margin:0;}
.cc-toggle{position:relative;width:44px;height:24px;flex:0 0 auto;margin-top:3px;}
.cc-toggle input{opacity:0;width:0;height:0;position:absolute;}
.cc-slider{position:absolute;inset:0;background:rgba(42,20,16,.2);border-radius:24px;cursor:pointer;transition:.3s;}
.cc-slider::before{content:'';position:absolute;height:18px;width:18px;left:3px;top:3px;background:#FAF5EA;border-radius:50%;transition:.3s;box-shadow:0 1px 3px rgba(0,0,0,.2);}
.cc-toggle input:checked+.cc-slider{background:#C0392B;}
.cc-toggle input:checked+.cc-slider::before{transform:translateX(20px);}
.cc-toggle input:disabled+.cc-slider{background:#C9A75D;cursor:not-allowed;opacity:.7;}
.cc-modal-actions{display:flex;gap:10px;margin-top:26px;}
.cc-modal-actions .cc-btn{flex:1;}
@media (max-width:600px){.cc-banner{left:12px;right:12px;bottom:12px;padding:22px 20px 18px;}.cc-title{font-size:19px;}.cc-actions{flex-direction:column;}.cc-btn{width:100%;flex:1 1 100%;}.cc-btn-prefs{order:3;text-align:center;}}
</style>
<div class="cc-banner" id="ccBanner" role="dialog" aria-live="polite" aria-label="Cookie consent">
  <p class="cc-eyebrow">Privacy</p>
  <h2 class="cc-title">A note on cookies</h2>
  <p class="cc-text">We use essential and anonymous analytics cookies to keep this site running and improve it. With your consent, we may also use marketing cookies in the future. Read more in our <a href="/cookies.html">Cookies Policy</a>.</p>
  <div class="cc-actions">
    <button class="cc-btn cc-btn-reject" id="ccReject">Reject non-essential</button>
    <button class="cc-btn cc-btn-accept" id="ccAccept">Accept all</button>
    <button class="cc-btn-prefs" id="ccPrefs">Customise</button>
  </div>
</div>
<div class="cc-modal-bg" id="ccModalBg" role="dialog" aria-modal="true" aria-label="Cookie preferences">
  <div class="cc-modal">
    <h3>Cookie preferences</h3>
    <p>Choose which cookies you allow. Essential and anonymous analytics cookies are always on (legitimate interest, anonymised IP). Your choice is saved on your device and you can change it anytime from the Cookies Policy page.</p>
    <div class="cc-row">
      <div class="cc-row-info"><h4>Essential</h4><p>Required for core features such as remembering your language and that you have seen this notice. Always active.</p></div>
      <label class="cc-toggle"><input type="checkbox" checked disabled><span class="cc-slider"></span></label>
    </div>
    <div class="cc-row">
      <div class="cc-row-info"><h4>Anonymous analytics</h4><p>Google Analytics with anonymised IP, used to understand how the site is used in aggregate. Always active under legitimate interest.</p></div>
      <label class="cc-toggle"><input type="checkbox" checked disabled><span class="cc-slider"></span></label>
    </div>
    <div class="cc-row">
      <div class="cc-row-info"><h4>Marketing</h4><p>Reserved for future use (e.g. retargeting). Off until you allow it.</p></div>
      <label class="cc-toggle"><input type="checkbox" id="ccMarketing"><span class="cc-slider"></span></label>
    </div>
    <div class="cc-modal-actions">
      <button class="cc-btn cc-btn-reject" id="ccSavePrefs">Save choices</button>
      <button class="cc-btn cc-btn-accept" id="ccAcceptModal">Accept all</button>
    </div>
  </div>
</div>
<script id="smt-consent-js">
(function(){
  var KEY='smt_cookie_consent_v1';
  var banner=document.getElementById('ccBanner');
  var modalBg=document.getElementById('ccModalBg');
  var marketingToggle=document.getElementById('ccMarketing');
  function getConsent(){try{var v=localStorage.getItem(KEY);return v?JSON.parse(v):null;}catch(e){return null;}}
  function saveConsent(o){o.ts=new Date().toISOString();try{localStorage.setItem(KEY,JSON.stringify(o));}catch(e){}}
  var GA_ID='__GA_ID__';
  var analyticsLoaded=false;
  function loadAnalytics(){
    if(analyticsLoaded)return;analyticsLoaded=true;
    if(!GA_ID||GA_ID.indexOf('XXX')>-1)return;
    var s=document.createElement('script');s.async=true;
    s.src='https://www.googletagmanager.com/gtag/js?id='+GA_ID;
    document.head.appendChild(s);
    window.dataLayer=window.dataLayer||[];
    function gtag(){dataLayer.push(arguments);}window.gtag=gtag;
    gtag('js',new Date());
    gtag('config',GA_ID,{anonymize_ip:true});
  }
  // Analytics her durumda yuklenir (mesru menfaat + anonim IP).
  loadAnalytics();
  function apply(c){
    // Gelecekte marketing/advertising cerezleri buraya eklenir.
    // Ornek: if(c&&c.marketing===true) loadMarketingPixels();
  }
  function showBanner(){setTimeout(function(){banner.classList.add('cc-show');},700);}
  function hideBanner(){banner.classList.remove('cc-show');}
  function openModal(){var c=getConsent();if(marketingToggle){marketingToggle.checked=c?!!c.marketing:false;}modalBg.classList.add('cc-show');}
  function closeModal(){modalBg.classList.remove('cc-show');}
  function acceptAll(){var c={essential:true,analytics:true,marketing:true};saveConsent(c);apply(c);hideBanner();closeModal();}
  function rejectNon(){var c={essential:true,analytics:true,marketing:false};saveConsent(c);hideBanner();closeModal();}
  function savePrefs(){var c={essential:true,analytics:true,marketing:marketingToggle?!!marketingToggle.checked:false};saveConsent(c);apply(c);hideBanner();closeModal();}
  document.getElementById('ccAccept').addEventListener('click',acceptAll);
  document.getElementById('ccReject').addEventListener('click',rejectNon);
  document.getElementById('ccPrefs').addEventListener('click',openModal);
  document.getElementById('ccAcceptModal').addEventListener('click',acceptAll);
  document.getElementById('ccSavePrefs').addEventListener('click',savePrefs);
  modalBg.addEventListener('click',function(e){if(e.target===modalBg)closeModal();});
  window.SMTopenCookiePrefs=openModal;
  var existing=getConsent();
  if(existing){apply(existing);}else{showBanner();}
})();
</script>
""" + END


def inject(html: str) -> str:
    # Eski consent blogunu (varsa) cikar
    html = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.DOTALL)
    # </body> oncesine yenisini koy
    idx = html.rfind("</body>")
    if idx == -1:
        return None  # </body> yok, atla
    # GA_ID'yi enjekte et
    block = CONSENT_BLOCK.replace("__GA_ID__", GA_ID)
    return html[:idx] + block + "\n" + html[idx:]


def main():
    print("Cookie consent banner ekleniyor ...")
    if "XXX" in GA_ID:
        print("  ! UYARI: GA_ID hala placeholder ('" + GA_ID + "').")
        print("  ! Bu dosyanin basindaki GA_ID degerini gercek Measurement ID'nle degistir,")
        print("  ! sonra bu script'i tekrar calistir. Yoksa GA yuklenmez.")
    pages = list(Path(".").glob("*.html")) + list(Path(".").glob("*/*.html"))
    updated = 0
    skipped = []
    for p in pages:
        h = p.read_text(encoding="utf-8")
        new = inject(h)
        if new is None:
            skipped.append(str(p)); continue
        if new != h:
            p.write_text(new, encoding="utf-8"); updated += 1
    print(f"  OK  {updated} sayfaya consent banner eklendi/guncellendi")
    if skipped:
        print(f"  ! </body> bulunamadi, atlanan: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
