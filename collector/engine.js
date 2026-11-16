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
  { id: 'pud',  name: 'Pudhari',          url: 'https://pudhari.news/news_sitemap.xml', kind: 'newsmap', path: /pudhari\.news\/(maharashtra\/pune|pimpri-chinchwad)\//i },
  { id: 'lkm',  name: 'Lokmat',           url: 'https://www.lokmat.com/sitemap.xml', kind: 'urlmap', path: /lokmat\.com\/(pune|pimpri-chinchwad)\//i },
  { id: 'skl',  name: 'Sakal',            url: 'https://www.esakal.com/sitemap/sitemap-daily-{date}.xml', kind: 'urlmap', daily: true, path: /esakal\.com\/(pune|pimpri-chinchwad)\//i },
];

// Area list. Coordinates are approximate locality centres (area-level only, never an incident spot).
// r: 'city' = Pune City Police area, 'pcmc' = Pimpri-Chinchwad, 'rural' = Pune district outside both.
export const AREAS = [
  ['shivajinagar','Shivajinagar',18.5308,73.8475,'city',['model colony','gokhale nagar','gokhalenagar','senapati bapat road','sb road','मॉडेल कॉलनी','गोखलेनगर','सेनापती बापट रस्त','shivajinagar','shivaji nagar','शिवाजीनगर']],
  ['deccan','Deccan / FC Road',18.5180,73.8410,'city',['deccan','fc road','fergusson college road','jm road','jangli maharaj road','डेक्कन']],
  ['camp','Camp',18.5110,73.8800,'city',['pune camp','camp area','mg road','lashkar police','cantonment','लष्कर पोलीस','लष्कर पोलिस','कॅम्प परिसर']],
  ['kp','Koregaon Park',18.5362,73.8939,'city',['koregaon park','कोरेगाव पार्क']],
  ['mundhwa','Mundhwa',18.5320,73.9300,'city',['keshav nagar','keshavnagar','केशवनगर','mundhwa','मुंढवा','मुंढव्या']],
  ['yerawada','Yerawada',18.5510,73.8800,'city',['kalyani nagar','kalyaninagar','shastrinagar','कल्याणीनगर','शास्त्रीनगर','yerawada','yerwada','येरवडा','येरवड्या']],
  ['kharadi','Kharadi',18.5510,73.9430,'city',['kharadi','खराडी']],
  ['chandannagar','Chandan Nagar',18.5610,73.9330,'city',['wadgaon sheri','vadgaon sheri','वडगाव शेरी','chandan nagar','chandannagar','चंदननगर']],
  ['vimannagar','Viman Nagar',18.5679,73.9143,'city',['viman nagar','vimannagar','vimantal','विमाननगर','विमानतळ']],
  ['lohegaon','Lohegaon',18.5960,73.9200,'city',['lohegaon','लोहगाव']],
  ['vishrantwadi','Vishrantwadi',18.5770,73.8780,'city',['tingre nagar','tingrenagar','टिंगरेनगर','vishrantwadi','विश्रांतवाडी']],
  ['dhanori','Dhanori',18.5950,73.8960,'city',['dhanori','धानोरी']],
  ['wagholi','Wagholi',18.5800,73.9800,'city',['kesnand','perne','केसनंद','पेरणे','wagholi','lonikand','loni kand','वाघोली','लोणीकंद']],
  ['kothrud','Kothrud',18.5074,73.8077,'city',['paud road','sutardara','kothrud depot','पौड रस्त','सुतारदरा','kothrud','कोथरूड','कोथरुड']],
  ['karvenagar','Karve Nagar',18.4900,73.8200,'city',['karve nagar','karvenagar','karve road','कर्वेनगर']],
  ['erandwane','Erandwane',18.5100,73.8300,'city',['erandwane','erandwana','एरंडवणे']],
  ['warje','Warje',18.4810,73.8000,'city',['warje','वारजे','वारज्या']],
  ['bavdhan','Bavdhan',18.5150,73.7780,'city',['bhugaon','chandani chowk','chandni chowk','भूगाव','चांदणी चौक','bavdhan','बावधन']],
  ['pashan','Pashan',18.5400,73.7930,'city',['pashan','पाषाण']],
  ['baner','Baner',18.5590,73.7790,'city',['baner','बाणेर']],
  ['balewadi','Balewadi',18.5760,73.7790,'city',['balewadi','बालेवाडी']],
  ['aundh','Aundh',18.5600,73.8080,'city',['chaturshringi','chatushrungi','चतुःशृंगी','चतु:शृंगी','चतुःश्रृंगी','aundh','औंध']],
  ['khadki','Khadki',18.5640,73.8510,'city',['khadki','kirkee','खडकी']],
  ['bopodi','Bopodi',18.5720,73.8330,'city',['bopodi','बोपोडी']],
  ['swargate','Swargate',18.5010,73.8580,'city',['mukund nagar','mukundnagar','sarasbaug','मुकुंदनगर','सारसबाग','swargate','स्वारगेट']],
  ['peth','Old city peths',18.5150,73.8560,'city',['खडक','खडक पोलिस','फरासखाना पोलिस','विश्रामबाग पोलिस','khadak','tulshibaug','tulsi baug','kasba','navi peth','shivajinagar gaothan','तुळशीबाग','नवी पेठ','कसबा','kasba peth','budhwar peth','shukrawar peth','raviwar peth','sadashiv peth','narayan peth','shaniwar peth','nana peth','bhavani peth','ganesh peth','somwar peth','mangalwar peth','rasta peth','ganj peth','guruwar peth','faraskhana','khadak police','vishrambaug','laxmi road','mandai','कसबा पेठ','बुधवार पेठ','शुक्रवार पेठ','रविवार पेठ','सदाशिव पेठ','नारायण पेठ','नाना पेठ','भवानी पेठ','गणेश पेठ','फरासखाना','खडक पोलीस','विश्रामबाग']],
  ['station','Pune Station / Bund Garden',18.5290,73.8740,'city',['ghorpadi','tadiwala road','koregaon park police','घोरपडी','ताडीवाला','pune station','pune railway station','bund garden','bundgarden','sassoon','पुणे स्टेशन','बंडगार्डन','ससून']],
  ['parvati','Parvati / Sahakarnagar',18.4900,73.8480,'city',['padmavati','taljai','पद्मावती','तळजाई','parvati','sahakarnagar','sahakar nagar','dattawadi','पर्वती','सहकारनगर','दत्तवाडी']],
  ['bibwewadi','Bibwewadi',18.4690,73.8640,'city',['sukhsagar nagar','sukhsagarnagar','सुखसागरनगर','bibwewadi','bibvewadi','बिबवेवाडी']],
  ['marketyard','Market Yard',18.4860,73.8680,'city',['salisbury park','maharshi nagar','maharshinagar','मार्केटयार्ड','सॅलिसबरी पार्क','महर्षीनगर','market yard','marketyard','gultekdi','मार्केट यार्ड','गुलटेकडी']],
  ['dhankawadi','Dhankawadi',18.4640,73.8530,'city',['balaji nagar','balajinagar','बालाजीनगर','dhankawadi','धनकवडी']],
  ['bharati','Bharati Vidyapeeth',18.4575,73.8560,'city',['bharati vidyapeeth','भारती विद्यापीठ']],
  ['katraj','Katraj',18.4483,73.8578,'city',['navale bridge','navale pul','jambhulwadi','katraj ghat','नवले पुल','नवले पूल','जांभूळवाडी','katraj','कात्रज']],
  ['ambegaon','Ambegaon / Narhe',18.4480,73.8300,'city',['ambegaon budruk','ambegaon khurd','ambegaon pathar','आंबेगाव बुद्रुक','आंबेगाव खुर्द','आंबेगाव पठार','narhe','नऱ्हे']],
  ['sinhgadroad','Sinhgad Road',18.4680,73.8200,'city',['kirkatwadi','manikbaug','vitthalwadi','hingne','sinhagad fort','सिंहगड घाट','किरकटवाडी','माणिकबाग','हिंगणे','sinhgad road','sinhagad road','vadgaon budruk','dhayari','anandnagar','nanded city','सिंहगड रस्ता','सिंहगड रोड','धायरी','वडगाव बुद्रुक']],
  ['kondhwa','Kondhwa',18.4636,73.8927,'city',['kausar baug','kondhwa budruk','kondhwa khurd','कौसरबाग','kondhwa','yewalewadi','कोंढवा','कोंढव्या','येवलेवाडी']],
  ['nibm','NIBM / Undri',18.4560,73.9010,'city',['nibm','undri','pisoli','mohammadwadi','mohammedwadi','उंड्री']],
  ['wanowrie','Wanowrie',18.4860,73.8990,'city',['lullanagar','fatima nagar','fatimanagar','लुल्लानगर','फातिमानगर','wanowrie','wanawadi','wanwadi','वानवडी']],
  ['hadapsar','Hadapsar',18.5089,73.9260,'city',['kalepadal','kale padal','amanora','gadital','sasane nagar','काळेपडळ','गाडीतळ','ससाणेनगर','hadapsar','magarpatta','हडपसर','मगरपट्टा']],
  ['manjri','Manjri / Fursungi',18.4900,73.9700,'city',['shewalewadi','शेवाळेवाडी','manjri','fursungi','uruli devachi','मांजरी बुद्रुक','मांजरी खुर्द','मांजरी परिसर','फुरसुंगी']],
  ['lonikalbhor','Loni Kalbhor',18.4850,74.0250,'city',['theur','kadamwakvasti','kadamwak vasti','kunjirwadi','sortapwadi','थेऊर','कदमवाकवस्ती','कुंजीरवाडी','सोरतापवाडी','उरुळी कांचन','loni kalbhor','loni-kalbhor','uruli kanchan','लोणी काळभोर','उरुळी कांचन']],
  ['uttamnagar','Uttamnagar / Shivane',18.4640,73.7700,'city',['uttamnagar','uttam nagar','shivane','khadakwasla','उत्तमनगर','शिवणे','खडकवासला','खडकवासल्या']],
  ['sus','Sus / Mahalunge',18.5600,73.7500,'city',['sus road','sus gaon','mhalunge','म्हाळुंगे']],
  // Pimpri-Chinchwad
  ['pimpri','Pimpri',18.6298,73.7997,'pcmc',['kasarwadi','nehrunagar','nehru nagar','dapodi','कासारवाडी','नेहरूनगर','दापोडी','pimpri','पिंपरी']],
  ['chinchwad','Chinchwad',18.6280,73.7820,'pcmc',['chinchwad','चिंचवड']],
  ['nigdi','Nigdi / Akurdi',18.6520,73.7700,'pcmc',['nigdi','akurdi','pradhikaran','निगडी','आकुर्डी']],
  ['bhosari','Bhosari',18.6260,73.8500,'pcmc',['bhosari','भोसरी']],
  ['hinjewadi','Hinjewadi',18.5913,73.7389,'pcmc',['marunji','maan','मारुंजी','hinjewadi','hinjawadi','हिंजवडी']],
  ['wakad','Wakad',18.5990,73.7620,'pcmc',['tathawade','punawale','ताथवडे','पुनावळे','wakad','वाकड']],
  ['pimplesaudagar','Pimple Saudagar / Sangvi',18.5950,73.8000,'pcmc',['pimple saudagar','pimple gurav','pimple nilakh','sangvi','पिंपळे सौदागर','पिंपळे गुरव','सांगवी']],
  ['kalewadi','Kalewadi / Thergaon',18.6100,73.7750,'pcmc',['kalewadi','thergaon','rahatani','काळेवाडी','थेरगाव','रहाटणी']],
  ['ravet','Ravet / Dehu Road',18.6480,73.7400,'pcmc',['dehu','देहू','ravet','dehu road','dehuroad','kiwale','punawale','रावेत','देहूरोड']],
  ['chikhali','Chikhali / Moshi',18.6700,73.8300,'pcmc',['talawade','तळवडे','chikhali','chikhli','moshi','चिखली','मोशी']],
  ['dighi','Dighi / Alandi',18.6200,73.8750,'pcmc',['charholi','चऱ्होली','dighi','alandi','दिघी','आळंदी']],
  ['chakan','Chakan',18.7600,73.8630,'pcmc',['chakan','mahalunge','nighoje','चाकण']],
  ['talegaon','Talegaon Dabhade',18.7350,73.6760,'pcmc',['talegaon','तळेगाव']],
  // Pune district
  ['lonavala','Lonavala / Maval',18.7540,73.4060,'rural',['khandala','lohagad','lohgad','maval','खंडाळा','लोहगड','मावळ','lonavala','lonavla','kamshet','vadgaon maval','लोणावळा','लोणावळ्या','कामशेत']],
  ['shikrapur','Shikrapur / Ranjangaon',18.6930,74.1380,'rural',['koregaon bhima','sanaswadi','pabal','talegaon dhamdhere','कोरेगाव भीमा','सणसवाडी','पाबळ','तळेगाव ढमढेरे','shikrapur','ranjangaon','शिक्रापूर','रांजणगाव']],
  ['shirur','Shirur',18.8270,74.3730,'rural',['karegaon','mandavgan','कारेगाव','मांडवगण','shirur','nhavare','शिरूर','शिरुर','न्हावरे']],
  ['khed','Rajgurunagar / Khed',18.8540,73.8880,'rural',['kadus','dawadi','कडूस','दावडी','खेड तालुक','rajgurunagar','khed taluka','khed police','राजगुरुनगर','राजगुरूनगर']],
  ['junnar','Junnar / Ambegaon taluka',19.2000,73.8750,'rural',['ghodegaon','nirgudsar','ambegaon taluka','घोडेगाव','निरगुडसर','आंबेगाव तालुक','आंबेगाव','ambegaon','पिंपळवंडी','junnar','narayangaon','manchar','otur','alephata','ale phata','जुन्नर','नारायणगाव','मंचर','ओतूर','आळेफाटा']],
  ['mulshi','Mulshi / Pirangut',18.5100,73.6800,'rural',['lavale','lavasa','लवळे','ताम्हिणी','mulshi','pirangut','paud','मुळशी','पिरंगुट','पौड']],
  ['bhor','Bhor',18.1530,73.8450,'rural',['khed shivapur','nasrapur','खेड शिवापूर','नसरापूर','bhor','भोर तालुक','भोर पोलीस','भोर पोलिस','भोरमध्ये','भोर येथे']],
  ['velhe','Velhe / Rajgad',18.2950,73.6400,'rural',['panshet','पानशेत','velhe','rajgad','torna','pabe ghat','वेल्हे','राजगड','तोरणा','पाबे घाट']],
  ['baramati','Baramati',18.1520,74.5770,'rural',['malegaon budruk','माळेगाव बुद्रुक','supe','morgaon','vadgaon nimbalkar','wadgaon nimbalkar','pandare','सुपे','मोरगाव','वडगाव निंबाळकर','पणदरे','शेरेवाडी','baramati','बारामती']],
  ['indapur','Indapur',18.1150,75.0230,'rural',['bhigwan','walchandnagar','nimgaon ketki','nimgaon ketaki','भिगवण','वालचंदनगर','निमगाव केतकी','indapur','इंदापूर']],
  ['daund','Daund',18.4630,74.5820,'rural',['yavat','patas','kedgaon','kurkumbh','यवत','पाटस','केडगाव','कुरकुंभ','daund','दौंड']],
  ['saswad','Saswad / Jejuri',18.3450,74.0300,'rural',['nira','नीरा','saswad','jejuri','purandar','सासवड','जेजुरी','पुरंदर']],
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

export const RULES_VERSION = 8;

/* ------------------------------------------------------------------------------------------------
   How a report is judged (version 8).

   1. Is it a report of an incident at all?  Headlines that are politics, court stages, statistics,
      advisories, reactions, suicides or features are dropped (NOISE).
   2. What type?  Each type has signal words and a guard: words that show the signal is being used
      in another sense ("crash" of a website, "drug" in Food and Drug Administration, हत्या in हत्यार).
      The headline decides; the article's opening may decide only with police/casualty wording.
   3. Did it happen in Pune district?
   4. Fresh incident or follow-up?  Suspensions, further arrests, custody, probe developments are
      follow-ups: they attach to the incident they are about and never count as a new one.
   5. When did it happen?  The day (and time of day) stated in the article, not the day of the report.
   ------------------------------------------------------------------------------------------------ */

// Compounds that contain an incident word but mean something else. Removed before matching.
const FIGURATIVE = /आत्महत्य\S*|(आमदार|खासदार|नगरसेवक|कार्यकर्त|मंत्र्य)\S*\s(\S+\s)?राडा|(सभागृहात|सभेत|विधानसभेत|बैठकीत|कार्यक्रमात)\s(\S+\s){0,3}राडा|टांगती तलवार|घटस्फोट\S*|गांधीहत्य\S*|मतचोरी|वोट ?चोरी|मतांची चोरी|करचोरी|वीज ?चोरी|पाणी ?चोरी|गौप्यस्फोट|आगपाखड|हल्लाबोल|शाब्दिक हल्ल\S*|लोकसंख्येचा स्फोट|heart attack|panic attack|cyber ?attack|under fire|fire sale|vote theft|daylight robbery/gi;
const norm = s => String(s).replace(FIGURATIVE, ' ');

const VEH = '(car|suv|bus|buses|truck|bike|biker|motorcycl\\w+|two[- ]wheeler|scooter|moped|tempo|tanker|container|dumper|trailer|rickshaw|auto|autorickshaw|vehicle|lorry|van|jeep|tractor|ambulance|pick[- ]?up|cab|taxi)';
const WOMAN_MR = '(महिले|महिला|मुली|मुलगी|तरुणी|युवती|अल्पवयीन|विद्यार्थिनी|बालिके|चिमुकली|विवाहिते)';
const RULES = [
  ['murder', /\b(murder(s|ed|er|ing)?)\b|खून|खुना|हत्या(?!र)|हत्ये|ठार मारले|ठार केले|संपवलं|संपवले|संपविले/i, null],
  ['accident', new RegExp('\\b(accident|hit[- ]and[- ]run|run over|mowed down|mows down|collision|collides?|collided|rams? into|rammed|overturn(s|ed)?|plunges?|knocked down)\\b|अपघात|हिट अँड रन|ड्रंक अँड ड्राइव्ह|चिरडले|चिरडून|धडकेत|धडकून|धडकेने|धडक दिल्याने|ची धडक|ला धडक|उलटून|उलटला|उलटली|दरीत कोसळ|\\b' + VEH + '\\b[^.;:]{0,70}\\bcrash(es|ed)?\\b|\\bcrash(es|ed)?\\b[^.;:]{0,40}\\b' + VEH + '\\b', 'i'),
    /\b(online|website|site|server|app|portal|booking|system|market|stocks?|shares?|prices?|safety|awareness|helmet|leopards?)\b|जनजागृती|सुरक्षा सप्ताह|प्रतीक्षा|घटले|धोका|निमंत्रण|बिबट्या|भासव|बनाव|अपघात नसून|धडक कारवाई|धडकेबाज/i],
  ['murder', /\b(hacked to death|stabbed to death|beaten to death|shot dead|strangled|strangulat\w+|bludgeon\w*|killed (over|by|for|after|in (a )?(fight|dispute|quarrel|attack|brawl))|kills? (his |her )?(wife|husband|friend|father|mother|son|daughter|brother|sister|man|woman|youth|lover|neighbour|girlfriend|boyfriend)|body found|found murdered|chopp\w+ .{0,20}(to|into) pieces)\b|ठार मारले|ठार केले|गळा (दाबून|चिरून|आवळून)|भोसकून|निर्घृण/i, null],
  ['women', new RegExp('\\b(rape[ds]?|raping|gang[- ]?rape\\w*|molest\\w*|sexual(ly)? (assault|harass|abus|exploit)\\w*|stalk(ed|ing|er)|dowry|outrag\\w+ (her |the )?modesty|pocso|eve[- ]teasing|domestic violence|acid attack|voyeur\\w*)\\b|बलात्कार|विनयभंग|लैंगिक अत्याचार|लैंगिक छळ|लैंगिक शोषण|पोक्सो|पॉक्सो|हुंडा|हुंड्या|छेडछाड|छेड काढ|अतिप्रसंग|' + WOMAN_MR + '[^.।]{0,40}अत्याचार|अत्याचार[^.।]{0,40}' + WOMAN_MR, 'i'), null],
  ['kidnap', /\b(kidnap\w*|abduct\w*)\b|अपहरण/i, null],
  ['extortion', /\b(extort\w*|ransom|protection money|sextortion|blackmail\w*)\b|खंडणी|ब्लॅकमेल|हप्त्याची मागणी/i, null],
  ['robbery', /\b(robb(ed|ery|ers?|eries|ing)|loot(ed|ing|s)?|heist|dacoit\w*|chain[- ]snatch\w*|snatch(es|ed|ing|ers?)?|mugg(ed|ing)|at knife[- ]?point|at gun[- ]?point)\b|दरोडा|दरोड्या|लुटले|लुटून|लुटणार|लूटमार|लुटमार|जबरी चोरी|सोनसाखळी|मंगळसूत्र|हिसकाव|धाक दाखव|स्प्रे मारून|डोळ्यात (मिरची|स्प्रे)/i,
    /\b(loot the|looting (public|farmers|customers)|scam|fraud\w*|online|cyber)\b|फसवणूक|फसवणुक|गंडा|सायबर|ऑनलाइन|ग्राहकांची लूट|आर्थिक लूट|जनतेची लूट|शेतकऱ्यांची लूट/i],
  ['burglary', /\b(burglar\w*|burgl\w+|house[- ]?break\w*|break[- ]in|broke into|breaking into|breaks? into)\b|घरफोड|(सदनिका|फ्लॅट|घरे|घर|दुकाने|दुकान|बंगला|बंगले|दानपेटी)\s*फोड|कुलूप तोडून[^.।]{0,50}(चोरी|लंपास|ऐवज)|कडीकोयंडा/i, null],
  ['drugs', /\b(mephedrone|ganja|cannabis|cocaine|heroin|charas|hashish|opium|narcotics?|ndps|meth|contraband|peddlers?|drugs? (peddl\w+|racket|cartel|bust|haul|trafficking|smuggl\w+|seizure|seized|worth|party|den|syndicate|supplier|case)|(seiz\w+|smuggl\w+|peddl\w+|supply\w*|sell\w*|sold) (of )?drugs)\b|गांजा|गांजाची|अमली पदार्थ|अंमली पदार्थ|मेफेड्रोन|ड्रग्ज|ड्रग्स|एमडी ड्रग|चरस|अफू|कोकेन/i,
    /\b(food and drugs?|fda|drug[- ]free|de-?addiction|pharma\w*|medicines?|chemist|drug store|awareness)\b|अन्न व औषध|व्यसनमुक्ती|जनजागृती/i],
  ['cyber', /\b(cyber ?(crime|fraud\w*|crook\w*|cheat\w*|scam\w*|thie\w+)|fraud(s|sters?)?|cheat(ed|ing|s)|duped?|dupes|scam(s|mers?|med)?|digital arrest|swindl\w+|ponzi|phishing|fake call cent(re|er)|embezzl\w+|misappropriat\w+|siphon\w+|loses? (rs|₹))\b|फसवणूक|फसवणुक|फसवणुकी|फसवले|गंडा|सायबर चोर|सायबर भामट|डिजिटल अरेस्ट|अपहार/i,
    /\b(warns?|warning|advisory|awareness|beware|cautions?|tips|fraudulent job offers|dues|auction|property tax|voter|voters|election|poll)\b|सावध|आवाहन|जनजागृती|इशारा|मतदार|भरती|होऊ नये|स्पष्टीकरण|पारदर्शक|सावट|पार्श्वभूमीवर/i],
  ['violence', /\b(assault(ed|s|ing)?|attack(ed|s|ers?)?|stabb?(ed|ing|s)?|koyta|sickles?|firing|fired (at|on|upon|shots?)|opens? fire|shot at|gunshot|gunmen|beaten (up|by|with|over)|thrash(ed|es|ing)|vandalis\w+|vandaliz\w+|rioting|clash(es|ed)?|brawl|pistols?|firearms?|sword|machete|gang ?war|road rage|hurl(s|ed|ing)?)\b|हत्यार|शस्त्र बाळग|हल्ला|हल्ले|हल्ल्या|जीवे मारण्याची धमकी|राडा|मारहाण|कोयता|कोयत्या|गोळीबार|तोडफोड|पिस्तूल|पिस्तुल|पिस्टल|चाकूने|तलवार|वार केले|वार करून|हाणामारी|दगडफेक|दहशत माजव|कोयता फिरवत|अग्निशस्त्र|काडतुस|गावठी कट्ट|चॉपर|कुऱ्हाड/i,
    /\b(slams?|hits? out|lash(es|ed)? out|verbal|jibe|dig at|criticis\w+|leopards?|stray dogs?|dogs?|rabid|bees?|monkeys?|tigers?|opposition|devotees|after .{0,30}(firing|attack) incident)\b|टोला|टीका|टीके|निशाणा|हृदयविकार|बिबट्या|बिबट्याचा|कुत्र्य|मधमाश|राजकीय|माकड|वाघा|वाघाची|गव्या|हत्तीच्या|अस्वल/i],
  ['theft', /\b(theft|thefts|stolen|steal(s|ing)?|stole|thie(f|ves)|pickpocket\w*|shoplift\w*)\b|घेऊन पसार|घेऊन [^.।;]{0,25}पसार|लांबवले|लांबविले|डल्ला|चोरी|चोऱ्या|चोरट|चोरले|चोरून|चोरण|चोरां|चोराला|चोर(?![ऀ-ॿ])|लंपास/i,
    /\b(water|electricity|power|sand|prevention)\b|चोरी नाही|पाणी|वीज/i],
  ['fire', /\b(fire breaks? out|fire broke out|caught fire|catches fire|blaze|gutted|major fire|massive fire|fire (at|in) (a |an |the )?\w+|cylinder blast|explosion)\b|आग लाग|भीषण आग|अचानक आग|ला आग|आगीत|आगीच्या|आग भडक|पेट घेत|घेतला पेट|जळून खाक|स्फोट/i,
    /\b(firing|fire safety|fire audit|firecrackers?)\b|अग्निसुरक्षा|फटाके|फटाक्या/i],
];
// Most serious first. When reports of one incident disagree on type (theft / robbery), the incident takes the first in this order.
const SEVERITY = ['murder', 'women', 'kidnap', 'extortion', 'robbery', 'burglary', 'drugs', 'cyber', 'violence', 'theft', 'accident', 'fire'];

// Headlines that use incident words but are not reports of an incident.
const NOISE = new RegExp([
  // entertainment, sport, markets
  '\\b(viral video|movie|film|trailer|box office|web series|actors?|actress|bollywood|co-star|celebrit\\w+|poses|ott|album|concert|cricket|ipl|wicket|marathon|run for unity|tournament|cup|football|tennis|horoscope|recipe|sensex|nifty|poetry|lit fest)\\b',
  // politics, statements, reactions, claims
  '\\b(election|poll|manifesto|rally|budget|minister says|alleges|demands?|protest(s|ed|ers)?|morcha|remembrance|statue|condemn\\w*|reacts?|rumou?rs?)\\b',
  // court stages
  '\\b(trial|bail|verdict|convict\\w*|sentenc\\w+|acquit\\w*|hearing|high court|supreme court|hc|plea|life imprisonment|life term|jail term|court awards?|awards? life|gets life|rigorous imprisonment|years? (in jail|imprisonment)|prosecutor)\\b',
  // policy, regulation, aftermath, advisories, statistics, features
  '\\b(months? after|years? after|compensation|ex[- ]gratia|free (homes|flats)|to recruit|recruitment|helpline|campaign|special drive|data shows|statistics|survey|licen[cs]es?|food safety|revamp|inaugurat\\w+|tourism|plane crash|ajit pawar|workshop|meeting|todays latest|followup|follow up|txt|crime rates?|prevention|rbi|sebi|guidelines?|new rules?|reporting rule|introduces?|explained|how the|accident zone|black ?spots?)\\b',
  // Marathi: politics, reactions, claims
  'अजित पवार|अजितदादा|विमान|हल्लाबोल|टोला|निवडणूक|निवडणुक|मोर्चा|आंदोलन|उपोषण|निषेध|दावा खोटा|झाल्याचा दावा|गेल्याचा दावा|असल्याचा दावा|अफवा|स्पष्टता|अहवाल लवकर|अहवाल सादर|चौकशी अहवाल|भूमिका योग्य|कोण\\?|पडसाद|सवाल|अधिवेशन|पुण्यतिथी|जयंती',
  // Marathi: court stages
  'खटला|खटल्या|फाशी|युक्तीवाद|युक्तिवाद|जामीन|जन्मठेप|सक्तमजुरी|शिक्षा|सुनावणी|न्यायालया|हायकोर्ट|उच्च न्यायालय|सर्वोच्च न्यायालय|निर्दोष|आरोपीची सुटका|अभियोक्ता|वॉरंट रद्द',
  // Marathi: statistics, features, aftermath, self-harm, animals, entertainment
  'चोऱ्यांमध्ये वाढ|चोऱ्यांत वाढ|हजारी पार|गुन्ह्यांची संख्या|गुन्ह्यांत वाढ|गुन्ह्यांमध्ये वाढ|महिन्यांत|वर्षभरात|आकडेवारी|नेमके चित्र|सापळा|पुन्हा गजबजणार|मोफत|घरांचा आधार|मदत जाहीर|भरपाई|नुकसानभरपाई|जनजागृती|सत्कार|अंत्यसंस्कार',
  'संपव\\S*\\s+जीवन|जीवन\\s+संपव|गळफास|गोळी झाडून घेत|गायी|गाईचा|म्हशी|बैलाचा|जनावर|खेळाडू|अभिनेत्|चित्रपट|क्रिकेट|स्पर्धा',
].join('|'), 'i');
// "Sharad Pawar on Vidyanand Bapat: ..." — a named person's reaction to something.
const REACTION = /^[A-Z][a-z]+ [A-Z][a-z]+ on [A-Z]/;

// A later development in a case, not the incident itself.
const FOLLOW = new RegExp([
  '\\b((\\d+|two|three|four|five) more|more (held|arrested|arrests)|another (arrest|accused|held)|(2nd|second|3rd|third|another) (police )?(officer|cop|accused|suspect))\\b',
  '\\b(suspend(ed|s|sion)|dismiss(ed|al)|sacked|transferred|charge ?sheet\\w*|probe[sd]?|mastermind|mcoca|searches|(new|fresh) twist|behind (the )?(attack|murder|robbery|killing)|(days|weeks) (after|later))\\b',
  'निलंबित|निलंबन|बडतर्फ|नवे वळण|नवा खुलासा|नवा ट्विस्ट|खुलासा|कोठडी वाढ|कोठडीत वाढ|कारागृहात रवानगी|आरोपपत्र|तपास वेगवान|शोधासाठी|आणखी\\s+\\S+\\s+(जणांना\\s+|जण\\s+)?अटक|आणखी\\s+\\S+\\s+अटक|प्रकरणाला|सूत्रधार|मकोका|मोक्का|भोवले|गूढ|छडा लवकरच',
].join('|'), 'i');

// Police / casualty language. A summary may assign a type only when this is present.
const CONTEXT = /\b(police|cops?|arrest\w*|held|booked|nabbed|detained|fir|case (has been |was |is )?registered|accused|complain\w+|crime branch|victim|injured|died|dead|hospitalis\w+|hospitaliz\w+)\b|पोलीस|पोलिस|अटक|गुन्हा|गुन्हे|आरोपी|जखमी|मृत्यू|ताब्यात|जेरबंद|गजाआड|ठार/i;
// A headline that itself reports an event: a crime/accident label, or an arrest, death or injury.
const EVENT = /^\W*(pune |pimpri chinchwad )?(crime|road accident|accident|theft|fire|fraud)\b|\b(arrest\w*|held|booked|killed|dies|died|dead|injured)\b|अटक|गुन्हा दाखल|गुन्हे दाखल|मृत्यू|ठार|जखमी|जेरबंद|गजाआड|लंपास/i;
// "Road accident" means the road: a vehicle, a driver, a highway. A fall into a well or an electric shock is not one.
const ROAD = new RegExp('\\b' + VEH + '\\b|\\b(highway|expressway|road|flyover|bridge|ghat|driver|rider|pedestrian|hit[- ]and[- ]run|drunk[- ]driv\\w+)\\b|वाहन|कार(?![\\u0900-\\u097F])|कारच्या|कारने|मोटार|दुचाकी|ट्रक|बस(?![\\u0900-\\u097F])|बसच्या|बसला|बसने|टेम्पो|रिक्षा|ट्रॅक्टर|टँकर|टॅंकर|डंपर|कंटेनर|ट्रॅव्हल्स|महामार्ग|रस्त्या|रस्ता|घाट|फाट्या|चालक|धडक', 'i');

// Pune roads and highways named after other cities. Stripped before asking "did this happen elsewhere?".
const ROADS = /(पोलीस|पोलिस)\s*ठाण\S*|\b(pune|mumbai)\s*[-–]\s*[a-z]+( (highway|expressway|road))?|\bpune (nashik|solapur|satara|nagar|ahmednagar|nagpur|mumbai|bangalore|bengaluru|kolhapur|panshet|kolad)\b( (highway|expressway|road|travels|bus))?|\b(satara|solapur|nagar|ahmednagar|nashik|mumbai|bangalore|bengaluru|paud|saswad|alandi|sinhgad) (road|highway|phata)\b|सातारा (रस्ता|रस्त्या\S*|रोड)|सोलापूर (रस्ता|रस्त्या\S*|रोड)|नगर (रस्ता|रस्त्या\S*|रोड)|नाशिक फाटा|मुंबई[- ]पुणे|पुणे[- ]मुंबई|पुणे[- ](सोलापूर|सातारा|नाशिक|नगर|बंगळुरू|बेंगळुरू|अहिल्यानगर)\s?(महामार्ग\S*|रस्ता|रस्त्या\S*|रोड)?|नगर[- ]पुणे\s?(महामार्ग\S*|रस्ता|रस्त्या\S*|रोड)?|मुंबई[- ]बंगळुरू/gi;
const OTHER_EN = 'mumbai|thane|navi mumbai|kalamboli|panvel|uran|kalyan|dombivli|ulhasnagar|vasai|virar|juhu|andheri|bandra|nagpur|nashik|malegaon|chhatrapati sambhajinagar|sambhajinagar|aurangabad|karmad|kolhapur|ichalkaranji|solapur|barshi|sangola|mangalvedha|pandharpur|mohol|karmala|akkalkot|akluj|satara|karad|phaltan|wai|mahabaleshwar|sangli|miraj|dharashiv|beed|jalna|parbhani|hingoli|raigad|ratnagiri|sindhudurg|palghar|gadchiroli|chandrapur|bhandara|gondia|wardha|yavatmal|buldhana|washim|dhule|nandurbar|karjat|ahilyanagar|ahmednagar|sangamner|shirdi|parner|shrigonda|jamkhed|jalgaon|latur|amravati|akola|belgaum|belagavi|gokak|saundatti|soundatti|savadatti|hubli|hubballi|vijayapura|bijapur|delhi|bengaluru|bangalore|hyderabad|chennai|kolkata|goa|gujarat|uttar pradesh|bihar|kerala|punjab|rajasthan|karnataka|pakistan|bangladesh|china|dubai';
const OTHER_MR = 'मुंबई|ठाणे|झारखंड|बिहार|उत्तर प्रदेश|गुजरात|राजस्थान|मध्य प्रदेश|केरळ|पंजाब|हरियाणा|तेलंगण|गोवा|गोव्या|अमेरिके|नेरुळ|नालासोपार|गोरेगाव|भिवंडी|अंबरनाथ|बदलापूर|उरण|नागपूर|नागपुर|नाशिक|मालेगाव|संभाजीनगर|कोल्हापूर|कोल्हापुर|इचलकरंजी|सोलापूर|सोलापुर|बार्शी|सांगोला|पंढरपूर|मोहोळ|करमाळा|अक्कलकोट|अकलूज|माळशिरस|सातारा|साताऱ्या|कराड|फलटण|महाबळेश्वर|सांगली|मिरज|धाराशिव|बीड|जालना|परभणी|हिंगोली|रायगड|रत्नागिरी|सिंधुदुर्ग|पालघर|गडचिरोली|चंद्रपूर|भंडारा|गोंदिया|वर्धा|यवतमाळ|बुलढाणा|वाशीम|धुळे|नंदुरबार|अहिल्यानगर|अहमदनगर|संगमनेर|शिर्डी|श्रीगोंदा|जामखेड|जळगाव|लातूर|नांदेड|अमरावती|अकोला|बेळगाव|गोकाक|सौंदत्ती|दिल्ली|कर्नाटक|कल्याण|डोंबिवली|उल्हासनगर|पनवेल|वसई|विरार';
const ELSEWHERE = new RegExp('\\b(' + OTHER_EN + ')\\b|' + OTHER_MR, 'i');
// The other place is where it happened: "Kalamboli hit-and-run: ...", "... near Karmad", "बेळगावमध्ये ...", "फलटण : ...", "Maharashtra's Uran".
const HAPPENED_ELSEWHERE = new RegExp('^\\W*(' + OTHER_EN + ')\\b[^:]{0,30}:|\\b(in|at|near|on|off)\\s+(the\\s+)?(' + OTHER_EN + ')\\b|\\bin maharashtra[’\']s\\s+(?!pune)[a-z]|^\\W*(' + OTHER_MR + ')\\s*:|(' + OTHER_MR + ')\\s?(मध्ये|मधील|त |तील|जवळ|येथे|येथील| जिल्ह)', 'i');
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
const toAscii = s => String(s).replace(/[०-९]/g, d => '०१२३४५६७८९'.indexOf(d));

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
  const seg = decodeURIComponent(String(url).replace(/\/+$/, '').split('/').pop() || '');
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

// Readable paragraph text of an article page (read once to find type, place and time; never stored).
export function pageText(html) {
  const body = String(html).replace(/<(script|style|noscript|header|footer|nav|aside)[\s\S]*?<\/\1>/gi, ' ');
  const meta = metaOf(html, 'description') || metaOf(html, 'og:description');
  const ld = (String(html).match(/"articleBody"\s*:\s*"((?:[^"\\]|\\.)*)"/) || [])[1] || '';
  const paras = [...body.matchAll(/<p[\s>][\s\S]*?<\/p>/gi)].map(m => strip(m[0])).filter(p => p.length > 60).join(' ');
  return (strip(meta) + ' . ' + strip(ld.replace(/\\[nrt]/g, ' ').replace(/\\"/g, '"')) + ' . ' + paras).slice(0, 4000);
}
// On Marathi sites the opening English lines are a machine-written summary. Start at the Marathi text.
const marathiLead = text => {
  const i = text.search(/[ऀ-ॿ]/);
  if (i < 0 || i > 900) return text;
  return text.slice(i).replace(/[A-Za-z][A-Za-z0-9 ,.'’:;₹()\/-]{24,}/g, ' ');      // and drop English passages further in
};

const sectionOf = u => { try { return decodeURIComponent(new URL(u).pathname).split('/').filter(Boolean).slice(0, -1).join(' ').replace(/-/g, ' '); } catch { return ''; } };
const filedElsewhere = u => ELSEWHERE.test(sectionOf(u));
const CRIME_WORDS = /\b(crime|police|cops?|arrest\w*|accused|booked|nabbed|detained|gang|thie\w+|stolen|jewel\w+|kill\w+|dead|death|dies|died|injured|weapon\w*|knife|sickle|koyta)\b/i;
const pick = s => { for (const [id, re, guard] of RULES) if (re.test(s) && !(guard && guard.test(s))) return id; return null; };

// Returns a type id, or null when the item is not a report of an incident.
export function classify(title, text = '') {
  if (NOISE.test(title) || REACTION.test(title)) return null;
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
export function inPune(title, text = '', index = false) {
  const t = title.replace(ROADS, ' ');
  if (HAPPENED_ELSEWHERE.test(t)) return false;
  if (ELSEWHERE.test(t) && !IN_PUNE.test(t)) return false;
  // Headline silent on place: let the opening of the article say it happened elsewhere.
  if (!IN_PUNE.test(t) && !locate(title) && textElsewhere(text, index)) return false;
  return true;
}
const PUNE_TALUKA = /हवेल|मुळश|मावळ|खेड|आंबेगाव|जुन्नर|शिरू|शिरु|दौंड|इंदाप|बारामत|पुरंदर|भोर|वेल्ह|राजगड|पुणे/;   // stems, so a misspelt tag still counts
const OTHER_MR_RE = new RegExp(OTHER_MR);
/* Does the article itself place the incident outside Pune district?  A passing mention does not count ("an accused
   from Mumbai", "a gang also active in Solapur district"). What counts is how the paper marks the place of the event:
     Marathi papers: the taluka or district tag after the village, "साठेगाव (ता. फलटण)", "(जि. सातारा)", and the dateline
                     that opens the story, "करमाळा, ता. १३ :".
     English papers: the first sentence, "... near Cambridge Chowk in Chhatrapati Sambhajinagar".                       */
function textElsewhere(text, index) {
  const s = String(text).slice(0, 450).replace(ROADS, ' ');
  if (!index) return HAPPENED_ELSEWHERE.test(s.slice(0, 220));
  const tag = s.match(/\(\s*(?:ता|जि)\.\s*([^\s)\d०-९]+)/);
  if (tag && !PUNE_TALUKA.test(tag[1])) return true;
  const dateline = s.match(/^[^ऀ-ॿ]{0,12}([ऀ-ॿ]+(?:\s[ऀ-ॿ]+)?)\s*,\s*ता\.\s*[\d०-९]/);
  return !!(dateline && OTHER_MR_RE.test(dateline[1]));
}
// A Marathi story that opens with a Pune dateline: "पुणे, ता. २७ :" / "पिंपरी, ता. ३ :".
const PUNE_DATELINE = /^[^ऀ-ॿ]{0,12}(पुणे|पिंपरी)\s*,\s*ता\./;

const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const DEV = '\\u0900-\\u097F';
// Marathi place names take endings (कोथरूडमध्ये, हडपसरला) but must not match inside another word (कॅम्प in कॅम्पस).
// "From" endings (मधून, हून, वरून) are left out on purpose: "ससूनमधून परतले" is where someone came from.
const MR_END = 'ा?(?:मध्ये|मधील|मधल्या|त|तील|ला|जवळ|जवळील|चा|ची|चे|च्या|येथे|येथील|वर|वरील|कडे|साठी)?(?![' + DEV + '])';
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
  let score = 0;                                  // a bare mention (below 2) never counts: it may be a surname or where someone lives
  for (const { a, src } of areaRes()) {
    for (const m of body.matchAll(new RegExp(src, 'gi'))) {
      const name = m.slice(1).find(Boolean) || '';
      const start = m.index + m[0].indexOf(name), end = start + name.length;
      const before = body.slice(Math.max(0, start - 28), start);
      const after = body.slice(end, end + 24);
      if (LIVES.test(before)) continue;
      // Strongest: the police station, or a Marathi dateline ("लोणी काळभोर, ता. १५ :"). Then "in X" / "Xमध्ये".
      // A Marathi mention outranks an English one of equal strength: the English lines on Marathi sites are machine-written.
      // Also strongest: the taluka tag after a village, "आलेगाव (ता. दौंड)".
      const s = (/^\S{0,6}\s*(police|पोलीस|पोलिस)/i.test(after) || /^\s*,\s*ता\./.test(after) || /\(\s*ता\.\s*$/.test(before) ? 3 : (AT.test(before) || AT_MR.test(after)) ? 2 : 1)
        + (/[ऀ-ॿ]/.test(name) ? 0.5 : 0);
      if (s >= 2 && (s > score || (s === score && start < pos))) { score = s; pos = start; best = a; }
    }
  }
  return best ? best.id : null;
}

/* ---------------------------------- When it happened ---------------------------------- */
const DAY = 864e5, IST = 19800000;
const dayOf = t => Math.floor((new Date(t).getTime() + IST) / DAY);            // calendar day in India, as a number
const dayStr = n => new Date(n * DAY).toISOString().slice(0, 10);
const band = h => (h >= 6 && h < 12 ? 'morning' : h >= 12 && h < 17 ? 'afternoon' : h >= 17 && h < 21 ? 'evening' : 'night');
const BAND_OF = { 'late night': 'night', night: 'night', midnight: 'night', morning: 'morning', evening: 'evening', afternoon: 'afternoon',
  'मध्यरात्री': 'night', 'रात्री': 'night', 'पहाटे': 'night', 'सकाळी': 'morning', 'दुपारी': 'afternoon', 'सायंकाळी': 'evening', 'संध्याकाळी': 'evening' };
const MR_NUM = { 'एक': 1, 'दोन': 2, 'तीन': 3, 'चार': 4, 'पाच': 5, 'सहा': 6, 'सात': 7, 'आठ': 8, 'नऊ': 9, 'दहा': 10, 'अकरा': 11, 'बारा': 12 };
// Days of the month written out, longest first so that "एकवीस" is not read as "एक".
const MR_DAY = ['एकतीस', 'तीस', 'एकोणतीस', 'अठ्ठावीस', 'सत्तावीस', 'सव्वीस', 'पंचवीस', 'चोवीस', 'तेवीस', 'बावीस', 'एकवीस', 'वीस', 'एकोणीस', 'अठरा', 'सतरा', 'सोळा', 'पंधरा', 'चौदा', 'तेरा', 'बारा', 'अकरा', 'दहा', 'नऊ', 'आठ', 'सात', 'सहा', 'पाच', 'चार', 'तीन', 'दोन', 'एक'];
const MR_DAY_N = { 'एकतीस': 31, 'तीस': 30, 'एकोणतीस': 29, 'अठ्ठावीस': 28, 'सत्तावीस': 27, 'सव्वीस': 26, 'पंचवीस': 25, 'चोवीस': 24, 'तेवीस': 23, 'बावीस': 22, 'एकवीस': 21, 'वीस': 20, 'एकोणीस': 19, 'अठरा': 18, 'सतरा': 17, 'सोळा': 16, 'पंधरा': 15, 'चौदा': 14, 'तेरा': 13, 'बारा': 12, 'अकरा': 11, 'दहा': 10, 'नऊ': 9, 'आठ': 8, 'सात': 7, 'सहा': 6, 'पाच': 5, 'चार': 4, 'तीन': 3, 'दोन': 2, 'एक': 1 };

// Clock time or part of day stated in the report. Returns {h, b}; both null when the report does not say.
export function whenOf(title, text = '') {
  const s = toAscii(title + ' . ' + text.slice(0, 1200));
  const m = s.match(/\b(\d{1,2})(?:[:.](\d{2}))?\s*(a\.?m\.?|p\.?m\.?)(?![a-z])/i);
  if (m && +m[1] >= 1 && +m[1] <= 12) {
    let h = +m[1] % 12;
    if (/^p/i.test(m[3])) h += 12;
    return { h, b: band(h) };
  }
  // "रात्री साडेअकरा वाजता", "दुपारी 2 च्या सुमारास", "पहाटे साडेचारच्या सुमारास"
  const mr = s.match(/(पहाटे|सकाळी|दुपारी|सायंकाळी|संध्याकाळी|रात्री|मध्यरात्री)\s*(?:साडे|सव्वा|पावणे)?\s*(\d{1,2}|एक|दोन|तीन|चार|पाच|सहा|सात|आठ|नऊ|दहा|अकरा|बारा)\s*(?:च्या सुमारास|च्या दरम्यान|वाजता|वाजण्याच्या|वाजले)/);
  if (mr) {
    const n = MR_NUM[mr[2]] || +mr[2], p = mr[1];
    if (n >= 1 && n <= 12) {
      let h = n % 12;
      if (p === 'दुपारी' || p === 'सायंकाळी' || p === 'संध्याकाळी') h += 12;
      else if ((p === 'रात्री' || p === 'मध्यरात्री') && n >= 6 && n <= 11) h += 12;
      return { h, b: band(h) };
    }
  }
  if (/\b(night|midnight|wee hours|early hours|overnight)\b|मध्यरात्री|रात्री|पहाटे/i.test(s)) return { h: null, b: 'night' };
  if (/\b(evening)\b|सायंकाळी|संध्याकाळी/i.test(s)) return { h: null, b: 'evening' };
  if (/\b(afternoon|noon|broad daylight)\b|दुपारी|दिवसाढवळ्या|भरदिवसा/i.test(s)) return { h: null, b: 'afternoon' };
  if (/\b(morning)\b|सकाळी/i.test(s)) return { h: null, b: 'morning' };
  return { h: null, b: null };
}

const WD_EN = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
const WD_MR = ['रविवार', 'सोमवार', 'मंगळवार', 'बुधवार', 'गुरुवार', 'शुक्रवार', 'शनिवार'];
const MON_EN = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];
const MON_MR = ['जानेवारी', 'फेब्रुवारी', 'मार्च', 'एप्रिल', 'मे', 'जून', 'जुलै', 'ऑगस्ट', 'सप्टेंबर', 'ऑक्टोबर', 'नोव्हेंबर', 'डिसेंबर'];
const MON_EN_RE = '(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)';
const BAND_NEAR = /^[\s,)]{0,3}(?:\(\s*ता\.?\s*\d{1,2}\s*\)\s*)?(late night|night|midnight|morning|evening|afternoon|मध्यरात्री|रात्री|पहाटे|सकाळी|दुपारी|सायंकाळी|संध्याकाळी)/i;
const OLD = /\b(last (month|year)|(\d+|two|three|four|five|six|seven|eight|nine|ten|several|few) (months?|years?) (ago|back|old))\b|महिन्यांपूर्वी|महिन्यापूर्वी|वर्षांपूर्वी|वर्षापूर्वी|गेल्या वर्षी|गेल्या महिन्यात/i;

/* The day the incident happened, as the article states it: a weekday ("on Tuesday night", "बुधवारी (ता. १२) रात्री"),
   a date ("on November 10", "१० नोव्हेंबर रोजी") or "yesterday". An article usually names more than one day (the arrest,
   the court date); the incident is the earliest of them, so the earliest day within ten days of publication is taken.
   Returns { day: 'YYYY-MM-DD', stated, old, band }.  stated=false means no day was given and the report day is used.
   old=true means the article only points to something long past. */
export function whenHappened(title, text, pub, follow = false) {
  const s = toAscii(title + ' . ' + String(text).slice(0, 1500));
  const P = dayOf(pub), pd = new Date(P * DAY), Y = pd.getUTCFullYear(), M = pd.getUTCMonth(), dow = pd.getUTCDay();
  const cands = [];
  const add = (day, idx, end) => { if (day == null) return; const m = BAND_NEAR.exec(s.slice(end, end + 30)); cands.push({ day, idx, band: m ? BAND_OF[m[1].toLowerCase()] : null }); };
  // A day later than publication is still to come (a hearing, the end of custody): it is not when the incident happened.
  // The one exception is the turn of the month or year: "(ता. ३०)" in a story of the 2nd means the 30th just gone.
  const pdom = pd.getUTCDate();
  const domDay = dom => {
    if (dom <= pdom + 1) return Math.floor(Date.UTC(Y, M, dom) / DAY);
    return pdom <= 7 && dom >= 22 ? Math.floor(Date.UTC(Y, M - 1, dom) / DAY) : null;
  };
  const mdDay = (mon, dom, yr) => {
    const d = Math.floor(Date.UTC(yr || Y, mon, dom) / DAY);
    if (yr || d <= P + 1) return d;
    return d - P > 300 ? Math.floor(Date.UTC(Y - 1, mon, dom) / DAY) : null;
  };
  let m, re;

  re = /\b(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b/gi;
  while ((m = re.exec(s))) add(P - ((dow - WD_EN.indexOf(m[1].toLowerCase()) + 7) % 7), m.index, re.lastIndex);

  re = /(रविवार|सोमवार|मंगळवार|बुधवार|गुरुवार|शुक्रवार|शनिवार)(?:ी|च्या)?(?:\s*\(\s*ता\.?\s*(\d{1,2})\s*\))?/g;
  while ((m = re.exec(s))) add(m[2] ? domDay(+m[2]) : P - ((dow - WD_MR.indexOf(m[1]) + 7) % 7), m.index, re.lastIndex);

  re = /\(\s*ता\.?\s*(\d{1,2})\s*\)/g;                       // Sakal: "(ता. १२)" after the event; the dateline "पुणे, ता. १५ :" has no brackets
  while ((m = re.exec(s))) if (+m[1] >= 1 && +m[1] <= 31) add(domDay(+m[1]), m.index, re.lastIndex);

  re = new RegExp('\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+' + MON_EN_RE + '\\b\\.?(?:,?\\s+(20\\d\\d))?|\\b' + MON_EN_RE + '\\b\\.?\\s+(\\d{1,2})(?:st|nd|rd|th)?\\b(?:,?\\s+(20\\d\\d))?', 'gi');
  while ((m = re.exec(s))) {
    const dom = +(m[1] || m[5]), mon = MON_EN.indexOf((m[2] || m[4]).slice(0, 3).toLowerCase()), yr = +(m[3] || m[6]) || 0;
    if (dom >= 1 && dom <= 31 && mon >= 0) add(mdDay(mon, dom, yr), m.index, re.lastIndex);
  }

  re = new RegExp('(\\d{1,2}|' + MR_DAY.join('|') + ')\\s*(' + MON_MR.join('|') + ')(?:ला|मध्ये|च्या|पासून)?(?:\\s*रोजी)?(?![' + DEV + '])', 'g');
  while ((m = re.exec(s))) { const dom = MR_DAY_N[m[1]] || +m[1]; if (dom >= 1 && dom <= 31) add(mdDay(MON_MR.indexOf(m[2]), dom, 0), m.index, re.lastIndex); }

  re = new RegExp('\\b(yesterday|last night)\\b|(?:^|[^' + DEV + '])(काल)(?![' + DEV + '])', 'gi');
  while ((m = re.exec(s))) { add(P - 1, m.index, re.lastIndex); if (/last night/i.test(m[0])) cands[cands.length - 1].band = 'night'; }
  re = new RegExp('\\b(today|this (?:morning|afternoon|evening))\\b|(?:^|[^' + DEV + '])(आज)(?![' + DEV + '])', 'gi');
  while ((m = re.exec(s))) add(P, m.index, re.lastIndex);

  const choose = list => list.sort((a, b) => a.day - b.day || a.idx - b.idx)[0];
  // A follow-up is written days or weeks later: for it, the incident is the earliest day named in the last two months.
  // Crimes are often registered or revealed weeks late ("robbed on October 7 ... case registered on October 28"),
  // so the window reaches back a month; two months for a follow-up, which is written later still.
  const span = follow ? 60 : 30;
  const hit = choose(cands.filter(c => c.day <= P && c.day >= P - span));
  if (hit) return { day: dayStr(hit.day), stated: true, old: false, band: hit.band };
  const oldYear = (s.match(/\b(?:19|20)\d\d\b/g) || []).some(y => +y < Y && +y > 1990);
  const longAgo = cands.some(c => c.day < P - span) || OLD.test(s) || oldYear;
  return { day: dayStr(P), stated: false, old: longAgo, band: null };
}

/* ---------------------------------- One decision per report ---------------------------------- */

/* Everything the system concludes about one report. Null when it should not be kept.
     title, link, text  the headline, address and article text (text may be only the feed summary, or '')
     pub                publication time
     home               filed under the paper's Pune section (or a Pune-only feed)
     index              came from a headline-less index (Sakal, Lokmat): stricter, because their Pune sections
                        carry other districts and their English lines are machine-written
     keepArea           an area found on an earlier reading, used only when the text cannot be read now        */
export function assess({ title, link, text = '', pub, home, index, keepArea = null, trace = null }) {
  const no = why => { if (trace) trace.why = why; return null; };          // trace: for audits, says which check failed
  const slug = slugTitle(link);
  if (filedElsewhere(link)) return no('filed under another district');
  if (NOISE.test(title) || REACTION.test(title)) return no('headline is not an incident report: ' + ((title.match(NOISE) || title.match(REACTION) || [''])[0]));
  if (index && NOISE.test(slug)) return no('address words are not an incident report: ' + (slug.match(NOISE) || [''])[0]);
  const lead = index ? marathiLead(text) : text;
  if (!inPune(title, lead, index) || (index && HAPPENED_ELSEWHERE.test(slug))) return no('outside Pune district');

  // Type. The headline decides; the opening of the article may decide only for a headline that itself reports an event.
  let c = classify(title);
  if (!c && (!index || EVENT.test(title))) c = classify(title, lead);
  if (!c) return no('no incident type');
  if (c === 'accident' && !ROAD.test(title + ' ' + slug + ' ' + lead.slice(0, 500))) return no('accident, but not on the road');

  // Place.
  const a = locate(title, text) || locate(slug) || (text ? null : keepArea);
  if (!a) {
    if (index && !IN_PUNE.test(title.replace(ROADS, ' ')) && !PUNE_DATELINE.test(lead)) return no('no area found, and neither headline nor dateline says Pune');         // no area: the headline itself must say Pune
    if (!index && !home && !IN_PUNE.test(title) && !IN_PUNE.test(lead.slice(0, 300))) return no('no area found and no Pune signal');
  }
  if (!home && !PUNE.test(title + ' ' + slug + ' ' + lead.slice(0, 600))) return no('other section, never says Pune');  // area names repeat across cities

  // Stage and time.
  // Custody and remand appear in first reports too ("attacked with a rod, 3 remanded"). They mark a follow-up only when
  // the headline is about a known case ("...प्रकरणी दोघांना पोलिस कोठडी", "custody extended in ... case").
  const follow = FOLLOW.test(title) || (/कोठडी|\b(custody|remand(ed)?)\b/i.test(title) && /प्रकरण|\bcase\b|\bextended\b/i.test(title));
  const w = whenHappened(title, lead, pub, follow);
  if (follow && w.old) return no('follow-up to an old case');                                               // a later turn in an old case
  const t = whenOf(title, lead);
  let h = t.h, b = t.b;
  if (w.band) { b = w.band; if (h != null && band(h) !== w.band) h = null; }       // the part of day attached to the incident's day wins
  const out = { c, a, h, b, i: w.day, f: fingerprint(title + ' . ' + lead.slice(0, 900)) };
  if (w.stated) out.ip = 1;
  if (follow) out.k = 'f';
  return out;
}

export function hashId(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(36);
}
const feedOf = id => FEEDS.find(f => f.id === id) || {};
const isHome = (feed, link) => (feed.path ? feed.path.test(link) : !!feed.pune);
const record = (feed, title, link, date, v) => ({ id: hashId(link), t: title, u: link, s: feed.id, d: new Date(date).toISOString(), ...v, r: RULES_VERSION });

// One source's feed or index -> incident records (only items that look like incidents in or around Pune).
// For indexes without headlines the result is a list of candidates {link, slug, date}; the collector reads
// each page and calls finish().
export function extract(feed, xml) {
  const out = [];
  for (const it of (feed.kind ? parseSitemap(xml) : parseFeed(xml))) {
    const home = isHome(feed, it.link);
    if (filedElsewhere(it.link)) continue;                               // filed under another district
    // Other sections of the paper: only stories whose address or headline names Pune or one of its areas.
    if (feed.path && !home && !/pune|pimpri/i.test(it.link) && !locate(feed.kind === 'urlmap' ? slugTitle(it.link) : it.title)) continue;
    if (feed.kind === 'urlmap') {
      const slug = slugTitle(it.link);
      // Wide net here; the page's own headline and text make the real decision in finish().
      if ((classify(slug) || CRIME_WORDS.test(slug)) && !NOISE.test(slug) && !HAPPENED_ELSEWHERE.test(slug)) out.push({ cand: 1, link: it.link, slug, date: it.date, home });
      continue;
    }
    if (!it.title || !it.date) continue;
    const v = assess({ title: it.title, link: it.link, text: it.text, pub: it.date, home, index: false });
    if (v) out.push(record(feed, it.title, it.link, it.date, v));
  }
  return out;
}

// Turn a candidate from a headline-less index into a record, using the article page. Null when it fails the checks.
export function finish(feed, cand, html, fallbackDate) {
  const head = pageHead(html), text = pageText(html);
  const date = head.date || cand.date || fallbackDate;
  if (!head.title || !date) return null;
  const v = assess({ title: head.title, link: cand.link, text, pub: date, home: cand.home, index: true });
  if (!v) return null;
  const rec = record(feed, head.title, cand.link, date, v);
  rec.e = 1;
  return rec;
}

// Judge a stored record again with its article text (or '' if the page cannot be read). False when it should be removed.
export function recheck(rec, text, trace = null) {
  const feed = feedOf(rec.s);
  const v = assess({ title: rec.t, link: rec.u, text, pub: rec.d, home: isHome(feed, rec.u), index: feed.kind === 'urlmap', keepArea: rec.a, trace });
  if (!v) return false;
  for (const k of ['c', 'a', 'h', 'b', 'i', 'ip', 'k', 'f']) { if (v[k] === undefined) delete rec[k]; else rec[k] = v[k]; }
  rec.r = RULES_VERSION;
  return true;
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

/* ---------------------------------- Reports -> incidents ----------------------------------
   One real incident is reported by several papers, in two languages, over several days, and then followed up.
   Each report carries a fingerprint of the hard details in it (ages, sums of money, other figures). Reports are
   joined into one incident when they agree on place, kind of crime and day AND their fingerprints share a detail.
   Two crimes of the same kind in the same area on the same day stay separate when their details differ.
   Follow-ups never start an incident of their own: they join the incident whose details they share, or stand
   apart, marked, and are left out of the map and the counts.                                                    */
const FAMILY = { robbery: 'property', burglary: 'property', theft: 'property', murder: 'person', violence: 'person', kidnap: 'person', extortion: 'person' };
const fam = c => FAMILY[c] || c;
const UNIT = [[/^(lakh|lac|लाख)/, 'L'], [/^(crore|cr|कोटी)/, 'C'], [/^(thousand|हजार)/, 'K'], [/^(tola|तोळ)/, 'T']];

// The hard details of a report: sums ("30L", "5.25L", "22T"), ages ("a71"), and other figures of three digits or more.
export function fingerprint(text) {
  const s = toAscii(text).toLowerCase();
  const out = new Set();
  for (const m of s.matchAll(/(\d+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr|thousand|tolas?|लाख|कोटी|हजार|तोळ)/g)) {
    const u = UNIT.find(([re]) => re.test(m[2]));
    if (u) out.add(m[1] + u[1]);
  }
  for (const m of s.matchAll(/(\d{1,2})\s*-?\s*(?:year[- ]old|years?[- ]old|yr[- ]old|वर्षीय|वर्षांच्या|वर्षाच्या|वर्षांचा|वर्षांची)|(?:वय|aged)\s*(\d{1,2})/g)) out.add('a' + (m[1] || m[2]));
  for (const m of s.matchAll(/\d[\d,]{2,}/g)) { const v = m[0].replace(/,/g, ''); if (v.length >= 3 && v.length <= 9 && !/^(19|20)\d\d$/.test(v)) out.add(v); }
  return [...out].slice(0, 16);
}
const isSum = t => /[LCKT]$/.test(t);
// A sum distinctive enough to identify a case on its own: a crore figure, ten lakh or more, or an odd amount such as 5.25 lakh.
const bigSum = t => /C$/.test(t) || (/L$/.test(t) && (parseFloat(t) >= 10 || t.includes('.'))) || (/T$/.test(t) && parseFloat(t) >= 10);
const shareCount = (a, b) => { let k = 0; for (const x of a) if (b.has(x)) k++; return k; };
const shares = (a, b, pred) => { for (const x of a) if (b.has(x) && (!pred || pred(x))) return true; return false; };

export function groupEvents(items) {
  const num = s => Math.floor(Date.parse(s + 'T00:00:00Z') / DAY);
  const recs = items.map(r => ({ r, fp: new Set(r.f || fingerprint(r.t)), day: r.i ? num(r.i) : dayOf(r.d), stated: !!r.ip, follow: r.k === 'f' }));
  const events = [];
  const start = x => {
    const e = { c: x.r.c, a: x.r.a || null, day: x.day, stated: x.stated, h: null, b: null, reports: [], fp: new Set(), src: new Set(), late: false, orphan: false };
    events.push(e); return e;
  };
  const join = (e, x, anchor) => {
    e.reports.push(x.r); e.src.add(x.r.s);
    x.fp.forEach(v => e.fp.add(v));
    if (anchor && x.follow) e.late = true;                  // the incident is known through a follow-up that names its day
    if (!anchor) return;
    if (SEVERITY.indexOf(x.r.c) < SEVERITY.indexOf(e.c)) e.c = x.r.c;
    if (!e.a && x.r.a) e.a = x.r.a;
    if (x.stated && (!e.stated || x.day < e.day)) { e.day = x.day; e.stated = true; }
    if (!x.follow && !e.b && x.r.b) { e.b = x.r.b; e.h = x.r.h ?? null; }
  };

  // 1. Reports that fix an incident in time: fresh reports, and follow-ups that state the day it happened.
  const anchors = recs.filter(x => !x.follow || x.stated).sort((p, q) => p.day - q.day || (p.r.d < q.r.d ? -1 : 1));
  for (const x of anchors) {
    let ev = null;
    for (const e of events) {
      if (fam(e.c) !== fam(x.r.c)) continue;
      const gap = Math.abs(x.day - e.day);
      const sameArea = !!x.r.a && e.a === x.r.a, oneUnplaced = !x.r.a || !e.a;
      const detail = shares(x.fp, e.fp), big = shares(x.fp, e.fp, bigSum);
      // With no details on one side, only a different paper reporting the same kind of crime, same place, same day, is taken as the same incident.
      const blind = (!x.fp.size || !e.fp.size) && e.c === x.r.c && !e.src.has(x.r.s);
      if (sameArea && gap <= 1 && (detail || blind)) { ev = e; break; }
      if (sameArea && x.follow && gap <= 1) { ev = e; break; }               // a follow-up naming that day and place
      if (sameArea && (x.r.c === 'murder' || x.r.c === 'kidnap') && e.c === x.r.c && gap <= 3 && (detail || blind)) { ev = e; break; }
      if (sameArea && big && gap <= 45 && (x.follow || e.late)) { ev = e; break; }   // the same large sum in the same place: one case, surfacing late
      if (oneUnplaced && big && gap <= 3) { ev = e; break; }                  // same large sum, same days, one report without a place
    }
    join(ev || start(x), x, true);
  }

  // 2. Follow-ups with no day of their own: join the most recent incident whose details they share, else stand apart.
  for (const x of recs.filter(x => x.follow && !x.stated).sort((p, q) => (p.r.d < q.r.d ? -1 : 1))) {
    let ev = null;
    for (const e of events) {
      if (e.orphan || e.day > x.day || x.day - e.day > 45 || fam(e.c) !== fam(x.r.c)) continue;
      const sameArea = !!x.r.a && e.a === x.r.a, oneUnplaced = !x.r.a || !e.a;
      const sure = shares(x.fp, e.fp, bigSum) || shareCount(x.fp, e.fp) >= 2;   // one shared age is not enough to tie a follow-up to a case
      if ((sameArea || oneUnplaced) && sure && (!ev || e.day > ev.day)) ev = e;
    }
    if (!ev) { ev = start(x); ev.orphan = true; }
    join(ev, x, false);
  }

  for (const e of events) {
    e.reports.sort((p, q) => (p.d < q.d ? 1 : -1));
    e.last = e.reports[0].d;                                  // most recent report
    e.d = dayStr(e.day) + 'T06:30:00.000Z';                   // the day it happened (noon, India time)
  }
  return events;
}
