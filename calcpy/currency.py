import requests
from xml.etree import ElementTree
import IPython
import sympy
from contextlib import redirect_stdout
from time import sleep

country_to_currency = {
    # ISO2 country code, currency # country name ISO3 currency name
    # 'AF': 'AFN', # Afghanistan	AFG	Afghani
    # 'AL': 'ALL', # Albania	ALB	Lek
    # 'DZ': 'DZD', # Algeria	DZA	Algerian Dinar
    'AS': 'USD', # American Samoa	ASM	US Dollar
    'AD': 'EUR', # Andorra	AND	Euro
    # 'AO': 'AOA', # Angola	AGO	Kwanza
    # 'AI': 'XCD', # Anguilla	AIA	E. Caribbean Dollar
    # 'AG': 'XCD', # Antigua and Barbuda	ATG	E. Caribbean Dollar
    # 'AR': 'ARS', # Argentina	ARG	Argentine Peso
    # 'AM': 'AMD', # Armenia	ARM	Armenian Dram
    # 'AW': 'AWG', # Aruba	ABW	Aruban Guilder
    'AU': 'AUD', # Australia	AUS	Australian Dollar
    'AT': 'EUR', # Austria	AUT	Euro
    # 'AZ': 'AZN', # Azerbaijan	AZE	Azerbaijan Manat
    # 'BS': 'BSD', # BAhamas	BHS	Bahamian Dollar
    # 'BH': 'BHD', # Bahrain	BHR	Bahraini Dinar
    # 'BD': 'BDT', # Bangladesh	BGD	Taka
    # 'BB': 'BBD', # Barbados	BRB	Barbados Dollar
    # 'BY': 'BYR', # Belarus	BLR	Belarusian Ruble
    'BE': 'EUR', # Belgium	BEL	Euro
    # 'BZ': 'BZD', # Belize	BLZ	Belize Dollar
    # 'BJ': 'XOF', # Benin	BEN	CFA Franc BCEAO
    # 'BM': 'BMD', # Bermuda	BMU	Bermudian Dollar
    # 'BT': 'INRBTN', # Bhutan	BTN	Indian Rupee Bhutan Ngultrum
    # 'BO': 'BOB', # Bolivia	BOL	Boliviano
    'BQ': 'USD', # Bonaire Sint Eustatius, and Saba	BES	US Dollar
    # 'BA': 'BAM', # Bosnia and Herzegovina	BIH	Convertible Mark
    # 'BW': 'BWP', # Botswana	BWA	Pula
    'BV': 'NOK', # Bouvet Is.	BVT	Norwegian Krone
    'BR': 'BRL', # Brazil	BRA	Brazilian Real
    'IO': 'USD', # British Indian Ocean Territory	IOT	US Dollar
    'VG': 'USD', # British Virgin Is.	VGB	US Dollar
    # 'BN': 'BND', # Brunei Darussalam	BRN	Brunei Dollar
    'BG': 'BGN', # Bulgaria	BGR	Bulgarian Lev
    # 'BF': 'XOF', # Burkina Faso	BFA	CFA Franc BCEAO
    # 'BI': 'BIF', # Burundi	BDI	Burundi Franc
    # 'KH': 'KHR', # Cambodia	KHM	Riel
    # 'CM': 'XAF', # Cameroon, United Republic of	CMR	CFA Franc BEAC
    'CA': 'CAD', # Canada	CAN	Canadian Dollar
    # 'KY': 'KYD', # Cayman Is.	CYM	Cayman Is. Dollar
    # 'CF': 'XAF', # Central African Republic	CAF	CFA Franc BEAC
    # 'TD': 'XAF', # Chad	TCD	CFA Franc BEAC
    # 'CL': 'CLP', # Chile/td>	TCD	Chilean Peso
    'CN': 'CNY', # China	CHN	Yuan Renminbi
    'CX': 'AUD', # Christmas Is.	CXR	Australian Dollar
    'CC': 'AUD', # Cocos (Keeling) Is.	CCK	Australian Dollar
    # 'CO': 'COP', # Colombia	COL	Colombian Peso
    # 'KM': 'KMF', # Comoros	COM	Comoro Franc
    # 'CG': 'XAF', # Congo	COG	CFA Franc BEAC
    'CK': 'NZD', # Cook Is.	COK	New Zealand Dollar
    # 'CR': 'CRC', # Costa Rica	CRI	Costa Rican Colon
    # 'CI': 'XOF', # Cote d'Ivoire (Ivory Coast)	CIV	CFA Franc BCEAO
    'HR': 'HRK', # Croatia	HRV	Croatian Kuna
    # 'CU': 'CUP', # Cuba	CUW	Cuban Peso
    # 'CW': 'ANG', # Curacao	CUW	Netherlands Antillean Guilder
    'CY': 'EUR', # Cyprus	CYP	Euro
    'CZ': 'CZK', # Czech Republic	CZE	Czech Koruna
    # 'CD': 'CDF', # Democratic Republic of the Congo	COD	Franc Congolais
    'DK': 'DKK', # Denmark	DNK	Danish Krone
    # 'DJ': 'DJF', # Djibouti	DJI	Djibouti Franc
    # 'DM': 'XCD', # Dominica	DMA	E. Caribbean Dollar
    'DO': 'DOP', # Dominican Rep.	DOM	Dominican Peso
    'EC': 'USD', # Ecuador	ECU	US Dollar
    'EG': 'EGP', # Egypt	EGY	Egyptian Pound
    'SV': 'USD', # El Salvador	SLV	US Dollar
    # 'GQ': 'XAF', # Equatorial Guinea	GNQ	CFA Franc BEAC
    # 'ER': 'ERN', # Eritrea	ERI	Eritrean Nakfa
    'EE': 'EUR', # Estonia	EST	Euro
    # 'ET': 'ETB', # Ethiopia	ETH	Ethiopian Birr
    'FO': 'DKK', # Faroe Is.	FRO	Danish Krone
    # 'FK': 'FKP', # Falkland Is. (Malvinas)	FLK	Falkland Is. Pound
    # 'FJ': 'FJD', # Fiji	FJI	Fiji Dollar
    'FI': 'EUR', # Finland	FIN	Euro
    'FR': 'EUR', # France	FRA	Euro
    'FX': 'EUR', # France, Metropolitan	FXX	Euro
    'GF': 'EUR', # French Guiana	GUF	Euro
    # 'PF': 'XPF', # French Polynesia	PYF	CFP Franc
    'TF': 'Euro', # French Southern Territory	ATF	Euro
    # 'GA': 'XAF', # Gabon	GAB	CFA Franc BEAC
    # 'GA': 'GMD', # Gambia	GAB	Dalasi
    # 'GE': 'GEL', # Georgia	GEO	Lari
    'DE': 'EUR', # Germany	DEU	Euro
    # 'GH': 'GHS', # Ghana	GHA	Cedi
    # 'GI': 'GIP', # Gibraltar	GIB	Gibraltar Pound
    'GR': 'EUR', # Greece	GRC	Euro
    'GL': 'DKK', # Greenland	GRL	Danish Krone
    # 'GD': 'XCD', # Grenada	GRD	E. Caribbean Dollar
    'GP': 'EUR', # Guadeloupe	GLP	Euro
    'GU': 'USD', # Guam	GUM	US Dollar
    # 'GT': 'GTQ', # Guatemala	GTM	Quetzal
    # 'GN': 'GNF', # Guinea	GIN	Guinea Franc
    # 'GW': 'GWP', # Guinea-Bissau	GNB	Guinea-Bissau Peso
    # 'GY': 'GYD', # Guyana	GUY	Guyana Dollar
    # 'HT': 'HTG', # Haiti	HTI	Gourde
    'HM': 'AUD', # Heard and McDonald Is.	HMD	Australian Dollar
    'VA': 'EUR', # Holy See (Vatican City State)	VAT	Euro
    # 'HN': 'HNL', # Honduras	HND	Lempira
    'HK': 'HKD', # Hong Kong, China	HKG	Hong Kong Dollar
    'HU': 'HUF', # Hungary	HUN	Forint
    'IS': 'ISK', # Iceland	ISL	Iceland Krona
    'IN': 'INR', # India	IND	Indian Rupee
    'ID': 'IDR', # Indonesia	IDN	Rupiah
    # 'IR': 'IRR', # Iran	IRN	Iranian Rial
    # 'IQ': 'IQD', # Iraq	IRQ	Iraqi Dinar
    'IE': 'EUR', # Ireland, Republic of	IRL	Euro
    'IL': 'ILS', # Isreal	ISR	New Israeli Shequel
    'IT': 'EUR', # Italy	ITA	Euro
    # 'JM': 'JMD', # Jamaica	JAM	Jamaican Dollar
    'JP': 'JPY', # Japan	JPN	Yen
    # 'JO': 'JOD', # Jordan	JOR	Jordanian Dinar
    # 'KZ': 'KZT', # Kazakhstan	KAZ	Tenge
    # 'KE': 'KES', # Kenya	KEN	Kenyan Shilling
    'KI': 'AUD', # Kiribati	KIR	Australian Dollar
    # 'KP': 'KPW', # Korea, Democratic People's Republic of (North Korea)	PRK	North Korean Won
    'KR': 'KRW', # Korea, Republic of	KOR	Won
    # 'KW': 'KWD', # Kuwait	KWT	Kuwaiti Dinar
    # 'KG': 'KGS', # Kyrgyzstan	KGZ	Som
    # 'LA': 'LAK', # Laos	LAO	Kip
    'LV': 'EUR', # Latvia	LVA	Euro
    # 'LB': 'LBP', # Lebanon	LBN	Lebanese Pound
    # 'LS': 'LSLZAR', # Lesotho	LSO	Lesotho LotiRand
    # 'LR': 'LRD', # Liberia	LBR	Liberian Dollar
    # 'LY': 'LYD', # Libyan Arab Jamahiriya	LBY	Libyan Dinar
    'LI': 'CHF', # Liechtenstein	LIE	Swiss Franc
    'LT': 'EUR', # Lithuania	LTU	Euro
    'LU': 'EUR', # Luxembourg	LUX	Euro
    # 'MO': 'MOP', # Macau, China	MAC	Pataca
    # 'MK': 'MKD', # Macedonia, the Former Yugoslav Republic of	MKD	Denar
    # 'MG': 'MGA', # Madagascar	MDG	Malagasy Ariary
    # 'MW': 'MWK', # Malawi	MWI	Kwacha
    'MY': 'MYR', # Malaysia	MYS	Malaysian Ringgit
    # 'MV': 'MVR', # Maldives	MDV	Rufiyaa
    # 'ML': 'XOF', # Mali	MLI	CFA Franc BCEAO
    'MT': 'EUR', # Malta	MLT	Euro
    'MH': 'USD', # Marshall Islands	MHL	US Dollar
    'MQ': 'EUR', # Martinique	MTQ	Euro
    # 'MR': 'MRO', # Mauritania	MRT	Ouguiya
    # 'MU': 'MUR', # Mauritius	MUS	Mauritius Rupee
    'YT': 'EUR', # Mayotte	MYT	Euro
    'MX': 'MXN', # Mexico	MEX	Mexican Peso
    'FM': 'USD', # Micronesia	FSM	US Dollar
    # 'MD': 'MDL', # Moldova, Republic of	MDA	Moldovan Leu
    'MC': 'EUR', # Monaco	MCO	Euro
    # 'MN': 'MNT', # Mongolia	MNG	Tugrik
    'ME': 'EUR', # Montenegro	MNE	Euro
    # 'MS': 'XCD', # Montserrat	MSR	E. Caribbean Dollar
    # 'MA': 'MAD', # Morocco	MAr	Moroccan Dirham
    # 'MZ': 'MZN', # Mozambique	MOZ	Mozambique Metical
    # 'MM': 'MMK', # Myanmar	MMR	Kyat
    # 'NA': 'NADZAR', # Namibia	NAM	Namibia DollarRand
    'NR': 'AUD', # Nauru	NRU	Australian Dollar
    # 'NR': 'NPR', # Nepal	NPL	Nepalese Rupee
    'NL': 'EUR', # Netherlands	NLD	Euro
    # 'AN': 'ANG', # Netherlands Antilles	ANT	Netherlands Antillean Guilder
    # 'NC': 'XPF', # New Caledonia	NCL	CFP Franc
    'NZ': 'NZD', # New Zealand	NZL	New Zealand Dollar
    # 'NI': 'NIO', # Nicaragua	NIC	Cordoba Oro
    # 'NE': 'XOF', # Niger	NER	CFA Franc BCEAO
    # 'NG': 'NGA', # Nigeria	NGA	Naira
    'NU': 'NZD', # Niue	NIU	New Zealand Dollar
    'NF': 'AUD', # Norfolk Is.	NFK	Australian Dollar
    'MP': 'USD', # Northern Mariana Islands	MNP	US Dollar
    'NO': 'NOK', # Norway	NOR	Norwegian Krone
    # 'OM': 'OMR', # Oman	OMN	Rial Omani
    'PK': 'PKR', # Pakistan	PAK	Pakistan Rupee
    'PW': 'USD', # Palau	PLW	US Dollar
    'PS': 'USD', # Palestinian Territory, Occupied	PSE	US Dollar
    # 'PA': 'PAB', # Panama	PAN	Balboa
    # 'PG': 'PGK', # Papua New Guinea	PNG	Kina
    # 'PY': 'PYG', # Paraguay	PRY	Guarani
    # 'PE': 'PEN', # Peru	PER	Nuevo Sol
    'PH': 'PHP', # Philippines	PHL	Philippine Peso
    'PN': 'NZD', # Pitcairn	PCN	New Zealand Dollar
    'PL': 'PLN', # Poland	POL	Zloty
    'PT': 'EUR', # Portugal	PRT	Euro
    'PR': 'USD', # Puerto Rico	PRI	US Dollar
    # 'QA': 'QAR', # Qatar	QAT	Qatari Rial
    'RE': 'EUR', # Reunion	REU	Euro
    'RO': 'RON', # Romania	ROM	Leu
    'RU': 'RUB', # Russian Federation	RUS	Russian Ruble
    # 'RW': 'RWF', # Rwanda	RWA	Rwanda Franc
    # 'WS': 'WST', # Samoa	WSM	Tala
    'SM': 'EUR', # San Marino	SMR	Euro
    # 'ST': 'STD', # Sao Tome and Principe	STP	Dobra
    # 'SA': 'SAR', # Saudi Arabia	SAU	Saudi Riyal
    # 'SN': 'XOF', # Senegal	SEN	CFA Franc BCEAO
    # 'RS': 'RSD', # Serbia, Republic of	SRB	Serbian Dinar
    # 'SC': 'SCR', # Seychelles	SYC	Seychelles Rupee
    # 'SL': 'SLL', # Sierra Leone	SLE	Leone
    'SG': 'SGD', # Singapore	SGP	Singapore Dollar
    'SK': 'EUR', # Slovakia	SVK	Euro
    'SI': 'EUR', # Slovenia	SVN	Euro
    # 'SB': 'SBD', # Solomon Is.	SLB	Solomon Is. Dollar
    # 'SO': 'SOS', # Somalia	SOM	Somali Shilling
    # 'ZA': 'ZAF', # South Africa	ZAF	Rand
    'GS': 'GBP', # So. Georgia and So. Sandwich Is.	SGS	Pound Sterling
    'ES': 'EUR', # Spain	ESP	Euro
    # 'LK': 'LKR', # Sri Lanka	LKA	Sri Lanka Rupee
    # 'SH': 'SHP', # St. Helena	SHN	St. Helena Pound
    # 'KN': 'XCD', # St. Kitts-Nevis	KNA	E. Caribbean Dollar
    # 'LC': 'XCD', # St. Lucia	LCA	E. Caribbean Dollar
    # 'SX': 'ANG', # St Maarten	SXM	Netherlands Antillean Guilder
    'PM': 'EUR', # St. Pierre and Miquelon	SPM	Euro
    # 'VC': 'XCD', # St. Vincent and The Grenadines	VCT	E. Caribbean Dollar
    # 'SD': 'SDG', # Sudan	SDN	Sudanese Pound
    # 'SS': 'SSP', # South Sudan	SSD	South Sudanese Pound
    # 'SR': 'SRD', # Suriname	SUR	Surinam Dollar
    'SJ': 'NOK', # Svalbard and Jan Mayen Is.	SJM	Norwegian Krone
    # 'SZ': 'SZL', # Swaziland	SWZ	Lilangeni
    'SE': 'SEK', # Sweden	SWE	Swedish Krona
    'CH': 'CHF', # Switzerland	CHE	Swiss Franc
    # 'SY': 'SYP', # Syrian Arab Rep.	SYR	Syrian Pound
    # 'TW': 'TWD', # Taiwan	TWN	New Taiwan Dollar
    # 'TJ': 'TJS', # Tajikistan	TJK	Somoni
    # 'TZ': 'TZS', # Tanzania, United Republic of	TZA	Tanzanian Shilling
    'TH': 'THB', # Thailand	THA	Baht
    'TL': 'USD', # Timor-Leste	TLS	US Dollar
    # 'TG': 'XOF', # Togo	TGO	CFA Franc BCEAO
    'TK': 'NZD', # Tokelau	TKL	New Zealand Dollar
    # 'TO': 'TOP', # Tonga	TON	Pa'anga
    # 'TT': 'TTD', # Trinidad and Tobago	TTO	Trinidad and Tobago Dollar
    # 'TN': 'TND', # Tunisia	TUN	Tunisian Dinar
    'TR': 'TRY', # Turkey	TUR	Turkish Lira
    # 'TM': 'TMT', # Turkmenistan	TKM	Manat
    'TC': 'USD', # Turks and Caicos Is.	TCA	US Dollar
    'TV': 'AUD', # Tuvalu	TUV	Australian Dollar
    # 'UG': 'UGX', # Uganda	UGA	Uganda Shilling
    # 'UA': 'UAH', # Ukraine	UKR	Ukrainian Hryvnia
    # 'AE': 'AED', # United Arab Emirates	ARE	U.A.E. Dirham
    'GB': 'GBP', # United Kingdom	GBR	Pound Sterling
    'QZ': 'EUR', # United Nations Interim Administration Mission in Kosovo	QZZ	Euro
    'US': 'USD', # United States	USA	US Dollar
    'UM': 'USD', # US Minor Outlying Islands	UMI	US Dollar
    'VI': 'USD', # US Virgin Is.	VIR	US Dollar
    # 'UY': 'UYU', # Uruguay	URY	Peso Uruguayo
    # 'UZ': 'UZS', # Uzbekistan	UZB	Uzbekistan Sum
    # 'VU': 'VUV', # Vanuatu	VUT	Vatu
    # 'VE': 'VEF', # Venezuela	VEN	Bolivar Fuerte
    # 'VN': 'VND', # Vietnam	VNM	Dong
    # 'WF': 'XPF', # Wallis and Futuna Is.	WLF	CFP Franc
    # 'EH': 'MAD', # Western Sahara	ESH	Moroccan Dirham
    # 'YE': 'YER', # Yemen	YEM	Yemeni Rial
    # 'ZM': 'ZMW', # Zambia	ZMB	Zambian Kwacha
    # 'ZW': 'ZWD', # Zimbabwe	ZWE	Zimbabwe Dollar
}

# currencies supported by european central bank api:
# USD, JPY, BGN, CZK, DKK, GBP, HUF, PLN, RON, SEK, CHF, ISK, NOK, HRK, TRY, AUD, BRL, CAD, CNY, HKD, IDR, ILS, INR, KRW, MXN, MYR, NZD, PHP, SGD, THB, ZAR

BASE_CURRENCY_VAR_NAME = 'base_currency'
COMMON_CURRENCIES_VAR_NAME = 'common_currencies'

def set_base_currency(calcpy, base_curr, update=True):
    base_curr = base_curr.upper()
    calcpy.shell.push({BASE_CURRENCY_VAR_NAME: base_curr})
    with redirect_stdout(None):
        calcpy.shell.run_line_magic('store', BASE_CURRENCY_VAR_NAME)
    if update:
        set_rates(calcpy)

def get_base_currency(calcpy):
    base_curr = calcpy.shell.user_ns.get(BASE_CURRENCY_VAR_NAME, None)
    if base_curr is not None:
        return base_curr

    resp = requests.get('http://ipinfo.io/json')
    country = resp.json()['country']
    base_curr = country_to_currency.get(country, 'USD')

    set_base_currency(calcpy, base_curr, update=False)
    print(f'Base currency was set to \'{base_curr}\', you can change it by setting calcpy.base_currency')

    return base_curr

def set_common_currencies(calcpy, comm_currs, update=True):
    comm_currs = list(map(str.upper, comm_currs))
    calcpy.shell.push({COMMON_CURRENCIES_VAR_NAME: comm_currs})
    with redirect_stdout(None):
        calcpy.shell.run_line_magic('store', COMMON_CURRENCIES_VAR_NAME)
    if update:
        set_rates(calcpy)

def get_common_currencies(calcpy):
    comm_currs = calcpy.shell.user_ns.get(COMMON_CURRENCIES_VAR_NAME, None)
    if comm_currs is not None:
        return comm_currs

    comm_currs = ["USD", "EUR", "GBP", "CNY" , "JPY"]
    set_common_currencies(calcpy, comm_currs, update=False)

    return comm_currs

def get_rates():
    ns_cube = '{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube'
    resp = requests.get('https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml')
    element = ElementTree.fromstring(resp.content)
    element = element.find(ns_cube)
    element = element.find(ns_cube)
    time = element.attrib['time']
    rates = {'EUR': 1.00}
    for child in element.findall(ns_cube):
        rates[child.attrib['currency']] = float(child.attrib['rate'])
    return rates

def set_rates(calcpy):
    try:
        base_curr = calcpy.base_currency
        comm_currs = list(filter(base_curr.__ne__, calcpy.common_currencies))
        rates = get_rates()
    except requests.exceptions.ConnectionError:
        print("Can't update currency rates (connection error)")
        return

    base_rate = rates[base_curr]
    rates_vars = {key: (base_rate/value)*sympy.Symbol(base_curr) for key, value in rates.items()}
    calcpy.shell.push(rates_vars, interactive=False)
    calcpy.shell.push({k.lower(): v for k, v in rates_vars.items()}, interactive=False)
    base_table = sympy.Matrix([[(rates[curr]/base_rate)*sympy.Symbol(curr) for curr in comm_currs]])
    calcpy.shell.push({base_curr: base_table}, interactive=False)
    calcpy.shell.push({base_curr.lower(): base_table}, interactive=False)

def update_currency_job(ip):
    while True:
        try:
            set_rates(ip.calcpy)
        except Exception as e:
            print(f'update currency job failed with: {e}')
        sleep(60*60*12)

def init(ip:IPython.InteractiveShell):
    type(ip.calcpy).base_currency = property(get_base_currency, set_base_currency)
    type(ip.calcpy).common_currencies = property(get_common_currencies, set_common_currencies)

    ip.calcpy.jobs.new(update_currency_job, ip, daemon=True)



