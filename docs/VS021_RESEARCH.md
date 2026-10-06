# VS021 source research

Research-only review completed 2026-10-06. Scope: Ecuadorian universities in `data/ecuador_universities.csv`, plus official public research institutes and government organizations likely to recruit researchers, faculty, or academic-adjacent staff. Only official public sources were considered; LinkedIn and third-party job boards not linked as the institution's official recruitment channel were excluded.

Legend:
- GenericHTMLCollector possible: whether the current collector can reasonably read the public listing page without custom code.
- Existing template reusable: whether an existing CareerOS template appears reusable as-is or with narrow configuration overrides.
- Volume estimate: expected annual/current academic or research vacancy flow, not total institutional hiring.

## University review

| Institution | Official recruitment URL | Recruitment platform | GenericHTMLCollector possible | Existing template reusable | Expected vacancy volume | Estimated maintenance | Recommendation |
|---|---|---:|---:|---:|---:|---:|---|
| Escuela Politecnica Nacional | https://www.epn.edu.ec/?s=OFERTA+LABORAL | Institutional WordPress search | Yes | Yes | Medium | Medium | Keep existing collector blocked only by external SSL issue; do not disable SSL. |
| Escuela Superior Politecnica de Chimborazo | https://www.espoch.edu.ec/ | Institutional site/news | No | No | Low | High | Skip until a stable employment/convocatorias index is found. |
| Escuela Superior Politecnica Agropecuaria de Manabi Manuel Felix Lopez | https://www.espam.edu.ec/ | Institutional site/news/PDFs | No | No | Low | High | Skip; no stable public careers listing found. |
| Universidad Central del Ecuador | https://www.uce.edu.ec/ | Faculty/institutional pages | Partial | No | Medium | High | Watch, but skip central collector until a stable central vacancy index is identified. |
| Universidad de Guayaquil | https://www.ug.edu.ec/ | Institutional site/PDFs | No | No | Medium | High | Skip; public calls are document-heavy and not a stable HTML listing. |
| Universidad de Cuenca | https://www.ucuenca.edu.ec/ | Institutional site/PDFs | No | No | Medium | High | Skip unless a current HTML concursos page is exposed. |
| Universidad Nacional de Loja | https://unl.edu.ec/ | Institutional site/news | Partial | No | Low | Medium | Low priority; current official pages mix academic events with non-employment calls. |
| Universidad Tecnica de Manabi | https://www.utm.edu.ec/ | Institutional site/PDFs | No | No | Medium | High | Skip for now; document-heavy recruitment. |
| Universidad Tecnica de Ambato | https://uta.edu.ec/convocatoria-seleccion-personal-academico-no-titular/ | Institutional WordPress + PDFs | Partial | No | Medium | Medium | Candidate, but only if HTML listing links remain stable; do not parse PDFs. |
| Universidad Tecnica de Machala | https://www.utmachala.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no reliable official listing found. |
| Universidad Tecnica Luis Vargas Torres de Esmeraldas | https://www.utelvt.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment page found. |
| Universidad Tecnica de Babahoyo | https://www.utb.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable official recruitment listing found. |
| Universidad Tecnica Estatal de Quevedo | https://www.uteq.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable official recruitment listing found. |
| Universidad Tecnica del Norte | https://www.utn.edu.ec/ | Institutional site/news/PDFs | No | No | Low | High | Skip until a central HTML vacancy index is available. |
| Universidad Laica Eloy Alfaro de Manabi | https://www.uleam.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; source discovery needed later. |
| Universidad Estatal de Bolivar | https://www.ueb.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment page found. |
| Universidad Agraria del Ecuador | https://www.uagraria.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment page found. |
| Universidad Nacional de Chimborazo | https://www.unach.edu.ec/ | Institutional WordPress/news | Yes | No | High | Medium | Top candidate; homepage/news feed exposes repeated academic hiring calls as HTML links. |
| Universidad Tecnica de Cotopaxi | https://www.utc.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable public recruitment listing found. |
| Escuela Superior Politecnica del Litoral | https://www.espol.edu.ec/es/concurso-meritos-2026 | Institutional HTML table | Yes | Yes | Medium | Medium | Keep existing collector; official contest page is suitable when active. |
| Universidad Andina Simon Bolivar | https://www.uasb.edu.ec/ | Institutional site/isolated PDFs | Partial | No | Low | High | Monitor; isolated professor contests exist, but no stable employment listing found. |
| Universidad Estatal Peninsula de Santa Elena | https://www.upse.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable official recruitment listing found. |
| Universidad Estatal de Milagro | https://www.unemi.edu.ec/ | Institutional site/news | No | No | Medium | High | Skip pending a stable public employment index. |
| Universidad Estatal del Sur de Manabi | https://www.unesum.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Facultad Latinoamericana de Ciencias Sociales FLACSO | https://www.flacso.edu.ec/es/concurso_meritos_oposicion_sociologia_2026 | Institutional HTML contest pages | Partial | No | Medium | Medium | Candidate if a discoverable contest index/search page is used; individual pages are clean HTML. |
| Instituto de Altos Estudios Nacionales IAEN | https://www.iaen.edu.ec/convocatorias/ | Institutional HTML + registration portal | Yes | No | Low | Low | Candidate; clean HTML call for docente bank, but volume is low. |
| Universidad Estatal Amazonica | https://www.uea.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable official recruitment listing found. |
| Universidad Intercultural de las Nacionalidades y Pueblos Indigenas Amawtay Wasi | https://www.uaw.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment page found. |
| Universidad Politecnica Estatal del Carchi | https://www.upec.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment page found. |
| Universidad de las Fuerzas Armadas ESPE | https://uth.espe.edu.ec/concurso-de-meritos/ | Institutional HTML | Yes | Existing custom collector | Medium | Medium | Already implemented; future migration to GenericHTML optional, not necessary now. |
| Universidad Regional Amazonica Ikiam | https://www.ikiam.edu.ec/index.php/trabaja-con-nosotros/ | Institutional WordPress careers page | Yes | No | High | Medium | Top candidate; official careers page lists academic and support-academic roles. |
| Universidad de Investigacion de Tecnologia Experimental Yachay | https://www.yachaytech.edu.ec/ | Institutional site/news | No | No | Medium | High | Investigate further later; likely valuable but no stable public listing confirmed. |
| Universidad de las Artes | https://www.uartes.edu.ec/sitio/en/trabaja-en-la-uartes/ | Institutional WordPress downloads/listing | Partial | No | High | High | Candidate with caution: high volume, but many links are download/result notices and current LinkFilter may reject `/download/` URLs. |
| Universidad Nacional de Educacion | https://www.unae.edu.ec/ | Institutional site/news | No | No | Medium | High | Skip until stable public calls page is located. |
| Universidad de Seguridad Ciudadana y Ciencias Policiales | https://www.usecipol.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad Publica de Santo Domingo de los Tsachilas | https://www.upsd.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Pontificia Universidad Catolica del Ecuador | https://cisealpuce.edu.ec/nosotros/trabajo.html | Institutional HTML/PDF links | Yes | Yes | Low | Medium | Keep existing collector; official source is narrow and may often return zero. |
| Universidad Catolica de Santiago de Guayaquil | https://www.ucsg.edu.ec/ | Institutional site/form/news | No | No | Low | High | Skip; no stable institutional vacancy listing found. |
| Universidad Catolica de Cuenca | https://www.ucacue.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad Laica Vicente Rocafuerte de Guayaquil | https://www.ulvr.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad Tecnica Particular de Loja | https://utpl.hiringroom.com/jobs | HiringRoom | Yes | Yes | High | Low | Keep existing collector; reusable HiringRoom template. |
| Universidad UTE | https://www.ute.edu.ec/ | Institutional site/news/forms | No | No | Low | High | Skip; no stable public vacancy listing found. |
| Universidad del Azuay | https://www.uazuay.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad Politecnica Salesiana | https://www.ups.edu.ec/ | Institutional site/external docs | No | No | Low | High | Skip; no reliable official listing found. |
| Universidad Particular Internacional SEK | https://uisek.edu.ec/personal/trabaja-con-nosotros/ | Institutional form | No | No | Low | Low | Skip for GenericHTML; form-only, no vacancy listing. |
| Universidad de Especialidades Espiritu Santo | https://www.uees.edu.ec/ | Institutional site/form | No | No | Low | High | Skip; no stable public listing found. |
| Universidad San Francisco de Quito | https://www.usfq.edu.ec/es/trabaja-con-nosotros/vacantes-abiertas | Institutional HTML vacancy cards | Yes | Yes | Medium | Low | Keep existing collector; strong official HTML source. |
| Universidad de Las Americas | https://empleos.udla.edu.ec/search/?q=&locationsearch= | SAP SuccessFactors | Yes | Yes | High | Low | Keep existing collector; reusable SAP SuccessFactors template. |
| Universidad Internacional del Ecuador | https://www.uide.edu.ec/ | Institutional site/forms/news | No | No | Low | High | Skip; no stable institutional hiring listing confirmed. |
| Universidad Regional Autonoma de Los Andes | https://www.uniandes.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad del Pacifico Escuela de Negocios | https://www.upacifico.edu.ec/ | Institutional site/contact | No | No | Low | High | Skip; no public vacancy listing found. |
| Universidad Tecnologica Indoamerica | https://www.uti.edu.ec/ | Institutional site/news/forms | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad Casa Grande | https://www.casagrande.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad Tecnologica Empresarial de Guayaquil | https://www.uteg.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad Tecnologica Israel | https://www.uisrael.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad de Especialidades Turisticas | https://www.uet.edu.ec/ | Institutional site/contact | No | No | Low | High | Skip; no public vacancy listing found. |
| Universidad Metropolitana | https://www.umet.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad de Otavalo | https://www.uotavalo.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad San Gregorio de Portoviejo | https://www.sangregorio.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad de Los Hemisferios | https://www.uhemisferios.edu.ec/ | Institutional site/contact; occasional external notices | No | No | Low | High | Skip; no public vacancy listing, though official contact/email hiring may occur. |
| Universidad Iberoamericana del Ecuador | https://www.unibe.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad Tecnologica ECOTEC | https://www.ecotec.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |
| Universidad del Rio | https://www.udr.edu.ec/ | Institutional site/contact | No | No | Low | High | Skip; no public recruitment listing found. |
| Universidad Bolivariana del Ecuador | https://www.ube.edu.ec/ | Institutional site/news | No | No | Low | High | Skip; no stable recruitment listing found. |

## Research institutes and government research organizations

| Institution | Official recruitment URL | Recruitment platform | GenericHTMLCollector possible | Existing template reusable | Expected vacancy volume | Estimated maintenance | Recommendation |
|---|---|---:|---:|---:|---:|---:|---|
| Instituto Nacional de Biodiversidad (INABIO) | https://inabio.biodiversidad.gob.ec/ | Institutional site/news | No | No | Low | High | Monitor; no stable employment listing found. |
| Instituto Nacional de Investigaciones Agropecuarias (INIAP) | https://www.iniap.gob.ec/ | Institutional site/news | No | No | Medium | High | Valuable domain, but skip until an official opportunities page is found. |
| Instituto Nacional de Investigación en Salud Pública (INSPI) | https://www.investigacionsalud.gob.ec/ | Government institutional site | No | No | Medium | High | Monitor; hiring likely occurs through government channels, not a stable HTML listing. |
| Instituto Nacional de Meteorología e Hidrología (INAMHI) | https://www.inamhi.gob.ec/administracion-de-recursos-humanos/ | HR information page | No | No | Low | Medium | Skip; HR page is informational, not vacancies. |
| Instituto Geográfico Militar (IGM) | https://www.geoportaligm.gob.ec/ | Government institutional site | No | No | Low | High | Skip; no official recruitment listing found. |
| Instituto Oceanográfico y Antártico de la Armada (INOCAR) | https://www.inocar.mil.ec/web/ | Government institutional site/news | No | No | Low | High | Skip; public calls found are not stable employment listings. |
| CIESPAL | https://ciespal.org/ | Institutional site/news | No | No | Low | High | Monitor only; no stable employment listing found. |
| SENESCYT | https://www.educacionsuperior.gob.ec/ | Government institutional site | No | No | Low | High | Skip for CareerOS jobs; not a regular academic vacancy source. |
| Ministerio del Trabajo - Encuentra Empleo | https://encuentraempleo.trabajo.gob.ec/ | Government employment platform | No | No | Medium | High | Do not integrate via GenericHTML; broad job platform, not institution-specific academic source. |

## Top 15 implementation candidates

1. Universidad Tecnica Particular de Loja — HiringRoom — high volume, existing template, low maintenance.
2. Universidad de Las Americas — SAP SuccessFactors — high volume, existing template, low maintenance.
3. Universidad Nacional de Chimborazo — Generic HTML — high academic-call volume, official HTML links.
4. Universidad Regional Amazonica Ikiam — Generic HTML — high relevance, dedicated official careers page.
5. Universidad San Francisco de Quito — Generic HTML — already configured, good official vacancy cards.
6. Universidad de las Artes — Generic HTML/download listing — high volume, but needs careful filtering around result notices and `/download/` URLs.
7. Escuela Superior Politecnica del Litoral — Generic HTML table — official academic contest page.
8. Escuela Politecnica Nacional — Generic HTML search — good source once external SSL issue is resolved normally.
9. Universidad Tecnica de Ambato — Generic HTML/PDF listing — recurring academic calls, moderate maintenance.
10. FLACSO Ecuador — Generic HTML contest pages — valuable academic roles; needs stable index/search entry point.
11. IAEN — Generic HTML — clean docente-bank page, lower volume.
12. Pontificia Universidad Catolica del Ecuador — Generic HTML/PDF links — already configured but narrow source.
13. Universidad Central del Ecuador — Generic HTML if a central source emerges — likely volume, currently fragmented.
14. Universidad Andina Simon Bolivar — Generic HTML if a listing emerges — high-value roles, currently isolated PDF calls.
15. Yachay Tech — source discovery candidate — likely high value if official vacancy page is found.

## Grouped by reusable platform

### Existing reusable templates

| Platform/template | Sources |
|---|---|
| HiringRoom vacancy cards | UTPL |
| SAP SuccessFactors job results | UDLA |
| Existing institutional generic templates | USFQ, PUCE, ESPOL, EPN |

### New reusable Generic HTML patterns worth creating

| Pattern | Candidate sources | Notes |
|---|---|---|
| WordPress/news academic-call links | UNACH, UTA, possibly UCE/UNL later | Filter aggressively for `docente`, `personal académico`, `apoyo académico`, and exclude mobility, scholarships, student calls. |
| Dedicated WordPress careers lists | Ikiam | Reusable if more Ecuadorian universities expose simple careers pages. |
| WordPress download-manager listings | UArtes | High-value but conflicts with current download/PDF blocking semantics; treat as a special GenericHTML configuration only if source links resolve to HTML detail pages. |
| HTML contest/detail pages | FLACSO, IAEN | Low structural complexity, but discovery/index stability is the main risk. |

### Platforms not confirmed as official university sources

| Platform | Finding |
|---|---|
| Magneto | No official Ecuadorian university recruitment source confirmed in this pass. |
| HiringRoom | Confirmed for UTPL; no additional university source confirmed. |
| SAP SuccessFactors | Confirmed for UDLA; no additional university source confirmed. |
