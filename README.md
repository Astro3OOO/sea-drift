# Dreifa modelēšanas rīks

Konteineris ir paradzēts jūras objektu dreifa simulācijas palaišanai. Projekts ir veidots uz [OpenDrift](https://opendrift.github.io/) **Pyhton** bibliotēkas bāzes. Ka *input* tas pieņiem JSON konfigurācijas failu un datasetus GRIB vai NetCDF formatā. *output* ir datasets ar kustības trajektoriju, kas ir saglabāta NetCDF formatā.

# Projekta struktūra
```
opendrift-container/
│
├── main.py                     # pamata programma
├── config_verification.py      # JSON faila validācija un sadalīšana uz simulācijas un datu konfigurācijam
├── case_study_tool.py          # simulācijas un datu sagatavošanas funkcijas
│
├── DATA/
│   └── VariableMapping.json    # Iekšeja vārdnīca priekš korektu parametru nosaukumu ielasīšanās
│
├── INPUT/                      # fitktīvais konfigurācijas fails priekš testiem (TO DO)
│   └── input_test.json
│
├── requirements.txt            # Python nepieciešamas paketes
├── Dockerfile                  # Konteinera iestatījumi
├── .dockerignore               # faili, kurus konteineris ignorēs
├── .gitignore                  # faili, kurus Git ignorēs
└── README.md    
```
# Setup & Usage


-image izveidošana:

```docker build -t opendrift-container .```

-konteinera palaišana:

```
docker run \
	-v path/to/host/dataset/folder:/DATASETS \
   	-v path/to/host/config/file.json:/opendrift-container/INPUT/config.json \
	-v path/to/store/results:/OUTPUT \
	opendrift_container python main.py config.json 
``` 
# Konfigurācijas fails

Visām apakšminētām configirācijas atribūtām jābūt apkopotiem viena vienotā JSON failā, piemēram kā: [config.json](INPUT/input_test.json).