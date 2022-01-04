from conllu import parse 
import requests
from collections import Counter, OrderedDict
from decimal import Decimal
import csv
from locale import LC_NUMERIC
from locale import setlocale

## nastavení "lokality"
setlocale(LC_NUMERIC, "cs_CZ.UTF-8")

## NAČÍTÁNÍ DAT
# alternativa 1) načíst věty ke zpracování pro udpipe2 z vlastního txt-souboru (do prvního řádku vepisuju název souboru, kde mám text ke zpracování (za open, má příponu .txt))
data_z_webu = requests.post('http://lindat.mff.cuni.cz/services/udpipe/api/process', data={'tokenizer': "", 'tagger': "", 'parser': ""}, files={"data": open("nazev_souboru_k_segmentaci.txt", encoding="UTF-8")}) # odešle požadavek na web
data = data_z_webu.json()['result'] 
# with open("vysledek_udpipe_conllu_terce.txt", encoding="UTF-8", mode="w") as soubor:   # můžu uložit i jako .conllu
#     print(data, file=soubor)

# alternativa 2) vložit větu/věty ke zpracování pro web přímo do příkazu za část >'data':<
# data_z_webu = requests.get('http://lindat.mff.cuni.cz/services/udpipe/api/process?tokenizer&tagger&parser', params={'data':'Ušatá Karla žere dobré seno.'})
# data = data_z_webu.json()['result'] 

# alternativa 3) vložit data conllu přímo sem (které jsem vytěžila z udpipe2 webu)
# data = """
# # sent_id = 1
# # text = Ušatá roztomilá Karla žere dobré seno.
# 1	Ušatá	ušatý	ADJ	AAFS1----1A----	Case=Nom|Degree=Pos|Gender=Fem|Number=Sing|Polarity=Pos	3	amod	_	TokenRange=0:5
# 2	roztomilá	roztomilý	ADJ	AAFS1----1A----	Case=Nom|Degree=Pos|Gender=Fem|Number=Sing|Polarity=Pos	3	amod	_	TokenRange=6:15
# 3	Karla	Karel	PROPN	NNFS1-----A----	Case=Nom|Gender=Fem|NameType=Giv|Number=Sing|Polarity=Pos	4	nsubj	_	TokenRange=16:21
# 4	žere	žrát	VERB	VB-S---3P-AA---	Mood=Ind|Number=Sing|Person=3|Polarity=Pos|Tense=Pres|VerbForm=Fin|Voice=Act	0	root	_	TokenRange=22:26
# 5	dobré	dobrý	ADJ	AANS4----1A----	Case=Acc|Degree=Pos|Gender=Neut|Number=Sing|Polarity=Pos	6	amod	_	TokenRange=27:32
# 6	seno	seno	NOUN	NNNS4-----A----	Case=Acc|Gender=Neut|Number=Sing|Polarity=Pos	4	obj	_	SpaceAfter=No|TokenRange=33:37
# 7	.	.	PUNCT	Z:-------------	_	4	punct	_	TokenRange=37:38
# 


# PŘECHROUSTÁNÍ CONLLU FORMÁTU
parsovani = parse(data)

# PŘEHLAVOVÁNÍ KOORDINOVANÝCH TOKENŮ + ŘEŠENÍ typů "aby", "kdyby"
nova_data = "" 

def bez_tokenu_navic(p):
    return veta.filter(id=lambda x: type(x) is int) # odstraní všechny ty tokeny s divným id (např. 3-4)

# řešení "aby", "kdyby" & spol.
for veta in parsovani:
    for token_pomocny in veta: 
        if type(token_pomocny["id"]) is not int: 
            id_pomocne = token_pomocny["id"][-1]
            form_pomocne = token_pomocny["form"] # pro kontrolu
            for token_pomocny_dva in veta:
                if token_pomocny_dva["id"] == id_pomocne:
                    token_pomocny_dva["head"] = None 

# řešení koordinace (pokud bych chtěla "narovnat" koordinované členy; způsobuje ale zase další automaticky zatím neřešitelné problémy)
# for veta in parsovani:
#     veta = bez_tokenu_navic(parsovani)
#     for token in veta:
#         if token["deprel"] == "conj":
#             token_od_hlavy = veta[token["head"] - 1] #8 - 1 = 7 # UWAGA když je ale věta s bych, kdyby, tak se tam vsere jeden token (dva tokeny!) navíc a rozhodí to celé počítánííí aa
#             token["head"] = token_od_hlavy["head"] 
#             #print(f'token s názvem {token["form"]} má hlavu {token["head"]}')
#     # uložení přepsaných dat do nového conllu
#     nova_veta = veta.serialize()
#     nova_data = nova_data + nova_veta

# # # uložení nových conllu do souboru (změny bo koordinace a typ "abych")
# with open("vysledek_prepsani_conllu_terce.txt", encoding="UTF-8", mode="w") as soubor: 
#         print(nova_data, file=soubor)

# odstranění interpunkce
def bez_interpunkce(veta):
    return veta.filter(xpos=lambda x: x != "Z:-------------") 

# počítadlo frekvencí
def pocitadlo(soubor):
    frekvence = Counter(soubor)
    return frekvence

# hledání predikátů
def hledani_predikatu(): 
    morfo_kategorie_predikatu = ("VB", "Vp", "Vi", "Vs")
    morfo_kategorie_predikatu_jmennych = ("VB", "Vp", "Vs")
    id_predikaty = []
    form_predikaty = []
    for veta in parsovani:
        veta_predikaty = []
        veta_predikaty_form = []
        veta = bez_interpunkce(veta)
        for token in veta:
            if token["upos"] == "VERB" and token["xpos"][0:2] in morfo_kategorie_predikatu: # 🐮
                veta_predikaty.append(token["id"])
                veta_predikaty_form.append(token["form"]) 
            if token["upos"] == "AUX" and token["xpos"][0:2] in morfo_kategorie_predikatu_jmennych: # za predikát označuju nominální část přísudku, proto ukládám "head"
                veta_predikaty.append(token["head"]) 
                veta_predikaty_form.append(token["form"]) # to jen pro kontrolu
        veta_hotove_predikaty = sorted(set(veta_predikaty)) 
        id_predikaty.append(veta_hotove_predikaty) 
        form_predikaty.append(veta_predikaty_form)
    return id_predikaty, form_predikaty

nalezene_predikaty, form_predikaty = hledani_predikatu()


# hledání první úrovně slov (prozatímní řešení, mělo by nejspíš jít vyřešit rovnou v té rekurzi níže naráz)
prvni_pulci_id = []
prvni_pulci_form = []
for veta in parsovani:
    prvni_pulci_id_veta = []
    prvni_pulci_form_veta = []
    prvni_pulci_id.append(prvni_pulci_id_veta)
    prvni_pulci_form.append(prvni_pulci_form_veta)

for x, veta in enumerate(parsovani):
    veta = bez_interpunkce(veta)
    for y, id in enumerate(nalezene_predikaty[x]):
        prvni_pulci_id_klauze = []
        prvni_pulci_form_klauze = []

        for token in veta:
            if (token["id"] not in nalezene_predikaty[x] and token["head"] == id): 
                prvni_pulci_id_klauze.append(token["id"])
                prvni_pulci_form_klauze.append(token["form"])

        prvni_pulci_id[x].append(prvni_pulci_id_klauze)
        prvni_pulci_form[x].append(prvni_pulci_form_klauze)

## rekurzivní hledání pulců (tedy jdu až po konce stromů)
# funkce s rekurzí
def hledani(x, veta, hlavy, y):
    nove_hlavy = []
    if len(hlavy) == 0:
        return 
    else:
        for token in veta:   
            if (token["id"] not in nalezene_predikaty[x] and token["head"] in hlavy):   
                nove_hlavy.append(token["id"])
                dalsi_pulci_id[x][y].append(token["id"])
                dalsi_pulci_form[x][y].append(token["form"])
    hledani(x, veta, nove_hlavy, y)

# formy pulců 
dalsi_pulci_form = []
for i in prvni_pulci_id:
    mezicast = []
    for k in i:
        mezicast.append([])
    dalsi_pulci_form.append(mezicast)

# id pulců
dalsi_pulci_id = []
for i in prvni_pulci_id:
    mezicast = []
    for k in i:
        mezicast.append([])
    dalsi_pulci_id.append(mezicast)

# tu spouštím hledání zbytku pulců
for x, veta in enumerate(parsovani):
    veta = bez_interpunkce(veta)
    for y, neco in enumerate(prvni_pulci_id[x]):
        hledani(x, veta, prvni_pulci_id[x][y], y)   


# spojuju, ať mám pro každou klauzi její slova
vsichni_pulci_id = [] # resp. všechny slova
vsichni_pulci_form = []
delka_klauzi_vsech = []

for i in prvni_pulci_form:
    vsichni_pulci_form.append([])
    delka_klauzi_vsech.append([])

# hledání správných forem predikátů, opravdu ta slova, co jsou tím headem
predikaty_formy_spravne = []
for polozka in nalezene_predikaty:
    predikaty_formy_spravne.append([])

for x, polozka in enumerate(nalezene_predikaty):
    for y, polozka_dve in enumerate(polozka):
        predikaty_formy_spravne[x].append([])

for x, veta in enumerate(parsovani):
    for y, predikat in enumerate(nalezene_predikaty[x]):
        for token in veta:
            if token["id"] == predikat:
                predikaty_formy_spravne[x][y].append(token["form"])

# spojování všech slov jedné klauze
for x, prvni in enumerate(prvni_pulci_form):
    for y, prvni_slovo in enumerate(prvni):
        vsichni_pulci_form_mezicast = predikaty_formy_spravne[x][y] + prvni_slovo + dalsi_pulci_form[x][y]

        vsichni_pulci_form[x].append(vsichni_pulci_form_mezicast)

# nové počítání délek
delka_vet_vsech= []
for x, veta in enumerate(parsovani):
    veta = bez_interpunkce(veta)
    veta = bez_tokenu_navic(parsovani) # asi ty dva řády nepotřebuju ale
    
    delka_vety = len(nalezene_predikaty[x])
    delka_vet_vsech.append(delka_vety)

    for y, klauze in enumerate(vsichni_pulci_form[x]):
        delka_klauze = len(klauze)
        delka_klauzi_vsech[x].append(delka_klauze)

# funkce pro zobrazení výsledků 
def kontrola():
    y = 1
    x = 0
    kontrola_vystup = []
    for veta in parsovani:
        veta = bez_interpunkce(veta)
        veta = bez_tokenu_navic(parsovani)
        print(f'VĚTA {y}')
        print(veta)
        strom = veta.to_tree()
        strom.print_tree()
        print(f'id predikátů: {nalezene_predikaty[x]}')
        print(f'predikáty tvar: {form_predikaty[x]}')
        print(f'délka věty v počtu klauzí = {delka_vet_vsech[x]}')
        print(f'délka klauzí v počtu slov = {delka_klauzi_vsech[x]}')
        print(f'slova jednotlivých klauzí jsou: {vsichni_pulci_form[x]}')
        print("\t")
        # pro uložení výsledků pro kontrolu v txt souboru
        ktera_veta = "VĚTA Č.: " + str(y)
        a = "id predikátů: " + str(nalezene_predikaty[x])
        b = "délka věty v počtu klauzí: " + str(delka_vet_vsech[x])
        c = "délka klauzí v počtu slov: " + str(delka_klauzi_vsech[x] )
        d = "slova jednotlivých klauzí jsou: " + str(vsichni_pulci_form[x])
        radek = "\n"
        aktualni_veta = ktera_veta + radek + a + radek + b + radek + c + radek + d
        kontrola_vystup.append(aktualni_veta)
        y = y + 1
        x = x + 1
    return kontrola_vystup

kontrola_vystup = kontrola()

# ULOŽENÍ KONTROLY DO TXT
vety_info = ""
for polozka in kontrola_vystup:
    vety_info = vety_info + polozka + "\n\n"

#print(pokus)
with open("výsledky_kontrola_nazev_souboru.txt", encoding="UTF-8", mode="w") as soubor: 
    print(vety_info, file=soubor)

# výpočet a uložení dat pro výpočet MALu
def data_pro_mal():
    # příprava proměnných
    delka_vet_v_klauzich = [] # chcu to fakt? viz níže
    delka_vet_ve_slovech = []
    x = 0

    # ukládám do proměnných délky vět v počtu klauzí a v počtu frází: delka_vet_v_klauzich[0] = délka první věty v počtu klauzí, delka_vet_ve_frazich[0] = délka první věty v počtu frází (=součet frází všech klauzí dané věty)
    for veta in parsovani:
        delka_vet_v_klauzich.append(delka_vet_vsech[x]) # to dělám pro jistotu, abych si nějak nepřepsala ten seznam delka_vet_vsech
        delka_vet_ve_slovech.append(sum(delka_klauzi_vsech[x]))
        x = x + 1

    # počítání
        # Counter spočítá počet stejných prvků (kolik je tam jedniček, dvojek, trojek, ...)
    #frekvence_pocitadlo = Counter(delka_vet_v_klauzich) # Counter je třída grr, vypluvne něco, co se jmenuje Counter, ale chová se jako slovník (prosím rozlišujme!)
    frekvence_vet = pocitadlo(delka_vet_v_klauzich)
    # slovník, kde ukládám data pro další výpočet: pro každou x-klauzovou větu součet všech jejích délek ve frázích, takový mezisoučet před počítáním průměru
    slovnik_dvojic = {}
    for i, klic in enumerate(delka_vet_v_klauzich):
        if klic not in slovnik_dvojic:
            slovnik_dvojic[klic] = 0
        slovnik_dvojic[klic] += delka_vet_ve_slovech[i]
    
    # další mezikrok, připojuju k tomu ještě informaci o frekvenci x-klauzových vět
    slovnik_trojic = {}
    for klic in slovnik_dvojic:
        slovnik_trojic[klic] = (slovnik_dvojic[klic], frekvence_vet[klic])   
    #print(dict(sorted(slovnik_trojic.items()))) # seřazený slovník podle klíčů, pozor na seřazování slovníku, je ošemetné

    # výsledný seznam n-tic, každá obsahuje 3 základní infa: (šel by z toho udělat aj slovník případně)
        # nultá pozice = počet klauzí
        # první pozice = počet takto dlouhých vět
        # druhá pozice = průměrná délka takto dlouhých vět
    vysledek = []
    for klic in sorted(slovnik_trojic): # tahá ze seřazeného seznamu klíčů, ale nic nepřepisuje !
        if klic == 0:
            pass
        else:
            prumer = round(Decimal(str(slovnik_trojic[klic][0] / (slovnik_trojic[klic][1] * klic))),2)
            mezivysledek_carka = (klic, slovnik_trojic[klic][1], f"{prumer:n}") # to f"..." dělám proto, aby se převedly korektně desetinné tečky na desetinné čárky
            vysledek.append(mezivysledek_carka)
    print("data pro MAL pro rovinu věta-klauze-slovo:", vysledek)

    # uložení výsledků do tabulky
    with open("data_V_K_S_nazev_souboru.csv", "wt") as csvfile: 
        vysledek_data = csv.writer(csvfile, delimiter=';',lineterminator='\n')
        vysledek_data.writerow(["věta v KL", "frce", "PRŮM ve SL"])
        for i in vysledek:
            vysledek_data.writerow([i[0], i[1], i[2]])
    
    return vysledek

vysledek_data = data_pro_mal()
