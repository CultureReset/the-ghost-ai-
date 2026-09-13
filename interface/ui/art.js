/* Glyphs and hero art, drawn rather than fetched.
 *
 * Nothing here reaches the network. The box is expected to work in a dock
 * office with bad wifi and on a boat with none, so every pixel on screen is
 * either a vector defined in this file or a colour from tokens.css. That also
 * means no logo belongs here: an app tile is a coloured square with a glyph,
 * never somebody else's mark. */

const svg = (d, o = {}) =>
  `<svg viewBox="0 0 24 24" width="${o.w || 18}" height="${o.w || 18}" fill="none"
     stroke="${o.s || "currentColor"}" stroke-width="${o.sw || 1.7}"
     stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;

export const I = {
  chev:    o => svg(`<path d="M9 5l7 7-7 7"/>`, o),
  caret:   o => svg(`<path d="M9 5l7 7-7 7"/>`, { w: 13, ...o }),
  back:    o => svg(`<path d="M15 5l-7 7 7 7"/>`, o),
  search:  o => svg(`<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>`, o),
  gear:    o => svg(`<circle cx="12" cy="12" r="3"/><path d="M12 2.5v2.2M12 19.3v2.2M21.5 12h-2.2M4.7 12H2.5M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6M18.7 18.7l-1.6-1.6M6.9 6.9L5.3 5.3"/>`, o),
  bell:    o => svg(`<path d="M18 15V10a6 6 0 10-12 0v5l-1.6 2.4h15.2z"/><path d="M10 20a2 2 0 004 0"/>`, o),
  spark:   o => svg(`<path d="M12 3l1.9 5.4L19 10l-5.1 1.6L12 17l-1.9-5.4L5 10l5.1-1.6z"/><path d="M18.5 15.5l.7 1.9 1.8.6-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.6z"/>`, o),
  clip:    o => svg(`<path d="M20 11.5l-7.8 7.8a4.2 4.2 0 01-6-6l8-8a2.8 2.8 0 014 4l-8 8a1.4 1.4 0 01-2-2l7.3-7.3"/>`, o),
  up:      o => svg(`<path d="M12 19V6M6 12l6-6 6 6"/>`, o),
  chart:   o => svg(`<path d="M4 20V11M10 20V5M16 20v-6M22 20H2"/>`, o),
  star:    o => svg(`<path d="M12 3.6l2.6 5.4 5.9.8-4.3 4.1 1 5.9-5.2-2.8-5.2 2.8 1-5.9L3.5 9.8l5.9-.8z"/>`, o),
  box:     o => svg(`<path d="M3.5 7.5L12 3l8.5 4.5v9L12 21l-8.5-4.5z"/><path d="M3.5 7.5L12 12l8.5-4.5M12 12v9"/>`, o),
  cal:     o => svg(`<rect x="3.5" y="5" width="17" height="16" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>`, o),
  chat:    o => svg(`<path d="M20.5 12a7.5 7.5 0 01-10.9 6.7L4 20l1.3-4.3A7.5 7.5 0 1120.5 12z"/>`, o),
  clock:   o => svg(`<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5.2l3.2 2"/>`, o),
  mega:    o => svg(`<path d="M4 10v4h3l6 4V6l-6 4z"/><path d="M17.5 9a4.5 4.5 0 010 6"/>`, o),
  down:    o => svg(`<path d="M12 4v11M7.5 11L12 15.5 16.5 11M4.5 19.5h15"/>`, o),
  doc:     o => svg(`<path d="M13.5 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8.5z"/><path d="M13.5 3v5.5H19"/>`, o),
  people:  o => svg(`<circle cx="9" cy="8.5" r="3.3"/><path d="M3 20a6 6 0 0112 0"/><path d="M16.5 6.2a3.3 3.3 0 010 6.4M17 14.4A5.6 5.6 0 0121 20"/>`, o),
  tag:     o => svg(`<path d="M3.5 11.4V4.5a1 1 0 011-1h6.9a2 2 0 011.4.6l7.1 7.1a2 2 0 010 2.8l-6.9 6.9a2 2 0 01-2.8 0L4.1 13.8a2 2 0 01-.6-1.4z"/><circle cx="8" cy="8" r="1.3" fill="currentColor" stroke="none"/>`, o),
  home:    o => svg(`<path d="M4 10.5L12 4l8 6.5V20a1 1 0 01-1 1h-4v-6H9v6H5a1 1 0 01-1-1z"/>`, o),
  grid:    o => svg(`<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="2"/>`, o),
  bot:     o => svg(`<rect x="4" y="7.5" width="16" height="12" rx="3.5"/><path d="M12 3.5v4M8.5 13h.01M15.5 13h.01M9.5 16.5h5"/>`, o),
  play:    o => svg(`<circle cx="12" cy="12" r="8.5"/><path d="M10 8.8l5.5 3.2-5.5 3.2z" fill="currentColor"/>`, o),
  folder:  o => svg(`<path d="M3.5 7.5a2 2 0 012-2h3.2l2 2.2h7.8a2 2 0 012 2v8.3a2 2 0 01-2 2h-13a2 2 0 01-2-2z"/>`, o),
  mail:    o => svg(`<rect x="3" y="5.5" width="18" height="13" rx="2.5"/><path d="M3.6 7.2L12 13l8.4-5.8"/>`, o),
  check:   o => svg(`<circle cx="12" cy="12" r="8.5"/><path d="M8.4 12.3l2.5 2.5 4.7-5"/>`, o),
  alert:   o => svg(`<circle cx="12" cy="12" r="8.5"/><path d="M12 7.6v5M12 16.2h.01"/>`, o),
  route:   o => svg(`<path d="M4 20L20 4M20 4v6M20 4h-6"/>`, o),
  drift:   o => svg(`<path d="M3.5 12h4l2.5-6 4 12 2.5-6h4"/>`, o),
  screen:  o => svg(`<rect x="3" y="4.5" width="18" height="12" rx="2"/><path d="M8 20.5h8M12 16.5v4"/>`, o),
  image:   o => svg(`<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><circle cx="9" cy="10" r="1.8"/><path d="M4 17l4.8-4.4L20 19.5"/>`, o),
  ship:    o => svg(`<path d="M3.5 15.5l1.7 4.2a1 1 0 00.9.6h11.8a1 1 0 00.9-.6l1.7-4.2"/><path d="M5.5 15V8.5L12 6l6.5 2.5V15M12 3v3"/>`, o),
};

/* Hero art. Two moods, both drawn: a dawn ridge for the personal shell and a
   warm room for a business workspace. */
export function heroArt(kind) {
  if (kind === "room") return `
  <svg viewBox="0 0 900 420" preserveAspectRatio="xMidYMid slice">
    <defs>
      <linearGradient id="rm" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#2A1C12"/><stop offset="1" stop-color="#0C0908"/>
      </linearGradient>
      <radialGradient id="glow" cx=".62" cy=".34" r=".5">
        <stop offset="0" stop-color="#FF9A3C" stop-opacity=".55"/>
        <stop offset="1" stop-color="#FF9A3C" stop-opacity="0"/>
      </radialGradient>
      <radialGradient id="glow2" cx=".28" cy=".62" r=".42">
        <stop offset="0" stop-color="#E8503A" stop-opacity=".3"/>
        <stop offset="1" stop-color="#E8503A" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <rect width="900" height="420" fill="url(#rm)"/>
    <rect width="900" height="420" fill="url(#glow)"/>
    <rect width="900" height="420" fill="url(#glow2)"/>
    <g opacity=".5" fill="#FFB765">
      ${Array.from({ length: 22 }, (_, i) => {
        const x = 40 + ((i * 137) % 840), y = 40 + ((i * 89) % 330);
        const r = 1.4 + ((i * 7) % 5) * 0.5;
        return `<circle cx="${x}" cy="${y}" r="${r}" opacity="${
          0.25 + ((i * 13) % 60) / 100}"/>`;
      }).join("")}
    </g>
    <g stroke="#FFC489" stroke-width="2.2" fill="none" opacity=".55">
      <path d="M604 96h86M604 126h118M604 156h74"/>
    </g>
    <rect y="330" width="900" height="90" fill="#0A0706" opacity=".65"/>
  </svg>`;

  return `
  <svg viewBox="0 0 900 420" preserveAspectRatio="xMidYMid slice">
    <defs>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="#0B1017"/>
        <stop offset=".52" stop-color="#243247"/>
        <stop offset=".78" stop-color="#6B5A5A"/>
        <stop offset="1"   stop-color="#C08A5E"/>
      </linearGradient>
      <radialGradient id="sun" cx=".66" cy=".79" r=".30">
        <stop offset="0"   stop-color="#FFE6B8"/>
        <stop offset=".35" stop-color="#FFB65E" stop-opacity=".75"/>
        <stop offset="1"   stop-color="#FF9A3C" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <rect width="900" height="420" fill="url(#sky)"/>
    <g fill="#EAF0F6">
      ${Array.from({ length: 34 }, (_, i) => {
        const x = ((i * 211) % 890) + 5, y = ((i * 67) % 190) + 6;
        return `<circle cx="${x}" cy="${y}" r="${i % 5 ? 0.9 : 1.4}"
                  opacity="${0.12 + ((i * 17) % 45) / 100}"/>`;
      }).join("")}
    </g>
    <rect width="900" height="420" fill="url(#sun)"/>
    <path d="M0 300 L120 214 L196 262 L300 176 L392 250 L470 208 L556 268 L640 216
             L742 276 L830 232 L900 282 L900 420 L0 420 Z" fill="#2A3444"/>
    <path d="M300 176 L336 208 L318 218 L352 246 L392 250 Z" fill="#E9EFF6" opacity=".82"/>
    <path d="M120 214 L146 236 L134 242 L160 258 L196 262 Z" fill="#E9EFF6" opacity=".6"/>
    <path d="M0 336 L108 288 L214 330 L318 282 L438 340 L540 296 L664 344 L780 300
             L900 348 L900 420 L0 420 Z" fill="#1A222E"/>
    <path d="M0 384 L160 352 L318 388 L470 350 L640 392 L800 356 L900 380
             L900 420 L0 420 Z" fill="#11161E"/>
  </svg>`;
}
