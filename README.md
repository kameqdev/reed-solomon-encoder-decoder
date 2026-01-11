# Projekt: Koder i Dekoder Reeda-Solomona RS(255, 223)

Niniejszy projekt to implementacja wydajnego algorytmu korekcji błędów Reeda-Solomona, skonfigurowanego do pracy w standardzie przemysłowym. System potrafi wziąć blok 223 bajtów danych, wygenerować 32 bajty nadmiarowe, a następnie, po stronie odbiorcy, wykryć i skorygować do 16 całkowicie błędnych bajtów w odebranym 255-bajtowym bloku.

---

## Kluczowe Parametry Techniczne

Cała implementacja opiera się na precyzyjnie zdefiniowanej matematyce w ciele skończonym. Poniższe parametry definiują "reguły gry" dla wszystkich operacji kodowania i dekodowania.

| Parametr                 | Wybrana Wartość                | Opis                                                                                                                                                        |
| :----------------------- | :----------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ciało Galois**         | **$GF(2^8)$**                  | **$m=8$**. Oznacza to, że algorytm nie operuje na bitach, lecz na 8-bitowych **symbolach (bajtach)**. Daje to zbiór 256 unikalnych elementów (od 0 do 255). |
| **Zdolność Korekcyjna**  | **$t = 16$**                   | Jest to serce projektu. Oznacza, że dekoder jest w stanie wykryć i **naprawić do 16 dowolnie uszkodzonych bajtów** w bloku.                                 |
| **Wielomian Prymitywny** | **$p(x) = x^8+x^4+x^3+x^2+1$** | Definiuje "reguły mnożenia" w ciele $GF(2^8)$. Jest to standardowy wielomian używany m.in. w **AES** i **kodach QR**.                                       |
| **Reprezentacja Hex**    | `0x11D`                        | Szesnastkowa reprezentacja wielomianu $p(x)$ (bez wiodącego $x^8$), często używana w implementacjach do optymalizacji mnożenia.                             |

---

## Parametry Wynikowe Kodu

Bazując na powyższych ustawieniach, parametry naszego kodu $RS(n, k)$ są następujące:

- **Liczba Symboli Nadmiarowych (Parzystości): $2t$**

  - $2 \times 16 = $**32 symbole (bajty)**.
  - Fundamentalna zasada RS: aby skorygować $t$ błędów, potrzebujemy $2t$ symboli nadmiarowych. Dzieje się tak, ponieważ każdy błąd ma dwie niewiadome: **pozycję** i **wartość**. 32 symbole parzystości pozwalają wygenerować 32 "wskazówki" (syndromy) do rozwiązania tego układu równań.

- **Maksymalna Długość Bloku: $n$**

  - $n = 2^m - 1 = 2^8 - 1 = $**255 symboli (bajtów)**.
  - To całkowity rozmiar bloku przesyłanego przez kanał.

- **Długość Danych (Wiadomości): $k$**
  - $k = n - 2t = 255 - 32 = $**223 symbole (bajty)**.
  - Tyle bajtów "użytkownika" mieści się w jednym bloku kodowym.

### Finalne Oznaczenie Kodu: **RS(255, 223)**

Implementujemy jeden z najpopularniejszych standardów RS, używany powszechnie m.in. w systemach telewizji cyfrowej (DVB) i komunikacji satelitarnej.

---

## Zaimplementowane Algorytmy

Aby zrealizować kodowanie i dekodowanie, projekt implementuje następujące algorytmy:

### 1. Koder `RS(255, 223)`

1.  **Generowanie $g(x)$:** Na starcie obliczany jest **wielomian generatora** $g(x)$. Jest to wielomian stopnia $2t = 32$, którego pierwiastkami są 32 kolejne potęgi $\alpha$ (elementu prymitywnego ciała):
    $$g(x) = (x + \alpha^1)(x + \alpha^2) \cdots (x + \alpha^{32})$$

2.  **Kodowanie (LFSR):** Proces kodowania polega na znalezieniu reszty z dzielenia wielomianu wiadomości $M(x)$ przez $g(x)$. W praktyce jest to implementowane jako szybki **rejestr przesuwny (LFSR)** o długości 32 bajtów:
    - Wiadomość (223 bajty) jest "przepuszczana" przez rejestr.
    - 32 bajty, które pozostają w rejestrze, to obliczone symbole parzystości $P(x)$.
    - Finalny blok $C(x)$ to 223 bajty danych + 32 bajty parzystości.

### 2. Dekoder `RS(255, 223)`

Proces dekodowania jest znacznie bardziej złożony i składa się z 4 głównych etapów:

1.  **Obliczanie Syndromów:**

    - Odebrany blok $R(x)$ jest sprawdzany pod kątem "kontraktu" $g(x)$.
    - Obliczane są **32 syndromy** ($S_1 \dots S_{32}$) poprzez wstawienie 32 pierwiastków $g(x)$ do wielomianu $R(x)$.
    - Jeśli wszystkie syndromy są zerowe, blok jest poprawny. Jeśli nie, przechodzimy dalej.

2.  **Znalezienie Lokalizacji Błędów (BMA):**

    - Zestaw 32 syndromów jest "poszlaką".
    - Implementowany jest **Algorytm Berlekampa-Masseya (BMA)**, który na podstawie syndromów znajduje **Wielomian Lokatora Błędów** ($\Lambda(x)$).

3.  **Znalezienie Wartości Błędów (Chien i Forney):**

    - **Wyszukiwanie Chiena (Chien Search):** Szybko znajduje pierwiastki wielomianu $\Lambda(x)$. Pozycje tych pierwiastków to **dokładne lokalizacje** błędnych bajtów w bloku.
    - **Algorytm Forneya:** Używając syndromów i $\Lambda(x)$, oblicza **dokładne wartości** błędów (np. że na pozycji 42 bajt `0xAA` został pomylony z `0xBB`).

4.  **Korekcja:**
    - Błędy (wartości i pozycje) są odejmowane (XOR) od odebranego bloku $R(x)$.
    - Wynikiem jest idealnie odtworzony, oryginalny blok $C(x)$.

---