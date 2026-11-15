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
  ['sus','Sus / Mahalunge',18.5600,73.7500,'city',['sus road','sus gaon','mhalunge','म्हाळुंगे']],
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
  ['chakan','Chakan',18.7600,73.8630,'pcmc',['chakan','mahalunge','nighoje','चाकण']],
  ['talegaon','Talegaon Dabhade',18.7350,73.6760,'pcmc',['talegaon','तळेगाव']],
  // Pune district
  ['lonavala','Lonavala / Maval',18.7540,73.4060,'rural',['lonavala','lonavla','kamshet','vadgaon maval','लोणावळा','कामशेत']],
  ['shikrapur','Shikrapur / Ranjangaon',18.6930,74.1380,'rural',['shikrapur','ranjangaon','शिक्रापूर','रांजणगाव']],
  ['shirur','Shirur',18.8270,74.3730,'rural',['shirur','nhavare','शिरूर','शिरुर','न्हावरे']],
  ['khed','Rajgurunagar / Khed',18.8540,73.8880,'rural',['rajgurunagar','khed taluka','khed police','राजगुरुनगर','राजगुरूनगर']],
  ['junnar','Junnar / Narayangaon',19.2000,73.8750,'rural',['junnar','narayangaon','manchar','जुन्नर','नारायणगाव','मंचर']],
  ['mulshi','Mulshi / Pirangut',18.5100,73.6800,'rural',['mulshi','pirangut','paud','मुळशी','पिरंगुट','पौड']],
  ['bhor','Bhor',18.1530,73.8450,'rural',['bhor','भोर']],
  ['velhe','Velhe / Rajgad',18.2950,73.6400,'rural',['velhe','rajgad','torna','pabe ghat','वेल्हे','राजगड','तोरणा','पाबे घाट']],
  ['baramati','Baramati',18.1520,74.5770,'rural',['baramati','बारामती']],
  ['indapur','Indapur',18.1150,75.0230,'rural',['indapur','इंदापूर']],
  ['daund','Daund',18.4630,74.5820,'rural',['daund','दौंड']],
  ['saswad','Saswad / Jejuri',18.3450,74.0300,'rural',['saswad','jejuri','purandar','सासवड','जेजुरी','पुरंदर']],
].map(([id, name, lat, lon, r, alias]) => ({ id, name, lat, lon, r, alias }));

export const CATS = [
  { id: 'murder',    name: 'Murder' },
  { id: 'women',     name: 'Crimes against women & children' },
  { id: 'kidnap',    name: 'Kidnapping' },
  { id: 'extortion', name: 'Extortion & blackmail' },
  { id: 'robbery',   name: 'Robbery & snatching' },
  { id: 'burglary',  name: 'Burglary' },
  { id: 'drugs',     name: 'Drugs' },
  { id: 'cyber',     name: 'Cyber & fraud' },
  { id: 'violence',  name: 'Assault & weapons' },
  { id: 'theft',     name: 'Theft' },
  { id: 'accident',  name: 'Road accident' },
  { id: 'fire',      name: 'Fire' },
];

export const RULES_VERSION = 2;

/* ------------------------------------------------------------------------------------------------
   Sorting rules, version 2.
   A word alone is not enough: "drug" appears in "Food and Drug Administration", "crash" in a website
   crash, "attack" in a political speech. So each type has (1) words that signal it, and (2) a guard:
   words that, when present, mean the signal is being used in another sense. The headline decides.
   The article summary may decide only when it also carries police/casualty language.
   ------------------------------------------------------------------------------------------------ */
const VEH = '(car|suv|bus|buses|truck|bike|biker|motorcycl\\w+|two[- ]wheeler|scooter|moped|tempo|tanker|container|dumper|trailer|rickshaw|auto|autorickshaw|vehicle|lorry|van|jeep|tractor|ambulance|pick[- ]?up|cab|taxi)';
const RULES = [
  ['murder', /\b(murder(s|ed|er|ing)?)\b|खून|हत्या/i, null],
  ['accident', new RegExp('\\b(accident|hit[- ]and[- ]run|run over|mowed down|mows down|collision|collides?|collided|rams? into|rammed|overturn(s|ed)?|plunges?|knocked down|drunk[- ]driv\\w+)\\b|अपघात|\\b' + VEH + '\\b[^.;:]{0,70}\\bcrash(es|ed)?\\b|\\bcrash(es|ed)?\\b[^.;:]{0,40}\\b' + VEH + '\\b', 'i'),
    /\b(online|website|site|server|app|portal|booking|system|market|stocks?|shares?|prices?)\b/i],
  ['murder', /\b(hacked to death|stabbed to death|beaten to death|shot dead|strangled|strangulat\w+|bludgeon\w*|killed (over|by|for|after|in (a )?(fight|dispute|quarrel|attack|brawl))|kills? (his |her )?(wife|husband|friend|father|mother|son|daughter|brother|sister|man|woman|youth|lover|neighbour|girlfriend|boyfriend)|body found|found murdered|chopp\w+ .{0,20}(to|into) pieces)\b/i, null],
  ['women', /\b(rape[ds]?|raping|gang[- ]?rape\w*|molest\w*|sexual(ly)? (assault|harass|abus|exploit)\w*|stalk(ed|ing|er)|dowry|outrag\w+ (her |the )?modesty|pocso|eve[- ]teasing|domestic violence|acid attack|voyeur\w*)\b|बलात्कार|विनयभंग|लैंगिक अत्याचार|लैंगिक छळ|पोक्सो|हुंडा|छेडछाड/i, null],
  ['kidnap', /\b(kidnap\w*|abduct\w*)\b|अपहरण/i, null],
  ['extortion', /\b(extort\w*|ransom|protection money|sextortion|blackmail\w*)\b|खंडणी/i, null],
  ['robbery', /\b(robb(ed|ery|ers?|eries|ing)|loot(ed|ing|s)?|heist|dacoit\w*|chain[- ]snatch\w*|snatch(es|ed|ing|ers?)?|mugg(ed|ing)|at knife[- ]?point|at gun[- ]?point)\b|दरोडा|लुटले|लुटून|जबरी चोरी|सोनसाखळी|हिसकाव/i, null],
  ['burglary', /\b(burglar\w*|burgl\w+|house[- ]?break\w*|break[- ]in|broke into|breaking into)\b|घरफोड/i, null],
  ['drugs', /\b(mephedrone|ganja|cannabis|cocaine|heroin|charas|hashish|opium|narcotics?|ndps|meth|contraband|peddlers?|drugs? (peddl\w+|racket|cartel|bust|haul|trafficking|smuggl\w+|seizure|seized|worth|party|den|syndicate|supplier|case)|(seiz\w+|smuggl\w+|peddl\w+|supply\w*|sell\w*|sold) (of )?drugs)\b|गांजा|अमली पदार्थ|अंमली पदार्थ|मेफेड्रोन|ड्रग्ज/i,
    /\b(food and drugs?|fda|drug[- ]free|de-?addiction|pharma\w*|medicines?|chemist|drug store|awareness)\b|अन्न व औषध/i],
  ['cyber', /\b(cyber ?(crime|fraud\w*|crook\w*|cheat\w*|scam\w*|thie\w+)|fraud(s|sters?)?|cheat(ed|ing|s)|duped?|dupes|scam(s|mers?|med)?|digital arrest|swindl\w+|ponzi|phishing|fake call cent(re|er)|embezzl\w+|misappropriat\w+|siphon\w+|loses? (rs|₹))\b|फसवणूक|फसवणुक|सायबर चोर|गंडा घात/i,
    /\b(warns?|warning|advisory|awareness|beware|cautions?|tips|fraudulent job offers|dues|auction|property tax)\b/i],
  ['violence', /\b(assault(ed|s|ing)?|attack(ed|s|ers?)?|stabb?(ed|ing|s)?|koyta|sickles?|firing|fired (at|on|upon|shots?)|opens? fire|shot at|gunshot|gunmen|beaten (up|by|with|over)|thrash(ed|es|ing)|vandalis\w+|vandaliz\w+|rioting|clash(es|ed)?|brawl|pistols?|firearms?|sword|machete|gang ?war|mcoca|tadipaar|externed|road rage|hurl(s|ed|ing)?)\b|हल्ला|मारहाण|कोयता|कोयत्या|गोळीबार|तोडफोड|पिस्तूल|मोक्का/i,
    /\b(slams?|hits? out|lash(es|ed)? out|verbal|jibe|dig at|criticis\w+|heart attack|cyber ?attack|leopard|stray dogs?|dog attack|bee attack|opposition|after .{0,30}(firing|attack) incident)\b|हल्लाबोल|टोला|टीका|निशाणा|हृदयविकार|बिबट्या/i],
  ['theft', /\b(theft|thefts|stolen|steal(s|ing)?|stole|thie(f|ves)|pickpocket\w*|shoplift\w*)\b|चोरी|चोरट/i, null],
  ['fire', /\b(fire breaks? out|fire broke out|caught fire|catches fire|blaze|gutted|major fire|massive fire|fire (at|in) (a |an |the )?\w+|cylinder blast|explosion)\b|आग लाग|भीषण आग|आगीत|स्फोट/i,
    /\b(under fire|fire sale|firing)\b/i],
];

// Headlines that use incident words but are not reports of an incident.
const NOISE = new RegExp([
  // entertainment, sport, markets
  '\\b(movie|film|trailer|box office|web series|actors?|actress|bollywood|co-star|celebrit\\w+|poses|ott|album|concert|cricket|ipl|wicket|marathon|run for unity|tournament|horoscope|recipe|sensex|nifty)\\b',
  // politics and statements
  '\\b(election|poll|manifesto|rally|budget|minister says|alleges|demands?|protest(s|ed|ers)?|morcha)\\b',
  // court stages, policy, aftermath, advisories, statistics
  '\\b(trial|bail|verdict|convict\\w*|sentenc\\w+|acquit\\w*|charge ?sheet\\w*|hearing|high court|supreme court|hc|plea)\\b',
  '\\b(months? after|years? after|compensation|ex[- ]gratia|free homes|to recruit|recruitment|helpline|campaign|special drive|data shows|statistics|survey|licen[cs]es?|food safety|revamp|inaugurat\\w+|tourism|plane crash|ajit pawar)\\b',
  'अजित पवार|विमान|युक्तीवाद|जामीन|हल्लाबोल|टोला|निवडणूक|मोर्चा',
].join('|'), 'i');

// Police / casualty language. A summary may assign a type only when this is present.
const CONTEXT = /\b(police|cops?|arrest\w*|held|booked|nabbed|detained|fir|case (has been |was |is )?registered|accused|complain\w+|crime branch|victim|injured|died|dead|hospitalis\w+|hospitaliz\w+)\b|पोलीस|पोलिस|अटक|गुन्हा|आरोपी|जखमी|मृत्यू/i;

const OTHER_EN = 'mumbai|thane|navi mumbai|kalamboli|panvel|kalyan|dombivli|vasai|virar|juhu|andheri|bandra|nagpur|nashik|chhatrapati sambhajinagar|sambhajinagar|aurangabad|karmad|kolhapur|solapur|satara|sangli|dharashiv|beed|jalna|parbhani|raigad|ratnagiri|palghar|gadchiroli|chandrapur|karjat|ahilyanagar|ahmednagar|jalgaon|latur|amravati|akola|belgaum|belagavi|delhi|bengaluru|bangalore|hyderabad|chennai|kolkata|goa|gujarat|uttar pradesh|bihar|kerala|punjab|rajasthan|karnataka|pakistan|bangladesh|china|dubai';
const OTHER_MR = 'मुंबई|ठाणे|नागपूर|नाशिक|संभाजीनगर|कोल्हापूर|सोलापूर|सातारा|सांगली|बेळगाव|दिल्ली|कर्नाटक';
const ELSEWHERE = new RegExp('\\b(' + OTHER_EN + ')\\b|' + OTHER_MR, 'i');
// The other place is where it happened: "Kalamboli hit-and-run: ...", "... near Karmad", "बेळगावमध्ये ..."
const HAPPENED_ELSEWHERE = new RegExp('^\\W*(' + OTHER_EN + ')\\b[^:]{0,30}:|\\b(in|at|near|on|off)\\s+(the\\s+)?(' + OTHER_EN + ')\\b|(' + OTHER_MR + ')(मध्ये|त|जवळ|येथे)', 'i');
const PUNE = /\bpune\b|\bpimpri\b|\bpcmc\b|\bpmc\b|पुणे|पुण्यात|पिंपरी/i;
const IN_PUNE = /\bin pune\b|\bpune (police|city|crime|station|airport|court|jewell\w+|school|college|techie|businessman)\b|पुण्यात(?!ील)|पुणे पोलिस/i;

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

const pick = s => { for (const [id, re, guard] of RULES) if (re.test(s) && !(guard && guard.test(s))) return id; return null; };

// Returns a type id, or null when the item is not a report of an incident.
export function classify(title, text = '') {
  if (NOISE.test(title)) return null;
  const c = pick(title);
  if (c) return c;
  // A guard that fires on the headline rules the item out, whatever the summary says.
  for (const [, re, guard] of RULES) if (guard && re.test(title) && guard.test(title)) return null;
  const sum = text.slice(0, 300);
  if (!sum || !CONTEXT.test(title + ' ' + sum)) return null;
  return pick(sum);
}

// False when the headline places the incident outside Pune district.
export function inPune(title, text = '') {
  const route = s => s.replace(/\bpune\s*[-–]\s*[a-z]+/gi, ' ');   // "Pune-Nagpur bus" is a route
  const t = route(title);
  if (HAPPENED_ELSEWHERE.test(t)) return false;
  if (ELSEWHERE.test(t) && !IN_PUNE.test(t)) return false;
  // Headline silent on place: let the opening of the article say it happened elsewhere.
  if (!IN_PUNE.test(t) && !locate(title) && HAPPENED_ELSEWHERE.test(route(text.slice(0, 300)))) return false;
  return true;
}

const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const AREA_RE = AREAS.map(a => ({
  a,
  src: a.alias.map(x => /[a-z]/i.test(x) ? '\\b' + esc(x).replace(/ /g, '[ -]?') + '\\b' : esc(x)).join('|'),
}));
// "Pimpri-Chinchwad police" names the force, not the place.
const cleanPlace = s => s.replace(/pimpri[- ]chinchwad|पिंपरी[- ]चिंचवड/gi, ' ');
const LIVES = /(residents? of|resident,|native of|natives of|hails? from|hailing from|lives? in|living in|based in|from|रा\.|राहणार|रहिवासी|येथील रहिवासी)\s*$/i;
const AT = /\b(in|at|near|on|outside|opposite|towards)\s+(the\s+)?$/i;

// Area of the incident. The headline wins. In the article body a place counts only when the wording
// ties it to the incident ("in Kothrud", "Kothrud police"), never when it is where someone lives.
export function locate(title, text = '') {
  const t = cleanPlace(title);
  let best = null, pos = Infinity;
  for (const { a, src } of AREA_RE) {
    const m = new RegExp(src, 'i').exec(t);
    if (m && m.index < pos) { pos = m.index; best = a; }
  }
  if (best) return best.id;

  const body = cleanPlace(text.slice(0, 2500));
  let score = 1;                                  // a bare mention (score 1) is not enough
  for (const { a, src } of AREA_RE) {
    for (const m of body.matchAll(new RegExp(src, 'gi'))) {
      const before = body.slice(Math.max(0, m.index - 28), m.index);
      const after = body.slice(m.index + m[0].length, m.index + m[0].length + 22);
      if (LIVES.test(before)) continue;
      const s = /^\s*(police|पोलीस|पोलिस)/i.test(after) ? 3 : (AT.test(before) || /^(त |मध्ये| येथे| परिसरात| भागात)/.test(after)) ? 2 : 1;
      if (s > score || (s === score && s > 1 && m.index < pos)) { score = s; pos = m.index; best = a; }
    }
  }
  return best ? best.id : null;
}

const band = h => (h >= 6 && h < 12 ? 'morning' : h >= 12 && h < 17 ? 'afternoon' : h >= 17 && h < 21 ? 'evening' : 'night');

// Time of the incident as stated in the report. Returns {h, b}; both null when the report does not say.
export function whenOf(title, text = '') {
  const s = title + ' . ' + text.slice(0, 1200);
  const m = s.match(/\b(\d{1,2})(?:[:.](\d{2}))?\s*(a\.?m\.?|p\.?m\.?)(?![a-z])/i);
  if (m && +m[1] >= 1 && +m[1] <= 12) {
    let h = +m[1] % 12;
    if (/^p/i.test(m[3])) h += 12;
    return { h, b: band(h) };
  }
  if (/\b(night|midnight|wee hours|early hours|overnight)\b|मध्यरात्री|रात्री|पहाटे/i.test(s)) return { h: null, b: 'night' };
  if (/\b(evening)\b|सायंकाळी|संध्याकाळी/i.test(s)) return { h: null, b: 'evening' };
  if (/\b(afternoon|noon|broad daylight)\b|दुपारी|दिवसाढवळ्या/i.test(s)) return { h: null, b: 'afternoon' };
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
  if (!rec.a) rec.a = locate(rec.t, text);
  if (!rec.b) { const w = whenOf(rec.t, text); rec.h = w.h; rec.b = w.b; }
  return rec;
}

// Re-check a record stored under older rules. Returns false when it should be removed.
// `text` is the article text if it could be read again, else ''.
export function recheck(rec, text) {
  if (!inPune(rec.t, text)) return false;
  const c = classify(rec.t, text);
  if (!c) return false;
  rec.c = c;
  if (text) {
    rec.a = locate(rec.t, text);
    const w = whenOf(rec.t, text); rec.h = w.h; rec.b = w.b;
  } else if (locate(rec.t)) rec.a = locate(rec.t);
  rec.r = RULES_VERSION;
  return true;
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
    if (!c || !inPune(it.title, it.text)) continue;
    const a = locate(it.title, it.text);
    if (!a && !feed.pune && !PUNE.test(it.title + ' ' + it.text.slice(0, 400))) continue;   // general feed, no Pune signal
    const w = whenOf(it.title, it.text);
    out.push({ id: hashId(it.link), t: it.title, u: it.link, s: feed.id, d: it.date.toISOString(), c, a, h: w.h, b: w.b, r: RULES_VERSION });
  }
  return out;
}

export function merge(existing, incoming, rejected = new Set()) {
  const seen = new Set(existing.map(x => x.id));
  const titles = new Set(existing.map(x => x.s + '|' + x.t));
  let added = 0;
  for (const r of incoming) {
    if (seen.has(r.id) || rejected.has(r.id) || titles.has(r.s + '|' + r.t)) continue;
    seen.add(r.id); titles.add(r.s + '|' + r.t);
    existing.push(r); added++;
  }
  existing.sort((x, y) => (x.d < y.d ? 1 : -1));
  return added;
}

/* One real incident is often reported by several papers, sometimes under different labels and a day apart.
   Reports in the same area are counted as one incident when they are the same type on the same day, or
   when they are related types within two days and their headlines share a distinctive number or words. */
const FAMILY = { robbery: 'property', burglary: 'property', theft: 'property', murder: 'person', violence: 'person', kidnap: 'person', extortion: 'person' };
const STOP = new Set('police arrested arrest accused registered against people persons student worker incident station attack attacked killed injured maharashtra'.split(' '));
const tokens = t => {
  const s = t.replace(/[०-९]/g, d => '०१२३४५६७८९'.indexOf(d)).toLowerCase();
  const nums = (s.match(/\d[\d,]*/g) || []).map(n => n.replace(/,/g, '')).filter(n => n.length >= 3 && !/^20\d\d$/.test(n));
  const words = (s.match(/[a-z]{6,}/g) || []).filter(w => !STOP.has(w));
  return { nums: new Set(nums), words: new Set(words) };
};
const istDay = d => new Date(new Date(d).getTime() + 19800000).toISOString().slice(0, 10);

export function groupEvents(items) {
  const events = [];
  const byArea = {};
  for (const r of [...items].sort((x, y) => (x.d < y.d ? -1 : 1))) {
    const tk = tokens(r.t);
    let ev = null;
    if (r.a) {
      for (const e of byArea[r.a] || []) {
        if (Math.abs(new Date(r.d) - new Date(e.last)) > 48 * 3600e3) continue;
        const sameDay = e.c === r.c && e.days.has(istDay(r.d));
        const fam = e.c === r.c || (FAMILY[e.c] && FAMILY[e.c] === FAMILY[r.c]);
        const shared = [...tk.nums].some(n => e.nums.has(n)) || [...tk.words].filter(w => e.words.has(w)).length >= 2;
        if (sameDay || (fam && shared)) { ev = e; break; }
      }
    }
    if (!ev) {
      ev = { c: r.c, a: r.a, d: r.d, last: r.d, h: null, b: null, reports: [], days: new Set(), nums: new Set(), words: new Set() };
      events.push(ev);
      if (r.a) (byArea[r.a] = byArea[r.a] || []).push(ev);
    }
    ev.reports.push(r); ev.last = r.d; ev.days.add(istDay(r.d));
    tk.nums.forEach(n => ev.nums.add(n)); tk.words.forEach(w => ev.words.add(w));
    if (!ev.b && r.b) { ev.b = r.b; ev.h = r.h; }
  }
  return events;
}
