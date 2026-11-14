// VIDRAKSH Live — shared logic. No dependencies. Runs in Node (collector) and in a browser (tests).
// Stores headline + link only; article text is read for sorting and then discarded.

export const FEEDS = [
  { id: 'ie',   name: 'Indian Express',   url: 'https://indianexpress.com/section/cities/pune/feed/', pune: true },
  { id: 'ht',   name: 'Hindustan Times',  url: 'https://www.hindustantimes.com/feeds/rss/cities/pune-news/rssfeed.xml', pune: true },
  { id: 'toi',  name: 'Times of India',   url: 'https://timesofindia.indiatimes.com/rssfeeds/-2128821991.cms', pune: true },
  { id: 'ptm',  name: 'Pune Times Mirror', url: 'https://punemirror.com/feed', pune: true },
  { id: 'pkn',  name: 'Punekar News',     url: 'https://www.punekarnews.in/feed/', pune: true },
  { id: 'ppl',  name: 'Pune Pulse',       url: 'https://www.mypunepulse.com/feed/', pune: true },
  { id: 'fpj',  name: 'Free Press Journal', url: 'https://www.freepressjournal.in/stories.rss?section=pune', pune: false },
  { id: 'tv9',  name: 'TV9 Marathi',      url: 'https://www.tv9marathi.com/maharashtra/pune/feed', pune: true },
  { id: 'abp',  name: 'ABP Majha',        url: 'https://marathi.abplive.com/news/pune/feed', pune: true },
  { id: 'prb',  name: 'Dainik Prabhat',   url: 'https://www.dainikprabhat.com/feed/', pune: false },
];

// Area list. Coordinates are approximate locality centres (area-level only, never an incident spot).
// r: 'city' = Pune City Police area, 'pcmc' = Pimpri-Chinchwad, 'rural' = Pune district outside both.
export const AREAS = [
  ['shivajinagar','Shivajinagar',18.5308,73.8475,'city',['shivajinagar','shivaji nagar','शिवाजीनगर']],
  ['deccan','Deccan / FC Road',18.5180,73.8410,'city',['deccan','fc road','fergusson college road','jm road','jangli maharaj road','डेक्कन']],
  ['camp','Camp',18.5110,73.8800,'city',['pune camp','camp area','mg road','lashkar police','cantonment','लष्कर','कॅम्प']],
  ['kp','Koregaon Park',18.5362,73.8939,'city',['koregaon park','कोरेगाव पार्क']],
  ['mundhwa','Mundhwa',18.5320,73.9300,'city',['mundhwa','मुंढवा']],
  ['yerawada','Yerawada',18.5510,73.8800,'city',['yerawada','yerwada','येरवडा']],
  ['kharadi','Kharadi',18.5510,73.9430,'city',['kharadi','खराडी']],
  ['chandannagar','Chandan Nagar',18.5610,73.9330,'city',['chandan nagar','chandannagar','चंदननगर']],
  ['vimannagar','Viman Nagar',18.5679,73.9143,'city',['viman nagar','vimannagar','vimantal','विमाननगर','विमानतळ']],
  ['lohegaon','Lohegaon',18.5960,73.9200,'city',['lohegaon','लोहगाव']],
  ['vishrantwadi','Vishrantwadi',18.5770,73.8780,'city',['vishrantwadi','विश्रांतवाडी']],
  ['dhanori','Dhanori',18.5950,73.8960,'city',['dhanori','धानोरी']],
  ['wagholi','Wagholi',18.5800,73.9800,'city',['wagholi','वाघोली']],
  ['kothrud','Kothrud',18.5074,73.8077,'city',['kothrud','कोथरूड','कोथरुड']],
  ['karvenagar','Karve Nagar',18.4900,73.8200,'city',['karve nagar','karvenagar','karve road','कर्वेनगर']],
  ['erandwane','Erandwane',18.5100,73.8300,'city',['erandwane','erandwana','एरंडवणे']],
  ['warje','Warje',18.4810,73.8000,'city',['warje','वारजे']],
  ['bavdhan','Bavdhan',18.5150,73.7780,'city',['bavdhan','बावधन']],
  ['pashan','Pashan',18.5400,73.7930,'city',['pashan','पाषाण']],
  ['baner','Baner',18.5590,73.7790,'city',['baner','बाणेर']],
  ['balewadi','Balewadi',18.5760,73.7790,'city',['balewadi','बालेवाडी']],
  ['aundh','Aundh',18.5600,73.8080,'city',['aundh','औंध']],
  ['khadki','Khadki',18.5640,73.8510,'city',['khadki','kirkee','खडकी']],
  ['bopodi','Bopodi',18.5720,73.8330,'city',['bopodi','बोपोडी']],
  ['swargate','Swargate',18.5010,73.8580,'city',['swargate','स्वारगेट']],
  ['peth','Old city peths',18.5150,73.8560,'city',['kasba peth','budhwar peth','shukrawar peth','raviwar peth','sadashiv peth','narayan peth','shaniwar peth','nana peth','bhavani peth','ganesh peth','somwar peth','mangalwar peth','rasta peth','ganj peth','guruwar peth','faraskhana','khadak police','vishrambaug','laxmi road','mandai','कसबा पेठ','बुधवार पेठ','शुक्रवार पेठ','रविवार पेठ','सदाशिव पेठ','नारायण पेठ','नाना पेठ','भवानी पेठ','गणेश पेठ','फरासखाना','खडक पोलीस','विश्रामबाग']],
  ['station','Pune Station / Bund Garden',18.5290,73.8740,'city',['pune station','pune railway station','bund garden','bundgarden','sassoon','पुणे स्टेशन','बंडगार्डन','ससून']],
  ['parvati','Parvati / Sahakarnagar',18.4900,73.8480,'city',['parvati','sahakarnagar','sahakar nagar','dattawadi','पर्वती','सहकारनगर','दत्तवाडी']],
  ['bibwewadi','Bibwewadi',18.4690,73.8640,'city',['bibwewadi','bibvewadi','बिबवेवाडी']],
  ['marketyard','Market Yard',18.4860,73.8680,'city',['market yard','marketyard','gultekdi','मार्केट यार्ड','गुलटेकडी']],
  ['dhankawadi','Dhankawadi',18.4640,73.8530,'city',['dhankawadi','धनकवडी']],
  ['bharati','Bharati Vidyapeeth',18.4575,73.8560,'city',['bharati vidyapeeth','भारती विद्यापीठ']],
  ['katraj','Katraj',18.4483,73.8578,'city',['katraj','कात्रज']],
  ['ambegaon','Ambegaon / Narhe',18.4480,73.8300,'city',['ambegaon','narhe','आंबेगाव','नऱ्हे']],
  ['sinhgadroad','Sinhgad Road',18.4680,73.8200,'city',['sinhgad road','sinhagad road','vadgaon budruk','dhayari','anandnagar','nanded city','सिंहगड रस्ता','सिंहगड रोड','धायरी','वडगाव बुद्रुक']],
  ['kondhwa','Kondhwa',18.4636,73.8927,'city',['kondhwa','yewalewadi','कोंढवा','येवलेवाडी']],
  ['nibm','NIBM / Undri',18.4560,73.9010,'city',['nibm','undri','pisoli','mohammadwadi','mohammedwadi','उंड्री']],
  ['wanowrie','Wanowrie',18.4860,73.8990,'city',['wanowrie','wanawadi','wanwadi','वानवडी']],
  ['hadapsar','Hadapsar',18.5089,73.9260,'city',['hadapsar','magarpatta','हडपसर','मगरपट्टा']],
  ['manjri','Manjri / Fursungi',18.4900,73.9700,'city',['manjri','fursungi','uruli devachi','मांजरी','फुरसुंगी']],
  ['lonikalbhor','Loni Kalbhor',18.4850,74.0250,'city',['loni kalbhor','loni-kalbhor','uruli kanchan','लोणी काळभोर','उरुळी कांचन']],
  ['uttamnagar','Uttamnagar / Shivane',18.4640,73.7700,'city',['uttamnagar','uttam nagar','shivane','khadakwasla','उत्तमनगर','शिवणे','खडकवासला']],
  ['sus','Sus / Mahalunge',18.5600,73.7500,'city',['sus road','sus gaon','mahalunge','म्हाळुंगे']],
  // Pimpri-Chinchwad
  ['pimpri','Pimpri',18.6298,73.7997,'pcmc',['pimpri','पिंपरी']],
  ['chinchwad','Chinchwad',18.6280,73.7820,'pcmc',['chinchwad','चिंचवड']],
  ['nigdi','Nigdi / Akurdi',18.6520,73.7700,'pcmc',['nigdi','akurdi','pradhikaran','निगडी','आकुर्डी']],
  ['bhosari','Bhosari',18.6260,73.8500,'pcmc',['bhosari','भोसरी']],
  ['hinjewadi','Hinjewadi',18.5913,73.7389,'pcmc',['hinjewadi','hinjawadi','हिंजवडी']],
  ['wakad','Wakad',18.5990,73.7620,'pcmc',['wakad','वाकड']],
  ['pimplesaudagar','Pimple Saudagar / Sangvi',18.5950,73.8000,'pcmc',['pimple saudagar','pimple gurav','pimple nilakh','sangvi','पिंपळे सौदागर','पिंपळे गुरव','सांगवी']],
  ['kalewadi','Kalewadi / Thergaon',18.6100,73.7750,'pcmc',['kalewadi','thergaon','rahatani','काळेवाडी','थेरगाव','रहाटणी']],
  ['ravet','Ravet / Dehu Road',18.6480,73.7400,'pcmc',['ravet','dehu road','dehuroad','kiwale','punawale','रावेत','देहूरोड']],
  ['chikhali','Chikhali / Moshi',18.6700,73.8300,'pcmc',['chikhali','chikhli','moshi','चिखली','मोशी']],
  ['dighi','Dighi / Alandi',18.6200,73.8750,'pcmc',['dighi','alandi','दिघी','आळंदी']],
  ['chakan','Chakan',18.7600,73.8630,'pcmc',['chakan','mahalunge midc','nighoje','khed taluka','चाकण']],
  ['talegaon','Talegaon Dabhade',18.7350,73.6760,'pcmc',['talegaon','तळेगाव']],
  // Pune district
  ['lonavala','Lonavala',18.7540,73.4060,'rural',['lonavala','lonavla','लोणावळा']],
  ['shikrapur','Shikrapur / Ranjangaon',18.6930,74.1380,'rural',['shikrapur','ranjangaon','शिक्रापूर','रांजणगाव']],
  ['baramati','Baramati',18.1520,74.5770,'rural',['baramati','बारामती']],
  ['daund','Daund',18.4630,74.5820,'rural',['daund','दौंड']],
  ['saswad','Saswad / Jejuri',18.3450,74.0300,'rural',['saswad','jejuri','सासवड','जेजुरी']],
].map(([id, name, lat, lon, r, alias]) => ({ id, name, lat, lon, r, alias }));

export const CATS = [
  { id: 'murder',    name: 'Murder',                 color: '#BC0006' },
  { id: 'women',     name: 'Crimes against women & children', color: '#C2410C' },
  { id: 'kidnap',    name: 'Kidnapping',             color: '#9333EA' },
  { id: 'extortion', name: 'Extortion',              color: '#7C2D12' },
  { id: 'robbery',   name: 'Robbery & snatching',    color: '#DB2777' },
  { id: 'burglary',  name: 'Burglary',               color: '#2563EB' },
  { id: 'drugs',     name: 'Drugs',                  color: '#059669' },
  { id: 'cyber',     name: 'Cyber & fraud',          color: '#0891B2' },
  { id: 'violence',  name: 'Assault & weapons',      color: '#EA580C' },
  { id: 'theft',     name: 'Theft',                  color: '#4F46E5' },
  { id: 'accident',  name: 'Road accident',          color: '#CA8A04' },
  { id: 'fire',      name: 'Fire',                   color: '#F59E0B' },
];

// Order matters: first match wins.
const RULES = [
  ['murder', /\b(murder(s|ed|er|ing)?)\b|खून|हत्या/i],
  ['accident',/\b(accident|hit[- ]and[- ]run|run over|mowed down|mows down|collision|collides?|collided|crash(es|ed)?|rams? into|rammed|overturn(s|ed)?|plunges?|knocked down|drunk[- ]driving)\b|अपघात/i],
  ['murder', /\b(murder(s|ed|er|ing)?|hacked to death|stabbed to death|beaten to death|strangled|strangulat\w+|bludgeon\w*|kills? (wife|husband|friend|father|mother|son|daughter|brother|man|woman|youth)|killed by|body found)\b|खून|हत्या/i],
  ['women', /\b(rape[ds]?|raping|gang[- ]?rape\w*|molest\w*|sexual(ly)? (assault|harass|abus)\w*|sexually|stalk(ed|ing|er)|dowry|outrag\w+ (her )?modesty|pocso|obscene|eve[- ]teasing|domestic violence|acid attack|minor girl|voyeur\w*)\b|बलात्कार|विनयभंग|लैंगिक|अत्याचार|पोक्सो|हुंडा|छेडछाड/i],
  ['kidnap', /\b(kidnap\w*|abduct\w*)\b|अपहरण/i],
  ['extortion', /\b(extort\w*|ransom|protection money)\b|खंडणी/i],
  ['robbery', /\b(robb(ed|ery|ers?|eries)|loot(ed|ing|s)?|heist|dacoit\w*|chain[- ]snatch\w*|snatch\w*|mugg(ed|ing)|at knife[- ]?point|at gun[- ]?point)\b|दरोडा|लूट|लुटले|जबरी चोरी|सोनसाखळी|हिसकाव/i],
  ['burglary', /\b(burglar\w*|burgl\w+|house[- ]?break\w*|break[- ]in|broke into|breaking into)\b|घरफोड/i],
  ['drugs', /\b(drugs?|mephedrone|ganja|cannabis|cocaine|heroin|charas|narcotics?|ndps|md worth|contraband)\b|गांजा|अमली पदार्थ|अंमली पदार्थ|मेफेड्रोन/i],
  ['cyber', /\b(cyber\w*|fraud\w*|cheat(ed|ing|s)|duped?|dupes|scam\w*|digital arrest|swindl\w+|ponzi|phishing|fake (call centre|police|officer)|embezzl\w+|misappropriat\w+)\b|फसवणूक|फसवणुक|सायबर|गंडा/i],
  ['violence', /\b(assault(ed|s|ing)?|attack(ed|s|ers?)?|stabb?(ed|ing|s)?|koyta|sickle|firing|fired (at|on|upon|shots?)|opens? fire|shot (at|dead)|gunshot|beaten (up|by|with|over)|thrash(ed|es|ing)|vandalis\w+|vandaliz\w+|rioting|clash(es|ed)?|brawl|pistols?|firearms?|sword|machete|gang ?war|mcoca|tadipaar|externed)\b|हल्ला|मारहाण|कोयता|कोयत्या|गोळीबार|तोडफोड|पिस्तूल|मोक्का/i],
  ['theft', /\b(theft|thefts|stolen|steal(s|ing)?|stole|thie(f|ves)|pickpocket\w*|shoplift\w*)\b|चोरी|चोरट/i],
  ['fire', /\b(fire breaks? out|fire broke out|caught fire|catches fire|blaze|gutted|fire brigade|major fire|massive fire|fire at|fire in|cylinder blast|explosion)\b|आग लाग|भीषण आग|आगीत|स्फोट/i],
];

// Headlines that match incident words but are not incidents.
const NOISE = /अजित पवार|विमान|\b(ajit pawar|plane crash|revamp|inaugurat\w+|tourism|leopard|movie|film|trailer|box office|cricket|ipl|match|wicket|web series|season \d|horoscope|recipe|review|stock|sensex|nifty|election|poll|manifesto|rally|budget|court (grants|rejects)|hc |high court|supreme court)\b/i;

const ELSEWHERE = /\b(mumbai|thane|navi mumbai|nagpur|nashik|chhatrapati sambhajinagar|aurangabad|kolhapur|solapur|satara|sangli|dharashiv|beed|jalna|parbhani|raigad|ratnagiri|palghar|gadchiroli|chandrapur|karjat|ahilyanagar|ahmednagar|jalgaon|latur|nanded|amravati|akola|delhi|bengaluru|bangalore|hyderabad|chennai|kolkata|goa|gujarat|uttar pradesh|bihar|kerala|punjab|rajasthan|pakistan|bangladesh|china)\b|मुंबई|नागपूर|नाशिक|कोल्हापूर|सोलापूर|सातारा|दिल्ली/i;
const PUNE = /\bpune\b|\bpimpri\b|\bpcmc\b|\bpmc\b|पुणे|पुण्यात|पिंपरी/i;

const ENT = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', rsquo: '’', lsquo: '‘', rdquo: '”', ldquo: '“', ndash: '–', mdash: '—', hellip: '…' };
export function decode(s) {
  return String(s || '')
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&([a-z]+);/gi, (m, n) => ENT[n.toLowerCase()] ?? m);
}
const strip = s => decode(decode(s)).replace(/<(script|style)[\s\S]*?<\/\1>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
const tag = (block, name) => {
  const m = block.match(new RegExp('<' + name + '(?:\\s[^>]*)?>([\\s\\S]*?)</' + name + '>', 'i'));
  return m ? m[1] : '';
};

export function parseFeed(xml) {
  const out = [];
  for (const m of String(xml).matchAll(/<item[\s>][\s\S]*?<\/item>/gi)) {
    const b = m[0];
    const title = strip(tag(b, 'title'));
    const link = strip(tag(b, 'link')) || strip(tag(b, 'guid'));
    const date = new Date(strip(tag(b, 'pubDate')));
    if (!title || !/^https?:\/\//.test(link) || isNaN(date)) continue;
    const text = strip(tag(b, 'description')) + ' ' + strip(tag(b, 'content:encoded'));
    out.push({ title, link: link.split('#')[0].split('?')[0], date, text });
  }
  return out;
}

export function classify(title, text) {
  const head = title + ' . ' + text.slice(0, 280);
  if (NOISE.test(title)) return null;
  for (const [id, re] of RULES) if (re.test(title)) return id;
  for (const [id, re] of RULES) if (re.test(head)) return id;
  return null;
}

const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const AREA_RE = AREAS.map(a => ({
  a,
  re: new RegExp(a.alias.map(x => /[a-z]/i.test(x) ? '\\b' + esc(x).replace(/ /g, '[ -]?') + '\\b' : esc(x)).join('|'), 'i'),
}));

// Earliest mention wins; the headline is searched before the body.
export function locate(title, text) {
  // "Pimpri-Chinchwad police" names the force, not the place.
  const clean = s => s.replace(/pimpri[- ]chinchwad|पिंपरी[- ]चिंचवड/gi, ' ');
  for (const src of [clean(title), clean(text.slice(0, 1500))]) {
    let best = null, pos = Infinity;
    for (const { a, re } of AREA_RE) {
      const m = re.exec(src);
      if (m && m.index < pos) { pos = m.index; best = a; }
    }
    if (best) return best.id;
  }
  return null;
}

const band = h => (h >= 6 && h < 12 ? 'morning' : h >= 12 && h < 17 ? 'afternoon' : h >= 17 && h < 21 ? 'evening' : 'night');

// Time of the incident as stated in the report. Returns {h, b}; both null when the report does not say.
export function whenOf(title, text) {
  const s = title + ' . ' + text.slice(0, 1200);
  const m = s.match(/\b(\d{1,2})(?:[:.](\d{2}))?\s*(a\.?m\.?|p\.?m\.?)(?![a-z])/i);
  if (m) {
    let h = +m[1] % 12;
    if (/^p/i.test(m[3])) h += 12;
    if (+m[1] >= 1 && +m[1] <= 12) return { h, b: band(h) };
  }
  if (/\b(night|midnight|late[- ]night|late at night|wee hours|early hours|at night|last night|overnight|night of)\b|मध्यरात्री|रात्री|पहाटे/i.test(s)) return { h: null, b: 'night' };
  if (/\b(evening)\b|सायंकाळी|संध्याकाळी/i.test(s)) return { h: null, b: 'evening' };
  if (/\b(afternoon|noon)\b|दुपारी/i.test(s)) return { h: null, b: 'afternoon' };
  if (/\b(morning)\b|सकाळी/i.test(s)) return { h: null, b: 'morning' };
  return { h: null, b: null };
}

// Readable paragraph text of an article page (used once per article to find the area and time; never stored).
export function pageText(html) {
  const body = String(html).replace(/<(script|style|noscript|header|footer|nav|aside)[\s\S]*?<\/\1>/gi, ' ');
  const meta = (body.match(/<meta[^>]+(?:name|property)=["'](?:description|og:description)["'][^>]*content=["']([^"']*)["']/i) || [])[1] || '';
  const ld = (String(html).match(/"articleBody"\s*:\s*"((?:[^"\\]|\\.)*)"/) || [])[1] || '';
  const paras = [...body.matchAll(/<p[\s>][\s\S]*?<\/p>/gi)].map(m => strip(m[0])).filter(p => p.length > 60).join(' ');
  return (strip(meta) + ' . ' + strip(ld.replace(/\\[nrt]/g, ' ').replace(/\\"/g, '"')) + ' . ' + paras).slice(0, 4000);
}

// Fill in area/time on a record from the article text, where the feed alone did not give them.
export function enrich(rec, text) {
  if (!rec.a) rec.a = locate('', text);
  if (!rec.b) { const w = whenOf('', text); rec.h = w.h; rec.b = w.b; }
  return rec;
}

export function hashId(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(36);
}

// One feed's XML -> incident records (only items that look like incidents in or around Pune).
export function extract(feed, xml) {
  const out = [];
  for (const it of parseFeed(xml)) {
    const c = classify(it.title, it.text);
    if (!c) continue;
    const a = locate(it.title, it.text);
    const head = it.title + ' ' + it.text.slice(0, 400);
    if (!a) {
      if (!feed.pune && !PUNE.test(head)) continue;       // general feed, no Pune signal
      const t = it.title.replace(/\bpune\s*[-–]\s*[a-z]+/gi, ' ');   // "Pune-Nagpur bus" is a route, not a place
      if (ELSEWHERE.test(it.title) && !PUNE.test(t)) continue; // headline is about another place
    }
    const w = whenOf(it.title, it.text);
    out.push({ id: hashId(it.link), t: it.title, u: it.link, s: feed.id, d: it.date.toISOString(), c, a, h: w.h, b: w.b });
  }
  return out;
}

export function merge(existing, incoming) {
  const seen = new Set(existing.map(x => x.id));
  const titles = new Set(existing.map(x => x.s + '|' + x.t));
  let added = 0;
  for (const r of incoming) {
    if (seen.has(r.id) || titles.has(r.s + '|' + r.t)) continue;
    seen.add(r.id); titles.add(r.s + '|' + r.t);
    existing.push(r); added++;
  }
  existing.sort((x, y) => (x.d < y.d ? 1 : -1));
  return added;
}
