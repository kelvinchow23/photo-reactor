"""
JLC/LCSC part numbers for rev B, looked up on jlcpcb.com parts library.
Keyed by MPN (as written in the schematic), or by (value, package) for
generic passives. 'TBD' = not yet looked up; do not order until filled in.

Stock figures are as seen at lookup time and will drift -- recheck before
ordering. Basic parts carry no JLC loading fee; each unique Extended part
costs a one-time loading fee per order.
"""

# MPN -> (LCSC#, Basic/Extended, stock at lookup, note)
BY_MPN = {
    'CR1206FR430P05R': ('C175800','Extended',206,'2026-10-06; 0.43ohm 1% 1206 0.25W; 233mA nominal; +/-600ppm/C; verify full-load ripple'),
    'XL-HD6070UGC-A2-BD': ('C42458855','Extended',775,'520-530nm; bin unspecified; single reflow <=220C/6s; supplier process approval required'),
    'CC0805KRX7R9BB104': ('C49678','Basic',20967215,'2026-10-06 JLC listing; 100nF 50V X7R 10% 0805'),
    'L1C1-GRN1000000000':    ('C17589373','Extended','UNCONFIRMED','C.2 LED: request wavelength bin and sourcing quote; ENIG required'),
    'S4B-PH-SM4-TB(LF)(SN)': ('C265102','Extended',25140,'C.2 four-wire fan connector; PHR-4 mating housing'),
    'CL21A106KAYNNNE':       ('C15850','Basic',4822648,'10uF 25V X5R; verify effective capacitance at 5V'),
    '0805W8F1002T5E':        ('C17414','Basic',60014692,'10k 1% 0805 PWM pull-up'),
    'AL8860WT-7':            ('C125330',  'Extended', 13028,  ''),
    'TPS563200DDCR':         ('C97253',   'Extended', 13270,  ''),
    'THVD1400DR':            ('C3235232', 'Extended', 19129,  ''),
    'MCP6002T-I/SN':         ('C7377',    'Extended', 50509,  ''),
    'DMP3099L-7':            ('C155244',  'Extended', 86058,  ''),
    '2N7002':                ('C8545',    'Basic',    1703989, ''),
    'SS14':                  ('C2480',    'Basic',    1222756, ''),
    'B5819W SL':             ('C8598',    'Basic',    560106, 'SOD-123'),
    'SMAJ16A':               ('C74561',   'Extended', 18867,  ''),
    'MMSZ5240B':             ('C21564',   'Extended', 11353,  ''),
    'SRN6045TA-680M':        ('C1330786', 'Extended', 195,    'LOW STOCK'),
    'SRN6045TA-6R8M':        ('C2041457', 'Extended', 239,    'LOW STOCK'),
    '1812L110/16MR':         ('C49318444','Extended', 2213,   'listed as 1812L110/16V'),
    'BLM21PG600SN1D':        ('C18305',   'Extended', 88780,  ''),
    'UWT1E101MCL1GS':        ('C87067',   'Extended', 207,    'LOW STOCK'),
    'SM04B-SRSS-TB(LF)(SN)': ('C160404',  'Extended', 38319,  ''),
    'S6B-PH-SM4-TB(LF)(SN)': ('C265405', 'Extended', 5423, 'Verify stock and drawing at quote'),
    'S2B-PH-SM4-TB(LF)(SN)': ('C295747',  'Extended', 22011,  ''),
    'PJ-102AH':              ('C3096093', 'Extended', 1117,   'through-hole, hand'),
    'JXT-IDC2.54-2X5P-A2':   ('C54803513','Extended', 320,    'keyed SMD box header; check footprint vs drawing'),
    'CVS-03TB':              ('TBD',      '',         0,
                              'JLC has no CVS-03; nearest is KH-10027B-SMT2.54-3P '
                              'C2842910 (22 in stock) -- needs a footprint change'),
}

# (value, footprint-substring) -> (LCSC#, Basic/Extended, stock, note)
BY_VALUE = {
    ('0R30', '1206'): ('C104940', 'Extended', 5130,   'RTT06R300FTP, 1%, 200 ppm'),
    ('1u',   '0805'): ('C28323',  'Basic',    2407354, ''),
    ('100n', '0805'): ('C1711',   'Extended', 1487402,
                       'found Extended; a Basic 100 nF almost certainly exists -- TBD'),
    ('Pico WH socket', 'Pico'): ('C2905423', 'Extended', 6734,
                       '2x 1x20 female header, through-hole, hand'),
    ('FAN1', 'PinHeader_1x04'): ('C41417361', 'Extended', 53055, 'HX PZ2.54-1x4P TP-YQ; check pad style'),
    ('FAN2', 'PinHeader_1x04'): ('C41417361', 'Extended', 53055, 'HX PZ2.54-1x4P TP-YQ; check pad style'),
}

def lookup(value, mpn, footprint):
    if mpn in BY_MPN:
        return BY_MPN[mpn]
    for (v, fp), rec in BY_VALUE.items():
        if value == v and fp in footprint:
            return rec
    return ('TBD', '', 0, '')

# Controller C9 exact sourcing selections; live allocation is checked by JLC quote.
BY_MPN.update({
    '0805W8F1000T5E': ('C17408', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    '0805W8F1001T5E': ('C17513', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    '0805W8F1002T5E': ('C17414', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    '0805W8F1003T5E': ('C149504', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    '0805W8F3301T5E': ('C26010', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    '0805W8F4701T5E': ('C17673', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    '1812L200/16DR': ('C439873', 'Extended', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'CC0805KRX7R9BB104': ('C49678', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'CL21A106KAYNNNE': ('C15850', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'CL21A475KAQNNNE': ('C1779', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'CL21B102KCANNNC': ('C15177', 'Extended', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'CL21B105KBFNNNE': ('C28323', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'GRM32ER71C226KE15L': ('C162513', 'Extended', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'KT-0805G': ('C2297', 'Basic', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'PTS645SK43SMTR92LFS': ('C221871', 'Extended', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'RC0805FR-0718K2L': ('C483023', 'Extended', "QUOTE", "Selected 2026-10-07; availability not reserved"),
    'TSM-103-01-L-SV-TR': ('C7074494', 'Extended', "QUOTE", "Selected 2026-10-07; availability not reserved"),
})

BY_MPN["694106301002"] = ("HAND-BUY", "Hand assembly", "External", "Wurth 5.5/2.1mm jack; manufacturer drawing checked 2026-10-07")

BY_MPN["TCC1210X7R226K250MT"] = ("C49118556", "Extended", "QUOTE", "22uF 25V X7R 10% 1210; matched in saved JLC cart 2026-10-07")
