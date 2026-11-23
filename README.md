# Secure Chat Hub

Homepage pokazuje dostępność pokoju i otwiera go z kafelka **Czat**. Panel działa pod `/`, pokój pod `/chat/`, a wiadomości płyną przez `/chat/ws`. Link **← Panel** prowadzi z pokoju z powrotem na stronę główną. Caddy obsługuje oba serwisy pod tym samym adresem. Hasło pokoju jest wymagane również po zalogowaniu przez Cloudflare Access.

## Wdrożenie lokalne

Potrzebujesz Docker Engine z wtyczką Compose v2.20 lub nowszą albo Docker Desktop z kontenerami Linux. Poniższe polecenia wykonuj w Bash, np. w terminalu Linux, macOS lub WSL. Na komputerze z Windows możesz potem otworzyć panel w zwykłej przeglądarce.

1. Pobierz projekt i otwórz katalog zawierający `compose.yaml`. Jeśli pobierasz paczkę ZIP, najpierw ją rozpakuj. Aby sklonować repozytorium do katalogu `secure-chat-hub`, wykonaj:

   ```bash
   git clone https://github.com/commummy83-blip/empty.git secure-chat-hub
   cd secure-chat-hub
   ```
2. Przy pierwszej instalacji przygotuj prywatny plik konfiguracji.

   ```bash
   umask 077
   cp -n .env.example .env
   openssl rand -hex 24
   ```

   Wpisz wygenerowaną wartość po `CHAT_PASSWORD=` w pliku `.env`. Udostępnij ją uczestnikom pokoju. Minimalna długość to 12 znaków. Plik `.env` jest pomijany przez Git.
3. Zbuduj i uruchom kontenery.

   ```bash
   docker compose config --quiet
   docker compose up -d --build --wait
   docker compose ps
   curl -fsS http://127.0.0.1:8080/chat/healthz
   ```

   Oczekiwana odpowiedź to `{"status":"ok"}`. Jeśli port 8080 jest zajęty, zmień `LOCAL_PORT` w `.env`, ponownie wykonaj `docker compose up -d` i użyj nowego portu w adresie panelu.

4. Otwórz [panel lokalny](http://127.0.0.1:8080/), wybierz **Czat**, wpisz pseudonim i hasło. W drugim oknie użyj innego pseudonimu. Wyślij wiadomość z pierwszego okna i sprawdź jej odbiór w drugim. Kliknij **← Panel**, wróć do pokoju i sprawdź historię.

Port wejściowy jest przypisany do `127.0.0.1`. Na zdalnym serwerze możesz sprawdzić panel ze swojego komputera przez `ssh -L 8080:127.0.0.1:8080 użytkownik@serwer`, a potem otworzyć ten sam adres lokalny.

## Dostęp przez HTTPS i Cloudflare Tunnel

Wariant zdalny wymaga domeny obsługiwanej przez Cloudflare i konta Zero Trust. W poniższych krokach zastąp `panel.example.org` własną nazwą hosta.

1. W Cloudflare Zero Trust dodaj aplikację **Access → Applications → Self-hosted** dla całego hosta `panel.example.org`. Dodaj regułę **Allow** dla wybranych użytkowników lub grup oraz wybierz metodę logowania. Pozostaw pole ścieżki puste, aby ochrona objęła panel, czat i połączenia WebSocket. [Instrukcja Cloudflare Access](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/)
2. Utwórz zdalnie zarządzany Cloudflare Tunnel lub wybierz istniejący przeznaczony dla tej instalacji. W konfiguracji tunelu dodaj trasę publikowanej aplikacji z nazwą `panel.example.org`, typem **HTTP** i adresem usługi `gateway:8080`. Kontener tunelu rozwiązuje nazwę `gateway` w sieci Compose. [Konfiguracja tras Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/)
3. W `.env` ustaw `PUBLIC_HOST=panel.example.org` i dodaj `CLOUDFLARE_TUNNEL_TOKEN=` z tokenem tego tunelu. Zachowaj dotychczasowe `CHAT_PASSWORD`. Jeśli migrujesz ruch z dotychczasowej instalacji, najpierw sprawdź nowy stos na osobnym hoście i tunelu. Konektory jednego tunelu muszą mieć dostęp do tych samych usług.
4. Uruchom stos z nakładką tunelu.

   ```bash
   docker compose -f compose.yaml -f compose.tunnel.yaml config --quiet
   docker compose -f compose.yaml -f compose.tunnel.yaml up -d --build --wait
   docker compose -f compose.yaml -f compose.tunnel.yaml logs --tail=50 cloudflared
   ```

5. W prywatnym oknie otwórz `https://panel.example.org/chat/`. Pierwszy ekran powinien wymagać logowania do Access. Po zalogowaniu sprawdź kafelek na stronie głównej, hasło pokoju i wymianę wiadomości w dwóch oknach. Wejście do pokoju bez logowania do Access oznacza, że trzeba poprawić zakres aplikacji lub politykę dostępu.

## Obsługa

| Objaw lub zadanie | Co sprawdzić |
| --- | --- |
| Panel zgłasza odrzucony host | Ustaw `PUBLIC_HOST` na nazwę używaną przez przeglądarkę, bez schematu i ścieżki. Zastosuj konfigurację poleceniem `up -d` z plikami wybranego wariantu. |
| Kafelek wskazuje niedostępny czat albo brama zwraca 502 | Sprawdź `docker compose ps`, `docker compose logs --tail=50 chat gateway homepage` oraz adres `/chat/healthz`. Usługa czatu wymaga hasła o długości co najmniej 12 znaków. |
| Strona pokoju otwiera się, ale połączenie nie dochodzi do skutku | W narzędziach sieciowych przeglądarki sprawdź żądanie `/chat/ws` i kod zmiany protokołu 101. W tunelu zweryfikuj trasę do `gateway:8080`, dostęp dla całego hosta i obsługę WebSocket w domenie. |
| Zmiana hasła lub aktualizacja kodu | Zmień `.env` lub pobierz nową wersję kodu i ponownie wykonaj polecenie `up -d --build --wait` dla wybranego wariantu. Odtworzenie kontenera czatu rozłączy użytkowników i wyczyści historię pokoju. |
| Zatrzymanie | Lokalnie wykonaj `docker compose down`. Dla tunelu użyj `docker compose -f compose.yaml -f compose.tunnel.yaml down`. |
| Kopia konfiguracji | Zachowaj pliki projektu i osobną, prywatną kopię `.env`. Czat przechowuje do 100 ostatnich zdarzeń, w tym wejścia i wyjścia, w pamięci jednego procesu. |

## Panel i zgodność ze źródłami

Projekt łączy [secure_dashboard_chat](https://github.com/commummy83-blip/secure_dashboard_chat) oraz [webchat](https://github.com/commummy83-blip/webchat). Z panelu pochodzą widżety zasobów, wyszukiwarka, zegar i odnośnik do Cloudflare. Własne adresy Portainera i routera można włączyć w `homepage/config/services.yaml`. Kafelek czatu sprawdza bezpośrednio jego endpoint zdrowia. Domyślna instalacja obywa się bez dostępu panelu do gniazda Docker i bez zewnętrznej sieci Compose.

Oryginalny czat można też uruchomić samodzielnie. W katalogu `chat/` utwórz środowisko Python 3.11+, zainstaluj `python -m pip install -r requirements.txt` i uruchom `python webchat.py --expose local`. Program wyświetli adres i losowe hasło. Nadal obsługuje tryby `tailscale`, `funnel` i `cloudflare`, które wymagają odpowiednio skonfigurowanych narzędzi na hoście. Kontener używa osobnego punktu startowego i hasła z konfiguracji Compose.
