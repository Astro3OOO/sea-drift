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
├── INPUT/                      
│   └── input_test.json			# fitktīvais konfigurācijas fails priekš conteinera testa
│
├── tests/                     
│   └── test_functions.py		# galveno funkciju testi: konfigu verificēšanas, datu sagatavošanas un simulaciju palaišanas korektības pārbaude.  
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

- **OBLIGĀTIE**
	- *model* - modeļu veids, viens no dotiem: OceanDrift, Leeway vai ShipDrift. [`str`]
	- *start_position* - sākuma pozicijas koordinātes. Saraksts ar garumu 2, kur pirmā vietā ir `Latitude` un otrā `Longitude`. Garumam un platumam var būt gan `float` gan sraksti ar `float`, tomēr ir obligāti, lai izmēri sarakstiem sakrīt. Pie tam, ja turpmāk ir izvēlets `"seed_type" = "cone"`, tad obligāti lai katra coordinate sastāv tieši no divām vertībam (līnija sākumpunkts un beigu punkts). [`list`] 
	- *start_t* - sakuma laiks, kas ir ielasmas ar `pandas.to_datetime`. piemēram : `2025-12-08 11:00:00`. [`str`]
	- *end_t* - beigu laiks, kas ir ielasmas ar `pandas.to_datetime`. piemēram : `2025-12-31 12:00:00`. [`str`]
- **DATA RELATED**
	- *vocabulary* - vārdnīca, kur parametra vārdam no pievienota datatseta tiek piekārtots atbilstošais standarta CF nosaukums. [`dict`]
	- *folder* - pēc nokulsējumja tas ir '/DATASETS'. Tas ir konteinera iekšēja mape, kas veidojas palaišanas laikā. Tai talāk tiek piemantota jebukra lokāla hosta mape. Mapei ir jāsastāv no `GRIB` vai `NetCDF` failiem, kas nav atsevišķ jānorada. [`str`]
		- *concatenation* - pēc izvēles, var piemantot mapi ar apakšmapēm un ieslēgt doto opciju. Pieņiem vertības `True` vai `False`, pēc noklusējuma ir `False`. Piemēram, gadījuma ja ir jāpalaiž ilga simulācija (vairāk par vienu vidēji ilgo prognozes ranu), tad var sadalīt visas lidzīgas prognozes pa apakšmapēm, un sakombinēt tos. Piemēram, sadalīt mapēs : wave-model, atmospheric-model. Tad ar šo opciju datu faili no katras mapes būs sašūti kopā pa vienu datasetu atbilstoši katrai mapei. ['bool']  
	- *copernicus* - var datus ielasīt arī no copernicus marine datubāzes ar API pieslēgšanu. Pagaidām var paņemt datus vai no Baltijas jūras modeļa, vai no globāla modeļa. Lai to izdarītu, vajag ieslēgt šo opciju ar `True` vērtību. Pēc noklusējuma tā ir izslēgta. [`bool`]
		- *border* - saraksts ar apskatāma apgabala robežu. Pēc noklusējuma tas ir [54, 62, 13, 30], kas ir atbilstoši [min_lat, max_lat, min_lon, max_lon]. [`list`]
		- *user* - username priekš piekļuves copernicus marine kontam. Pagaidām nav droši uzprogramēts, login credential netiek šifrēti. [`str`]
		- *pword* - parole, priekš piekļuves copernicus marine kontam.
- **SIMULĀCIJAS**
	- *num* - simulēto daļiņu skaits. Tam jābūt veselam pozitīvam skaitlim. Pēc noklusējuma tas ir 100. [`int`]
	- *seed_type* - ir pieejami divi punktu izvietošnas veidi: 'elements' un 'cone'.Pēc noklusējuma tas ir 'elemnets', kas sēj daļiņas ka atsevišķus punktus. [`str`]
	- *rad* - punktu dispersijas rādiuss apkārt izvēlēt sākumpunkta. Ja ir izvēlēts 'elemnts' ka *seed_type* parametrs, tad radiuss var būt vai no vesels pozitīvs skaitlis, vai saraksts ar garumu vienādu ar `Latitude` un `Longitude` sarakstu garumiem. Ja ir izvēlēts 'cone', tad radiuss var būt vai nu viens pozitīvs vesels skaitlis, vai srakasts ar dieviem skaitļiem. Piemērma konuss ar rad = [0, 1000] izviedo sākuma punktu kopu, kur pie pirmā pinktu būs daļiņu izklēdie 0m un pie pedēja izklēde būs 1000m. Pēc noklusējuma vērtība radiusam ir 0 metri. [`int`] vai [`list`] ar [`int`]. 
	- *backtracking* - var pieslēgt šo opciju ar `True` vērtību, bet tad ***OBLIGĀTI*** sākuma laikam jābūt lielākam par beigu laiku un *time_step* juābūt negatīvam. Pēc noklusējuma šī opcija ir izslēgta. [`bool`]
	- *time_step* - var noradīt simulācijas laiak soli sekundēs. Skaitļim jābūs veselam. Pēc noklusējuma, tas ir 1800 sekundes (30 min), bet var palielināt un samazināt. Ir atļauta negatīva vertība, tikai ja ir ieslēgts *backtracking* ar `True` vēretību un sākuma laiks ir pirms beigu laika. [`int`]
- **MODĒĻU IESTATĪJUMI**
	- *wdf* - vēja dreifa faktors, kas ir nosakošais parametrs OceanDrift modelim. Tam jābūt intervālā no 0 līdz 1. Pēc nokjlusējuma tas ir 0.02 jeb 2%, kas nozīmē, ka objekts parvietojas ar 2% ātrumu no vēja atruma. [`float`]
	- *lw_obj* - Leeway objektu numurs, no 1 līdz 85. [Leeway objektu saraksts](https://github.com/OpenDrift/opendrift/blob/master/opendrift/models/OBJECTPROP.DAT). Pēc noklusējuma tas ir 1. [`int`]
	- *ship* - nosakošais parametrs priekš ShipDrift modeļa. Tas ir 4 vērtību saraksts ar kuģu izmēriem [length, beam, height, draft] metros, pēc noklusējuma tas ir [62, 8, 10, 5]. [`list`]
		- *orientation* - kuģu priekšejas daļas orientācija pret vēju. Var būt 'left', 'right' un 'random'. Pēc noklusejuma tas ir 'random', kas nozīme, ka use no objektiem būs ar kreiso un puse būs ar labo sāni pret vēju. [`str`]
- **PAPILDUS**
	- *configurations* - var pievienot papildus simulācijas konfigurācijas no [saraksta](https://lvgmc.sharepoint.com/:x:/s/KSMN/IQCL8Fl45boXSbFMqqSm7mWGAXYaslD0hSFFY1kOkYhtdfU?e=grtsTH). [`dict`]
	- *file_name* - var pievienot *output* faila nosaukumu. Ja nav noradīts, tad tas tiek ģenerēts automātiski: '{model}_{start_time}_{now_time}.nc'. [`str`]