"""
Kukonharjun Psykologinen Vibe-analyysi - kaynnistysskripti.

Kaynnista sovellus komennolla:

    python run.py

Sovellus on talloin kaytettavissa osoitteessa http://<taman-koneen-ip>:8000
kaikille samassa (mokin) WiFi-verkossa oleville laitteille.
"""
import socket

import uvicorn

from app.config import ADMIN_TOKEN, HOST, PORT


def _local_ip() -> str:
    """Arvaa taman koneen paikallisverkko-osoitteen ilman ulkoista internet-yhteytta."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # UDP "connect" ei laheta paketteja - se vain kysyy kayttojarjestelmalta,
        # mita verkkokorttia kaytettaisiin. Toimii siis myos ilman nettiyhteytta,
        # kunhan paikallisverkko (WiFi-reititin) on paalla.
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    ip = _local_ip()
    print("=" * 64)
    print("  Kukonharjun Psykologinen Vibe-analyysi v4.2")
    print("=" * 64)
    print(f"  Osallistujille (QR-koodi taman osoitteen ymparille):")
    print(f"    http://{ip}:{PORT}")
    print()
    print(f"  Admin-paneeli (pida salassa):")
    print(f"    http://{ip}:{PORT}/admin/{ADMIN_TOKEN}")
    print("=" * 64)
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
