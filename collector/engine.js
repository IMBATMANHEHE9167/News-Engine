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
  // Marathi dailies without feeds: read from their article indexes.
  //   newsmap = index carries headlines; urlmap = addresses only, so each candidate page is read for its headline.
  //   path    = the paper's Pune / Pimpri-Chinchwad section.
  { id: 'lks',  name: 'Loksatta',         url: 'https://www.loksatta.com/news-sitemap.xml', kind: 'newsmap', path: /loksatta\.com\/(pune|pimpri-chinchwad)\//i },
  { id: 'pud',  name: 'Pudhari',          url: 'https://pudhari.news/news_sitemap.xml', kind: 'newsmap', path: /pudhari\.news\/maharashtra\/(pune|pimpri-chinchwad)\//i },
  { id: 'lkm',  name: 'Lokmat',           url: 'https://www.lokmat.com/sitemap.xml', kind: 'urlmap', path: /lokmat\.com\/(pune|pimpri-chinchwad)\//i },
  { id: 'skl',  name: 'Sakal',            url: 'https://www.esakal.com/sitemap/sitemap-daily-{date}.xml', kind: 'urlmap', daily: true, path: /esakal\.com\/(pune|pimpri-chinchwad)\//i },
];

// Area list. Coordinates are approximate locality centres (area-level only, never an incident spot).
// r: 'city' = Pune City Police area, 'pcmc' = Pimpri-Chinchwad, 'rural' = Pune district outside both.
export const AREAS = [
  ['shivajinagar','Shivajinagar',18.5308,73.8475,'city',['shivajinagar','shivaji nagar','शिवाजीनगर']],
  ['deccan','Deccan / FC Road',18.5180,73.8410,'city',['deccan','fc road','fergusson college road','jm road','jangli maharaj road','डेक्कन']],
  ['camp','Camp',18.5110,73.8800,'city',['pune camp','camp area','mg road','lashkar police','cantonment','लष्कर पोलीस','लष्कर पोलिस','कॅम्प परिसर']],
  ['kp','Koregaon Park',18.5362,73.8939,'city',['koregaon park','कोरेगाव पार्क']],
  ['mundhwa','Mundhwa',18.5320,73.9300,'city',['mundhwa','मुंढवा','मुंढव्या']],
  ['yerawada','Yerawada',18.5510,73.8800,'city',['yerawada','yerwada','येरवडा','येरवड्या']],
  ['kharadi','Kharadi',18.5510,73.9430,'city',['kharadi','खराडी']],
  ['chandannagar','Chandan Nagar',18.5610,73.9330,'city',['chandan nagar','chandannagar','चंदननगर']],
  ['vimannagar','Viman Nagar',18.5679,73.9143,'city',['viman nagar','vimannagar','vimantal','विमाननगर','विमानतळ']],
  ['lohegaon','Lohegaon',18.5960,73.9200,'city',['lohegaon','लोहगाव']],
  ['vishrantwadi','Vishrantwadi',18.5770,73.8780,'city',['vishrantwadi','विश्रांतवाडी']],
  ['dhanori','Dhanori',18.5950,73.8960,'city',['dhanori','धानोरी']],
  ['wagholi','Wagholi',18.5800,73.9800,'city',['wagholi','lonikand','loni kand','वाघोली','लोणीकंद']],
  ['kothrud','Kothrud',18.5074,73.8077,'city',['kothrud','कोथरूड','कोथरुड']],
  ['karvenagar','Karve Nagar',18.4900,73.8200,'city',['karve nagar','karvenagar','karve road','कर्वेनगर']],
  ['erandwane','Erandwane',18.5100,73.8300,'city',['erandwane','erandwana','एरंडवणे']],
  ['warje','Warje',18.4810,73.8000,'city',['warje','वारजे','वारज्या']],
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
  ['kondhwa','Kondhwa',18.4636,73.8927,'city',['kondhwa','yewalewadi','कोंढवा','कोंढव्या','येवलेवाडी']],
  ['nibm','NIBM / Undri',18.4560,73.9010,'city',['nibm','undri','pisoli','mohammadwadi','mohammedwadi','उंड्री']],
  ['wanowrie','Wanowrie',18.4860,73.8990,'city',['wanowrie','wanawadi','wanwadi','वानवडी']],
  ['hadapsar','Hadapsar',18.5089,73.9260,'city',['hadapsar','magarpatta','हडपसर','मगरपट्टा']],
  ['manjri','Manjri / Fursungi',18.4900,73.9700,'city',['manjri','fursungi','uruli devachi','मांजरी बुद्रुक','मांजरी खुर्द','मांजरी परिसर','फुरसुंगी']],
  ['lonikalbhor','Loni Kalbhor',18.4850,74.0250,'city',['loni kalbhor','loni-kalbhor','uruli kanchan','लोणी काळभोर','उरुळी कांचन']],
  ['uttamnagar','Uttamnagar / Shivane',18.4640,73.7700,'city',['uttamnagar','uttam nagar','shivane','khadakwasla','उत्तमनगर','शिवणे','खडकवासला','खडकवासल्या']],
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
  ['lonavala','Lonavala / Maval',18.7540,73.4060,'rural',['lonavala','lonavla','kamshet','vadgaon maval','लोणावळा','लोणावळ्या','कामशेत']],
  ['shikrapur','Shikrapur / Ranjangaon',18.6930,74.1380,'rural',['shikrapur','ranjangaon','शिक्रापूर','रांजणगाव']],
  ['shirur','Shirur',18.8270,74.3730,'rural',['shirur','nhavare','शिरूर','शिरुर','न्हावरे']],
  ['khed','Rajgurunagar / Khed',18.8540,73.8880,'rural',['rajgurunagar','khed taluka','khed police','राजगुरुनगर','राजगुरूनगर']],
  ['junnar','Junnar / Narayangaon',19.2000,73.8750,'rural',['junnar','narayangaon','manchar','जुन्नर','नारायणगाव','मंचर']],
  ['mulshi','Mulshi / Pirangut',18.5100,73.6800,'rural',['mulshi','pirangut','paud','मुळशी','पिरंगुट','पौड']],
  ['bhor','Bhor',18.1530,73.8450,'rural',['bhor','भोर तालुक','भोर पोलीस','भोर पोलिस','भोरमध्ये','भोर येथे']],
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

export const RULES_VERSION = 5;

/* ------------------------------------------------------------------------------------------------
   Sorting rules, version 3 (English and Marathi).
   A word alone is not enough: "drug" appears in "Food and Drug Administration", "crash" in a website
   crash, "attack" in a political speech, "हत्या" inside "आत्महत्या". So each type has (1) words that
   signal it, and (2) a guard: words that, when present, mean the signal is used in another sense.
   The headline decides. The article summary may decide only when it also carries police/casualty
   language.
   ------------------------------------------------------------------------------------------------ */

// Compounds that contain an incident word but mean something else. Removed before matching.
const FIGURATIVE = /आत्महत्य\S*|टांगती तलवार|घटस्फोट\S*|गांधीहत्य\S*|मतचोरी|वोट ?चोरी|मतांची चोरी|करचोरी|वीज ?चोरी|पाणी ?चोरी|गौप्यस्फोट|आगपाखड|हल्लाबोल|शाब्दिक हल्ल\S*|जीवन संपव\S*|लोकसंख्येचा स्फोट|heart attack|panic attack|cyber ?attack|under fire|fire sale|vote theft|daylight robbery/gi;
const norm = s => String(s).replace(FIGURATIVE, ' ');

const VEH = '(car|suv|bus|buses|truck|bike|biker|motorcycl\\w+|two[- ]wheeler|scooter|moped|tempo|tanker|container|dumper|trailer|rickshaw|auto|autorickshaw|vehicle|lorry|van|jeep|tractor|ambulance|pick[- ]?up|cab|taxi)';
const WOMAN_MR = '(महिले|महिला|मुली|मुलगी|तरुणी|युवती|अल्पवयीन|विद्यार्थिनी|बालिके|चिमुकली|विवाहिते)';
const RULES = [
  ['murder', /\b(murder(s|ed|er|ing)?)\b|खून|खुना|हत्या|हत्ये/i, null],
  ['accident', new RegExp('\\b(accident|hit[- ]and[- ]run|run over|mowed down|mows down|collision|collides?|collided|rams? into|rammed|overturn(s|ed)?|plunges?|knocked down|drunk[- ]driv\\w+)\\b|अपघात|हिट अँड रन|चिरडले|चिरडून|भरधाव|\\b' + VEH + '\\b[^.;:]{0,70}\\bcrash(es|ed)?\\b|\\bcrash(es|ed)?\\b[^.;:]{0,40}\\b' + VEH + '\\b', 'i'),
    /\b(online|website|site|server|app|portal|booking|system|market|stocks?|shares?|prices?|safety|awareness|helmet|leopards?)\b|जनजागृती|सुरक्षा सप्ताह|प्रतीक्षा|घटले|धोका|निमंत्रण|बिबट्या/i],
  ['murder', /\b(hacked to death|stabbed to death|beaten to death|shot dead|strangled|strangulat\w+|bludgeon\w*|killed (over|by|for|after|in (a )?(fight|dispute|quarrel|attack|brawl))|kills? (his |her )?(wife|husband|friend|father|mother|son|daughter|brother|sister|man|woman|youth|lover|neighbour|girlfriend|boyfriend)|body found|found murdered|chopp\w+ .{0,20}(to|into) pieces)\b|ठार मारले|ठार केले|गळा (दाबून|चिरून|आवळून)|भोसकून|निर्घृण/i, null],
  ['women', new RegExp('\\b(rape[ds]?|raping|gang[- ]?rape\\w*|molest\\w*|sexual(ly)? (assault|harass|abus|exploit)\\w*|stalk(ed|ing|er)|dowry|outrag\\w+ (her |the )?modesty|pocso|eve[- ]teasing|domestic violence|acid attack|voyeur\\w*)\\b|बलात्कार|विनयभंग|लैंगिक अत्याचार|लैंगिक छळ|लैंगिक शोषण|पोक्सो|पॉक्सो|हुंडा|हुंड्या|छेडछाड|छेड काढ|' + WOMAN_MR + '[^.।]{0,40}अत्याचार|अत्याचार[^.।]{0,40}' + WOMAN_MR, 'i'), null],
  ['kidnap', /\b(kidnap\w*|abduct\w*)\b|अपहरण/i, null],
  ['extortion', /\b(extort\w*|ransom|protection money|sextortion|blackmail\w*)\b|खंडणी|ब्लॅकमेल/i, null],
  ['robbery', /\b(robb(ed|ery|ers?|eries|ing)|loot(ed|ing|s)?|heist|dacoit\w*|chain[- ]snatch\w*|snatch(es|ed|ing|ers?)?|mugg(ed|ing)|at knife[- ]?point|at gun[- ]?point)\b|दरोडा|दरोड्या|लुटले|लुटून|लूटमार|लुटमार|जबरी चोरी|सोनसाखळी|मंगळसूत्र|हिसकाव|धाक दाखव/i,
    /\b(loot the|looting (public|farmers|customers)|scam|fraud\w*|online|cyber)\b|फसवणूक|फसवणुक|गंडा|सायबर|ऑनलाइन|ग्राहकांची लूट|आर्थिक लूट|जनतेची लूट|शेतकऱ्यांची लूट/i],
  ['burglary', /\b(burglar\w*|burgl\w+|house[- ]?break\w*|break[- ]in|broke into|breaking into)\b|घरफोड|(सदनिका|फ्लॅट|घरे|घर|दुकाने|दुकान|बंगला|बंगले)\s*फोड|कुलूप तोडून[^.।]{0,50}(चोरी|लंपास|ऐवज)|कडीकोयंडा/i, null],
  ['drugs', /\b(mephedrone|ganja|cannabis|cocaine|heroin|charas|hashish|opium|narcotics?|ndps|meth|contraband|peddlers?|drugs? (peddl\w+|racket|cartel|bust|haul|trafficking|smuggl\w+|seizure|seized|worth|party|den|syndicate|supplier|case)|(seiz\w+|smuggl\w+|peddl\w+|supply\w*|sell\w*|sold) (of )?drugs)\b|गांजा|गांजाची|अमली पदार्थ|अंमली पदार्थ|मेफेड्रोन|ड्रग्ज|ड्रग्स|एमडी ड्रग|चरस|अफू|कोकेन/i,
    /\b(food and drugs?|fda|drug[- ]free|de-?addiction|pharma\w*|medicines?|chemist|drug store|awareness)\b|अन्न व औषध|व्यसनमुक्ती|जनजागृती/i],
  ['cyber', /\b(cyber ?(crime|fraud\w*|crook\w*|cheat\w*|scam\w*|thie\w+)|fraud(s|sters?)?|cheat(ed|ing|s)|duped?|dupes|scam(s|mers?|med)?|digital arrest|swindl\w+|ponzi|phishing|fake call cent(re|er)|embezzl\w+|misappropriat\w+|siphon\w+|loses? (rs|₹))\b|फसवणूक|फसवणुक|फसवणुकी|फसवले|गंडा|सायबर चोर|सायबर भामट|डिजिटल अरेस्ट|अपहार/i,
    /\b(warns?|warning|advisory|awareness|beware|cautions?|tips|fraudulent job offers|dues|auction|property tax|voter|voters|election|poll)\b|सावध|आवाहन|जनजागृती|इशारा|मतदार|भरती|होऊ नये|स्पष्टीकरण|पारदर्शक|सावट|पार्श्वभूमीवर/i],
  ['violence', /\b(assault(ed|s|ing)?|attack(ed|s|ers?)?|stabb?(ed|ing|s)?|koyta|sickles?|firing|fired (at|on|upon|shots?)|opens? fire|shot at|gunshot|gunmen|beaten (up|by|with|over)|thrash(ed|es|ing)|vandalis\w+|vandaliz\w+|rioting|clash(es|ed)?|brawl|pistols?|firearms?|sword|machete|gang ?war|mcoca|tadipaar|externed|road rage|hurl(s|ed|ing)?)\b|हल्ला|हल्ल्या|मारहाण|कोयता|कोयत्या|गोळीबार|तोडफोड|पिस्तूल|पिस्तुल|मोक्का|चाकूने|तलवार|वार केले|वार करून|(गटांत|गटात|टोळक्या\S*|तरुणां\S*|गुंडां\S*) राडा|हाणामारी|दगडफेक|तडीपार|दहशत माजव|अग्निशस्त्र|काडतुस|गावठी कट्ट|चॉपर|कुऱ्हाड/i,
    /\b(slams?|hits? out|lash(es|ed)? out|verbal|jibe|dig at|criticis\w+|leopards?|stray dogs?|dogs?|rabid|bees?|monkeys?|tigers?|opposition|devotees|after .{0,30}(firing|attack) incident)\b|टोला|टीका|टीके|निशाणा|हृदयविकार|बिबट्या|बिबट्याचा|कुत्र्य|मधमाश|राजकीय|माकड|वाघा|वाघाची|गव्या|हत्तीच्या|अस्वल/i],
  ['theft', /\b(theft|thefts|stolen|steal(s|ing)?|stole|thie(f|ves)|pickpocket\w*|shoplift\w*)\b|घेऊन पसार|लांबवले|लांबविले|डल्ला|चोरी|चोऱ्या|चोरट|चोरले|चोरून|चोरां|चोराला|चोर(?![ऀ-ॿ])|लंपास/i, /चोरी नाही|पाणी|वीज/i],
  ['fire', /\b(fire breaks? out|fire broke out|caught fire|catches fire|blaze|gutted|major fire|massive fire|fire (at|in) (a |an |the )?\w+|cylinder blast|explosion)\b|आग लाग|भीषण आग|आगीत|आगीच्या|आग भडक|जळून खाक|स्फोट/i,
    /\b(firing|fire safety|fire audit|firecrackers?)\b|अग्निसुरक्षा|फटाके|फटाक्या/i],
];

// Headlines that use incident words but are not reports of an incident.
const NOISE = new RegExp([
  // entertainment, sport, markets
  '\\b(viral video|movie|film|trailer|box office|web series|actors?|actress|bollywood|co-star|celebrit\\w+|poses|ott|album|concert|cricket|ipl|wicket|marathon|run for unity|tournament|cup|football|tennis|horoscope|recipe|sensex|nifty|poetry|lit fest)\\b',
  // politics and statements
  '\\b(election|poll|manifesto|rally|budget|minister says|alleges|demands?|protest(s|ed|ers)?|morcha|remembrance|statue)\\b',
  // court stages, policy, aftermath, advisories, statistics
  '\\b(trial|bail|verdict|convict\\w*|sentenc\\w+|acquit\\w*|charge ?sheet\\w*|hearing|high court|supreme court|hc|plea|life imprisonment)\\b',
  '\\b(months? after|years? after|compensation|ex[- ]gratia|free (homes|flats)|to recruit|recruitment|helpline|campaign|special drive|data shows|statistics|survey|licen[cs]es?|food safety|revamp|inaugurat\\w+|tourism|plane crash|ajit pawar|workshop|meeting|todays latest)\\b',
  'अजित पवार|विमान|मोफत|घरांचा आधार|मदत जाहीर|भरपाई|खटला|खटल्या|फाशी|खेळाडू|अंत्यसंस्कार|पडसाद|सवाल|अभिनेत्|आकडेवारी|नेमके चित्र|सत्कार|युक्तीवाद|युक्तिवाद|जामीन|हल्लाबोल|टोला|निवडणूक|निवडणुक|मोर्चा|आंदोलन|उपोषण|जन्मठेप|सक्तमजुरी|शिक्षा सुनाव|सुनावणी|न्यायालया|हायकोर्ट|उच्च न्यायालय|सर्वोच्च न्यायालय|नुकसानभरपाई|जनजागृती|चित्रपट|अभिनेत्री|अभिनेता|क्रिकेट|स्पर्धा|पुण्यतिथी|जयंती|अधिवेशन',
].join('|'), 'i');

// Police / casualty language. A summary may assign a type only when this is present.
const CONTEXT = /\b(police|cops?|arrest\w*|held|booked|nabbed|detained|fir|case (has been |was |is )?registered|accused|complain\w+|crime branch|victim|injured|died|dead|hospitalis\w+|hospitaliz\w+)\b|पोलीस|पोलिस|अटक|गुन्हा|गुन्हे|आरोपी|जखमी|मृत्यू|ताब्यात|जेरबंद|गजाआड|ठार/i;

// Pune roads and highways named after other cities. Stripped before asking "did this happen elsewhere?".
const ROADS = /(पोलीस|पोलिस)\s*ठाण\S*|\b(pune|mumbai)\s*[-–]\s*[a-z]+( (highway|expressway|road))?|\bpune (nashik|solapur|satara|nagar|ahmednagar|nagpur|mumbai|bangalore|bengaluru|kolhapur)\b( (highway|expressway|road|travels|bus))?|\b(satara|solapur|nagar|ahmednagar|nashik|mumbai|bangalore|bengaluru|paud|saswad|alandi|sinhgad) (road|highway|phata)\b|सातारा (रस्ता|रस्त्या\S*|रोड)|सोलापूर (रस्ता|रस्त्या\S*|रोड)|नगर (रस्ता|रस्त्या\S*|रोड)|नाशिक फाटा|मुंबई[- ]पुणे|पुणे[- ]मुंबई|पुणे[- ](सोलापूर|सातारा|नाशिक|नगर|बंगळुरू|बेंगळुरू)\s?(महामार्ग\S*|रस्ता|रस्त्या\S*|रोड)?|मुंबई[- ]बंगळुरू/gi;
const OTHER_EN = 'mumbai|thane|navi mumbai|kalamboli|panvel|kalyan|dombivli|ulhasnagar|vasai|virar|juhu|andheri|bandra|nagpur|nashik|malegaon|chhatrapati sambhajinagar|sambhajinagar|aurangabad|karmad|kolhapur|ichalkaranji|solapur|barshi|sangola|mangalvedha|pandharpur|satara|karad|sangli|miraj|dharashiv|beed|jalna|parbhani|hingoli|raigad|ratnagiri|sindhudurg|palghar|gadchiroli|chandrapur|bhandara|gondia|wardha|yavatmal|buldhana|washim|dhule|nandurbar|karjat|ahilyanagar|ahmednagar|sangamner|shirdi|parner|jalgaon|latur|amravati|akola|belgaum|belagavi|delhi|bengaluru|bangalore|hyderabad|chennai|kolkata|goa|gujarat|uttar pradesh|bihar|kerala|punjab|rajasthan|karnataka|pakistan|bangladesh|china|dubai';
const OTHER_MR = 'मुंबई|ठाणे|झारखंड|बिहार|उत्तर प्रदेश|गुजरात|राजस्थान|मध्य प्रदेश|केरळ|पंजाब|हरियाणा|तेलंगण|गोवा|गोव्या|अमेरिके|नेरुळ|नालासोपार|गोरेगाव|भिवंडी|अंबरनाथ|बदलापूर|नागपूर|नागपुर|नाशिक|मालेगाव|संभाजीनगर|कोल्हापूर|कोल्हापुर|इचलकरंजी|सोलापूर|सोलापुर|बार्शी|सांगोला|पंढरपूर|सातारा|साताऱ्या|कराड|सांगली|मिरज|धाराशिव|बीड|जालना|परभणी|हिंगोली|रायगड|रत्नागिरी|सिंधुदुर्ग|पालघर|गडचिरोली|चंद्रपूर|भंडारा|गोंदिया|वर्धा|यवतमाळ|बुलढाणा|वाशीम|धुळे|नंदुरबार|अहिल्यानगर|अहमदनगर|संगमनेर|शिर्डी|जळगाव|लातूर|नांदेड|अमरावती|अकोला|बेळगाव|दिल्ली|कर्नाटक|कल्याण|डोंबिवली|उल्हासनगर|पनवेल|वसई|विरार';
const ELSEWHERE = new RegExp('\\b(' + OTHER_EN + ')\\b|' + OTHER_MR, 'i');
// The other place is where it happened: "Kalamboli hit-and-run: ...", "... near Karmad", "बेळगावमध्ये ..."
const HAPPENED_ELSEWHERE = new RegExp('^\\W*(' + OTHER_EN + ')\\b[^:]{0,30}:|\\b(in|at|near|on|off)\\s+(the\\s+)?(' + OTHER_EN + ')\\b|(' + OTHER_MR + ')(मध्ये|मधील|त |तील|जवळ|येथे|येथील| जिल्ह)', 'i');
const PUNE = /\bpune\b|\bpimpri\b|\bpcmc\b|\bpmc\b|पुणे|पुण्या|पिंपरी/i;
const IN_PUNE = /^\W*pune\b|^\W*(पुणे|पिंपरी)|\bin pune\b|\bpune (police|city|crime|station|airport|court|jewell\w+|school|college|techie|businessman)\b|पुण्यात(?!ील)|पुणे पोलिस|पुणे पोलीस|पुणे शहरात/i;

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

// A newspaper's article index (sitemap). Entries may carry a headline (news sitemaps) or only a URL.
export function parseSitemap(xml) {
  const out = [];
  for (const m of String(xml).matchAll(/<url>[\s\S]*?<\/url>/gi)) {
    const b = m[0];
    const link = strip(tag(b, 'loc'));
    if (!/^https?:\/\//.test(link)) continue;
    const date = new Date(strip(tag(b, 'news:publication_date')) || strip(tag(b, 'lastmod')));
    out.push({ title: strip(tag(b, 'news:title')), link: link.split('#')[0].split('?')[0], date: isNaN(date) ? null : date, text: '' });
  }
  return out;
}

// The English words in an article address, e.g. ".../pune/four-accused-arrested-for-theft-pjp78" -> "four accused arrested for theft".
export function slugTitle(url) {
  const seg = decodeURIComponent(url.replace(/\/+$/, '').split('/').pop() || '');
  const words = seg.split('-').filter(Boolean);
  while (words.length && /^(([a-z]{0,4}\d+[a-z]*)|\d+|txt|print|news)$/i.test(words[words.length - 1])) words.pop();
  return words.join(' ');
}

const metaOf = (html, key) => (String(html).match(new RegExp('<meta[^>]+(?:property|name)=["\']' + key + '["\'][^>]*content=["\']([^"\']*)["\']', 'i')) ||
  String(html).match(new RegExp('<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']' + key + '["\']', 'i')) || [])[1] || '';
// Headline and publication time of an article page.
export function pageHead(html) {
  let title = strip(metaOf(html, 'og:title')) || strip(tag(String(html), 'title'));
  title = title.replace(/\s*[|\-–]\s*(Sakal|eSakal|Lokmat|Lokmat\.com|Loksatta|Pudhari|Latest Marathi News[^|]*|Marathi News[^|]*)\s*$/i, '').trim();
  const d = new Date(metaOf(html, 'article:published_time') || (String(html).match(/"datePublished"\s*:\s*"([^"]+)"/) || [])[1] || '');
  return { title, date: isNaN(d) ? null : d };
}

const CRIME_WORDS = /\b(crime|police|cops?|arrest\w*|accused|booked|nabbed|detained|gang|thie\w+|stolen|jewel\w+|kill\w+|dead|death|dies|died|injured|weapon\w*|knife|sickle|koyta)\b/i;
const sectionOf = u => { try { return decodeURIComponent(new URL(u).pathname).split('/').filter(Boolean).slice(0, -1).join(' ').replace(/-/g, ' '); } catch { return ''; } };
const filedElsewhere = u => ELSEWHERE.test(sectionOf(u));
const pick = s => { for (const [id, re, guard] of RULES) if (re.test(s) && !(guard && guard.test(s))) return id; return null; };

// Returns a type id, or null when the item is not a report of an incident.
export function classify(title, text = '') {
  if (NOISE.test(title)) return null;
  const t = norm(title);
  const c = pick(t);
  if (c) return c;
  // A guard that fires on the headline rules the item out, whatever the summary says.
  for (const [, re, guard] of RULES) if (guard && re.test(t) && guard.test(t)) return null;
  const sum = norm(text.slice(0, 300));
  if (!sum.trim() || !CONTEXT.test(t + ' ' + sum)) return null;
  return pick(sum);
}

// False when the headline places the incident outside Pune district.
export function inPune(title, text = '') {
  const t = title.replace(ROADS, ' ');
  if (HAPPENED_ELSEWHERE.test(t)) return false;
  if (ELSEWHERE.test(t) && !IN_PUNE.test(t)) return false;
  // Headline silent on place: let the opening of the article say it happened elsewhere.
  if (!IN_PUNE.test(t) && !locate(title) && HAPPENED_ELSEWHERE.test(text.slice(0, 300).replace(ROADS, ' '))) return false;
  return true;
}

const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const DEV = '\\u0900-\\u097F';
// Marathi place names take endings (कोथरूडमध्ये, हडपसरला) but must not match inside another word (कॅम्प in कॅम्पस).
const MR_END = 'ा?(?:मध्ये|मधील|मधून|मधल्या|त|तील|तून|ला|जवळ|जवळील|चा|ची|चे|च्या|येथे|येथील|हून|वर|वरील|कडे|साठी)?(?![' + DEV + '])';
let AREA_RE = null;
function areaRes() {
  return AREA_RE || (AREA_RE = AREAS.map(a => ({
    a,
    src: a.alias.map(x => /[a-z]/i.test(x)
      ? '(?:^|[^a-z])(' + esc(x).replace(/ /g, '[ -]?') + ')(?![a-z])'
      : '(?:^|[^' + DEV + '])(' + esc(x) + ')' + MR_END).join('|'),
  })));
}
// "Pimpri-Chinchwad police" names the force, not the place.
const cleanPlace = s => s.replace(/pimpri[- ]chinchwad|पिंपरी[- ]चिंचवड/gi, ' ');
const LIVES = /(residents? of|resident,|native of|natives of|hails? from|hailing from|lives? in|living in|based in|from|रा\.|राहणार|रहिवासी)\s*$/i;
const AT = /\b(in|at|near|on|outside|opposite|towards)\s+(the\s+)?$/i;
const AT_MR = /^(मध्ये|मधील|मधल्या|त|तील|जवळ|जवळील|येथे|येथील|\s*(परिसरात|भागात|हद्दीत|येथे|येथील))/;

// Area of the incident. The headline wins. In the article body a place counts only when the wording
// ties it to the incident ("in Kothrud", "Kothrud police", "कोथरूडमध्ये"), never when it is where someone lives.
export function locate(title, text = '') {
  const t = cleanPlace(title);
  let best = null, pos = Infinity;
  for (const { a, src } of areaRes()) {
    const m = new RegExp(src, 'i').exec(t);
    if (m && m.index < pos) { pos = m.index; best = a; }
  }
  if (best) return best.id;

  const body = cleanPlace(text.slice(0, 2500));
  let score = 1.5;                                // a bare mention (1, or 1.5 in Marathi) is not enough
  for (const { a, src } of areaRes()) {
    for (const m of body.matchAll(new RegExp(src, 'gi'))) {
      const name = m.slice(1).find(Boolean) || '';
      const start = m.index + m[0].indexOf(name), end = start + name.length;
      const before = body.slice(Math.max(0, start - 28), start);
      const after = body.slice(end, end + 24);
      if (LIVES.test(before)) continue;
      // Strongest: the police station, or a Marathi dateline ("लोणी काळभोर, ता. १५ :"). Then "in X" / "Xमध्ये".
      // A Marathi mention outranks an English one of equal strength: the English lines on Marathi sites are machine-written.
      const s = (/^\S{0,6}\s*(police|पोलीस|पोलिस)/i.test(after) || /^\s*,\s*ता\./.test(after) ? 3 : (AT.test(before) || AT_MR.test(after)) ? 2 : 1)
        + (/[ऀ-ॿ]/.test(name) ? 0.5 : 0);
      if (s > score || (s === score && s > 1 && start < pos)) { score = s; pos = start; best = a; }
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
  if (/\b(afternoon|noon|broad daylight)\b|दुपारी|दिवसाढवळ्या|भरदिवसा/i.test(s)) return { h: null, b: 'afternoon' };
  if (/\b(morning)\b|सकाळी/i.test(s)) return { h: null, b: 'morning' };
  return { h: null, b: null };
}

// Readable paragraph text of an article page (used once per article to find the area and time; never stored).
export function pageText(html) {
  const body = String(html).replace(/<(script|style|noscript|header|footer|nav|aside)[\s\S]*?<\/\1>/gi, ' ');
  const meta = metaOf(html, 'description') || metaOf(html, 'og:description');
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

// True when the headline itself shows this is not an incident report: noise, or an incident word used in another sense.
function ruledOut(title) {
  if (NOISE.test(title)) return true;
  const t = norm(title);
  if (pick(t)) return false;
  return RULES.some(([, re, guard]) => guard && re.test(t) && guard.test(t));
}
// The article opening says it is in Pune: "पुण्यात", "पुणे पोलिस", or a dateline such as "पुणे, ता. १४" / "पुणे - ".
const SAYS_PUNE = /पुण्यात(?!ील)|पुणे शहरात|पुणे पोलिस|पुणे पोलीस|(^|[.।:;\s])पुणे\s*[,:]|(^|[.।:;\s])पुणे\s+[-–]\s|\bin pune\b|\bpune (police|city)\b/i;

// One decision for a story that came from an index without headlines, given its Marathi headline, the English
// words of its address, and its text. The Marathi headline and text outrank the address words, which are
// machine-written and sometimes name the wrong place.
function judge(title, slug, text) {
  if (ruledOut(title) || NOISE.test(slug)) return null;
  if (!inPune(title, text) || !inPune(slug, text)) return null;
  const c = classify(title, text) || classify(slug, text);
  if (!c) return null;
  const a = locate(title, text) || locate(slug);
  // Sakal and Lokmat file other districts under "Pune" too: without an area, the story itself must say Pune.
  if (!a && !IN_PUNE.test(title.replace(ROADS, ' ')) && !SAYS_PUNE.test(text.slice(0, 500))) return null;
  return { c, a };
}

// Re-check a record stored under older rules. Returns false when it should be removed.
// `text` is the article text if it could be read again, else ''.
export function recheck(rec, text) {
  const slug = slugTitle(rec.u), fromIndex = FEEDS.some(f => f.id === rec.s && f.kind === 'urlmap');
  if (filedElsewhere(rec.u)) return false;
  let c, a;
  if (fromIndex && text) {
    const j = judge(rec.t, slug, text);
    if (!j) return false;
    ({ c, a } = j);
  } else {
    if (!inPune(rec.t, text)) return false;
    c = classify(rec.t, text) || (fromIndex ? classify(slug) : null);
    if (!c) return false;
    a = text ? (locate(rec.t, text) || locate(slug)) : (locate(rec.t) || locate(slug) || rec.a || null);
  }
  rec.c = c; rec.a = a;
  if (text) { const w = whenOf(rec.t, text); rec.h = w.h; rec.b = w.b; }
  rec.r = RULES_VERSION;
  return true;
}

export function hashId(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(36);
}

const record = (feed, it, c, a) => {
  const w = whenOf(it.title, it.text);
  return { id: hashId(it.link), t: it.title, u: it.link, s: feed.id, d: it.date.toISOString(), c, a, h: w.h, b: w.b, r: RULES_VERSION };
};

// One source's feed or index -> incident records (only items that look like incidents in or around Pune).
// For indexes without headlines the result is a list of candidates {link, slug, date}; the collector reads
// each page and calls finish().
export function extract(feed, xml) {
  const out = [];
  const items = feed.kind ? parseSitemap(xml) : parseFeed(xml);
  for (const it of items) {
    const home = feed.path ? feed.path.test(it.link) : feed.pune;       // filed under the paper's Pune section
    if (filedElsewhere(it.link)) continue;                               // filed under another district
    // Other sections of the paper: only stories whose address or headline names Pune or one of its areas.
    if (feed.path && !home && !/pune|pimpri/i.test(it.link) && !locate(feed.kind === 'urlmap' ? slugTitle(it.link) : it.title)) continue;
    if (feed.kind === 'urlmap') {
      const slug = slugTitle(it.link);
      // Wide net here; the page's own headline and text make the real decision in finish().
      if ((classify(slug) || CRIME_WORDS.test(slug)) && !NOISE.test(slug) && inPune(slug)) out.push({ cand: 1, link: it.link, slug, date: it.date, home });
      continue;
    }
    if (!it.title || !it.date) continue;
    const c = classify(it.title, it.text);
    if (!c || !inPune(it.title, it.text)) continue;
    const a = locate(it.title, it.text) || locate(slugTitle(it.link));
    // Area names repeat across cities (Shivajinagar, Camp): outside the Pune section the story must also say Pune.
    if (feed.path && !home && !PUNE.test(it.title + ' ' + it.link)) continue;
    // Outside the paper's Pune section, "Pune" in passing is not enough ("a Pune family, in Karnataka").
    if (!a && !home && !IN_PUNE.test(it.title) && !IN_PUNE.test(it.text.slice(0, 300))) continue;
    out.push(record(feed, it, c, a));
  }
  return out;
}

// Turn a candidate from a headline-less index into a record, using the article page. Null when it fails the checks.
// The English address words are the paper's own summary of the story, so they set the type; the page gives the
// Marathi headline, the place and the time.
export function finish(feed, cand, html, fallbackDate) {
  const head = pageHead(html), text = pageText(html);
  if (!head.title) return null;
  const j = judge(head.title, cand.slug, text);
  if (!j) return null;
  if (!cand.home && !PUNE.test(head.title + ' ' + cand.slug + ' ' + text.slice(0, 600))) return null;
  const it = { title: head.title, link: cand.link, date: head.date || cand.date || fallbackDate, text };
  if (!it.date) return null;
  const rec = record(feed, it, j.c, j.a);
  rec.e = 1;
  return rec;
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
    if (!r.a) {
      // No area to go on: merge only on a shared distinctive number ("28 लाख", "10,000 km") in related types.
      for (const e of byArea['-'] || []) {
        if (Math.abs(new Date(r.d) - new Date(e.last)) > 48 * 3600e3) continue;
        const fam = e.c === r.c || (FAMILY[e.c] && FAMILY[e.c] === FAMILY[r.c]);
        if (fam && [...tk.nums].some(n => e.nums.has(n))) { ev = e; break; }
      }
    } else {
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
      (byArea[r.a || '-'] = byArea[r.a || '-'] || []).push(ev);
    }
    ev.reports.push(r); ev.last = r.d; ev.days.add(istDay(r.d));
    tk.nums.forEach(n => ev.nums.add(n)); tk.words.forEach(w => ev.words.add(w));
    if (!ev.b && r.b) { ev.b = r.b; ev.h = r.h; }
  }
  return events;
}
