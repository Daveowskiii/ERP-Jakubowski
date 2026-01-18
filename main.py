import json
from datetime import datetime

# --- 1. TŘÍDY PRO DATA ---
class Polozka:
    def __init__(self, nazev, cena, datum, pocet):
        self.nazev = nazev
        self.cena = cena
        # Datum musíme převést z textu na "čas", abychom mohli porovnávat stáří
        self.datum = datetime.strptime(datum, "%Y-%m-%d")
        self.pocet = pocet

# --- 2. STRATEGIE (LOGIKA VÝPOČTU) ---
class Strategie:
    """Rodičovská třída pro strategie."""
    def vypocitat(self, polozky, mnozstvi):
        pass

class StrategieFIFO(Strategie):
    """Metoda FIFO: Prodáváme od nejstaršího data."""
    def vypocitat(self, polozky, mnozstvi):
        # Seřadíme od nejmenšího data (nejstarší)
        serazene = sorted(polozky, key=lambda x: x.datum)
        
        cena_celkem = 0
        zbyva_odebrat = mnozstvi
        
        for p in serazene:
            if zbyva_odebrat <= 0: break
            
            # Vezmeme buď vše, co je ve várce, nebo jen zbytek do objednávky
            kolik_vezmu = min(p.pocet, zbyva_odebrat)
            
            cena_celkem = cena_celkem + (kolik_vezmu * p.cena)
            zbyva_odebrat = zbyva_odebrat - kolik_vezmu
            
        return cena_celkem

class StrategieLIFO(Strategie):
    """Metoda LIFO: Prodáváme od nejnovějšího data."""
    def vypocitat(self, polozky, mnozstvi):
        # Seřadíme OBRÁCENĚ (reverse=True) -> od nejnovějšího
        serazene = sorted(polozky, key=lambda x: x.datum, reverse=True)
        
        # Výpočet je stejný, jen pracujeme s jinak seřazeným seznamem
        cena_celkem = 0
        zbyva_odebrat = mnozstvi
        
        for p in serazene:
            if zbyva_odebrat <= 0: break
            
            kolik_vezmu = min(p.pocet, zbyva_odebrat)
            cena_celkem = cena_celkem + (kolik_vezmu * p.cena)
            zbyva_odebrat = zbyva_odebrat - kolik_vezmu
            
        return cena_celkem

# --- 3. SPRÁVA SKLADU A OBJEDNÁVKY ---
class Sklad:
    def __init__(self, soubor):
        self.zasoby = []
        try:
            with open(soubor, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for d in data:
                    item = Polozka(d['nazev'], d['cena_za_kus'], d['datum_naskladneni'], d['pocet_kusu'])
                    self.zasoby.append(item)
        except FileNotFoundError:
            print("CHYBA: Soubor sklad.json nebyl nalezen.")

    def najdi_zbozi(self, nazev):
        # Vrátí seznam položek, které mají zadaný název
        return [p for p in self.zasoby if p.nazev == nazev]
    
    def dej_nazvy_zbozi(self):
        # Získá unikátní názvy zboží pro menu (aby se neopakovaly)
        nazvy = set()
        for p in self.zasoby:
            nazvy.add(p.nazev)
        return sorted(list(nazvy))

class Objednavka:
    def __init__(self, sklad):
        self.sklad = sklad

    def zjistit_cenu(self, nazev, mnozstvi, strategie):
        polozky = self.sklad.najdi_zbozi(nazev)
        
        # Kontrola, jestli máme dost kusů
        celkem_ks = sum(p.pocet for p in polozky)
        if celkem_ks < mnozstvi:
            print(f"  ! POZOR: Chcete {mnozstvi} ks '{nazev}', ale na skladě je jen {celkem_ks}.")
            return 0
        
        # Pokud je vše OK, spočítáme cenu
        return strategie.vypocitat(polozky, mnozstvi)

# --- 4. HLAVNÍ PROGRAM (INTERAKTIVNÍ) ---
if __name__ == "__main__":
    sklad = Sklad("sklad.json")
    objednavka = Objednavka(sklad)
    seznam_zbozi = sklad.dej_nazvy_zbozi()

    print("--- Vítejte v ERP systému ---")
    
    # Seznam, kam si uživatel "hází" zboží
    kosik = []

    # Cyklus nákupu
    while True:
        print("\nCo chcete přidat do košíku?")
        for i, nazev in enumerate(seznam_zbozi):
            print(f"{i + 1}. {nazev}")
        print("0. Zaplatit a ukončit")
        
        volba = input("Vaše volba (číslo): ")
        
        if volba == "0":
            break # Ukončíme nákup
            
        try:
            cislo = int(volba) - 1 # Uživatel píše 1, my počítáme od 0
            if cislo >= 0 and cislo < len(seznam_zbozi):
                vybrany_nazev = seznam_zbozi[cislo]
                pocet_vstup = input(f"Kolik kusů '{vybrany_nazev}' chcete? ")
                mnozstvi = int(pocet_vstup)
                
                if mnozstvi > 0:
                    kosik.append([vybrany_nazev, mnozstvi])
                    print("--> Přidáno do košíku.")
                else:
                    print("Množství musí být větší než 0.")
            else:
                print("Neplatné číslo zboží.")
        except ValueError:
            print("Chyba: Musíte zadat celé číslo!")

    # --- Rekapitulace a výpočet ---
    print("\n" + "="*30)
    print("REKAPITULACE OBJEDNÁVKY")
    
    celkem_fifo = 0
    celkem_lifo = 0
    
    for polozka_v_kosiku in kosik:
        nazev = polozka_v_kosiku[0]
        pocet = polozka_v_kosiku[1]
        
        # Spočítáme cenu oběma způsoby
        cena_fifo = objednavka.zjistit_cenu(nazev, pocet, StrategieFIFO())
        cena_lifo = objednavka.zjistit_cenu(nazev, pocet, StrategieLIFO())
        
        celkem_fifo += cena_fifo
        celkem_lifo += cena_lifo
        
        print(f"{pocet}x {nazev} | FIFO: {cena_fifo} Kč | LIFO: {cena_lifo} Kč")
        
    print("="*30)
    print(f"CENA CELKEM (FIFO): {celkem_fifo} Kč")
    print(f"CENA CELKEM (LIFO): {celkem_lifo} Kč")
    print("="*30)
    
    input("Stiskněte Enter pro konec...")