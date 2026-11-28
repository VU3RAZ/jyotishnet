// SPDX-License-Identifier: AGPL-3.0-or-later
// Layer 1: Jyotish vocabulary in Hindi and Marathi. Standard Sanskrit terms in
// Devanagari; Hindi and Marathi share most of them and differ where the
// languages do (मंगल / मंगळ, सूर्य / रवि). Draft wording, for the reviewer.

import { getLang, Lang } from "./i18n";

type Tr = { hi: string; mr?: string };   // mr defaults to hi
type Table = Record<string, Tr>;

function look(table: Table, key: string): string | undefined {
  const l: Lang = getLang();
  if (l === "en") return undefined;
  const e = table[key];
  return e ? (l === "mr" ? e.mr ?? e.hi : e.hi) : undefined;
}

const EN_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];
const EN_SIGN_SHORT = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"];
const SIGNS_DEVA = ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
  "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"];
// Short forms for tight places (South Indian chart corners, table headers).
const SIGNS_DEVA_SHORT = ["मेष", "वृष", "मिथु", "कर्क", "सिंह", "कन्या",
  "तुला", "वृश्चि", "धनु", "मकर", "कुंभ", "मीन"];

const EN_GRAHA: Record<string, string> = {
  Su: "Sun", Mo: "Moon", Ma: "Mars", Me: "Mercury", Ju: "Jupiter", Ve: "Venus",
  Sa: "Saturn", Ra: "Rahu", Ke: "Ketu", La: "Lagna",
};
const GRAHA: Table = {
  Su: { hi: "सूर्य", mr: "रवि" }, Mo: { hi: "चंद्र" }, Ma: { hi: "मंगल", mr: "मंगळ" },
  Me: { hi: "बुध" }, Ju: { hi: "गुरु" }, Ve: { hi: "शुक्र" }, Sa: { hi: "शनि" },
  Ra: { hi: "राहु", mr: "राहू" }, Ke: { hi: "केतु", mr: "केतू" }, La: { hi: "लग्न" },
};
// The usual one- or two-letter chart labels.
const GRAHA_SHORT: Table = {
  Su: { hi: "सू", mr: "र" }, Mo: { hi: "चं" }, Ma: { hi: "मं" }, Me: { hi: "बु" },
  Ju: { hi: "गु" }, Ve: { hi: "शु" }, Sa: { hi: "श" }, Ra: { hi: "रा" }, Ke: { hi: "के" },
  La: { hi: "ल" },
};

const EN_VARGA: Record<number, string> = {
  1: "Rasi", 2: "Hora", 3: "Drekkana", 4: "Chaturthamsa", 7: "Saptamsa", 9: "Navamsa",
  10: "Dasamsa", 12: "Dwadasamsa", 16: "Shodasamsa", 20: "Vimsamsa", 24: "Chaturvimsamsa",
  27: "Bhamsa", 30: "Trimsamsa", 40: "Khavedamsa", 45: "Akshavedamsa", 60: "Shashtiamsa",
  5: "Panchamsa", 6: "Shashthamsa", 8: "Ashtamsa", 11: "Rudramsa", 81: "Navanavamsa",
  108: "Ashtottaramsa", 144: "Dwadasa-dwadasamsa",
};
const VARGA: Table = {
  1: { hi: "राशि", mr: "राशी" }, 2: { hi: "होरा" }, 3: { hi: "द्रेष्काण" }, 4: { hi: "चतुर्थांश" },
  5: { hi: "पंचमांश" }, 6: { hi: "षष्ठांश" }, 7: { hi: "सप्तांश" }, 8: { hi: "अष्टमांश" },
  9: { hi: "नवांश" }, 10: { hi: "दशांश" }, 11: { hi: "रुद्रांश" }, 12: { hi: "द्वादशांश" },
  16: { hi: "षोडशांश" }, 20: { hi: "विंशांश" }, 24: { hi: "चतुर्विंशांश" }, 27: { hi: "भांश" },
  30: { hi: "त्रिंशांश" }, 40: { hi: "खवेदांश" }, 45: { hi: "अक्षवेदांश" }, 60: { hi: "षष्ट्यंश" },
  81: { hi: "नवनवांश" }, 108: { hi: "अष्टोत्तरांश" }, 144: { hi: "द्वादश-द्वादशांश" },
};

/** Names the engine sends in English (nakshatras, panchanga, avasthas, ...), by spelling. */
const TERM: Table = {
  // Nakshatras
  Ashwini: { hi: "अश्विनी" }, Bharani: { hi: "भरणी" }, Krittika: { hi: "कृत्तिका" },
  Rohini: { hi: "रोहिणी" }, Mrigashira: { hi: "मृगशिरा" }, Ardra: { hi: "आर्द्रा" },
  Punarvasu: { hi: "पुनर्वसु", mr: "पुनर्वसू" }, Pushya: { hi: "पुष्य" }, Ashlesha: { hi: "आश्लेषा" },
  Magha: { hi: "मघा" }, "Purva Phalguni": { hi: "पूर्वा फाल्गुनी" },
  "Uttara Phalguni": { hi: "उत्तरा फाल्गुनी" }, Hasta: { hi: "हस्त" }, Chitra: { hi: "चित्रा" },
  Swati: { hi: "स्वाति", mr: "स्वाती" }, Vishakha: { hi: "विशाखा" }, Anuradha: { hi: "अनुराधा" },
  Jyeshtha: { hi: "ज्येष्ठा" }, Mula: { hi: "मूल" }, "Purva Ashadha": { hi: "पूर्वाषाढ़ा", mr: "पूर्वाषाढा" },
  "Uttara Ashadha": { hi: "उत्तराषाढ़ा", mr: "उत्तराषाढा" }, Shravana: { hi: "श्रवण" },
  Dhanishta: { hi: "धनिष्ठा" }, Shatabhisha: { hi: "शतभिषा" },
  "Purva Bhadrapada": { hi: "पूर्वा भाद्रपद" }, "Uttara Bhadrapada": { hi: "उत्तरा भाद्रपद" },
  Revati: { hi: "रेवती" },
  // Tithis (the engine writes "Shukla Pratipada" and so on)
  Shukla: { hi: "शुक्ल" }, Krishna: { hi: "कृष्ण" }, Pratipada: { hi: "प्रतिपदा" },
  Dwitiya: { hi: "द्वितीया" }, Tritiya: { hi: "तृतीया" }, Chaturthi: { hi: "चतुर्थी" },
  Panchami: { hi: "पंचमी" }, Shashthi: { hi: "षष्ठी" }, Saptami: { hi: "सप्तमी" },
  Ashtami: { hi: "अष्टमी" }, Navami: { hi: "नवमी" }, Dashami: { hi: "दशमी" },
  Ekadashi: { hi: "एकादशी" }, Dwadashi: { hi: "द्वादशी" }, Trayodashi: { hi: "त्रयोदशी" },
  Chaturdashi: { hi: "चतुर्दशी" }, Purnima: { hi: "पूर्णिमा" }, Amavasya: { hi: "अमावस्या" },
  // Nitya yogas (Shukla is above)
  Vishkambha: { hi: "विष्कुंभ" }, Priti: { hi: "प्रीति" }, Ayushman: { hi: "आयुष्मान" },
  Saubhagya: { hi: "सौभाग्य" }, Shobhana: { hi: "शोभन" }, Atiganda: { hi: "अतिगंड" },
  Sukarman: { hi: "सुकर्मा" }, Dhriti: { hi: "धृति" }, Shoola: { hi: "शूल" }, Ganda: { hi: "गंड" },
  Vriddhi: { hi: "वृद्धि" }, Dhruva: { hi: "ध्रुव" }, Vyaghata: { hi: "व्याघात" },
  Harshana: { hi: "हर्षण" }, Vajra: { hi: "वज्र" }, Siddhi: { hi: "सिद्धि" },
  Vyatipata: { hi: "व्यतीपात" }, Variyan: { hi: "वरीयान" }, Parigha: { hi: "परिघ" },
  Shiva: { hi: "शिव" }, Siddha: { hi: "सिद्ध" }, Sadhya: { hi: "साध्य" }, Shubha: { hi: "शुभ" },
  Brahma: { hi: "ब्रह्म" }, Indra: { hi: "इंद्र" }, Vaidhriti: { hi: "वैधृति" },
  // Karanas
  Bava: { hi: "बव" }, Balava: { hi: "बालव" }, Kaulava: { hi: "कौलव" }, Taitila: { hi: "तैतिल" },
  Garaja: { hi: "गर" }, Vanija: { hi: "वणिज" }, Vishti: { hi: "विष्टि" }, Shakuni: { hi: "शकुनि" },
  Chatushpada: { hi: "चतुष्पद" }, Naga: { hi: "नाग" }, Kimstughna: { hi: "किंस्तुघ्न" },
  // Weekdays
  Sunday: { hi: "रविवार" }, Monday: { hi: "सोमवार" }, Tuesday: { hi: "मंगलवार", mr: "मंगळवार" },
  Wednesday: { hi: "बुधवार" }, Thursday: { hi: "गुरुवार" }, Friday: { hi: "शुक्रवार" },
  Saturday: { hi: "शनिवार" },
  // Lunar months, with the Adhika / Nija prefix
  Chaitra: { hi: "चैत्र" }, Vaishakha: { hi: "वैशाख" }, Ashadha: { hi: "आषाढ़", mr: "आषाढ" },
  Bhadrapada: { hi: "भाद्रपद" }, Ashvina: { hi: "आश्विन" }, Kartika: { hi: "कार्तिक" },
  Margashirsha: { hi: "मार्गशीर्ष" }, Pausha: { hi: "पौष" }, Phalguna: { hi: "फाल्गुन" },
  Adhika: { hi: "अधिक" }, Nija: { hi: "निज" },
  // Samvatsaras (the 60-year cycle; the engine's spelling as JHora's)
  Prabhava: { hi: "प्रभव" }, Vibhava: { hi: "विभव" }, Sukla: { hi: "शुक्ल" }, Pramoda: { hi: "प्रमोद" },
  Prajapati: { hi: "प्रजापति" }, Angirasa: { hi: "अंगिरा" }, Sreemukha: { hi: "श्रीमुख" },
  Bhava: { hi: "भाव" }, Yuva: { hi: "युवा" }, Dhaata: { hi: "धाता" }, Isvara: { hi: "ईश्वर" },
  "Bahu-dhanya": { hi: "बहुधान्य" }, Pramathi: { hi: "प्रमाथी" }, Vikrama: { hi: "विक्रम" },
  Vrisha: { hi: "वृष" }, Chitrabhanu: { hi: "चित्रभानु" }, Subhanu: { hi: "सुभानु" },
  Tarana: { hi: "तारण" }, Parthiva: { hi: "पार्थिव" }, Vyaya: { hi: "व्यय" },
  "Sarva-jit": { hi: "सर्वजित्" }, "Sarva-dhari": { hi: "सर्वधारी" }, Virodhi: { hi: "विरोधी" },
  Vikriti: { hi: "विकृति" }, Khara: { hi: "खर" }, Nandana: { hi: "नंदन" }, Vijaya: { hi: "विजय" },
  Jaya: { hi: "जय" }, Manmatha: { hi: "मन्मथ" }, Durmukha: { hi: "दुर्मुख" },
  Hemalamba: { hi: "हेमलंब" }, Vilamba: { hi: "विलंब" }, Vikari: { hi: "विकारी" },
  Sharvari: { hi: "शार्वरी" }, Plava: { hi: "प्लव" }, "Shubha-krit": { hi: "शुभकृत्" },
  Krodhi: { hi: "क्रोधी" }, "Viswa-vasu": { hi: "विश्वावसु" }, Parabhava: { hi: "पराभव" },
  Plavanga: { hi: "प्लवंग" }, Keelaka: { hi: "कीलक" }, Saumya: { hi: "सौम्य" },
  Sadharana: { hi: "साधारण" }, "Virodha-krit": { hi: "विरोधकृत्" }, Paridhavi: { hi: "परिधावी" },
  Pramadi: { hi: "प्रमादी" }, Ananda: { hi: "आनंद" }, Rakshasa: { hi: "राक्षस" }, Nala: { hi: "नल" },
  Pingala: { hi: "पिंगल" }, "Kaala-yukta": { hi: "कालयुक्त" }, Siddarthi: { hi: "सिद्धार्थी" },
  Raudra: { hi: "रौद्र" }, Durmati: { hi: "दुर्मति" }, Dundubhi: { hi: "दुंदुभि" },
  Rudhirodgaari: { hi: "रुधिरोद्गारी" }, Raktaaksha: { hi: "रक्ताक्ष" }, Krodhana: { hi: "क्रोधन" },
  Kshaya: { hi: "क्षय" },
  // Avasthas
  Baala: { hi: "बाल" }, Kumara: { hi: "कुमार" }, Vriddha: { hi: "वृद्ध" }, Mrita: { hi: "मृत" },
  Jaagrita: { hi: "जाग्रत" }, Swapna: { hi: "स्वप्न" }, Sushupta: { hi: "सुषुप्त" },
  Deepta: { hi: "दीप्त" }, Swastha: { hi: "स्वस्थ" }, Mudita: { hi: "मुदित" }, Saanta: { hi: "शांत" },
  Deena: { hi: "दीन" }, Duhkhita: { hi: "दुःखित" }, Vikala: { hi: "विकल" }, Khala: { hi: "खल" },
  Kopita: { hi: "कोपित" }, Lajjita: { hi: "लज्जित" }, Garvita: { hi: "गर्वित" },
  // Taras and murthis (transits)
  Janma: { hi: "जन्म" }, Sampat: { hi: "संपत्" }, Vipat: { hi: "विपत्" }, Kshema: { hi: "क्षेम" },
  Pratyak: { hi: "प्रत्यक्" }, Saadhana: { hi: "साधक" }, Naidhana: { hi: "नैधन" }, Mitra: { hi: "मित्र" },
  "Parama Mitra": { hi: "परम मित्र" }, Swarna: { hi: "स्वर्ण", mr: "सुवर्ण" }, Rajata: { hi: "रजत" },
  Taamra: { hi: "ताम्र" }, Loha: { hi: "लोह" },
  // Yogini dashas
  Mangala: { hi: "मंगला" }, Dhanya: { hi: "धान्या" }, Bhramari: { hi: "भ्रामरी" },
  Bhadrika: { hi: "भद्रिका" }, Ulka: { hi: "उल्का" }, Sankata: { hi: "संकटा" },
  // Yoga groups
  Chandra: { hi: "चंद्र" }, Dhana: { hi: "धन" }, Kartari: { hi: "कर्तरी" },
  "Nabhasa Akriti": { hi: "नाभस आकृति" }, "Pancha Mahapurusha": { hi: "पंच महापुरुष" },
  Parivartana: { hi: "परिवर्तन" }, Raja: { hi: "राज" }, Surya: { hi: "सूर्य" },
  "Viparita Raja": { hi: "विपरीत राज" },
  // Reading topic groups
  Self: { hi: "स्वयं", mr: "स्वतः" }, Wealth: { hi: "धन" }, Work: { hi: "कार्य", mr: "काम" },
  Relationships: { hi: "संबंध", mr: "नातेसंबंध" }, Family: { hi: "परिवार", mr: "कुटुंब" },
  "Home and assets": { hi: "घर और संपत्ति", mr: "घर आणि मालमत्ता" },
  Learning: { hi: "शिक्षा", mr: "शिक्षण" }, Travel: { hi: "यात्रा", mr: "प्रवास" },
  Disputes: { hi: "विवाद", mr: "वाद" }, Spiritual: { hi: "आध्यात्मिक" }, Health: { hi: "स्वास्थ्य", mr: "आरोग्य" },
};
// English sign names, as the engine sends them for rasi dasha periods.
EN_SIGNS.forEach((s, i) => { TERM[s] = { hi: SIGNS_DEVA[i] }; });

const YOGA: Table = {
  dhana_2_11: { hi: "धन योग (2 और 11 के स्वामी)", mr: "धन योग (2 व 11 चे स्वामी)" },
  dhana_wealth_trikona: { hi: "धन योग (धन और त्रिकोण भावों के स्वामी)", mr: "धन योग (धन व त्रिकोण स्थानांचे स्वामी)" },
  lakshmi: { hi: "लक्ष्मी" }, raja_kendra_trikona: { hi: "राज योग (केंद्र-त्रिकोण)" },
  dharma_karmadhipati: { hi: "धर्म-कर्माधिपति" }, yogakaraka: { hi: "योगकारक" },
  harsha: { hi: "हर्ष (विपरीत राज)" }, sarala: { hi: "सरल (विपरीत राज)" }, vimala: { hi: "विमल (विपरीत राज)" },
  neecha_bhanga: { hi: "नीचभंग राज" }, maha_parivartana: { hi: "महा परिवर्तन" },
  khala_parivartana: { hi: "खल परिवर्तन" }, dainya_parivartana: { hi: "दैन्य परिवर्तन" },
  ruchaka: { hi: "रुचक" }, bhadra: { hi: "भद्र" }, hamsa: { hi: "हंस" }, malavya: { hi: "मालव्य" },
  sasa: { hi: "शश" }, sunapha: { hi: "सुनफा" }, anapha: { hi: "अनफा" }, durudhara: { hi: "दुरुधरा" },
  kemadruma: { hi: "केमद्रुम" }, gajakesari: { hi: "गजकेसरी" }, adhi: { hi: "अधि" },
  chandra_mangala: { hi: "चंद्र-मंगल", mr: "चंद्र-मंगळ" }, shakata: { hi: "शकट" },
  vasumati: { hi: "वसुमती" }, amala: { hi: "अमला" }, saraswati: { hi: "सरस्वती" },
  parvata: { hi: "पर्वत" }, kahala: { hi: "काहल" },
  shubha_kartari_lagna: { hi: "शुभ कर्तरी (लग्न)" }, papa_kartari_lagna: { hi: "पाप कर्तरी (लग्न)" },
  vesi: { hi: "वेशि" }, vosi: { hi: "वोशि" }, ubhayachari: { hi: "उभयचरी" },
  budha_aditya: { hi: "बुध-आदित्य (निपुण)" }, gada: { hi: "गदा" }, hala: { hi: "हल" }, vapi: { hi: "वापी" },
  // Nabhasa yogas (BPHS ch. 35)
  vallaki: { hi: "वल्लकी (वीणा)" }, damini: { hi: "दामिनी" }, pasha: { hi: "पाश" }, kedara: { hi: "केदार" },
  shoola: { hi: "शूल" }, yuga: { hi: "युग" }, gola: { hi: "गोल" }, rajju: { hi: "रज्जु" },
  musala: { hi: "मुसल" }, nala: { hi: "नल" }, mala: { hi: "माला (स्रक्)" }, sarpa: { hi: "सर्प" },
  shakata_akriti: { hi: "शकट (आकृति)", mr: "शकट (आकृती)" }, vihaga: { hi: "विहग" },
  shringataka: { hi: "शृंगाटक" }, kamala: { hi: "कमल (पद्म)" },
};

const TOPIC: Table = {
  personality: { hi: "व्यक्तित्व और स्वभाव", mr: "व्यक्तिमत्त्व आणि स्वभाव" },
  fame: { hi: "कीर्ति और प्रतिष्ठा", mr: "कीर्ती आणि प्रतिष्ठा" },
  earned_income: { hi: "अर्जित आय", mr: "कमावलेले उत्पन्न" },
  accumulated_wealth: { hi: "संचित धन" },
  career: { hi: "करियर की दिशा", mr: "कारकिर्दीची दिशा" },
  partnerships: { hi: "व्यापार और साझेदारी", mr: "व्यवसाय आणि भागीदारी" },
  marriage: { hi: "वैवाहिक जीवन की गुणवत्ता", mr: "वैवाहिक जीवनाची गुणवत्ता" },
  children: { hi: "संतान (केवल प्रजनन क्षमता)", mr: "संतती (केवळ प्रजननक्षमता)" },
  father: { hi: "पिता", mr: "वडील" }, mother: { hi: "माता", mr: "आई" },
  siblings: { hi: "भाई-बहन", mr: "भावंडे" },
  property: { hi: "संपत्ति और भूमि", mr: "मालमत्ता आणि जमीन" },
  vehicles: { hi: "वाहन", mr: "वाहने" },
  education: { hi: "विद्यालयी और उच्च शिक्षा", mr: "शालेय आणि उच्च शिक्षण" },
  foreign: { hi: "विदेश यात्रा और निवास", mr: "परदेश प्रवास आणि वास्तव्य" },
  disputes: { hi: "मुकदमे, शत्रु और प्रतिस्पर्धा", mr: "खटले, शत्रू आणि स्पर्धा" },
  spiritual: { hi: "आध्यात्मिक साधना" },
  health: { hi: "स्वास्थ्य के संकेतक (तकनीकी)", mr: "आरोग्याचे निर्देशक (तांत्रिक)" },
};

const EVENT: Table = {
  marriage: { hi: "विवाह" },
  child: { hi: "संतान का जन्म", mr: "अपत्यजन्म" },
  career: { hi: "करियर का आरंभ या पदोन्नति", mr: "नोकरीची सुरुवात किंवा बढती" },
  relocation: { hi: "स्थान परिवर्तन या संपत्ति", mr: "स्थलांतर किंवा मालमत्ता" },
  finance: { hi: "बड़ा आर्थिक लाभ या हानि", mr: "मोठा आर्थिक लाभ किंवा तोटा" },
  sibling: { hi: "भाई-बहन का जन्म या बड़ी घटना", mr: "भावंडाचा जन्म किंवा मोठी घटना" },
  vehicle: { hi: "वाहन क्रय या दुर्घटना", mr: "वाहन खरेदी किंवा अपघात" },
  spiritual: { hi: "आध्यात्मिक दीक्षा या तीर्थयात्रा", mr: "आध्यात्मिक दीक्षा किंवा तीर्थयात्रा" },
  education: { hi: "उपाधि या बड़ी परीक्षा का परिणाम", mr: "पदवी किंवा मोठ्या परीक्षेचा निकाल" },
  father_death: { hi: "पिता का निधन", mr: "वडिलांचे निधन" },
  mother_death: { hi: "माता का निधन", mr: "आईचे निधन" },
  illness: { hi: "शल्यक्रिया या गंभीर बीमारी", mr: "शस्त्रक्रिया किंवा गंभीर आजार" },
};

const MONTHS: Record<Lang, string[]> = {
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  hi: ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
  mr: ["जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून", "जुलै", "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"],
};

/** Sign name, 0 = Aries. */
export function signName(i: number): string { return getLang() === "en" ? EN_SIGNS[i] : SIGNS_DEVA[i]; }
/** Short sign name for tight places. */
export function signShort(i: number): string { return getLang() === "en" ? EN_SIGN_SHORT[i] : SIGNS_DEVA_SHORT[i]; }
/** Planet (or "La") full name; unknown codes come back as given. */
export function grahaName(code: string): string { return look(GRAHA, code) ?? EN_GRAHA[code] ?? code; }
/** Planet label in a chart: the code in English, the usual abbreviation in Devanagari. */
export function grahaShort(code: string): string { return look(GRAHA_SHORT, code) ?? code; }
/** Mark after a retrograde planet in a chart (वक्री). */
export function retroMark(): string { return getLang() === "en" ? "R" : "व"; }
export function vargaName(n: number): string { return look(VARGA, String(n)) ?? EN_VARGA[n] ?? ""; }
/** A name the engine sent in English; multi-word names are looked up whole, then word by word. */
export function term(en: string): string {
  if (getLang() === "en" || !en) return en;
  const whole = look(TERM, en);
  if (whole) return whole;
  return en.split(" ").map((w) => look(TERM, w) ?? w).join(" ");
}
export function yogaName(id: string, en: string): string { return look(YOGA, id) ?? en; }
export function topicName(id: string, en: string): string { return look(TOPIC, id) ?? en; }
export function eventName(id: string, en: string): string { return look(EVENT, id) ?? en; }
export function monthName(m: number): string { return MONTHS[getLang()][m]; }
