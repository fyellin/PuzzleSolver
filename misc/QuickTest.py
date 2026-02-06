import itertools

LINES = """
I/3 R Party snacks in curries regularly taken with supplement (6) C,R,I,S,PS
T/4 E Voter without English to be scripture reader (6)  [e]LECTOR
B/5 S Cops seizing alumnus bigwigs (6) NAB(OB)S - ob=old boy=alumnus
B/4 O Ivy or Bryony, say, shutting out the cold to warm up (6) [c]LIMBER
U/6 R Visit randomly with klutz hiding pained expression – get your act together! (7, 2 words) SH(APE)UP - from show up where ow -> ape=klutz
I/2 T Stagger with part of the personality that’s transparent (6) LIMP,ID
E/5 I Read in public – engaging with them ahead of elite (7)  PR,ELECT   pr=public relations = ”engaging with them”?? 
A/6 N Last in series about nursemaid depression returning – it makes Brazilians nuts (8) S,A,PUC<,AIA
- Fill up again with everyone else hiding seconds of punch (7) wp feels like “seconds of punch” in REST meaning “fill up again” but can’t make it work. REST,[s]OCK?  Ah, thank you!
- Imposing Western Institute of Police Entrapment (8) STING = police entrapment, FO,I,STING - rev(i=institute,of) 
- I’m on board over a tech giant’s stock growth (8, 2 words)  SAP maybe as second word? Or even APPLE (“stock growth?”)  O(A)K, APPLE is a gall,  IC: very nice++
- Baker’s set rumoured to have part about single man (8) BACH,ELOR< baker's set = batch = “bach” (homophone)
- Coercion of virtuous queen snakelike figure infiltrates (8) P(R,ESS)URE - r=regina=queen
- Resolution of clues, or resignation on reaching the end? (7) CLOSURE*
U/3 A Trained posh old dandy as stopgap between two editors (8) ED(U,CAT)ED - if cat=dandy? Yes “showily dressed man”
K/4 L Ratlines etc ship initially takes on (7) ENLIST,S not quite and no anagrind.   TACKLE,S.  
L/3 P Paperback, say, in which Ratty perhaps overcomes sign of hesitation (6) VOL(UM)E
S/4 H Without condition, life for us gets tricky (us, as editors of a certain age) (7) OURSELF - (l[if]e for us)*, “used, formerly, editorially”
M/4 A Jog Alps with me, getting several areas underfoot (6) PELMAS - (alps,me)*, soles=”several areas underfoot” - haha i guess.
S/5 B Clobbered miser to get shilling – that’s irresponsible (6) REMIS*,S
S/4 E Stretched more tightly, say, perfect resistance (6) TENSE,R ?  (perfect is e.g. a tense, r=resistance). Not thrilled. lgtm
E/5 T Bottom of Raleigh’s letter’s providing estimate (6) ASS,ESS - Raleigh is US indicator
L/6 I Mount incoming? That’s twice colt left work (8) [A] C,L,OP,C,L,OP - chatgpt helped again though it wanted clipclop with an almost correct parse.
- Put back securely on ledge for bible (8) [B] RE,FASTEN - re=on, but i don’t see “ledge for bible”, RE,ANCHOR,  RE,ATTACH, RE,BATTEN, all sorts of 6-letter synonyms for attach securely.  RE,BUCKLE, RE,BUTTON, RE,CLINCH, RE,SKEWER, RE,STAPLE, RE,STITCH, RESETTLE.  According to C, settle is a term for a ledge in the bible. 
- Night-patroller’s threatening look around operations (8, 2 words) [C] SC(OPS)OWL
- Strike down controversial levy wasting time and energy (7) [D] POLL [t]AX,E
H/2 C Active shipmaster wanting tea prepared for weaklings (7) [E] SHRIMPS - (shipmaster - tea)*
O/4 A Aoraki Park trees graduate removes like weeds (6) [F] Aoraki Park is NZ signifier. MA,HOES
O/2 L Blue origins of Chelsea’s original badge at Leek Town (6) [G] C,O,B,A,L,T - first letters
O/2 O To me, cup is complicated to work out (7) [H] COMPUTE*
D/3 R Baroque era dynasty using 75% of drugs (6) [I]  MEDICI[ne]  [Wikipedia says mostly Renaissance, but their influence continued into the Baroque period]
Y/2 D Oddball popery – cameo in red? (6) [J] PYROPE*
W/3 E Ares’ domain shrouded in bloody recognition of service (6) [K] RE(WAR)D
G/2 R Troublesome neighbours getting rambling bush uprooted with disregard (6) [K] IGNORE - (neighbours - bush)*
E/4 O No sooner provoked, one’s sore rage destroyed suits (6) [J] comp anag  (ones sore rage - sooner)* AGREES - chatgpt helped a bit! (gemini isn’t as good sad to say)
- Hitch over hilly region for hands-on searches (8) [C] could this be RUB,DOWNS - rev(bur=hitch?) or PAT,DOWNS?  Still not sure.  Rubdown doesn’t really fit the defn. 
- Cultivates makings of US return (8) [B] NURTURES*
R/4 F Misfiring leu follows banks in general (7, 3 words) [H] AS A R,ULE* - asar=banks
- Has a stab at New Seekers, sounding like White Stripes (7) [E]  KREESES = “stabs at with a kris” = SEEKERS*.  Is this a 3-parter?  Why “sounding like white stripes”? Ah, creases are lines on a cricket field.  So this is a double wordplay.
D/5 C Stricter about Ohio Society’s secret collectors (8) [A] H(O)ARDER,S
H/3 L Selected missing section in edition had repercussions (6) [I]  E(CHO[s]E)D
O/3 U Fruit mostly breaking when turned over in mouths (7) [D]    S(TOMAT[o])A  <
H/3 E Tweaked positions of chessmen, with partners missing strategy (6) [G] SCHEME - (chessmen - ns)*
N/5 S Utmost topping up of cargo drawing less power (6) [F]  [p]ULLING , but why utmost?? 
"""

def main():
    lines = [line for line in LINES.splitlines() if line]
    print(len(lines))

    def key(line):
        if line.startswith('-'):
            return line[2:].lower()
        else:
            return line[6:].lower()

    for line in sorted(lines, key=key):
        print(line)

if __name__ == '__main__':
    main2()
